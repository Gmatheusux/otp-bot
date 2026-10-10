"""
otpbot/actuation/movement.py — Andar pelo teclado numérico com Num Lock DESLIGADO, um sqm por vez [Q43].

    7 ↖   8 ↑   9 ↗
    4 ←         6 →
    1 ↙   2 ↓   3 ↘

Cada passo é confirmado pela coordenada (sensor `coords` no WorldState): aperta a tecla, espera uma leitura NOVA e
confere se o personagem chegou exatamente no sqm esperado. As teclas saem pela fila com o lease de quem pediu (nada
fora da trava, ARQUITETURA §3).

Eixos: 8 (↑) diminui o y e 6 (→) aumenta o x, como no Tibia. Confirmado ao vivo na E08: as 8 direções, um passo
cada, por PostMessage com o jogo sem foco; a coordenada muda 0,20–0,28 s depois da tecla.

`walk_to` só anda no mesmo andar (z) e não contorna obstáculo pelo minimapa: tenta a direção direta e, se bloquear,
as duas vizinhas (±45°). Quem decide o que fazer com `LOST` (parar e avisar) é a Hunt (E10).
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple

from otpbot.actuation.action_queue import KeyPress
from otpbot.perception.coords import Coord

logger = logging.getLogger("Movement")

# (dx, dy) -> tecla do numérico com Num Lock desligado (nomes do input_backend.NUMPAD_OFF)
KEYS = {
    (-1, -1): "num7", (0, -1): "num8", (1, -1): "num9",
    (-1, 0): "num4", (1, 0): "num6",
    (-1, 1): "num1", (0, 1): "num2", (1, 1): "num3",
}
# Sentido horário a partir do norte: os vizinhos de uma direção são os índices ±1
_RING = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
NAMES = {"n": (0, -1), "ne": (1, -1), "e": (1, 0), "se": (1, 1), "s": (0, 1), "sw": (-1, 1), "w": (-1, 0),
         "nw": (-1, -1)}


class Step(Enum):
    OK = "ok"                   # chegou no sqm esperado
    BLOCKED = "bloqueado"       # a coordenada não mudou no tempo
    OFF = "fora"                # mudou, mas para outro sqm (empurrado, teleporte, leitura de outro passo)
    NO_READING = "sem_leitura"  # sem coordenada confiável antes do passo
    REFUSED = "recusado"        # a fila não mandou (trava revogada, sem backend, erro de envio)


class Walk(Enum):
    ARRIVED = "chegou"
    LOST = "perdido"
    NO_READING = "sem_leitura"
    REFUSED = "recusado"


@dataclass
class StepResult:
    status: Step
    start: Optional[Coord]
    end: Optional[Coord]
    direction: Tuple[int, int]
    seconds: float = 0.0


@dataclass
class WalkResult:
    status: Walk
    position: Optional[Coord]
    steps: List[StepResult] = field(default_factory=list)
    reason: str = ""


def sign(v: int) -> int:
    return (v > 0) - (v < 0)


def direction_to(start: Coord, target: Coord) -> Optional[Tuple[int, int]]:
    d = (sign(target.x - start.x), sign(target.y - start.y))
    return d if d != (0, 0) else None


def neighbors(d: Tuple[int, int]) -> List[Tuple[int, int]]:
    i = _RING.index(d)
    return [_RING[(i - 1) % 8], _RING[(i + 1) % 8]]


def moved(c: Coord, d: Tuple[int, int]) -> Coord:
    return Coord(c.x + d[0], c.y + d[1], c.z)


def chebyshev(a: Coord, b: Coord) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


class Mover:
    """
    Anda usando a fila (`queue.send(lease, KeyPress)`) e o WorldStore (`coords`).

    step_timeout  tempo máximo para a coordenada mudar depois da 1ª tecla
    repress_s     sem mudança neste tempo, aperta de novo: o jogo ENGOLE a tecla que chega no fim da animação do
                  passo anterior [E08: a coordenada muda 0,20–0,28 s depois da tecla; com a tecla logo após um passo
                  confirmado, 3 de 5 ficaram sem efeito]
    settle_s      pausa depois de um passo confirmado, antes do próximo
    min_conf      confiança mínima da leitura de coordenada
    """

    def __init__(self, queue, store, step_timeout: float = 1.5, repress_s: float = 0.4, settle_s: float = 0.05,
                 min_conf: float = 0.9, max_age: float = 0.5, clock: Callable[[], float] = time.monotonic,
                 sleep=asyncio.sleep):
        self.queue = queue
        self.store = store
        self.step_timeout = step_timeout
        self.repress_s = repress_s
        self.settle_s = settle_s
        self.min_conf = min_conf
        self.max_age = max_age
        self._clock = clock
        self._sleep = sleep

    # ------------------------------------------------------------------ leitura
    def _valid(self, reading, since: Optional[float] = None) -> Optional[Coord]:
        if reading is None or reading.value is None or reading.confidence < self.min_conf:
            return None
        if since is not None and reading.at < since:
            return None
        if self._clock() - reading.at > self.max_age:
            return None
        return reading.value

    async def position(self, timeout: Optional[float] = None) -> Optional[Coord]:
        """Coordenada confiável e recente; espera até `timeout` por uma leitura nova se a atual não serve."""
        deadline = self._clock() + (self.step_timeout if timeout is None else timeout)
        while True:
            pos = self._valid(self.store.latest("coords"))
            if pos is not None:
                return pos
            left = deadline - self._clock()
            if left <= 0:
                return None
            await self.store.wait_new(["coords"], left)

    # ------------------------------------------------------------------ passo
    async def step(self, lease, d: Tuple[int, int]) -> StepResult:
        start = await self.position()
        if start is None:
            return StepResult(Step.NO_READING, None, None, d)
        target = moved(start, d)
        sent_at = self._clock()
        if not await self.queue.send(lease, KeyPress(KEYS[d])):
            return StepResult(Step.REFUSED, start, None, d)
        deadline = sent_at + self.step_timeout
        pressed_at = sent_at
        while True:
            pos = self._valid(self.store.latest("coords"), since=sent_at)
            if pos is not None and pos != start:
                status = Step.OK if pos == target else Step.OFF
                if status is Step.OK and self.settle_s:
                    await self._sleep(self.settle_s)
                return StepResult(status, start, pos, d, self._clock() - sent_at)
            now = self._clock()
            if now >= deadline:
                return StepResult(Step.BLOCKED, start, start, d, now - sent_at)
            if self.repress_s and now - pressed_at >= self.repress_s:
                pressed_at = now
                if not await self.queue.send(lease, KeyPress(KEYS[d])):
                    return StepResult(Step.REFUSED, start, None, d, now - sent_at)
                continue
            wake = min(deadline, pressed_at + self.repress_s) if self.repress_s else deadline
            await self.store.wait_new(["coords"], max(0.0, wake - now))

    # ------------------------------------------------------------------ caminho
    async def walk_to(self, lease, target: Coord, max_distance: int = 30, max_failures: int = 3,
                      max_steps: Optional[int] = None) -> WalkResult:
        """
        Anda até `target` no mesmo andar. LOST quando: andar diferente, longe demais (> max_distance sqm),
        `max_failures` rodadas seguidas sem conseguir andar (bloqueado ou desviado), ou passos demais.
        """
        steps: List[StepResult] = []
        pos = await self.position()
        if pos is None:
            return WalkResult(Walk.NO_READING, None, steps, "sem coordenada")
        if pos.z != target.z:
            return WalkResult(Walk.LOST, pos, steps, f"andar {pos.z} ≠ destino {target.z}")
        if chebyshev(pos, target) > max_distance:
            return WalkResult(Walk.LOST, pos, steps, f"destino a {chebyshev(pos, target)} sqm (máx. {max_distance})")
        limit = max_steps if max_steps is not None else 3 * max_distance
        failures = 0
        while True:
            d = direction_to(pos, target)
            if d is None:
                return WalkResult(Walk.ARRIVED, pos, steps)
            if len(steps) >= limit:
                return WalkResult(Walk.LOST, pos, steps, f"passos demais ({limit})")
            progressed = False
            for cand in [d] + neighbors(d):  # a tecla engolida já é repetida dentro do step
                r = await self.step(lease, cand)
                steps.append(r)
                if r.status is Step.REFUSED:
                    return WalkResult(Walk.REFUSED, pos, steps, "a fila recusou a tecla")
                if r.status is Step.NO_READING:
                    return WalkResult(Walk.NO_READING, pos, steps, "sem coordenada")
                if r.status is Step.OK:
                    pos, progressed = r.end, True
                    break
                if r.status is Step.OFF:
                    logger.warning(f"Passo {cand} de {r.start} terminou em {r.end} (esperado {moved(r.start, cand)})")
                    pos = r.end
                    break
                # BLOCKED: tenta a próxima direção
            failures = 0 if progressed else failures + 1
            if pos.z != target.z:
                return WalkResult(Walk.LOST, pos, steps, f"mudou de andar para {pos.z}")
            if chebyshev(pos, target) > max_distance:
                return WalkResult(Walk.LOST, pos, steps, "desviado para longe do destino")
            if failures >= max_failures:
                return WalkResult(Walk.LOST, pos, steps, f"{failures} tentativas sem avançar")
