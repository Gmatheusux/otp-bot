import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.heal_routine import ABORTED, DONE, INVALID, PokemonHealRoutine
from modules.screen_calibration import DEFAULT_CALIBRATION

SCREEN = (1920, 1080)


def make_routine(now=1000.0):
    events = []

    async def press(key):
        events.append(("tecla", key))

    async def click(point):
        events.append(("clique", point))

    async def sleep(_):
        pass

    routine = PokemonHealRoutine(press, click, sleep=sleep, clock=lambda: now, telemetry={})
    return routine, events


def config(**overrides):
    cfg = {
        "enabled": True, "hp_percent": 90, "swap_method": "pokebar",
        "healer_slot": 3, "farm_slot": 1, "rotation": ["f6", "f7"],
        "use_revive": True, "revive_key": "", "cooldown_s": 15,
    }
    cfg.update(overrides)
    return cfg


def pokebar_point(slot):
    # Centro da barra do slot na Pokébar do perfil 1920x1080 (x 44, y 172, 125x196, 4 slots)
    return (106, round(172 + 196 * (slot - 0.5) / 4))


def test_so_comeca_com_hp_baixo_e_area_limpa():
    routine, _ = make_routine()
    cfg = config()
    assert routine.should_start(cfg, {"player_hp": 85}, mobs_on_screen=0, is_boxed=False)
    assert not routine.should_start(cfg, {"player_hp": 95}, 0, False)        # HP acima do limite
    assert not routine.should_start(cfg, {"player_hp": 85}, 3, False)        # ainda tem selvagem
    assert not routine.should_start(cfg, {"player_hp": 85}, 0, True)         # box em andamento
    assert not routine.should_start(cfg, {"player_hp": None}, 0, False)      # sem leitura de HP
    assert not routine.should_start(config(enabled=False), {"player_hp": 50}, 0, False)


def test_rotina_completa_na_ordem_certa():
    routine, events = make_routine()
    result = asyncio.run(routine.run(config(), DEFAULT_CALIBRATION, SCREEN, fallback_revive_key="f2"))
    assert result == DONE
    assert events == [
        ("clique", pokebar_point(3)),   # chama o pokémon de cura
        ("tecla", "f6"), ("tecla", "f7"),  # rotação de cura
        ("tecla", "f2"),                # revive no curador (tecla do perfil, já que a da cura está vazia)
        ("clique", pokebar_point(1)),   # volta ao pokémon de farm
    ]
    assert routine.step == "parado"


def test_selvagem_no_meio_aborta_e_volta_ao_farm():
    routine, events = make_routine()
    checks = iter([False, True])  # depois do 1º golpe aparece selvagem
    result = asyncio.run(routine.run(config(), DEFAULT_CALIBRATION, SCREEN, danger=lambda: next(checks, True)))
    assert result == ABORTED
    assert events == [("clique", pokebar_point(3)), ("tecla", "f6"), ("clique", pokebar_point(1))]


def test_troca_por_tecla():
    routine, events = make_routine()
    cfg = config(swap_method="key", healer_key="ctrl+f1", farm_key="ctrl+f2", use_revive=False, rotation=["f6"])
    assert asyncio.run(routine.run(cfg, DEFAULT_CALIBRATION, SCREEN)) == DONE
    assert events == [("tecla", "ctrl+f1"), ("tecla", "f6"), ("tecla", "ctrl+f2")]


def test_configuracao_incompleta_nao_mexe_em_nada():
    routine, events = make_routine()
    assert asyncio.run(routine.run(config(rotation=[]), DEFAULT_CALIBRATION, SCREEN)) == INVALID
    assert asyncio.run(routine.run(config(healer_slot=1, farm_slot=1), DEFAULT_CALIBRATION, SCREEN)) == INVALID
    assert events == []


def test_respeita_intervalo_entre_curas():
    now = [1000.0]
    routine, _ = make_routine()
    routine._clock = lambda: now[0]
    asyncio.run(routine.run(config(), DEFAULT_CALIBRATION, SCREEN))
    now[0] += 5
    assert not routine.should_start(config(), {"player_hp": 50}, 0, False)
    now[0] += 11
    assert routine.should_start(config(), {"player_hp": 50}, 0, False)
