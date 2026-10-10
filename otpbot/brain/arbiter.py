"""
otpbot/brain/arbiter.py — Árbitro por prioridade (veio da decision_thread na E03).

A cada frame novo da percepção (ou alerta), tira uma foto do WorldState e dá o controle ao comportamento mais
importante que quer agir: Segurança > Companion > Sobrevivência > Hunt. O comportamento roda numa task com o
lease da trava de entrada. Se um mais importante aparece com outro rodando (ex.: rotina de cura):
  - o de baixo é cancelado; se o novo permite, ele faz a limpeza ainda com o lease dele (ex.: volta ao farm);
  - só depois a trava passa para o novo. A Segurança revoga a trava ANTES de cancelar: a limpeza não sai.
Pausa e kill revogam a trava e cancelam o que estiver rodando.
"""
import asyncio
import contextvars
import logging
from typing import Awaitable, Callable, List, Optional, Sequence

from otpbot.actuation.action_queue import CURRENT_LEASE, ActionQueue
from otpbot.actuation.input_lock import InputLock, Lease
from otpbot.brain.behaviors.base import HUNT, Behavior
from otpbot.state.world_state import WorldStore

logger = logging.getLogger("Arbiter")

TICK_KEYS = ("detections", "gm_alert")
CLEANUP_TIMEOUT_S = 8.0


class _Exclusive(Behavior):
    """Trabalho pedido pelo console (botões de teste da cura): ocupa a trava como se fosse a Hunt."""
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority


class Arbiter:
    def __init__(self, behaviors: Sequence[Behavior], store: WorldStore, lock: InputLock, queue: ActionQueue,
                 get_config: Callable[[], dict], pause_event: asyncio.Event, kill_event: asyncio.Event,
                 telemetry: Optional[dict] = None, tick_timeout: float = 1.0):
        self.behaviors: List[Behavior] = sorted(behaviors, key=lambda b: b.priority)
        self.store = store
        self.lock = lock
        self.queue = queue
        self.get_config = get_config
        self.pause_event = pause_event
        self.kill_event = kill_event
        self.telemetry = telemetry if telemetry is not None else {}
        self.tick_timeout = tick_timeout
        self._task: Optional[asyncio.Task] = None
        self._active: Optional[Behavior] = None
        self._lease: Optional[Lease] = None
        self._report(None)

    # ---------------------------------------------------------------- estado
    @property
    def active(self) -> Optional[Behavior]:
        return self._active

    def busy(self) -> bool:
        return self._task is not None and not self._task.done()

    def lease_of(self, owner: str) -> Optional[Lease]:
        """Lease atual se a trava for de `owner` (o navigator usa o da Hunt)."""
        cur = self.lock.current
        return cur if cur is not None and cur.owner == owner else None

    def _report(self, behavior: Optional[Behavior]) -> None:
        self.telemetry["active_behavior"] = behavior.name if behavior else None
        cur = self.lock.current
        self.telemetry["input_owner"] = cur.owner if cur else None

    # ---------------------------------------------------------------- laço
    async def run(self) -> None:
        logger.info("Árbitro iniciado (Segurança > Companion > Sobrevivência > Hunt).")
        while not self.kill_event.is_set():
            if not self.pause_event.is_set():
                await self.halt()
                await self.pause_event.wait()
                continue
            try:
                await self.store.wait_new(TICK_KEYS, self.tick_timeout)
                if self.kill_event.is_set():
                    break
                if not self.pause_event.is_set():
                    continue
                await self.tick()
            except Exception as e:
                logger.error(f"Erro no árbitro: {e}")
                await asyncio.sleep(1)
        await self.halt()
        logger.info("Árbitro encerrado (Kill Event).")

    async def tick(self) -> None:
        ws = self.store.snapshot()
        cfg = self.get_config()
        chosen = None
        for behavior in self.behaviors:
            try:
                if behavior.wants(ws, cfg):
                    chosen = behavior
                    break
            except Exception as e:
                logger.error(f"Erro em {behavior.name}.wants: {e}")
        if chosen is None:
            return
        if self.busy():
            if chosen.priority >= self._active.priority:
                return  # o que está rodando continua (ex.: rotina de cura)
            await self._preempt(chosen)
        self._start(chosen, lambda lease: chosen.step(ws, cfg, lease))

    def _start(self, behavior: Behavior, job: Callable[[Lease], Awaitable[None]]) -> asyncio.Task:
        if self._lease is not None and self._lease.owner != behavior.name:
            self.lock.release(self._lease)  # o dono anterior já terminou (ou foi interrompido)
        lease = self.lock.grant(behavior.name, behavior.priority)
        self._active, self._lease = behavior, lease
        self._report(behavior)

        async def runner():
            try:
                await job(lease)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Erro em {behavior.name}: {e}")

        context = contextvars.copy_context()
        context.run(CURRENT_LEASE.set, lease)
        self._task = asyncio.get_running_loop().create_task(runner(), context=context)
        return self._task

    async def _preempt(self, new: Behavior) -> None:
        old, task, lease = self._active, self._task, self._lease
        logger.warning(f">>> [ÁRBITRO] {new.name} interrompe {old.name} <<<")
        if not new.allows_cleanup:
            self.lock.revoke_all()
        await self._cancel(task)
        if new.allows_cleanup and old is not None:
            await self._cleanup(old, lease)

    async def _cancel(self, task: Optional[asyncio.Task]) -> None:
        if task is None or task.done():
            return
        task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=CLEANUP_TIMEOUT_S)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        except Exception as e:
            logger.error(f"Erro ao interromper: {e}")

    async def _cleanup(self, behavior: Behavior, lease: Optional[Lease]) -> None:
        token = CURRENT_LEASE.set(lease)
        try:
            await asyncio.wait_for(behavior.cleanup(lease), timeout=CLEANUP_TIMEOUT_S)
        except Exception as e:
            logger.error(f"Erro na limpeza de {behavior.name}: {e}")
        finally:
            CURRENT_LEASE.reset(token)

    async def halt(self) -> None:
        """Pausa/kill: ninguém mais manda entrada; o que estava rodando é cancelado."""
        self.lock.revoke_all()
        await self._cancel(self._task)
        self._task = None
        self._active = self._lease = None
        self.queue.release_all()
        self._report(None)

    # ---------------------------------------------------------------- console
    async def run_exclusive(self, name: str, job: Callable[[], Awaitable], priority: int = HUNT) -> bool:
        """Roda um trabalho do console com a trava. False se algo mais importante está no controle."""
        if self.busy():
            if self._active.priority < priority:
                return False
            await self._preempt(_Exclusive(name, priority))
        elif self.lock.current is not None and self.lock.current.priority < priority:
            return False
        task = self._start(_Exclusive(name, priority), lambda _lease: job())
        lease = self._lease
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            pass
        if self._lease == lease:
            self.lock.release(lease)
            self._active = self._lease = None
            self._report(None)
        return True
