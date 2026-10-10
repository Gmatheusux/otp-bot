"""
otpbot/brain/behaviors/survival.py — Sobrevivência: pokémon desmaiou → revive.

Só ocupa o lugar na prioridade; a regra é da E10. O revive de hoje (depois do combo quando cercado) continua
dentro da Hunt, como antes.
"""
from otpbot.brain.behaviors.base import SURVIVAL, Behavior


class SurvivalBehavior(Behavior):
    name = "survival"
    priority = SURVIVAL

    def wants(self, ws, cfg) -> bool:
        return False
