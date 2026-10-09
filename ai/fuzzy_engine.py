import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class FuzzyUtilityEngine:
    """
    Motor de Lógica Fuzzy (Utility AI) para o bot.
    Converte percepções matemáticas brutas em notas de Utilidade e Estresse.
    """
    def __init__(self):
        # 1. Antecedentes (Entradas da Visão)
        self.hp = ctrl.Antecedent(np.arange(0, 101, 1), 'hp')
        self.monster_count = ctrl.Antecedent(np.arange(0, 11, 1), 'monster_count')

        # 2. Consequentes (Saídas para o Arbiter)
        self.stress = ctrl.Consequent(np.arange(0, 101, 1), 'stress')
        self.utility_heal = ctrl.Consequent(np.arange(0, 101, 1), 'utility_heal')
        self.utility_attack = ctrl.Consequent(np.arange(0, 101, 1), 'utility_attack')

        # 3. Funções de Pertinência (Membership Functions)
        # HP: Crítico (0-50), Alerta (30-80), Saudável (50-100)
        self.hp['critical'] = fuzz.trapmf(self.hp.universe, [0, 0, 30, 50])
        self.hp['alert'] = fuzz.trimf(self.hp.universe, [30, 50, 80])
        self.hp['healthy'] = fuzz.trapmf(self.hp.universe, [50, 80, 100, 100])

        # Monstros: Isolado (0-3), Controlado (2-6), Massivo (5-10)
        self.monster_count['isolated'] = fuzz.trapmf(self.monster_count.universe, [0, 0, 1, 3])
        self.monster_count['controlled'] = fuzz.trimf(self.monster_count.universe, [2, 4, 6])
        self.monster_count['massive'] = fuzz.trapmf(self.monster_count.universe, [5, 8, 10, 10])

        # Estresse: Relaxado, Alerta, Pânico
        self.stress['relaxed'] = fuzz.trimf(self.stress.universe, [0, 0, 50])
        self.stress['alert'] = fuzz.trimf(self.stress.universe, [25, 50, 75])
        self.stress['panic'] = fuzz.trimf(self.stress.universe, [50, 100, 100])

        # Utilidade da Cura
        self.utility_heal['low'] = fuzz.trimf(self.utility_heal.universe, [0, 0, 50])
        self.utility_heal['high'] = fuzz.trimf(self.utility_heal.universe, [50, 100, 100])

        # Utilidade do Ataque em Área (AoE)
        self.utility_attack['low'] = fuzz.trimf(self.utility_attack.universe, [0, 0, 50])
        self.utility_attack['high'] = fuzz.trimf(self.utility_attack.universe, [50, 100, 100])

        # 4. Regras de Inferência
        # Estresse
        r_stress_1 = ctrl.Rule(self.hp['critical'] | self.monster_count['massive'], self.stress['panic'])
        r_stress_2 = ctrl.Rule(self.hp['healthy'] & self.monster_count['isolated'], self.stress['relaxed'])
        r_stress_3 = ctrl.Rule(self.hp['alert'], self.stress['alert'])

        # Cura
        r_heal_1 = ctrl.Rule(self.hp['critical'], self.utility_heal['high'])
        r_heal_2 = ctrl.Rule(self.hp['healthy'], self.utility_heal['low'])
        
        # Ataque
        r_atk_1 = ctrl.Rule(self.monster_count['massive'] & self.hp['healthy'], self.utility_attack['high'])
        r_atk_2 = ctrl.Rule(self.monster_count['isolated'], self.utility_attack['low'])
        r_atk_3 = ctrl.Rule(self.hp['critical'], self.utility_attack['low']) # Sobrevivência > Dano

        # 5. Compilação do Sistema
        self.ctrl_sys = ctrl.ControlSystem([
            r_stress_1, r_stress_2, r_stress_3, 
            r_heal_1, r_heal_2, 
            r_atk_1, r_atk_2, r_atk_3
        ])
        self.sim = ctrl.ControlSystemSimulation(self.ctrl_sys)

    def evaluate(self, current_hp: int, current_monsters: int) -> dict:
        """Processa os dados reais e retorna os scores de 0 a 100."""
        # Prevenção de out-of-bounds
        self.sim.input['hp'] = max(0, min(100, current_hp))
        self.sim.input['monster_count'] = max(0, min(10, current_monsters))
        
        self.sim.compute()
        
        return {
            'stress': self.sim.output.get('stress', 0),
            'utility_heal': self.sim.output.get('utility_heal', 0),
            'utility_attack': self.sim.output.get('utility_attack', 0)
        }
