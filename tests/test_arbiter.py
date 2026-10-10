"""Árbitro: prioridade, interrupção com/sem limpeza, pausa e trabalho do console."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import Brain, default_config, det  # noqa: E402
from otpbot.actuation.action_queue import KeyPress  # noqa: E402
from otpbot.brain.behaviors.base import SURVIVAL, Behavior  # noqa: E402
from otpbot.brain.heal_routine import PokemonHealRoutine  # noqa: E402
from otpbot.perception.bars import DEFAULT_CALIBRATION, region_point  # noqa: E402

HEALER = region_point(DEFAULT_CALIBRATION, "team", 1920, 1080, 2)
FARM = region_point(DEFAULT_CALIBRATION, "team", 1920, 1080, 0)


def heal_config():
    config = default_config()
    config["features"]["heal"]["pokemon_heal"].update(enabled=True, rotation=["f6"], healer_slot=3, farm_slot=1)
    return config


async def slow_sleep(_):
    await asyncio.sleep(5)  # a rotina "trava" esperando o curador sair: dá tempo de interromper


def brain_with_heal(extra=()):
    holder = {}
    brain = Brain(heal_config(), heal_routine=None, extra=extra)
    routine = PokemonHealRoutine(brain.queue.press_current, brain.queue.click_current, sleep=slow_sleep,
                                 telemetry=brain.telemetry)
    brain.ctx.heal_routine = routine
    holder["routine"] = routine
    return brain, routine


async def start_heal(brain):
    """HP 50 e área limpa: a Hunt começa a cura e fica parada no meio (chamou o curador)."""
    brain.frame([det(0, 0.5, 0.5)], {"player_hp": 50})
    await brain.arbiter.tick()
    for _ in range(50):
        await asyncio.sleep(0)
    assert brain.ctx.heal_routine.running


def owners(events):
    return [(e[0], e[1], e[2].owner if e[2] else None) for e in events]


def test_seguranca_interrompe_a_cura_no_meio_sem_limpeza():
    async def scenario():
        brain, routine = brain_with_heal()
        await start_heal(brain)
        brain.store.publish("gm_alert", True)
        await brain.tick_and_wait()
        return brain, routine

    brain, routine = asyncio.run(scenario())
    assert brain.killed == [True]
    assert not routine.running and routine.step == "parado"
    # Só o clique que chamou o curador saiu; a volta ao farm da limpeza foi barrada pela trava
    assert owners(brain.backend.events) == [("clique", HEALER, "hunt")]
    assert brain.queue.refused >= 1


class Fainted(Behavior):
    """Comportamento de teste acima da Hunt que permite a limpeza (como será a Sobrevivência na E10)."""
    name = "teste_sobrevivencia"
    priority = SURVIVAL

    def __init__(self, brain):
        self.brain = brain

    def wants(self, ws, cfg):
        return ws.get("fainted") is True

    async def step(self, ws, cfg, lease):
        await self.brain.queue.send(lease, KeyPress("f2"))


def test_outro_comportamento_interrompe_e_a_cura_volta_ao_farm_antes():
    async def scenario():
        holder = {}
        brain, routine = brain_with_heal()
        fainted = Fainted(brain)
        brain.arbiter.behaviors = sorted(brain.arbiter.behaviors + [fainted], key=lambda b: b.priority)
        await start_heal(brain)
        brain.store.publish("fainted", True)
        await brain.tick_and_wait()
        holder["brain"] = brain
        return brain

    brain = asyncio.run(scenario())
    assert owners(brain.backend.events) == [
        ("clique", HEALER, "hunt"),                 # chamou o curador
        ("clique", FARM, "hunt"),                   # limpeza: de volta ao farm, ainda com a trava da Hunt
        ("tecla", "f2", "teste_sobrevivencia"),     # só então o novo dono age
    ]


def test_pausa_corta_a_entrada_na_hora():
    async def scenario():
        brain, routine = brain_with_heal()
        await start_heal(brain)
        await brain.arbiter.halt()
        sent_before = list(brain.backend.events)
        # um envio atrasado da Hunt depois da pausa não sai
        late = await brain.queue.press_current("f1")
        return brain, routine, sent_before, late

    brain, routine, sent_before, late = asyncio.run(scenario())
    assert brain.lock.current is None and not routine.running
    assert brain.backend.events == sent_before
    assert late is False


def test_hunt_nao_interrompe_a_rotina_que_ja_esta_rodando():
    async def scenario():
        brain, routine = brain_with_heal()
        await start_heal(brain)
        brain.frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], {"player_hp": 50})  # selvagem apareceu
        await brain.arbiter.tick()
        running = routine.running
        await brain.arbiter.halt()
        return brain, running

    brain, running = asyncio.run(scenario())
    assert running  # a própria rotina decide abortar pelo danger(); o árbitro não corta a mesma prioridade
    assert [e[1] for e in brain.backend.events] == [HEALER]


def test_trabalho_do_console_passa_pela_trava_e_a_seguranca_corta():
    async def scenario():
        brain = Brain()
        steps = []

        async def job():
            await brain.queue.press_current("f6")
            steps.append("f6")
            await asyncio.sleep(5)
            await brain.queue.press_current("f7")  # nunca chega

        runner = asyncio.create_task(brain.arbiter.run_exclusive("teste_cura", job))
        for _ in range(20):
            await asyncio.sleep(0)
        brain.store.publish("gm_alert", True)
        await brain.tick_and_wait()
        ok = await asyncio.wait_for(runner, timeout=3)
        return brain, ok

    brain, ok = asyncio.run(scenario())
    assert ok is True
    assert owners(brain.backend.events) == [("tecla", "f6", "teste_cura")]
    assert brain.killed == [True]


def test_laco_do_arbitro_combate_e_para_no_kill():
    async def scenario():
        brain = Brain()
        task = asyncio.create_task(brain.arbiter.run())
        await asyncio.sleep(0)
        brain.frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)])
        for _ in range(50):
            await asyncio.sleep(0)
        brain.kill.set()
        brain.store.publish("detections", [])
        await asyncio.wait_for(task, timeout=3)
        return brain

    brain = asyncio.run(scenario())
    assert brain.backend.keys == ["f1"]
    assert brain.lock.current is None
