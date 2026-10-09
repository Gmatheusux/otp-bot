"""
core/heal_routine.py — Cura do jogador usando um pokémon de cura.

Fluxo: HP do jogador abaixo do limite + nenhum selvagem por perto ->
troca para o pokémon de cura -> rotação de cura -> revive no curador (zera a recarga
das skills) -> volta para o pokémon de farm.
Se aparecer selvagem no meio, aborta e volta para o pokémon de farm na hora.
"""
import asyncio
import logging
import time
from typing import Awaitable, Callable, Dict, Optional, Tuple

from modules.screen_calibration import region_point

logger = logging.getLogger("HealRoutine")

PressKey = Callable[[str], Awaitable[None]]
Click = Callable[[tuple], Awaitable[None]]

DONE, ABORTED, INVALID = "done", "aborted", "invalid"


class PokemonHealRoutine:
    def __init__(self, press_key: PressKey, click: Click, sleep=asyncio.sleep,
                 clock=time.monotonic, telemetry: Optional[dict] = None):
        self._press_key = press_key
        self._click = click
        self._sleep = sleep
        self._clock = clock
        self._lock = asyncio.Lock()
        self._telemetry = telemetry
        self.last_finished = float("-inf")
        self._set_step("parado")

    @property
    def running(self) -> bool:
        return self._lock.locked()

    def _set_step(self, step: str):
        self.step = step
        if self._telemetry is not None:
            self._telemetry["heal_routine"] = step

    def should_start(self, cfg: Dict, readings: Dict, mobs_on_screen: int, is_boxed: bool) -> bool:
        if not cfg.get("enabled") or self.running:
            return False
        hp = (readings or {}).get("player_hp")
        if hp is None:
            return False  # sem leitura de HP, não arrisca trocar de pokémon
        if is_boxed or mobs_on_screen > 0:
            return False  # espera a box acabar
        if self._clock() - self.last_finished < float(cfg.get("cooldown_s", 15)):
            return False
        return hp < float(cfg.get("hp_percent", 90))

    def validate(self, cfg: Dict) -> Optional[str]:
        """Motivo para não rodar, ou None se a configuração está completa."""
        if not [k for k in cfg.get("rotation", []) if k]:
            return "A rotação de cura está vazia."
        if cfg.get("swap_method", "pokebar") == "key":
            if not cfg.get("healer_key") or not cfg.get("farm_key"):
                return "Defina as teclas do pokémon de cura e do de farm."
        elif int(cfg.get("healer_slot", 0)) == int(cfg.get("farm_slot", 0)):
            return "O pokémon de cura e o de farm estão na mesma posição da Pokébar."
        return None

    async def swap(self, cfg: Dict, which: str, calibration: Dict, screen_size: Tuple[int, int]) -> bool:
        """Chama o pokémon 'healer' ou 'farm', pela Pokébar (clique) ou por tecla."""
        if cfg.get("swap_method", "pokebar") == "key":
            key = cfg.get(f"{which}_key", "")
            if not key:
                return False
            await self._press_key(key)
            return True
        slot = int(cfg.get(f"{which}_slot", 1)) - 1
        point = region_point(calibration, "team", screen_size[0], screen_size[1], slot)
        if point is None:
            logger.warning("Pokébar não calibrada: não sei onde clicar para trocar de pokémon.")
            return False
        await self._click(point)
        return True

    async def run(self, cfg: Dict, calibration: Dict, screen_size: Tuple[int, int],
                  fallback_revive_key: str = "", danger: Callable[[], bool] = lambda: False) -> str:
        problem = self.validate(cfg)
        if problem:
            logger.warning(f"Cura com pokémon não rodou: {problem} Ajuste na aba Cura.")
            self.last_finished = self._clock()  # evita repetir o aviso a cada frame
            return INVALID

        async with self._lock:
            delay = float(cfg.get("rotation_delay_ms", 800)) / 1000
            summon_wait = float(cfg.get("summon_wait_ms", 1500)) / 1000
            swapped = False
            try:
                name = cfg.get("healer_name") or f"posição {cfg.get('healer_slot', '?')}"
                logger.info(f">>> [CURA] HP baixo e área limpa: chamando o pokémon de cura ({name}) <<<")
                self._set_step("chamando curador")
                swapped = await self.swap(cfg, "healer", calibration, screen_size)
                if not swapped:
                    return INVALID
                await self._sleep(summon_wait)
                if danger():
                    return await self._abort(cfg, calibration, screen_size, summon_wait)

                self._set_step("rotação de cura")
                for key in [k for k in cfg.get("rotation", []) if k]:
                    await self._press_key(key)
                    await self._sleep(delay)
                    if danger():
                        return await self._abort(cfg, calibration, screen_size, summon_wait)

                revive_key = cfg.get("revive_key") or fallback_revive_key
                if cfg.get("use_revive", True) and revive_key:
                    self._set_step("revive no curador")
                    await self._press_key(revive_key)
                    await self._sleep(delay)

                self._set_step("voltando ao farm")
                await self.swap(cfg, "farm", calibration, screen_size)
                swapped = False
                await self._sleep(summon_wait)
                logger.info(">>> [CURA] Rotina concluída, de volta ao pokémon de farm <<<")
                return DONE
            finally:
                if swapped and self.step != "voltando ao farm":
                    # Erro inesperado no meio: nunca deixar o curador em campo
                    await self.swap(cfg, "farm", calibration, screen_size)
                self.last_finished = self._clock()
                self._set_step("parado")

    async def _abort(self, cfg, calibration, screen_size, summon_wait) -> str:
        logger.warning(">>> [CURA] Selvagens apareceram: abortando e voltando ao pokémon de farm <<<")
        self._set_step("voltando ao farm")
        await self.swap(cfg, "farm", calibration, screen_size)
        await self._sleep(summon_wait)
        return ABORTED
