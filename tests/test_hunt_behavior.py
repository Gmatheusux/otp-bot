"""
Regras da Hunt portadas da antiga decision_thread (E03). As expectativas (teclas, ordem e cliques) são as
mesmas dos testes de antes da E03: é a prova de que o comportamento não mudou.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import Brain, default_config, det  # noqa: E402
from otpbot.actuation.action_queue import KeyPress  # noqa: E402


class FakeNavigator:
    def __init__(self, is_playing=False):
        self.is_playing = is_playing
        self.stopped = False

    def stop_playback(self):
        self.is_playing = False
        self.stopped = True


def run_one_frame(detections, navigator, config_patch=None, readings=None, heal_routine=None):
    """Um frame pela pilha inteira; devolve (teclas, cliques, telemetria)."""
    async def scenario():
        config = default_config()
        if config_patch:
            config_patch(config)
        brain = Brain(config, navigator, heal_routine)
        brain.frame(detections, readings or {})
        await brain.tick_and_wait()
        return brain

    brain = asyncio.run(scenario())
    return brain.backend.keys, brain.backend.clicks, brain.telemetry


def test_combo_dispara_sem_cavebot():
    # Antes da correção nada acontecia se a rota não estivesse tocando
    pressed, _, telemetry = run_one_frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], FakeNavigator(is_playing=False))
    assert pressed == ["f1"]
    assert telemetry["mobs_on_screen"] == 1


def test_boxed_para_a_rota_e_solta_defesa_combo_revive():
    mobs = [det(1, 0.5 + 0.01 * i, 0.5) for i in range(8)]
    navigator = FakeNavigator(is_playing=True)
    pressed, _, telemetry = run_one_frame([det(0, 0.5, 0.5)] + mobs, navigator)
    assert navigator.stopped
    assert pressed == ["f3", "f1", "f2"]
    assert telemetry["is_boxed"] is True


def test_toggles_do_console_desligam_o_combo():
    def disable_combo(config):
        config["features"]["combat"]["auto_combo"] = False
    pressed, _, _ = run_one_frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], FakeNavigator(), disable_combo)
    assert pressed == []


def test_limiar_de_cercado_vem_da_config():
    def three_mobs_is_boxed(config):
        config["features"]["combat"]["boxed_mobs"] = 3
    mobs = [det(1, 0.5 + 0.01 * i, 0.5) for i in range(3)]
    pressed, _, telemetry = run_one_frame([det(0, 0.5, 0.5)] + mobs, FakeNavigator(), three_mobs_is_boxed)
    assert telemetry["is_boxed"] is True
    assert pressed == ["f3", "f1", "f2"]


def test_tecla_nao_definida_nao_e_apertada():
    def no_defense_key(config):
        config["pokemon_profile"]["defensive_buff_key"] = ""

    async def empty_key():
        brain = Brain()
        brain.lock.grant("hunt", 3)
        await brain.queue.send(brain.lock.current, KeyPress(""))
        return brain.backend.events

    assert asyncio.run(empty_key()) == []
    mobs = [det(1, 0.5 + 0.01 * i, 0.5) for i in range(8)]
    pressed, _, _ = run_one_frame([det(0, 0.5, 0.5)] + mobs, FakeNavigator(), no_defense_key)
    assert pressed == ["f1", "f2"]


def enable_auto_stance(config):
    config["features"]["stance"].update(auto=True, normal="offensive", lure="defensive", combo="offensive")


def test_postura_vai_para_defensivo_ao_juntar_selvagens():
    _, clicks, _ = run_one_frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], FakeNavigator(), enable_auto_stance,
                                 readings={"stance": "offensive"})
    # Frame 1920x1080 usa o perfil medido nessa resolução: centro da mão verde (3º botão)
    assert clicks == [(166, 118)]


def test_postura_no_cliente_maximizado_usa_o_perfil_do_cliente():
    async def scenario():
        from helpers import fake_window
        config = default_config()
        enable_auto_stance(config)
        brain = Brain(config, FakeNavigator())
        brain.frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], {"stance": "offensive"}, window=fake_window(1920, 1009))
        await brain.tick_and_wait()
        return brain.backend.clicks

    # Perfil 1920x1009 (E03): mãos em (88, 107, 93x30) -> 3º botão no centro (166, 122)
    assert asyncio.run(scenario()) == [(166, 122)]


def test_postura_ja_certa_ou_sem_leitura_nao_clica():
    lure = [det(0, 0.5, 0.5), det(1, 0.6, 0.5)]
    clicks = []
    clicks += run_one_frame(lure, FakeNavigator(), enable_auto_stance, readings={"stance": "defensive"})[1]
    clicks += run_one_frame(lure, FakeNavigator(), enable_auto_stance, readings={"stance": None})[1]
    clicks += run_one_frame(lure, FakeNavigator(), None, readings={"stance": "offensive"})[1]  # auto desligado
    assert clicks == []


def test_captura_aperta_a_bola_e_clica_no_corpo_em_pixels_do_cliente():
    pressed, clicks, _ = run_one_frame([det(0, 0.5, 0.5), det(2, 0.25, 0.5)], FakeNavigator())
    assert pressed == ["f4"]
    assert clicks == [(480, 540)]


class FakeHealRoutine:
    def __init__(self, running=False):
        self.running = running
        self.runs = []

    def should_start(self, cfg, readings, mobs_on_screen, is_boxed):
        return readings.get("player_hp", 100) < 90 and mobs_on_screen == 0 and not is_boxed

    async def run(self, cfg, calibration, screen_size, fallback_revive_key="", danger=None):
        self.runs.append((screen_size, fallback_revive_key))
        return "done"


def test_hp_baixo_sem_selvagens_dispara_a_cura():
    routine = FakeHealRoutine()
    pressed, _, _ = run_one_frame([det(0, 0.5, 0.5)], FakeNavigator(), readings={"player_hp": 70},
                                  heal_routine=routine)
    assert routine.runs == [((1920, 1080), "f2")]
    assert pressed == []


def test_cura_espera_a_box_acabar():
    routine = FakeHealRoutine()
    pressed, _, _ = run_one_frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], FakeNavigator(),
                                  readings={"player_hp": 70}, heal_routine=routine)
    assert routine.runs == []
    assert pressed == ["f1"]  # continua combatendo


def test_combate_pausa_enquanto_a_cura_roda():
    pressed, _, _ = run_one_frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], FakeNavigator(),
                                  heal_routine=FakeHealRoutine(running=True))
    assert pressed == []


def test_sem_deteccoes_nao_faz_nada():
    pressed, _, _ = run_one_frame([], FakeNavigator())
    assert pressed == []


def test_leitura_de_barras_vencida_nao_vale():
    # HP de 5 s atrás (limite 3 s): a cura não começa por uma leitura velha
    async def scenario():
        routine = FakeHealRoutine()
        brain = Brain(heal_routine=routine)
        brain.store.publish("bars", {"player_hp": 50}, at=brain.store.view().at - 5)
        brain.frame([det(0, 0.5, 0.5)])
        await brain.tick_and_wait()
        return routine.runs

    assert asyncio.run(scenario()) == []
