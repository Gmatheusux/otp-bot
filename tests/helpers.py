"""Peças falsas para montar a pilha do cérebro sem jogo: WorldState -> Árbitro -> Fila -> Trava -> backend."""
import asyncio

from otpbot.actuation.action_queue import ActionQueue
from otpbot.actuation.input_lock import InputLock
from otpbot.brain.arbiter import Arbiter
from otpbot.brain.behaviors.base import BrainContext
from otpbot.brain.behaviors.companion import CompanionBehavior
from otpbot.brain.behaviors.hunt import HuntBehavior
from otpbot.brain.behaviors.safety import SafetyBehavior
from otpbot.brain.behaviors.survival import SurvivalBehavior
from otpbot.interface.config_manager import ConfigManager
from otpbot.platform.game_window import GameWindow, Rect
from otpbot.platform.input_backend import InputBackend
from otpbot.state.world_state import WorldStore


class RecordingBackend(InputBackend):
    """Registra cada envio junto com o dono da trava NAQUELE instante."""
    name = "fake"

    def __init__(self, lock: InputLock):
        self.lock = lock
        self.events = []

    def key(self, name, hold=0.08):
        self.events.append(("tecla", name, self.lock.current))

    def click(self, x, y, button="left"):
        self.events.append(("clique", (x, y), self.lock.current))

    @property
    def keys(self):
        return [e[1] for e in self.events if e[0] == "tecla"]

    @property
    def clicks(self):
        return [e[1] for e in self.events if e[0] == "clique"]


async def direct(fn, *args):
    return fn(*args)


async def no_sleep(_):
    await asyncio.sleep(0)


def fake_window(w=1920, h=1080):
    return GameWindow(hwnd=1, client=Rect(0, 0, w, h), monitor=None, foreground=False, minimized=False)


def det(class_id, x, y):
    return {"class_id": class_id, "confidence": 0.9,
            "box_relative": {"x_center": x, "y_center": y, "width": 0.02, "height": 0.02}}


def default_config():
    config = ConfigManager.__new__(ConfigManager)._default_config()
    config["cooldowns"] = {}  # mantém os cooldowns de 10s registrados no Brain
    config["pokemon_profile"]["defensive_buff_key"] = "f3"
    return config


class Brain:
    """Pilha completa com backend falso. `extra` = comportamentos a mais (para testar interrupção)."""

    def __init__(self, config=None, navigator=None, heal_routine=None, extra=(), killed=None):
        self.lock = InputLock()
        self.backend = RecordingBackend(self.lock)
        self.queue = ActionQueue(self.lock, self.backend, sleep=no_sleep, run_blocking=direct)
        for name in ("defensive_buff", "auto_combo", "revive", "catch", "stance"):
            self.queue.register_action(name, 10.0)
        self.store = WorldStore()
        self.config = config if config is not None else default_config()
        self.telemetry = {"readings": {}}
        self.killed = killed if killed is not None else []
        self.ctx = BrainContext(queue=self.queue, store=self.store, telemetry=self.telemetry, navigator=navigator,
                                heal_routine=heal_routine, kill=lambda: self.killed.append(True))
        self.pause, self.kill = asyncio.Event(), asyncio.Event()
        self.pause.set()
        behaviors = [SafetyBehavior(self.ctx), CompanionBehavior(), SurvivalBehavior(), HuntBehavior(self.ctx),
                     *extra]
        self.arbiter = Arbiter(behaviors, self.store, self.lock, self.queue, lambda: self.config,
                               self.pause, self.kill, self.telemetry)

    def frame(self, detections, readings=None, window=None):
        self.store.publish("window", window or fake_window())
        if readings is not None:
            self.store.publish("bars", readings)
        self.store.publish("detections", detections)

    async def tick_and_wait(self):
        await self.arbiter.tick()
        task = self.arbiter._task
        if task is not None:
            await asyncio.wait_for(asyncio.shield(task), timeout=3)
