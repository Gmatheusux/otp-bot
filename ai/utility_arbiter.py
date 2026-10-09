import time
from .fuzzy_engine import FuzzyUtilityEngine

# Importação condicional/mock para simular a arquitetura Zero-Context do core
try:
    from core.keyboard import KeyboardController
    from core.mouse import MouseController
except ImportError:
    class KeyboardController:
        def press(self, key):
            print(f"[ZERO-CONTEXT KEYBOARD] Pressing {key} with Bezier noise...")
    class MouseController:
        def move_and_click(self, x, y, button='left'):
            print(f"[ZERO-CONTEXT MOUSE] Moving to ({x}, {y}) using Bezier and clicking {button}...")

class UtilityArbiter:
    """
    Orquestrador que consome as notas do FuzzyEngine e aciona os atuadores.
    Roda na Thread de Decisão.
    """
    def __init__(self):
        self.fuzzy_engine = FuzzyUtilityEngine()
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        
        # Sistema básico de cooldowns (prevenção de spam)
        self.cooldowns = {
            'heal': 0.0,
            'attack': 0.0,
            'loot': 0.0
        }
        
    def decide_and_act(self, hp: int, monster_count: int):
        """Avalia a utilidade e executa a ação vencedora."""
        scores = self.fuzzy_engine.evaluate(hp, monster_count)
        
        print(f"\n[PERCEPÇÃO] HP: {hp}% | Monstros: {monster_count}")
        print(f"[FUZZY SCORES] Estresse: {scores['stress']:.1f} | Cura: {scores['utility_heal']:.1f} | Ataque: {scores['utility_attack']:.1f}")
        
        now = time.time()
        
        # Ação com maior prioridade: Cura Crítica
        if scores['utility_heal'] > 75.0 and scores['utility_heal'] >= scores['utility_attack']:
            if now >= self.cooldowns['heal']:
                print(">> DECISÃO: Curar (Exura Vita / Potion)")
                self.keyboard.press('F1')
                self.cooldowns['heal'] = now + 1.2 # Cooldown de 1.2s
            else:
                print(">> DECISÃO: Aguardando cooldown da cura...")
                
        # Segunda prioridade: Ataque em Área
        elif scores['utility_attack'] > 60.0:
            if now >= self.cooldowns['attack']:
                print(">> DECISÃO: Ataque AoE (Exori Gran)")
                self.keyboard.press('F2')
                self.cooldowns['attack'] = now + 2.0 # Cooldown de 2.0s
            else:
                print(">> DECISÃO: Aguardando cooldown de ataque...")
                
        # Fallback
        else:
            print(">> DECISÃO: Idle / Movimentação Tática (Notas de utilidade muito baixas)")
