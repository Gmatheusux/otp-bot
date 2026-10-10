import asyncio
import time
import logging
import keyboard
from typing import Any, Dict, Optional

from otpbot.platform.input_backend import DEFAULT_BACKEND, make_backend, parse_key

logger = logging.getLogger("BotRuntime")


class BotRuntime:
    """
    Estado compartilhado entre o loop do bot e a API do console.
    Toda mutação de evento passa por call_soon_threadsafe, então pode ser
    chamada tanto do loop asyncio quanto das threads de hotkey/janela.
    """
    def __init__(self, loop: asyncio.AbstractEventLoop, pause_event: asyncio.Event, kill_event: asyncio.Event,
                 config_manager, navigator=None, sprites=None):
        self.loop = loop
        self.sprites = sprites
        self.pause_event = pause_event
        self.kill_event = kill_event
        self.config_manager = config_manager
        self.navigator = navigator
        self.started_at = time.time()
        self._hotkey_handles = []
        self.telemetry: Dict[str, Any] = {
            "device": "desconhecido",
            "model": None,
            "fps": 0.0,
            "detections": 0,
            "mobs_on_screen": 0,
            "is_boxed": False,
            "readings": {},  # barras lidas pela calibração (HP, EXP, time)
            "heal_routine": "parado",
            "game_window": None,      # "1920x1009 em \\.\DISPLAY2" ou None
            "input_backend": None,
            "integrity": None,        # D20: {"ok", "bot", "game", "message"}
            "active_behavior": None,
            "input_owner": None,
        }
        self.heal_routine = None
        self.arbiter = None   # brain/arbiter.py; dono da trava de entrada
        self.locator = None   # perception/capture.GameLocator
        self.queue = None     # actuation/action_queue.ActionQueue

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.pause_event.is_set(),
            "stopping": self.kill_event.is_set(),
            "cavebot_playing": bool(self.navigator and self.navigator.is_playing),
            "cavebot_recording": bool(self.navigator and self.navigator.is_recording),
            "uptime_s": int(time.time() - self.started_at),
            **self.telemetry,
        }

    def set_running(self, running: bool):
        def apply():
            if running and not self.pause_event.is_set():
                logger.info(">>> BOT RETOMADO <<<")
                self.pause_event.set()
            elif not running and self.pause_event.is_set():
                logger.info(">>> BOT PAUSADO <<<")
                self.pause_event.clear()
                if self.arbiter is not None:
                    self.loop.create_task(self.arbiter.halt())  # corta a entrada já, sem esperar o tick
        self.loop.call_soon_threadsafe(apply)

    def toggle_running(self):
        self.set_running(not self.pause_event.is_set())

    def stop(self):
        def kill():
            if not self.kill_event.is_set():
                logger.warning(">>> KILL SWITCH ACIONADO - INICIANDO SHUTDOWN <<<")
                self.kill_event.set()
                if self.arbiter is not None:
                    self.arbiter.lock.revoke_all()  # nada mais sai, nem o que já estava na fila
                # Libera quem estiver bloqueado em pause_event.wait() para enxergar o kill
                self.pause_event.set()
        try:
            self.loop.call_soon_threadsafe(kill)
        except RuntimeError:
            pass  # loop já encerrado

    def toggle_cavebot(self):
        if not self.navigator:
            return
        def apply():
            if self.navigator.is_playing:
                self.navigator.stop_playback()
            else:
                self.loop.create_task(self.navigator.play_route())
        self.loop.call_soon_threadsafe(apply)

    def toggle_recording(self):
        if self.navigator:
            self.loop.call_soon_threadsafe(self.navigator.toggle_recording)

    def heal_test(self, action: str, delay_s: float) -> bool:
        """Botões de teste da cura: troca para o curador/farm ou roda a rotina inteira."""
        routine = getattr(self, "heal_routine", None)
        if routine is None or routine.running or self.arbiter is None:
            return False

        async def test():
            config = self.config_manager.config
            cfg = config.get("features", {}).get("heal", {}).get("pokemon_heal", {})
            calibration = config.get("calibration", {})
            window = self.locator.window() if self.locator else None
            if window is None:
                logger.warning("Teste da cura: janela do jogo não encontrada.")
                return
            size = window.size  # cliques em pixels da área cliente
            if action == "full":
                revive = config.get("pokemon_profile", {}).get("revive_key", "")
                result = await routine.run(cfg, calibration, size, fallback_revive_key=revive)
                logger.info(f"Teste da cura terminou: {result}")
            else:
                ok = await routine.swap(cfg, action, calibration, size)
                who = "de cura" if action == "healer" else "de farm"
                logger.info(f"Teste: troca para o pokémon {who} {'enviada' if ok else 'não configurada'}")

        async def job():
            await asyncio.sleep(delay_s)
            # Passa pela trava como a Hunt: a Segurança ainda pode interromper
            if not await self.arbiter.run_exclusive("teste_cura", test):
                logger.warning("Teste da cura não rodou: outro comportamento está com a entrada.")

        self.loop.create_task(job())
        return True

    def apply_hotkeys(self):
        """(Re)registra as hotkeys globais a partir do config atual."""
        hotkeys = self.config_manager.get_hotkeys()
        bindings = {
            "pause": (hotkeys.get("pause", "f8"), self.toggle_running),
            "kill": (hotkeys.get("kill", "f9"), self.stop),
            "record": (hotkeys.get("record", "f10"), self.toggle_recording),
            "play": (hotkeys.get("play", "f11"), self.toggle_cavebot),
        }
        # unhook_all_hotkeys() da lib quebra antes do primeiro hook; removemos os nossos um a um
        for handle in self._hotkey_handles:
            keyboard.remove_hotkey(handle)
        self._hotkey_handles = []
        for name, (key, callback) in bindings.items():
            try:
                self._hotkey_handles.append(keyboard.add_hotkey(key, callback))
            except ValueError:
                logger.error(f"Hotkey '{name}' inválida: '{key}'. Ajuste na aba Atalhos.")
        logger.info("Hotkeys -> " + " | ".join(f"{n.upper()}: [{k.upper()}]" for n, (k, _) in bindings.items()))

    def validate_game_keys(self):
        """Avisa no log sobre teclas do jogo que o bot não consegue apertar."""
        config = self.config_manager.config
        keys = {
            "Combo": config.get("pokemon_profile", {}).get("auto_combo_key"),
            "Revive": config.get("pokemon_profile", {}).get("revive_key"),
            "Defesa": config.get("pokemon_profile", {}).get("defensive_buff_key"),
            "Pokébola": config.get("hotkeys", {}).get("catch_key"),
        }
        for label, key in keys.items():
            if not key:
                logger.warning(f"Tecla de {label} não definida: o bot não vai usar essa ação. Escolha na aba Atalhos.")
                continue
            try:
                parse_key(key)
            except ValueError as e:
                logger.warning(f"Tecla de {label} inválida: '{key}' ({e}). Use a captura de tecla na aba Atalhos.")

    def apply_input_backend(self):
        """Backend de entrada da config (`input.backend`): background (padrão, D11) ou foreground."""
        if self.queue is None:
            return
        name = self.config_manager.config.get("input", {}).get("backend", DEFAULT_BACKEND)
        current = getattr(self.queue.backend, "name", None)
        if current == name:
            return
        if self.queue.backend is not None:
            self.queue.release_all()
        self.queue.backend = make_backend(name, self.locator.window if self.locator else (lambda: None))
        self.telemetry["input_backend"] = self.queue.backend.name
        logger.info(f"Backend de entrada: {self.queue.backend.name}")

    def config_changed(self):
        self.apply_hotkeys()
        self.validate_game_keys()
        self.apply_input_backend()


runtime: Optional[BotRuntime] = None
