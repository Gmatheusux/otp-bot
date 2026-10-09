import asyncio
import logging
import time
from typing import Callable
from core.action_orchestrator import UtilityOrchestrator
from core.navigator import Navigator
from core.mouse_controller import MouseController
from modules.spatial_analyzer import SpatialAnalyzer
from modules.screen_calibration import STANCES, region_point
from core import humanizer as human
from core.humanizer import HumanProfile
import keyboard
import pyautogui

logger = logging.getLogger("DecisionThread")

def _tap(key: str, hold_s: float):
    keyboard.press(key)
    time.sleep(hold_s)
    keyboard.release(key)

async def press_key_action(key: str):
    """Aperta uma tecla como uma pessoa: respeita o ritmo das mãos e segura a tecla por um tempo variável."""
    if not key:
        return  # tecla ainda não escolhida no console; o aviso já sai no log
    hz = human.get()
    await hz.before_input()
    await asyncio.to_thread(_tap, key, hz.key_hold())

async def auto_catch_action(mouse_controller: MouseController, catch_key: str, screen_x: int, screen_y: int):
    """Corrotina para acionar a pokebola e clicar na coordenada do cadáver."""
    await press_key_action(catch_key)
    target = human.get().jitter_point((screen_x, screen_y), 2.0)
    await human.get().before_input()  # tempo da bola "engatilhar" no cursor, variável
    await asyncio.to_thread(mouse_controller.click, target)
    logger.info(f">>> [AUTO CATCH] Pokebola jogada em {target}! <<<")

async def click_action(mouse_controller: MouseController, point: tuple):
    """Clica num ponto da interface sem travar o loop (mira com alguns pixels de imprecisão)."""
    hz = human.get()
    await hz.before_input()
    await asyncio.to_thread(mouse_controller.click, hz.jitter_point(point, 1.5))

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
    telemetry: dict = None,
    heal_routine=None
) -> None:
    """
    Thread de Decisão Assíncrona: Cérebro Try-Hard (Foco no Summon).
    Avalia a visão espacial para controlar a utilidade de combate.
    A config é relida a cada frame, então mudanças no console valem na hora.
    """
    logger.info("Cérebro Try-Hard (Decision Thread) iniciado.")

    spatial = SpatialAnalyzer()
    screen_w, screen_h = pyautogui.size()
    human_cfg = None
    last_phase = None
    last_corpses = 0
    react_until = 0.0   # só age depois do tempo de reação a cada mudança de fase
    catch_ready_at = 0.0

    while not kill_event.is_set():
        await pause_event.wait()
        if kill_event.is_set():
            break

        try:
            try:
                detections = await asyncio.wait_for(state_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            # Rotina de cura rodando (ex: disparada pelo botão de teste): ela está no controle
            if heal_routine is not None and heal_routine.running:
                state_queue.task_done()
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
            hz = human.get()
            if config.get("features", {}).get("human") != human_cfg:
                human_cfg = config.get("features", {}).get("human")
                hz.set_profile(HumanProfile.from_config(human_cfg))
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
                telemetry["apm"] = hz.actions_last_minute()

            # Tempo de reação: uma pessoa não age no mesmo frame em que algo novo aparece
            now = time.monotonic()
            phase = combat_phase(is_boxed, mobs_on_screen)
            if phase != last_phase:
                last_phase = phase
                react_until = now + hz.reaction_delay()
            if len(dead_pokemons) > last_corpses:
                catch_ready_at = now + hz.reaction_delay()
            last_corpses = len(dead_pokemons)
            if now < react_until:
                state_queue.task_done()
                await asyncio.sleep(0.01)
                continue

            # Cura com pokémon: HP baixo e área limpa -> curador, rotação, revive, volta ao farm
            heal_cfg = config.get("features", {}).get("heal", {}).get("pokemon_heal", {})
            readings = (telemetry or {}).get("readings", {})
            if heal_routine is not None and heal_routine.should_start(heal_cfg, readings, mobs_on_screen, is_boxed):
                def danger() -> bool:
                    # Olha o frame mais novo da percepção sem esperar; sem frame novo, segue a rotina
                    try:
                        fresh = state_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        return False
                    state_queue.task_done()
                    s = spatial.calculate_spatial_state(fresh)
                    return s["is_boxed"] or s["mobs_on_screen"] > 0

                resume_route = navigator.is_playing
                if resume_route:
                    navigator.stop_playback()
                result = await heal_routine.run(heal_cfg, config.get("calibration", {}), (screen_w, screen_h),
                                                fallback_revive_key=revive_key, danger=danger)
                if resume_route and result == "done":
                    asyncio.create_task(navigator.play_route())
                state_queue.task_done()
                continue

            # Postura automática: clica na mão (ofensivo/neutro/defensivo) definida para a fase atual
            stance_cfg = config.get("features", {}).get("stance", {})
            if stance_cfg.get("auto") and telemetry is not None:
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
                # Cada ação volta só quando a própria recarga acabar: nada de rajada acima do limite humano

            elif mobs_on_screen > 0:
                # Dano na corrida (Kite)
                if combat.get("auto_combo", True) and combat.get("kite_combo", True) and orchestrator.can_execute("auto_combo"):
                    logger.info(">>> [CÉREBRO TRY-HARD] Kiting: Soltando AOE na corrida! <<<")
                    await orchestrator.execute("auto_combo", press_key_action, auto_combo_key)

            # Auto Catch (Livre de caixa)
            elif dead_pokemons and catch_enabled:
                if now >= catch_ready_at and orchestrator.can_execute("catch"):
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
