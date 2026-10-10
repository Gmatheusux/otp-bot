"""
otpbot/perception/chat.py — Monitor de GM: OCR do chat só quando a imagem muda (MSE).
A região lida é a "chat" do perfil de calibração (fonte única desde a E02), escolhido pelo tamanho da área
cliente do jogo (E03).
"""
import asyncio
import os
from typing import Callable, Dict, Optional, Tuple

import cv2
import numpy as np
import pytesseract
import logging

from otpbot.perception.bars import pick_profile, scaled_rect

logger = logging.getLogger("ChatAnalyzer")


def chat_roi(calibration: Dict, width: int, height: int) -> Optional[Tuple[int, int, int, int]]:
    """Região "chat" do perfil (x, y, w, h) em pixels do frame (área cliente); None se não calibrada."""
    _, profile, scale = pick_profile(calibration, width, height)
    region = (profile or {}).get("regions", {}).get("chat")
    if not region:
        return None
    return scaled_rect(region, scale, (height, width))


class ChatAnalyzer:
    def __init__(self, roi: Optional[tuple] = None,
                 tesseract_cmd: str = r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        """
        Analisador de Chat isolado e de alta performance.
        Args:
            roi: Região de Interesse (x, y, w, h) do chat, em pixels da área cliente; o monitor a atualiza
                 pela calibração.
        """
        self.roi = roi
        self.last_frame = None
        self.mse_threshold = 5.0  # Limiar de mudança de pixel para engatilhar OCR

        # Opcional: Caminho para o executável do tesseract (necessário no Windows)
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def _crop_roi(self, frame: np.ndarray) -> np.ndarray:
        x, y, w, h = self.roi
        return cv2.cvtColor(frame[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)  # Gray para facilitar o OCR e MSE

    def _mse(self, imageA: np.ndarray, imageB: np.ndarray) -> float:
        # Erro quadrático médio entre duas imagens
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
        return err

    def check_for_gm(self, frame: np.ndarray) -> bool:
        """
        Checa a região do chat no print da área cliente. Só engatilha o PyTesseract se a imagem mudou.
        Retorna True se 'GM' ou 'GameMaster' for detectado.
        """
        current_frame = self._crop_roi(frame)

        if self.last_frame is not None:
            err = self._mse(current_frame, self.last_frame)
            if err < self.mse_threshold:
                # Nenhuma alteração visual significativa no chat
                return False

        self.last_frame = current_frame

        # Preprocessamento para melhorar o OCR (Thresholding)
        _, thresh = cv2.threshold(current_frame, 150, 255, cv2.THRESH_BINARY_INV)

        # OCR em bloco: a região da calibração pega as últimas linhas do chat
        text = pytesseract.image_to_string(thresh, config='--psm 6').strip().lower()

        if text:
            # Lista de palavras-chave perigosas (GM, Admin, GameMaster)
            keywords = ["gm", "gamemaster", "admin", "tutor", "[gm]"]
            for word in keywords:
                if word in text:
                    logger.warning(f"MENSAGEM DE GM DETECTADA NO OCR! Texto: '{text}'")
                    return True

        return False


async def chat_monitor_thread(chat_analyzer: ChatAnalyzer, kill_event: asyncio.Event, pause_event: asyncio.Event,
                              get_config: Callable[[], dict], capture: Callable[[], tuple],
                              publish: Callable[[bool], None]) -> None:
    """
    Sensor do chat: roda a ~2 fps, lê só quando a imagem muda e PUBLICA `gm_alert` no WorldState.
    Quem desliga o bot é a Segurança (brain/behaviors/safety.py), não o sensor.
    `capture()` devolve (frame da área cliente, janela) ou (None, ...) sem o jogo.
    """
    tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
    if not os.path.exists(tesseract_cmd):
        logger.warning(f"Tesseract não encontrado em '{tesseract_cmd}'. Monitor de GM desativado nesta sessão.")
        return

    logger.info("Thread de Chat Analyzer iniciada.")
    warned_no_region = False
    while not kill_event.is_set():
        await pause_event.wait()
        if kill_event.is_set():
            break

        config = get_config()
        if not config.get("features", {}).get("safety", {}).get("gm_monitor", True):
            await asyncio.sleep(1)
            continue

        try:
            frame, _ = await asyncio.to_thread(capture)
            if frame is None:
                await asyncio.sleep(1)
                continue
            height, width = frame.shape[:2]
            roi = chat_roi(config.get("calibration", {}), width, height)
            if roi is None:
                if not warned_no_region:
                    logger.warning("Região 'chat' não calibrada para esta resolução: monitor de GM parado.")
                    warned_no_region = True
                await asyncio.sleep(1)
                continue
            warned_no_region = False
            if roi != chat_analyzer.roi:
                chat_analyzer.roi = roi
                chat_analyzer.last_frame = None  # tamanho mudou, MSE com o frame antigo não faz sentido

            # Roda check_for_gm no threadpool para não bloquear o event loop caso caia no tesseract
            gm_detected = await asyncio.to_thread(chat_analyzer.check_for_gm, frame)

            if gm_detected:
                publish(True)
                break

            await asyncio.sleep(0.5)  # Limita a 2 FPS
        except Exception as e:
            logger.error(f"Erro no Chat Analyzer: {e}")
            await asyncio.sleep(1)

    logger.info("Thread de Chat Analyzer encerrada.")
