"""
otpbot/state/world_state.py — Tudo o que os sensores sabem do jogo, num lugar só.

Regra (ARQUITETURA §3): sensor não decide. Ele publica valor, confiança e horário; a decisão lê uma foto
(`WorldState`) por tick. Leitura incerta (`None`), com confiança baixa ou velha demais vira `None` e ninguém age
sobre ela.

Chaves publicadas hoje:
  bars        resultado de `read_regions` (HP do jogador e do pokémon, EXP, Pokébar, postura, perfil)
  detections  lista de detecções do YOLO, relativas à área cliente do jogo
  gm_alert    True quando o monitor do chat viu uma mensagem de GM
  window      `GameWindow` atual (None = jogo não encontrado)
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

# Idade máxima padrão de cada leitura (s). Barras são lidas 2x/s; o YOLO a cada frame.
MAX_AGE = {"bars": 3.0, "detections": 1.0, "window": 5.0}


@dataclass(frozen=True)
class Reading:
    value: Any
    confidence: float
    at: float
    seq: int = 0

    def age(self, now: float) -> float:
        return now - self.at


@dataclass(frozen=True)
class WorldState:
    tick: int
    at: float
    readings: Mapping[str, Reading] = field(default_factory=dict)

    def reading(self, name: str) -> Optional[Reading]:
        return self.readings.get(name)

    def get(self, name: str, default: Any = None, max_age: Optional[float] = None, min_conf: float = 0.0) -> Any:
        """Valor da leitura, ou `default` se ela não existe, é incerta, tem pouca confiança ou venceu."""
        r = self.readings.get(name)
        if r is None or r.value is None or r.confidence < min_conf:
            return default
        limit = MAX_AGE.get(name) if max_age is None else max_age
        if limit is not None and r.age(self.at) > limit:
            return default
        return r.value


class WorldStore:
    """Onde os sensores escrevem. Usar só de dentro do loop asyncio (os sensores publicam depois do to_thread)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._readings: Dict[str, Reading] = {}
        self._seq = 0
        self._tick = 0
        self._waiters: Dict[str, asyncio.Event] = {}

    def publish(self, name: str, value: Any, confidence: float = 1.0, at: Optional[float] = None) -> None:
        self._seq += 1
        self._readings[name] = Reading(value, float(confidence), self._clock() if at is None else at, self._seq)
        event = self._waiters.get(name)
        if event is not None:
            event.set()

    def latest(self, name: str) -> Optional[Reading]:
        return self._readings.get(name)

    def snapshot(self) -> WorldState:
        self._tick += 1
        return WorldState(self._tick, self._clock(), dict(self._readings))

    def view(self) -> WorldState:
        """Foto sem avançar o tick (para checagens no meio de uma rotina)."""
        return WorldState(self._tick, self._clock(), dict(self._readings))

    async def wait_new(self, names: Iterable[str], timeout: float) -> bool:
        """Espera até alguma das chaves ser publicada de novo. False se deu o tempo."""
        events = []
        for name in names:
            event = self._waiters.setdefault(name, asyncio.Event())
            event.clear()
            events.append(event)
        waits = [asyncio.ensure_future(e.wait()) for e in events]
        try:
            done, _ = await asyncio.wait(waits, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
            return bool(done)
        finally:
            for w in waits:
                w.cancel()
