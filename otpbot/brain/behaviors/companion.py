"""
otpbot/brain/behaviors/companion.py — Companion: sua entrada no jogo pausa o bot.

Só ocupa o lugar na prioridade; a regra (entrada com o jogo em foco ou mouse sobre a janela) é da E10.
"""
from otpbot.brain.behaviors.base import COMPANION, Behavior


class CompanionBehavior(Behavior):
    name = "companion"
    priority = COMPANION

    def wants(self, ws, cfg) -> bool:
        return False
