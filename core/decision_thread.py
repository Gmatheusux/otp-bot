import asyncio
import logging
from typing import Callable
from core.action_orchestrator import UtilityOrchestrator
from core.navigator import Navigator
from core.mouse_controller import MouseController
from modules.spatial_analyzer import SpatialAnalyzer
from modules.screen_calibration import STANCES, region_point
import keyboard
import pyautogui

logger = logging.getLogger("DecisionThread")

async def press_key_action(key: str):
    """Corrotina helper para apertar tecla de forma não-bloqueante."""
    if not key:
        return  # tecla ainda não escolhida no console; o aviso já sai no log
    await asyncio.to_thread(keyboard.send, key)

async def auto_catch_action(mouse_controller: MouseController, catch_key: str, screen_x: int, screen_y: int):
    """Corrotina para acionar a pokebola e clicar na coordenada do cadáver."""
    await press_key_action(catch_key)
    await asyncio.sleep(0.1) # Breve delay para a pokebola "engatilhar" no cursor
    await asyncio.to_thread(mouse_controller.click, (screen_x, screen_y))
    logger.info(f">>> [AUTO CATCH] Pokebola jogada em ({screen_x}, {screen_y})! <<<")

async def click_action(mouse_controller: MouseController, point: tuple):
    """Corrotina para clicar num ponto da interface sem travar o loop."""
    await asyncio.to_thread(mouse_controller.click, point)

STANCE_LABELS = {"offensive": "Ofensivo", "neutral": "Neutro", "defensive": "Defensivo"}

def combat_phase(is_boxed: bool, mobs_on_screen: int) -> str:
    """normal = sem selvagens | lure = juntando selvagens | combo = cercado, hora do combo."""
    if is_boxed:
        return "combo"
    return "lure" if mobs_on_screen > 0 else "normal"

async def decision_thread(
    orchestrator: UtilityOrchestrator,
    navigator: Navigator,
    mouse_controller: MouseController,
    get_config: Callable[[], dict],
    state_queue: asyncio.Queue,
    pause_event: asyncio.Event,
    kill_event: asyncio.Event,
    telemetry: dict = None
) -> None:
    """
    Thread de Decisão Assíncrona: Cérebro Try-Hard (Foco no Summon).
    Avalia a visão espacial para controlar a utilidade de combate.
    A config é relida a cada frame, então mudanças no console valem na hora.
    """
    logger.info("Cérebro Try-Hard (Decision Thread) iniciado.")

    spatial = SpatialAnalyzer()
    screen_w, screen_h = pyautogui.size()

    while not kill_event.is_set():
        await pause_event.wait()
        if kill_event.is_set():
            break

        try:
            try:
                detections = await asyncio.wait_for(state_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            config = get_config()
            profile = config.get("pokemon_profile", {})
            combat = config.get("features", {}).get("combat", {})
            catch_enabled = config.get("features", {}).get("catch", {}).get("enabled", True)
            auto_combo_key = profile.get("auto_combo_key", "f1")
            revive_key = profile.get("revive_key", "f2")
            defensive_buff_key = profile.get("defensive_buff_key", "")
            catch_key = config.get("hotkeys", {}).get("catch_key", "f4")
            orchestrator.sync_cooldowns(config.get("cooldowns", {}))
            spatial.radius_threshold = combat.get("boxed_radius_pct", 15) / 100.0
            spatial.boxed_mob_count = int(combat.get("boxed_mobs", 8))

            # Extrai o estado espacial relativo ao Summon
            state = spatial.calculate_spatial_state(detections)
            mobs_on_screen = state.get("mobs_on_screen", 0)
            is_boxed = state.get("is_boxed", False)
            dead_pokemons = state.get("dead_pokemons", [])
            if telemetry is not None:
                telemetry["mobs_on_screen"] = mobs_on_screen
                telemetry["is_boxed"] = is_boxed

            # Postura automática: clica na mão (ofensivo/neutro/defensivo) definida para a fase atual
            stance_cfg = config.get("features", {}).get("stance", {})
            if stance_cfg.get("auto") and telemetry is not None:
                phase = combat_phase(is_boxed, mobs_on_screen)
                desired = stance_cfg.get(phase)
                current = telemetry.get("readings", {}).get("stance")
                # Sem leitura confiável da postura atual, não clica no escuro
                if desired in STANCES and current and current != desired and orchestrator.can_execute("stance"):
                    point = region_point(config.get("calibration", {}), "stance", screen_w, screen_h, STANCES.index(desired))
                    if point:
                        logger.info(f">>> [POSTURA] {STANCE_LABELS[current]} -> {STANCE_LABELS[desired]} (fase: {phase}) <<<")
                        await orchestrator.execute("stance", click_action, mouse_controller, point)

            # O combate vale com ou sem cavebot; a rota só é interrompida quando estiver tocando
            if is_boxed and combat.get("boxed_defense", True):
                # Limite de monstros ao redor do Summon (Dense Lure)
                if navigator.is_playing and combat.get("stop_route_when_boxed", True):
                    logger.warning(">>> [CÉREBRO TRY-HARD] Summon Boxed (Dense Lure)! Parando navegação e ativando Defesa! <<<")
                    navigator.stop_playback()
                else:
                    logger.warning(">>> [CÉREBRO TRY-HARD] Summon Boxed (Dense Lure)! Ativando Defesa! <<<")

                if orchestrator.can_execute("defensive_buff"):
                    await orchestrator.execute("defensive_buff", press_key_action, defensive_buff_key)

                if combat.get("auto_combo", True) and orchestrator.can_execute("auto_combo"):
                    await orchestrator.execute("auto_combo", press_key_action, auto_combo_key)

                if combat.get("revive_on_boxed", True) and orchestrator.can_execute("revive"):
                    await orchestrator.execute("revive", press_key_action, revive_key)

                # Reset instantâneo após o combo de sobrevivência
                orchestrator.force_reset_all_timers()

            elif mobs_on_screen > 0:
                # Dano na corrida (Kite)
                if combat.get("auto_combo", True) and combat.get("kite_combo", True) and orchestrator.can_execute("auto_combo"):
                    logger.info(">>> [CÉREBRO TRY-HARD] Kiting: Soltando AOE na corrida! <<<")
                    await orchestrator.execute("auto_combo", press_key_action, auto_combo_key)

            # Auto Catch (Livre de caixa)
            elif dead_pokemons and catch_enabled:
                if orchestrator.can_execute("catch"):
                    corpse_x_rel, corpse_y_rel = dead_pokemons[0]
                    abs_x = int(corpse_x_rel * screen_w)
                    abs_y = int(corpse_y_rel * screen_h)
                    await orchestrator.execute("catch", auto_catch_action, mouse_controller, catch_key, abs_x, abs_y)

            state_queue.task_done()
            await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Erro na thread de decisão: {e}")
            await asyncio.sleep(1)

    logger.info("Thread de Decisão encerrada (Kill Event).")
