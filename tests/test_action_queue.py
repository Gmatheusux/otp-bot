import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import RecordingBackend, direct, no_sleep  # noqa: E402
from otpbot.actuation.action_queue import ActionQueue, Click, KeyPress, Wait  # noqa: E402
from otpbot.actuation.input_lock import InputLock  # noqa: E402


def make_queue():
    lock = InputLock()
    backend = RecordingBackend(lock)
    return ActionQueue(lock, backend, sleep=no_sleep, run_blocking=direct), lock, backend


def test_cooldown_igual_ao_do_orchestrator():
    async def scenario():
        queue, lock, backend = make_queue()
        queue.sync_cooldowns({"auto_combo": 10})
        lease = lock.grant("hunt", 3)
        first = await queue.execute(lease, "auto_combo", KeyPress("f1"))
        second = await queue.execute(lease, "auto_combo", KeyPress("f1"))  # em recarga
        queue.force_reset_all_timers()
        third = await queue.execute(lease, "auto_combo", KeyPress("f1"))
        return first, second, third, backend.keys, queue.can_execute("nao_registrada")

    assert asyncio.run(scenario()) == (True, None, True, ["f1", "f1"], False)


def test_sem_lease_valido_nada_sai():
    async def scenario():
        queue, lock, backend = make_queue()
        old = lock.grant("hunt", 3)
        lock.grant("safety", 0)
        refused_old = await queue.send(old, KeyPress("f1"))
        refused_none = await queue.send(None, Click(1, 2))
        return refused_old, refused_none, backend.events, queue.refused

    assert asyncio.run(scenario()) == (False, False, [], 2)


def test_trava_conferida_antes_de_cada_envio_da_sequencia():
    async def scenario():
        queue, lock, backend = make_queue()
        lease = lock.grant("hunt", 3)

        async def revoke_during_wait(_):
            lock.grant("safety", 0)  # a Segurança entra no meio da sequência

        queue._sleep = revoke_during_wait
        ok = await queue.send(lease, KeyPress("f4"), Wait(0.1), Click(10, 20))
        return ok, backend.events

    ok, events = asyncio.run(scenario())
    assert ok is False
    assert [e[:2] for e in events] == [("tecla", "f4")]  # o clique depois da troca de dono não saiu


def test_envios_saem_um_por_vez_na_ordem():
    async def scenario():
        queue, lock, backend = make_queue()
        lease = lock.grant("hunt", 3)
        running = []

        async def slow(fn, *args):
            running.append(1)
            assert len(running) == 1  # nunca dois envios ao mesmo tempo
            await asyncio.sleep(0.01)
            fn(*args)
            running.pop()

        queue._run_blocking = slow
        await asyncio.gather(*(queue.send(lease, KeyPress(f"f{i}")) for i in range(1, 6)))
        return backend.keys

    assert asyncio.run(scenario()) == ["f1", "f2", "f3", "f4", "f5"]


def test_erro_do_backend_nao_derruba_a_fila():
    class Broken(RecordingBackend):
        def key(self, name, hold=0.08):
            raise RuntimeError("janela do jogo não encontrada")

    async def scenario():
        lock = InputLock()
        queue = ActionQueue(lock, Broken(lock), sleep=no_sleep, run_blocking=direct)
        return await queue.send(lock.grant("hunt", 3), KeyPress("f1"))

    assert asyncio.run(scenario()) is False
