"""
Módulo core/keyboard.py
Abstração Zero-Context para atuação de teclado com emulação matemática humana.
"""
import time
import random
import pydirectinput

# Desativar o pause nativo do pydirectinput (nós controlaremos o delay matematicamente)
pydirectinput.PAUSE = 0.0

# Perfis de tempo em segundos: (mu_down, sigma_down)
# mu: média de tempo que a tecla fica pressionada
# sigma: variação (desvio padrão)
PROFILES = {
    "fast": (0.04, 0.01),      # Ex: Spam de magias, reflexos rápidos
    "normal": (0.07, 0.02),    # Ex: Ações cotidianas, abrir janelas, atalhos normais
    "sluggish": (0.15, 0.05),  # Ex: Ações cansadas ou de menus pesados
}

def _get_gaussian_delay(mu: float, sigma: float, min_val: float, max_val: float) -> float:
    """
    Gera um delay humanizado baseado em curva de sino (Gaussiana),
    com um clamp (limite) para evitar anomalias matemáticas.
    """
    delay = random.gauss(mu, sigma)
    # Clamp para garantir que o tempo não seja negativo nem ridiculamente longo
    return max(min_val, min(delay, max_val))

def press(key: str, profile: str = "normal") -> None:
    """
    Pressiona uma tecla simulando a duração física do toque humano.
    
    Args:
        key (str): A tecla a ser pressionada (ex: 'f1', 'enter', 'a').
        profile (str): O perfil de velocidade ('fast', 'normal', 'sluggish').
    """
    if profile not in PROFILES:
        profile = "normal"
        
    mu, sigma = PROFILES[profile]
    
    # Calculando quanto tempo a tecla ficará pressionada fisicamente
    # Clamp: mínimo de 10ms, máximo de mu + 3*sigma
    hold_time = _get_gaussian_delay(mu, sigma, min_val=0.01, max_val=mu + (sigma * 3))
    
    pydirectinput.keyDown(key)
    time.sleep(hold_time)
    pydirectinput.keyUp(key)

def hold(key: str, base_duration: float) -> None:
    """
    Segura uma tecla por um período, injetando ruído no tempo total.
    Ideal para movimentação contínua.
    
    Args:
        key (str): A tecla a ser pressionada.
        base_duration (float): Duração base pretendida em segundos.
    """
    # Ruído de até 15% para mais ou para menos no tempo de segurar
    noise = random.uniform(-0.15, 0.15)
    actual_duration = base_duration * (1.0 + noise)
    
    # Garante que não zere ou fique negativo
    actual_duration = max(0.05, actual_duration)
    
    pydirectinput.keyDown(key)
    time.sleep(actual_duration)
    pydirectinput.keyUp(key)

def type_string(text: str, wpm_target: int = 80) -> None:
    """
    Digita uma string letra por letra com variações de velocidade entre as teclas.
    O WPM (Words Per Minute) define a base de velocidade.
    
    Args:
        text (str): Texto a ser digitado.
        wpm_target (int): Palavras por minuto pretendidas. Padrão: 80.
    """
    # WPM para CPS (Characters Per Second): 1 palavra = ~5 caracteres. 
    # CPS = (WPM * 5) / 60
    cps = (wpm_target * 5.0) / 60.0
    base_interval = 1.0 / cps if cps > 0 else 0.1
    
    for char in text:
        # Pressiona o caractere (usando um perfil rápido para simular o toque leve)
        press(char, profile="fast")
        
        # Delay de trânsito do dedo até a próxima tecla (Gaussiano)
        # Assumimos que a variação de trânsito seja 30% do base_interval
        sigma = base_interval * 0.3
        transit_delay = _get_gaussian_delay(
            mu=base_interval, 
            sigma=sigma, 
            min_val=0.01, 
            max_val=base_interval * 2.5
        )
        
        time.sleep(transit_delay)
