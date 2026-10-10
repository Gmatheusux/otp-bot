"""
otpbot/brain/behaviors/safety.py — Segurança: mensagem de GM no chat desliga o bot (igual ao de antes da E03).

Corta a entrada na hora, sem deixar a rotina interrompida fazer limpeza (decisão do usuário na E03).
A pausa com aviso e alarme por GM/jogador na tela é da E06.
"""
import logging

from otpbot.brain.behaviors.base import SAFETY, Behavior, BrainContext

logger = logging.getLogger("Safety")


class SafetyBehavior(Behavior):
    name = "safety"
    priority = SAFETY
    allows_cleanup = False

    def __init__(self, ctx: BrainContext):
        self.ctx = ctx

    def wants(self, ws, cfg) -> bool:
        return ws.get("gm_alert") is True

    async def step(self, ws, cfg, lease) -> None:
        logger.critical(">>> KILL EVENT ENGATILHADO PELO CHAT ANALYZER <<<")
        self.ctx.kill()
