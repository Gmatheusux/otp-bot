import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Garante que o interpretador ache os módulos na raiz do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.utility_arbiter import UtilityArbiter

class MockVisionEngine:
    def __init__(self):
        self.hp = 30
        self.monster_count = 0
        
    def read_state(self):
        return self.hp, self.monster_count

class TestE2EEmulation(unittest.TestCase):
    @patch('ai.utility_arbiter.MouseController')
    @patch('ai.utility_arbiter.KeyboardController')
    def test_critical_heal_trigger(self, MockKeyboard, MockMouse):
        # Arrange
        mock_keyboard_instance = MagicMock()
        MockKeyboard.return_value = mock_keyboard_instance
        
        arbiter = UtilityArbiter()
        vision = MockVisionEngine()
        
        hp, monsters = vision.read_state()
        
        # Força o tempo interno (Mock time) para garantir passagem no cooldown inicial
        with patch('time.time', return_value=1000.0):
            # Act
            arbiter.decide_and_act(hp, monsters)
            
        # Assert
        # Valida se o bot acionou FISICAMENTE a tecla F1 perante o mock de HP = 30%
        mock_keyboard_instance.press.assert_called_with('F1')
        
if __name__ == '__main__':
    unittest.main()
