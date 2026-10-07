import math
import random
import time
import numpy as np
import bezier

class MouseDriver:
    """
    Controlador estocástico de movimentação de mouse para automação 2D.
    Utiliza Curvas de Bézier para evitar linhas retas e Ruído Gaussiano
    para simular pausas biológicas imperfeitas.
    """
    def __init__(self, screen_width=1920, screen_height=1080):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_x = 0
        self.current_y = 0

    def _gaussian_delay(self, mean, std_dev, min_val, max_val):
        """
        Injeta um delay não-determinístico (Ruído Gaussiano), limitando os 
        valores de variação (clamping) para evitar tempos negativos.
        Substitui o uso estático de time.sleep().
        """
        delay = random.gauss(mean, std_dev)
        clamped_delay = max(min_val, min(delay, max_val))
        time.sleep(clamped_delay)

    def _generate_bezier_trajectory(self, start_x, start_y, end_x, end_y, min_nodes=1, max_nodes=3):
        """
        Gera uma trajetória matemática com N pontos de controle (deviation nodes).
        Calcula vetores ortogonais para garantir arcos orgânicos.
        """
        points = [[start_x, start_y]]
        
        dx = end_x - start_x
        dy = end_y - start_y
        dist = math.hypot(dx, dy)
        
        if dist <= 1:
            return [[end_x, end_y]]

        # Define a quantidade de nós de desvio na curva atual
        nodes_count = random.randint(min_nodes, max_nodes)
        
        for i in range(1, nodes_count + 1):
            # Distribui os nós proporcionalmente pela reta
            t = i / (nodes_count + 1)
            base_x = start_x + (dx * t)
            base_y = start_y + (dy * t)
            
            # Vetor ortogonal normalizado (-dy, dx)
            perp_x = -dy / dist
            perp_y = dx / dist
            
            # Magnitude randômica do desvio (ex: variação de até 15% da distância)
            deviation = random.uniform(-0.15 * dist, 0.15 * dist)
            
            cp_x = base_x + (perp_x * deviation)
            cp_y = base_y + (perp_y * deviation)
            points.append([cp_x, cp_y])

        points.append([end_x, end_y])
        
        # Array Fortran-contiguous exigido pela biblioteca bezier
        nodes = np.asfortranarray([
            [p[0] for p in points],
            [p[1] for p in points]
        ])
        
        curve = bezier.Curve(nodes, degree=len(points)-1)
        
        # Resolução dinâmica: mais pontos de interpolação para distâncias longas
        num_eval_points = max(10, int(dist / 4))
        s_vals = np.linspace(0.0, 1.0, num_eval_points)
        path = curve.evaluate_multi(s_vals)
        
        return [(path[0][i], path[1][i]) for i in range(num_eval_points)]

    def execute_move(self, target_x, target_y):
        """
        Interface principal. Invocado pela State Machine para interpolar
        a geometria e acionar o micro-delay (Easing).
        """
        trajectory = self._generate_bezier_trajectory(self.current_x, self.current_y, target_x, target_y)
        total_steps = len(trajectory)
        
        # Delay de reação ANTES de iniciar a movimentação real
        self._gaussian_delay(mean=0.1, std_dev=0.03, min_val=0.05, max_val=0.2)

        for i, (px, py) in enumerate(trajectory):
            progress = i / max(1, total_steps - 1)
            
            # TODO: Injetar as coordenadas na API de SO (ex: pyautogui, win32api, directinput)
            # win32api.SetCursorPos((int(px), int(py)))
            self.current_x = px
            self.current_y = py
            
            # Easing para 2D: Rápido no meio, Parada Brusca no final.
            if progress < 0.2:
                # Arranque da inércia
                step_mean = 0.007
                step_std = 0.002
            elif progress < 0.85:
                # Fase balística (Aceleração e fluidez)
                step_mean = 0.002
                step_std = 0.001
            else:
                # Desaceleração brusca (Freia abruptamente nos últimos 15%)
                step_mean = 0.015
                step_std = 0.005
                
            self._gaussian_delay(step_mean, step_std, 0.001, 0.05)

        # Confirma a posição final exata
        self.current_x = target_x
        self.current_y = target_y
        
        # Delay de acomodação (Homing) antes de um potencial clique
        self._gaussian_delay(mean=0.05, std_dev=0.01, min_val=0.02, max_val=0.1)

# Fim da Classe
