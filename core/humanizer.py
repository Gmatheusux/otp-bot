"""
core/humanizer.py — Limites humanos para tudo que o bot aperta ou clica.

Uma pessoa tem um par de mãos: todas as entradas (teclas e cliques) passam por aqui e
respeitam o mesmo teto de ações por minuto, um intervalo mínimo entre entradas e um
tempo de reação a cada novidade na tela. Os tempos seguem distribuições (lognormal /
gaussiana) e mudam de sessão para sessão (ritmo do dia) e ao longo da sessão (cansaço).
Nenhum tempo é fixo e nenhum fica abaixo do que uma pessoa rápida consegue fazer.
"""
import asyncio
import math
import random
import time
from collections import deque
from dataclasses import dataclass, replace
from typing import Deque, Dict, Optional, Tuple


@dataclass(frozen=True)
class HumanProfile:
    reaction_ms: float = 240.0        # mediana do tempo de reação a algo novo na tela
    reaction_min_ms: float = 160.0    # ninguém reage mais rápido que isso de forma consistente
    reaction_max_ms: float = 900.0
    key_hold_ms: float = 75.0         # tempo que a tecla fica apertada
    key_hold_sd_ms: float = 18.0
    gap_ms: float = 150.0             # mediana do intervalo entre duas entradas seguidas
    gap_min_ms: float = 80.0
    max_apm: float = 180.0            # teto de ações por minuto (janela de 60 s)
    cooldown_jitter_pct: float = 12.0  # recargas: sempre um pouco ACIMA do configurado, nunca abaixo
    hesitation: bool = True           # às vezes "pensa" 0,6–2,5 s antes de reagir
    hesitation_chance: float = 0.05   # ~1 em cada 20 reações
    session_spread: float = 0.07      # ritmo do dia: fator de velocidade ~ N(1, 0.07)
    fatigue_per_hour: float = 0.06    # fica ~6% mais lento por hora, até 18%

    @classmethod
    def from_config(cls, cfg: Optional[Dict]) -> "HumanProfile":
        cfg = cfg or {}
        base = cls()
        return replace(
            base,
            reaction_ms=max(base.reaction_min_ms, float(cfg.get("reaction_ms", base.reaction_ms))),
            max_apm=min(300.0, max(30.0, float(cfg.get("max_apm", base.max_apm)))),
            cooldown_jitter_pct=min(50.0, max(0.0, float(cfg.get("cooldown_jitter_pct", base.cooldown_jitter_pct)))),
            hesitation=bool(cfg.get("hesitation", base.hesitation)),
        )


class Humanizer:
    def __init__(self, profile: HumanProfile = HumanProfile(), rng: Optional[random.Random] = None,
                 clock=time.monotonic, sleep=asyncio.sleep, instant: bool = False):
        self.profile = profile
        self._rng = rng or random.Random()
        self._clock = clock
        self._sleep = sleep
        self._instant = instant
        self._started = clock()
        self._last_input = float("-inf")
        self._inputs: Deque[float] = deque()
        self._lock = asyncio.Lock()
        # Ritmo do dia: sorteado uma vez por sessão
        self.session_speed = min(1.15, max(0.87, self._rng.gauss(1.0, profile.session_spread)))

    @classmethod
    def instant(cls) -> "Humanizer":
        """Sem esperas: para testes."""
        return cls(instant=True)

    def set_profile(self, profile: HumanProfile):
        self.profile = profile

    # ------------------------------------------------------------ tempos

    def _pace(self) -> float:
        """Multiplicador de tempo (>1 = mais lento): ritmo do dia + cansaço da sessão."""
        hours = max(0.0, self._clock() - self._started) / 3600.0
        fatigue = min(0.18, self.profile.fatigue_per_hour * hours)
        return self.session_speed * (1.0 + fatigue)

    def _lognormal(self, median: float, sigma: float) -> float:
        return median * math.exp(self._rng.gauss(0.0, sigma))

    def reaction_delay(self) -> float:
        """Segundos entre algo aparecer na tela e a primeira ação sobre isso."""
        if self._instant:
            return 0.0
        p = self.profile
        ms = self._lognormal(p.reaction_ms * self._pace(), 0.22)
        if p.hesitation and self._rng.random() < p.hesitation_chance:
            ms += self._rng.uniform(600, 2500)  # hesitou
        return min(p.reaction_max_ms + 2500, max(p.reaction_min_ms, ms)) / 1000.0

    def key_hold(self) -> float:
        if self._instant:
            return 0.0
        p = self.profile
        ms = self._rng.gauss(p.key_hold_ms, p.key_hold_sd_ms) * self._pace()
        return min(p.key_hold_ms + 4 * p.key_hold_sd_ms, max(35.0, ms)) / 1000.0

    def input_gap(self) -> float:
        if self._instant:
            return 0.0
        p = self.profile
        return max(p.gap_min_ms, self._lognormal(p.gap_ms * self._pace(), 0.30)) / 1000.0

    def vary(self, seconds: float, spread: float = 0.10) -> float:
        """Um tempo configurado com variação gaussiana (±spread), nunca menor que 85% dele."""
        if self._instant or seconds <= 0:
            return max(0.0, seconds)
        return max(seconds * 0.85, self._rng.gauss(seconds, seconds * spread) * self._pace())

    def cooldown(self, seconds: float) -> float:
        """Recarga efetiva: a do jogo + uma folga aleatória (uma pessoa nunca aperta no frame exato)."""
        if self._instant or seconds <= 0:
            return max(0.0, seconds)
        extra = abs(self._rng.gauss(0.0, self.profile.cooldown_jitter_pct / 100.0))
        return seconds * (1.0 + extra) * max(1.0, self._pace())  # dia rápido não fura a recarga do jogo

    def jitter_point(self, point: Tuple[int, int], radius_px: float = 2.0) -> Tuple[int, int]:
        """Mira imperfeita: desvio gaussiano de alguns pixels em volta do alvo."""
        if self._instant or radius_px <= 0:
            return point
        dx = max(-3 * radius_px, min(3 * radius_px, self._rng.gauss(0.0, radius_px)))
        dy = max(-3 * radius_px, min(3 * radius_px, self._rng.gauss(0.0, radius_px)))
        return int(round(point[0] + dx)), int(round(point[1] + dy))

    # ------------------------------------------------------------ ritmo das entradas

    def actions_last_minute(self) -> int:
        now = self._clock()
        while self._inputs and now - self._inputs[0] > 60.0:
            self._inputs.popleft()
        return len(self._inputs)

    async def before_input(self):
        """Espera o que for preciso para a próxima entrada respeitar o intervalo mínimo e o teto de APM."""
        if self._instant:
            self._inputs.append(self._clock())
            return
        async with self._lock:
            wait = self._last_input + self.input_gap() - self._clock()
            if wait > 0:
                await self._sleep(wait)
            if self.actions_last_minute() >= self.profile.max_apm:
                await self._sleep(max(0.0, 60.0 - (self._clock() - self._inputs[0])) + self.input_gap())
            now = self._clock()
            self._last_input = now
            self._inputs.append(now)


# Instância única: teclado, mouse e rota dividem as mesmas "mãos"
_current = Humanizer()


def get() -> Humanizer:
    return _current


def set_humanizer(new: Humanizer):
    global _current
    _current = new
