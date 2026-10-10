"""
otpbot/perception/capture.py — Print do monitor inteiro (comportamento atual dos sensores).
Na E03 os sensores passam a usar `otpbot.platform.game_window.capture_client` (só a área cliente do jogo).
"""
import cv2
import mss
import numpy as np


def capture_screen(monitor_index: int = 1) -> np.ndarray:
    """Print do monitor em BGR. Instância nova de mss por chamada: pode rodar em qualquer thread."""
    with mss.mss() as sct:
        img = np.array(sct.grab(sct.monitors[monitor_index]))
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
