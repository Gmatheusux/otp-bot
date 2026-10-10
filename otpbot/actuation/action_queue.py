"""
otpbot/actuation/action_queue.py — Fila de ações com cooldowns (veio do action_orchestrator na E03).

Toda tecla e todo clique do bot entram aqui com o `Lease` de quem pediu. Os envios saem um de cada vez, na
ordem de chegada (asyncio.Lock é FIFO), e a trava é conferida ANTES DE CADA envio: se o lease foi revogado no
meio de uma sequência, o resto não sai.
"""
import asyncio
import contextvars
import logging
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Union

from otpbot.actuation.input_lock import InputLock, Lease

logger = logging.getLogger("ActionQueue")


@dataclass(frozen=True)
class KeyPress:
    key: str
    hold: float = 0.08


@dataclass(frozen=True)
class Click:
    """x, y em pixels da ÁREA CLIENTE do jogo."""
    x: int
    y: int
    button: str = "left"


@dataclass(frozen=True)
class Wait:
    seconds: float


Action = Union[KeyPress, Click, Wait]

# Lease de quem está rodando nesta task. O árbitro define ao criar a task de um comportamento; rotinas que só
# recebem "aperte esta tecla" (cura) mandam com o lease da task delas, nunca com o do dono atual da trava.
CURRENT_LEASE: contextvars.ContextVar[Optional[Lease]] = contextvars.ContextVar("current_lease", default=None)


class ActionTimer:
    """Cooldown independente de uma ação, medido com time.time() sem bloquear."""
    def __init__(self, cooldown_seconds: float):
        self.cooldown_seconds = cooldown_seconds
        self.last_execution_time: float = 0.0

    def is_ready(self) -> bool:
        return (time.time() - self.last_execution_time) >= self.cooldown_seconds

    def reset(self):
        self.last_execution_time = time.time()


class ActionQueue:
    def __init__(self, lock: InputLock, backend=None, sleep=asyncio.sleep,
                 run_blocking: Optional[Callable] = None):
        self.lock = lock
        self.backend = backend
        self._sleep = sleep
        self._run_blocking = run_blocking or asyncio.to_thread
        self._serial = asyncio.Lock()
        self._timers: Dict[str, ActionTimer] = {}
        self._action_locks: Dict[str, asyncio.Lock] = {}
        self.sent = 0
        self.refused = 0

    # ---------------------------------------------------------------- cooldowns (iguais ao orchestrator)
    def register_action(self, action_name: str, cooldown_seconds: float):
        self._timers[action_name] = ActionTimer(cooldown_seconds)
        self._action_locks[action_name] = asyncio.Lock()

    def sync_cooldowns(self, cooldowns: Dict[str, float]):
        """Aplica cooldowns vindos do console sem perder o tempo já decorrido de cada ação."""
        for action_name, seconds in cooldowns.items():
            if action_name in self._timers:
                self._timers[action_name].cooldown_seconds = float(seconds)
            else:
                self.register_action(action_name, float(seconds))

    def can_execute(self, action_name: str) -> bool:
        if action_name not in self._timers:
            logger.warning(f"Tentativa de checagem de ação não registrada: {action_name}")
            return False
        return self._timers[action_name].is_ready()

    def force_reset_all_timers(self):
        """Zera todos os cooldowns (Cérebro Try-Hard)."""
        for timer in self._timers.values():
            timer.last_execution_time = 0.0
        logger.warning(">>> TIMERS RESETADOS: Todas as magias prontas para uso imediato! <<<")

    async def execute(self, lease: Optional[Lease], action_name: str, *actions: Action) -> Optional[bool]:
        """Manda a sequência se a ação está fora do cooldown. O cooldown reinicia mesmo se o envio falhar."""
        if not self.can_execute(action_name):
            return None
        lock = self._action_locks[action_name]
        if lock.locked():
            return None
        async with lock:
            if not self.can_execute(action_name):
                return None
            try:
                return await self.send(lease, *actions)
            finally:
                self._timers[action_name].reset()

    # ---------------------------------------------------------------- envio
    async def send(self, lease: Optional[Lease], *actions: Action) -> bool:
        """True se a sequência inteira saiu. Tecla vazia (não escolhida no console) é pulada."""
        async with self._serial:
            for action in actions:
                if isinstance(action, Wait):
                    await self._sleep(action.seconds)
                    continue
                if isinstance(action, KeyPress) and not action.key:
                    continue
                if not self.lock.is_valid(lease):
                    self.refused += 1
                    who = lease.owner if lease else "sem trava"
                    logger.debug(f"Envio recusado ({who}): a trava de entrada não é dele agora.")
                    return False
                if self.backend is None:
                    logger.warning("Sem backend de entrada: ação descartada.")
                    return False
                try:
                    if isinstance(action, KeyPress):
                        await self._run_blocking(self.backend.key, action.key, action.hold)
                    else:
                        await self._run_blocking(self.backend.click, action.x, action.y, action.button)
                except Exception as e:  # inclui pywintypes.error (ex.: Access is denied por UIPI, D20)
                    logger.warning(f"Entrada não enviada ({action}): {e}")
                    return False
                self.sent += 1
            return True

    async def press_current(self, key: str) -> bool:
        """Tecla com o lease da task atual (callbacks da rotina de cura)."""
        return await self.send(CURRENT_LEASE.get(), KeyPress(key))

    async def click_current(self, point) -> bool:
        return await self.send(CURRENT_LEASE.get(), Click(int(point[0]), int(point[1])))

    def release_all(self) -> None:
        if self.backend is not None:
            try:
                self.backend.release_all()
            except Exception as e:
                logger.debug(f"release_all: {e}")
