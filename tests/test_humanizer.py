import asyncio
import os
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import humanizer as human
from core.action_orchestrator import UtilityOrchestrator
from core.humanizer import HumanProfile, Humanizer


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    async def sleep(self, seconds):
        self.now += max(0.0, seconds)


def make(seed=1, **profile):
    clock = FakeClock()
    hz = Humanizer(HumanProfile(**profile), rng=random.Random(seed), clock=clock, sleep=clock.sleep)
    return hz, clock


def test_reacao_nunca_abaixo_do_minimo_humano():
    hz, _ = make()
    delays = [hz.reaction_delay() for _ in range(2000)]
    assert min(delays) >= 0.16
    assert 0.18 < sorted(delays)[1000] < 0.33  # mediana perto de 240 ms


def test_tempos_variam_sempre():
    hz, _ = make()
    holds = {round(hz.key_hold(), 4) for _ in range(200)}
    assert len(holds) > 150
    assert min(hz.key_hold() for _ in range(500)) >= 0.035


def test_recarga_nunca_fica_abaixo_da_configurada():
    hz, _ = make()
    values = [hz.cooldown(2.0) for _ in range(2000)]
    assert min(values) >= 2.0
    assert len({round(v, 3) for v in values}) > 300


def test_teto_de_acoes_por_minuto():
    hz, clock = make(max_apm=60)
    start = clock.now

    async def spam():
        for _ in range(120):
            await hz.before_input()

    asyncio.run(spam())
    # 120 entradas com teto de 60/min levam pelo menos 1 minuto
    assert clock.now - start >= 60.0
    assert hz.actions_last_minute() <= 60


def test_intervalo_minimo_entre_entradas():
    hz, clock = make()
    stamps = []

    async def go():
        for _ in range(50):
            await hz.before_input()
            stamps.append(clock.now)

    asyncio.run(go())
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    assert min(gaps) >= 0.08


def test_mira_imperfeita_mas_perto():
    hz, _ = make()
    points = [hz.jitter_point((500, 500), 2.0) for _ in range(500)]
    assert len(set(points)) > 10
    assert all(abs(x - 500) <= 6 and abs(y - 500) <= 6 for x, y in points)


def test_config_do_console_tem_limites():
    p = HumanProfile.from_config({"max_apm": 9999, "reaction_ms": 10, "cooldown_jitter_pct": -5})
    assert p.max_apm == 300
    assert p.reaction_ms >= p.reaction_min_ms
    assert p.cooldown_jitter_pct == 0


def test_instant_nao_espera():
    hz = Humanizer.instant()
    assert hz.reaction_delay() == 0 and hz.key_hold() == 0 and hz.cooldown(2.0) == 2.0


def test_orquestrador_nao_libera_antes_da_recarga():
    previous = human.get()
    human.set_humanizer(Humanizer(rng=random.Random(3)))
    try:
        orch = UtilityOrchestrator()
        orch.register_action("combo", 2.0)
        timer = orch._timers["combo"]
        assert orch.can_execute("combo")

        async def noop():
            return None

        asyncio.run(orch.execute("combo", noop))
        assert not orch.can_execute("combo")
        assert timer._effective >= 2.0
        assert not hasattr(orch, "force_reset_all_timers")  # sem rajada acima do limite humano
    finally:
        human.set_humanizer(previous)
