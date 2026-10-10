"""
otpbot/perception/capture.py — Prints para os sensores e para o console.

Desde a E03 os sensores capturam SÓ a área cliente da janela do jogo (`GameLocator.capture`), em qualquer
monitor, e as regiões da calibração são relativas a ela. `capture_screen` (monitor inteiro) fica só como
reserva do console quando o jogo não está aberto.
"""
import logging
import threading
import time
from typing import Callable, Optional, Tuple

import cv2
import mss
import numpy as np

from otpbot.platform import game_window
from otpbot.platform.game_window import GameWindow

logger = logging.getLogger("Capture")


def capture_screen(monitor_index: int = 1) -> np.ndarray:
    """Print do monitor em BGR. Instância nova de mss por chamada: pode rodar em qualquer thread."""
    with mss.mss() as sct:
        img = np.array(sct.grab(sct.monitors[monitor_index]))
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


class GameLocator:
    """Acha a janela do jogo e guarda por `refresh_s`; captura a área cliente com um mss por thread."""

    def __init__(self, locate: Callable[[], Optional[GameWindow]] = game_window.locate, refresh_s: float = 1.0,
                 clock: Callable[[], float] = time.monotonic,
                 covered: Callable[[GameWindow], bool] = game_window.is_covered):
        self._locate = locate
        self._covered = covered
        self._warned_covered = False
        self._refresh_s = refresh_s
        self._clock = clock
        self._window: Optional[GameWindow] = None
        self._checked_at = float("-inf")
        self._guard = threading.Lock()
        self._local = threading.local()
        self._warned = False

    def window(self) -> Optional[GameWindow]:
        with self._guard:
            now = self._clock()
            if now - self._checked_at >= self._refresh_s:
                self._checked_at = now
                try:
                    self._window = self._locate()
                except Exception as e:
                    logger.debug(f"locate: {e}")
                    self._window = None
                if self._window is None and not self._warned:
                    logger.warning("Janela do jogo não encontrada: os sensores ficam sem leitura até ela abrir.")
                    self._warned = True
                elif self._window is not None and self._warned:
                    logger.info("Janela do jogo encontrada.")
                    self._warned = False
            return self._window

    def _sct(self):
        if not hasattr(self._local, "sct"):
            self._local.sct = game_window._new_mss()
        return self._local.sct

    def capture(self, region: Optional[Tuple[int, int, int, int]] = None
                ) -> Tuple[Optional[np.ndarray], Optional[GameWindow]]:
        """
        (frame BGR da área cliente, janela). Frame None se o jogo não está aberto, está minimizado ou tem outra
        janela por cima (o print pegaria a janela de cima: leitura falsa é pior que nenhuma).
        `region` (x, y, w, h relativo ao cliente) copia só aquele pedaço.
        """
        window = self.window()
        if window is None or window.minimized:
            return None, window
        try:
            covered = self._covered(window)
        except Exception as e:
            logger.debug(f"is_covered: {e}")
            covered = False
        if covered != self._warned_covered:
            self._warned_covered = covered
            (logger.warning if covered else logger.info)(
                "Janela do jogo coberta por outra: sensores sem leitura até ela ficar visível." if covered
                else "Janela do jogo visível de novo.")
        if covered:
            return None, window
        try:
            if region is None:
                return game_window.capture_client(window, self._sct()), window
            return game_window.capture_client(window, self._sct(), region), window
        except Exception as e:
            logger.debug(f"capture_client: {e}")
            return None, window


def capture_for_console(locator: Optional[GameLocator] = None) -> np.ndarray:
    """Print para o console (sprites, calibração): a área cliente do jogo; sem o jogo, o monitor principal."""
    if locator is not None:
        frame, _ = locator.capture()
        if frame is not None:
            return frame
    return capture_screen()
