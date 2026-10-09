import asyncio
import time
import logging
import keyboard
from typing import Any, Dict, Optional

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
        }
        self.heal_routine = None

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
        self.loop.call_soon_threadsafe(apply)

    def toggle_running(self):
        self.set_running(not self.pause_event.is_set())

    def stop(self):
        def kill():
            if not self.kill_event.is_set():
                logger.warning(">>> KILL SWITCH ACIONADO - INICIANDO SHUTDOWN <<<")
                self.kill_event.set()
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
        if routine is None or routine.running:
            return False

        async def job():
            import pyautogui
            await asyncio.sleep(delay_s)
            config = self.config_manager.config
            cfg = config.get("features", {}).get("heal", {}).get("pokemon_heal", {})
            calibration = config.get("calibration", {})
            size = tuple(pyautogui.size())
            if action == "full":
                revive = config.get("pokemon_profile", {}).get("revive_key", "")
                result = await routine.run(cfg, calibration, size, fallback_revive_key=revive)
                logger.info(f"Teste da cura terminou: {result}")
            else:
                ok = await routine.swap(cfg, action, calibration, size)
                who = "de cura" if action == "healer" else "de farm"
                logger.info(f"Teste: troca para o pokémon {who} {'enviada' if ok else 'não configurada'}")

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
                keyboard.key_to_scan_codes(key)
            except ValueError:
                logger.warning(f"Tecla de {label} inválida: '{key}'. Use a captura de tecla na aba Atalhos.")

    def config_changed(self):
        self.apply_hotkeys()
        self.validate_game_keys()


runtime: Optional[BotRuntime] = None
