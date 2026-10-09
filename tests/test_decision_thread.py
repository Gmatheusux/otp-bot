import asyncio
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import decision_thread as dt
from core.action_orchestrator import UtilityOrchestrator
from core.config_manager import ConfigManager


class FakeNavigator:
    def __init__(self, is_playing=False):
        self.is_playing = is_playing
        self.stopped = False

    def stop_playback(self):
        self.is_playing = False
        self.stopped = True


def det(class_id, x, y):
    return {"class_id": class_id, "confidence": 0.9,
            "box_relative": {"x_center": x, "y_center": y, "width": 0.02, "height": 0.02}}


def run_one_frame(detections, navigator, config_patch=None):
    """Roda a decision_thread com um único frame e devolve as teclas apertadas."""
    pressed = []

    async def fake_press(key):
        pressed.append(key)

    async def scenario():
        orchestrator = UtilityOrchestrator()
        for name in ("defensive_buff", "auto_combo", "revive", "catch"):
            orchestrator.register_action(name, 10.0)
        queue = asyncio.Queue(maxsize=1)
        pause, kill = asyncio.Event(), asyncio.Event()
        pause.set()
        telemetry = {}
        config = ConfigManager.__new__(ConfigManager)._default_config()
        config["cooldowns"] = {}  # mantém os cooldowns de 10s registrados acima
        config["pokemon_profile"]["defensive_buff_key"] = "f3"
        if config_patch:
            config_patch(config)

        task = asyncio.create_task(dt.decision_thread(
            orchestrator, navigator, None, lambda: config, queue, pause, kill, telemetry))
        await queue.put(detections)
        await asyncio.sleep(0.1)
        kill.set()
        await asyncio.wait_for(task, timeout=3)
        return telemetry

    with patch.object(dt, "press_key_action", fake_press), \
         patch.object(dt.pyautogui, "size", return_value=(1920, 1080)):
        telemetry = asyncio.run(scenario())
    return pressed, telemetry


def test_combo_dispara_sem_cavebot():
    # Antes da correção nada acontecia se a rota não estivesse tocando
    pressed, telemetry = run_one_frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], FakeNavigator(is_playing=False))
    assert pressed == ["f1"]
    assert telemetry["mobs_on_screen"] == 1


def test_boxed_para_a_rota_e_solta_defesa_combo_revive():
    mobs = [det(1, 0.5 + 0.01 * i, 0.5) for i in range(8)]
    navigator = FakeNavigator(is_playing=True)
    pressed, telemetry = run_one_frame([det(0, 0.5, 0.5)] + mobs, navigator)
    assert navigator.stopped
    assert pressed == ["f3", "f1", "f2"]
    assert telemetry["is_boxed"] is True


def test_toggles_do_console_desligam_o_combo():
    def disable_combo(config):
        config["features"]["combat"]["auto_combo"] = False
    pressed, _ = run_one_frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)], FakeNavigator(), disable_combo)
    assert pressed == []


def test_limiar_de_cercado_vem_da_config():
    def three_mobs_is_boxed(config):
        config["features"]["combat"]["boxed_mobs"] = 3
    mobs = [det(1, 0.5 + 0.01 * i, 0.5) for i in range(3)]
    pressed, telemetry = run_one_frame([det(0, 0.5, 0.5)] + mobs, FakeNavigator(), three_mobs_is_boxed)
    assert telemetry["is_boxed"] is True
    assert pressed == ["f3", "f1", "f2"]


def test_tecla_nao_definida_nao_e_apertada():
    def no_defense_key(config):
        config["pokemon_profile"]["defensive_buff_key"] = ""
    mobs = [det(1, 0.5 + 0.01 * i, 0.5) for i in range(8)]
    with patch.object(dt.keyboard, "send") as send:
        asyncio.run(dt.press_key_action(""))
    send.assert_not_called()
    pressed, _ = run_one_frame([det(0, 0.5, 0.5)] + mobs, FakeNavigator(), no_defense_key)
    assert "f1" in pressed and "f2" in pressed


def test_sem_deteccoes_nao_faz_nada():
    pressed, _ = run_one_frame([], FakeNavigator())
    assert pressed == []
