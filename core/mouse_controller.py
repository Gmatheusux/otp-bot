import time
import random
import math
import pydirectinput
from typing import Tuple, List

class MouseController:
    """
    Controlador cinemático de mouse responsável por simular movimentação humana
    utilizando Curvas de Bézier cúbicas, ruído estocástico e aceleração variável (easing).
    """
    
    def __init__(self):
        # Desabilita o fail-safe do pydirectinput para evitar crash acidental ao encostar nos cantos
        pydirectinput.FAILSAFE = False

    def _ease_in_out_cubic(self, t: float) -> float:
        """
        Função de easing para simular inércia natural humana. 
        O cursor acelera no começo do movimento e desacelera suavemente no final.
        """
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - math.pow(-2 * t + 2, 3) / 2

    def _generate_bezier_curve(self, p0: Tuple[int, int], p3: Tuple[int, int], num_points: int = 50) -> List[Tuple[int, int]]:
        """
        Gera uma curva de Bézier cúbica entre o ponto inicial (p0) e o ponto final (p3).
        Os pontos de controle p1 e p2 são gerados aleatoriamente para simular a imperfeição da trajetória.
        """
        x0, y0 = p0
        x3, y3 = p3

        # Distância Euclidiana entre os pontos
        dist = math.hypot(x3 - x0, y3 - y0)
        
        # Gera pontos de controle baseados na distância para garantir uma barriga natural na curva
        offset = dist * random.uniform(0.1, 0.3)
        
        # P1 (Primeiro ponto de controle - próximo à saída)
        x1 = x0 + (x3 - x0) * random.uniform(0.1, 0.4) + random.uniform(-offset, offset)
        y1 = y0 + (y3 - y0) * random.uniform(0.1, 0.4) + random.uniform(-offset, offset)
        
        # P2 (Segundo ponto de controle - próximo à chegada)
        x2 = x0 + (x3 - x0) * random.uniform(0.6, 0.9) + random.uniform(-offset, offset)
        y2 = y0 + (y3 - y0) * random.uniform(0.6, 0.9) + random.uniform(-offset, offset)

        curve_points = []
        for i in range(num_points):
            t = i / max(1, (num_points - 1))
            
            # Aplica easing ao t para simular inércia natural na distribuição temporal dos pontos
            t_eased = self._ease_in_out_cubic(t)
            
            # Equação polinomial da Curva de Bézier Cúbica
            x = (1 - t_eased)**3 * x0 + 3 * (1 - t_eased)**2 * t_eased * x1 + 3 * (1 - t_eased) * t_eased**2 * x2 + t_eased**3 * x3
            y = (1 - t_eased)**3 * y0 + 3 * (1 - t_eased)**2 * t_eased * y1 + 3 * (1 - t_eased) * t_eased**2 * y2 + t_eased**3 * y3
            
            curve_points.append((int(x), int(y)))
            
        return curve_points

    def _generate_noise(self, length: int, amplitude: float = 2.0) -> List[float]:
        """
        Gera ruído estocástico simples (Value Noise 1D) para simular microtremores naturais da mão,
        atuando como uma aproximação de Perlin Noise sem exigir dependências pesadas externas.
        """
        noise = []
        step = 5 # Frequência dos picos de ruído
        random_values = [random.uniform(-amplitude, amplitude) for _ in range(length // step + 2)]
        
        for i in range(length):
            idx = i // step
            t = (i % step) / step
            # Interpolação de Cosseno para suavizar os tremores e não parecer jitter robótico
            t_smooth = (1 - math.cos(t * math.pi)) / 2
            val = random_values[idx] * (1 - t_smooth) + random_values[idx + 1] * t_smooth
            noise.append(val)
            
        return noise

    def move_mouse(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], base_duration: float = None):
        """
        Orquestra o movimento do mouse aplicando a curva, o easing e o ruído estocástico,
        calculando o tempo dinamicamente se não for fornecido.
        """
        dist = math.hypot(end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
        
        if base_duration is None:
            # Tempo de duração randômico escalonado pela distância percorrida
            base_duration = random.uniform(0.3, 0.7) + (dist / 1500.0)
            
        # O número de pontos de interpolação escala de acordo com a distância
        num_points = max(20, min(100, int(dist / 3)))
        
        curve_points = self._generate_bezier_curve(start_pos, end_pos, num_points)
        
        # Gera matriz de ruído independente para X e Y
        noise_x = self._generate_noise(num_points, amplitude=1.5)
        noise_y = self._generate_noise(num_points, amplitude=1.5)
        
        sleep_time = base_duration / num_points

        for i in range(num_points):
            pt_x, pt_y = curve_points[i]
            
            # Injeta o ruído estocástico nas coordenadas perfeitamente calculadas
            final_x = int(pt_x + noise_x[i])
            final_y = int(pt_y + noise_y[i])
            
            pydirectinput.moveTo(final_x, final_y)
            
            # Micro-sleep randômico (distribuição Gaussiana) simulando a instabilidade do polling rate
            # humano e evitando padronização milimétrica identificável por anti-cheats
            time.sleep(max(0.001, random.gauss(sleep_time, sleep_time * 0.15)))

    def click(self, target_pos: Tuple[int, int] = None, button: str = 'left'):
        """
        Executa um clique humanizado. Se 'target_pos' for passado, o cursor realiza a 
        movimentação humanizada antes do clique.
        """
        if target_pos:
            current_pos = pydirectinput.position()
            self.move_mouse(current_pos, target_pos)
            
        pydirectinput.mouseDown(button=button)
        # Randomização de hold-time de clique (tempo que o dedo fica no mouse switch)
        time.sleep(random.uniform(0.040, 0.130))
        pydirectinput.mouseUp(button=button)
        
        # Micro-delay tático pós-clique
        time.sleep(random.uniform(0.05, 0.15))
