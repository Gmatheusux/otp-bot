import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from otpbot.state.world_state import WorldStore  # noqa: E402


def make_store():
    now = [100.0]
    return WorldStore(clock=lambda: now[0]), now


def test_leitura_tem_valor_confianca_e_idade():
    store, now = make_store()
    store.publish("bars", {"player_hp": 80}, confidence=0.9)
    now[0] += 2
    ws = store.snapshot()
    r = ws.reading("bars")
    assert r.value == {"player_hp": 80} and r.confidence == 0.9 and r.age(ws.at) == 2
    assert ws.get("bars") == {"player_hp": 80}


def test_leitura_vencida_incerta_ou_ausente_vira_none():
    store, now = make_store()
    store.publish("bars", {"player_hp": 80})
    store.publish("detections", None)
    store.publish("gm_alert", True, confidence=0.3)
    now[0] += 3.5  # barras valem 3 s
    ws = store.snapshot()
    assert ws.get("bars") is None
    assert ws.get("bars", max_age=10) == {"player_hp": 80}
    assert ws.get("detections", default=[]) == []
    assert ws.get("gm_alert", min_conf=0.5) is None
    assert ws.get("nao_existe") is None


def test_snapshot_e_uma_foto_e_conta_os_ticks():
    store, _ = make_store()
    store.publish("bars", 1)
    first = store.snapshot()
    store.publish("bars", 2)
    second = store.snapshot()
    assert first.get("bars") == 1 and second.get("bars") == 2
    assert (first.tick, second.tick) == (1, 2)
    assert second.reading("bars").seq > first.reading("bars").seq


def test_wait_new_acorda_na_publicacao():
    async def scenario():
        store = WorldStore()
        waiter = asyncio.create_task(store.wait_new(["detections"], timeout=2))
        await asyncio.sleep(0)
        store.publish("detections", [])
        woke = await waiter
        timed_out = await store.wait_new(["detections"], timeout=0.01)
        return woke, timed_out

    assert asyncio.run(scenario()) == (True, False)
