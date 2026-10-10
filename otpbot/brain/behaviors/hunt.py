"""
otpbot/brain/behaviors/hunt.py — Hunt: as regras de combate de antes da E03, portadas sem mudar o que fazem.

Ordem (igual à da antiga decision_thread): cura com pokémon (rotina longa) → postura automática → cercado
(para a rota, defesa, combo, revive, zera os timers) → kite → captura. A máquina de fases (andar, lurar, parar…)
é da E10.

Coordenadas: as detecções são relativas à área cliente do jogo, e todo clique sai em pixels do cliente.
"""
import asyncio
import logging

from otpbot.actuation.action_queue import Click, KeyPress, Wait
from otpbot.brain.behaviors.base import HUNT, Behavior, BrainContext
from otpbot.perception.bars import STANCES, region_point
from otpbot.perception.spatial_analyzer import SpatialAnalyzer

logger = logging.getLogger("Hunt")

STANCE_LABELS = {"offensive": "Ofensivo", "neutral": "Neutro", "defensive": "Defensivo"}


def combat_phase(is_boxed: bool, mobs_on_screen: int) -> str:
    """normal = sem selvagens | lure = juntando selvagens | combo = cercado, hora do combo."""
    if is_boxed:
        return "combo"
    return "lure" if mobs_on_screen > 0 else "normal"


def catch_actions(catch_key: str, x: int, y: int):
    """Pokébola: tecla, breve espera para a bola "engatilhar" no cursor, clique no corpo."""
    return KeyPress(catch_key), Wait(0.1), Click(x, y)


class HuntBehavior(Behavior):
    name = "hunt"
    priority = HUNT

    def __init__(self, ctx: BrainContext):
        self.ctx = ctx
        self.spatial = SpatialAnalyzer()

    def wants(self, ws, cfg) -> bool:
        return True  # é o comportamento padrão: roda sempre que nada mais importante quer

    def _configure_spatial(self, combat: dict) -> None:
        self.spatial.radius_threshold = combat.get("boxed_radius_pct", 15) / 100.0
        self.spatial.boxed_mob_count = int(combat.get("boxed_mobs", 8))

    async def step(self, ws, cfg, lease) -> None:
        ctx, queue = self.ctx, self.ctx.queue
        detections = ws.get("detections")
        window = ws.get("window")
        if detections is None or window is None:
            return  # sem frame confiável do jogo: não age
        detections_seq = ws.reading("detections").seq

        # Rotina de cura rodando (ex: disparada pelo botão de teste): ela está no controle
        if ctx.heal_routine is not None and ctx.heal_routine.running:
            return

        config = cfg
        profile = config.get("pokemon_profile", {})
        combat = config.get("features", {}).get("combat", {})
        catch_enabled = config.get("features", {}).get("catch", {}).get("enabled", True)
        auto_combo_key = profile.get("auto_combo_key", "f1")
        revive_key = profile.get("revive_key", "f2")
        defensive_buff_key = profile.get("defensive_buff_key", "")
        catch_key = config.get("hotkeys", {}).get("catch_key", "f4")
        queue.sync_cooldowns(config.get("cooldowns", {}))
        self._configure_spatial(combat)
        client_w, client_h = window.size

        state = self.spatial.calculate_spatial_state(detections)
        mobs_on_screen = state.get("mobs_on_screen", 0)
        is_boxed = state.get("is_boxed", False)
        dead_pokemons = state.get("dead_pokemons", [])
        ctx.telemetry["mobs_on_screen"] = mobs_on_screen
        ctx.telemetry["is_boxed"] = is_boxed

        navigator = ctx.navigator
        readings = ws.get("bars", {})

        # Cura com pokémon: HP baixo e área limpa -> curador, rotação, revive, volta ao farm
        heal_cfg = config.get("features", {}).get("heal", {}).get("pokemon_heal", {})
        heal_routine = ctx.heal_routine
        if heal_routine is not None and heal_routine.should_start(heal_cfg, readings, mobs_on_screen, is_boxed):
            seen = [detections_seq]

            def danger() -> bool:
                # Olha o frame mais novo da percepção sem esperar; sem frame novo, segue a rotina
                fresh = ctx.store.latest("detections")
                if fresh is None or fresh.seq <= seen[0] or fresh.value is None:
                    return False
                seen[0] = fresh.seq
                s = self.spatial.calculate_spatial_state(fresh.value)
                return s["is_boxed"] or s["mobs_on_screen"] > 0

            resume_route = navigator is not None and navigator.is_playing
            if resume_route:
                navigator.stop_playback()
            result = await heal_routine.run(heal_cfg, config.get("calibration", {}), (client_w, client_h),
                                            fallback_revive_key=revive_key, danger=danger)
            if resume_route and result == "done":
                asyncio.create_task(navigator.play_route())
            return

        # Postura automática: clica na mão (ofensivo/neutro/defensivo) definida para a fase atual
        stance_cfg = config.get("features", {}).get("stance", {})
        if stance_cfg.get("auto"):
            phase = combat_phase(is_boxed, mobs_on_screen)
            desired = stance_cfg.get(phase)
            current = readings.get("stance")
            # Sem leitura confiável da postura atual, não clica no escuro
            if desired in STANCES and current and current != desired and queue.can_execute("stance"):
                point = region_point(config.get("calibration", {}), "stance", client_w, client_h,
                                     STANCES.index(desired))
                if point:
                    logger.info(f">>> [POSTURA] {STANCE_LABELS[current]} -> {STANCE_LABELS[desired]} (fase: {phase}) <<<")
                    await queue.execute(lease, "stance", Click(*point))

        # O combate vale com ou sem cavebot; a rota só é interrompida quando estiver tocando
        if is_boxed and combat.get("boxed_defense", True):
            # Limite de monstros ao redor do Summon (Dense Lure)
            if navigator is not None and navigator.is_playing and combat.get("stop_route_when_boxed", True):
                logger.warning(">>> [CÉREBRO TRY-HARD] Summon Boxed (Dense Lure)! Parando navegação e ativando Defesa! <<<")
                navigator.stop_playback()
            else:
                logger.warning(">>> [CÉREBRO TRY-HARD] Summon Boxed (Dense Lure)! Ativando Defesa! <<<")

            if queue.can_execute("defensive_buff"):
                await queue.execute(lease, "defensive_buff", KeyPress(defensive_buff_key))

            if combat.get("auto_combo", True) and queue.can_execute("auto_combo"):
                await queue.execute(lease, "auto_combo", KeyPress(auto_combo_key))

            if combat.get("revive_on_boxed", True) and queue.can_execute("revive"):
                await queue.execute(lease, "revive", KeyPress(revive_key))

            # Reset instantâneo após o combo de sobrevivência
            queue.force_reset_all_timers()

        elif mobs_on_screen > 0:
            # Dano na corrida (Kite)
            if combat.get("auto_combo", True) and combat.get("kite_combo", True) and queue.can_execute("auto_combo"):
                logger.info(">>> [CÉREBRO TRY-HARD] Kiting: Soltando AOE na corrida! <<<")
                await queue.execute(lease, "auto_combo", KeyPress(auto_combo_key))

        # Auto Catch (Livre de caixa)
        elif dead_pokemons and catch_enabled:
            if queue.can_execute("catch"):
                corpse_x_rel, corpse_y_rel = dead_pokemons[0]
                x, y = int(corpse_x_rel * client_w), int(corpse_y_rel * client_h)
                if await queue.execute(lease, "catch", *catch_actions(catch_key, x, y)):
                    logger.info(f">>> [AUTO CATCH] Pokebola jogada em ({x}, {y})! <<<")
