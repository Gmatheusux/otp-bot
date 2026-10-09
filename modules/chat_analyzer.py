import asyncio
import os
import threading
import cv2
import mss
import numpy as np
import pytesseract
import logging
import re

from modules.sprite_library import pick_monitor

logger = logging.getLogger("ChatAnalyzer")

GM_PATTERN = re.compile(r"\b(gm|gamemaster|game master|admin|administrador|administrator|tutor)\b")


class ChatAnalyzer:
    def __init__(self, roi: tuple, tesseract_cmd: str = r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        """
        Analisador de Chat isolado e de alta performance.
        Args:
            roi: Regio de Interesse (x, y, w, h) contendo apenas a ltima linha do chat.
        """
        self.roi = roi
        self._local = threading.local()
        self.last_frame = None
        self.mse_threshold = 5.0 # Limiar de mudana de pixel para engatilhar OCR
        self.monitor_index = 0   # 0 = monitor principal
        
        # Opcional: Caminho para o executvel do tesseract (necessrio no Windows)
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    @property
    def sct(self):
        # mss guarda handles do Windows por thread; check_for_gm roda em threads do pool
        if not hasattr(self._local, "sct"):
            self._local.sct = mss.mss()
        return self._local.sct

    def _capture_roi(self) -> np.ndarray:
        monitor = pick_monitor(self.sct.monitors, self.monitor_index)
        # Aplica offset da ROI na tela do mss
        capture_box = {
            "top": monitor["top"] + self.roi[1],
            "left": monitor["left"] + self.roi[0],
            "width": self.roi[2],
            "height": self.roi[3]
        }
        sct_img = self.sct.grab(capture_box)
        img = np.array(sct_img)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY) # Gray para facilitar o OCR e MSE
        return img

    def _mse(self, imageA: np.ndarray, imageB: np.ndarray) -> float:
        # Erro quadrtico mdio entre duas imagens
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
        return err

    def check_for_gm(self) -> bool:
        """
        Checa a regio do chat. S engatilha o PyTesseract se a ltima linha mudou.
        Retorna True se 'GM' ou 'GameMaster' for detectado.
        """
        current_frame = self._capture_roi()

        if self.last_frame is not None:
            err = self._mse(current_frame, self.last_frame)
            if err < self.mse_threshold:
                # Nenhuma alterao visual significativa na linha de chat
                return False
        
        self.last_frame = current_frame

        # Preprocessamento para melhorar o OCR (Thresholding)
        _, thresh = cv2.threshold(current_frame, 150, 255, cv2.THRESH_BINARY_INV)
        
        # OCR
        text = pytesseract.image_to_string(thresh, config='--psm 7').strip().lower()
        
        # Palavra inteira: "gm" dentro de "segmento" ou "tutor" dentro de "tutorial" não derrubam o bot
        if text and GM_PATTERN.search(text):
            logger.warning(f"MENSAGEM DE GM DETECTADA NO OCR! Texto: '{text}'")
            return True

        return False

async def chat_monitor_thread(chat_analyzer: ChatAnalyzer, kill_event: asyncio.Event, pause_event: asyncio.Event, get_safety_config=None) -> None:
    """
    Thread assncrona dedicada ao monitoramento de chat (Kill Event).
    Roda a uma taxa fixa muito menor (ex: 2-5 fps) para no onerar a CPU,
    apenas lendo mudanas visuais.
    """
    tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
    if not os.path.exists(tesseract_cmd):
        logger.warning(f"Tesseract não encontrado em '{tesseract_cmd}'. Monitor de GM desativado nesta sessão.")
        return

    logger.info("Thread de Chat Analyzer iniciada.")
    while not kill_event.is_set():
        await pause_event.wait()
        if kill_event.is_set():
            break

        if get_safety_config is not None:
            safety = get_safety_config()
            if not safety.get("gm_monitor", True):
                await asyncio.sleep(1)
                continue
            chat_analyzer.monitor_index = int(safety.get("monitor", 0))
            roi = tuple(safety.get("chat_roi", chat_analyzer.roi))
            if roi != chat_analyzer.roi:
                chat_analyzer.roi = roi
                chat_analyzer.last_frame = None  # tamanho mudou, MSE com o frame antigo não faz sentido

        try:
            # Roda check_for_gm no threadpool para no bloquear o event loop caso caia no tesseract
            gm_detected = await asyncio.to_thread(chat_analyzer.check_for_gm)
            
            if gm_detected:
                logger.critical(">>> KILL EVENT ENGATILHADO PELO CHAT ANALYZER <<<")
                kill_event.set()
                break
                
            await asyncio.sleep(0.5) # Limita a 2 FPS
        except Exception as e:
            logger.error(f"Erro no Chat Analyzer: {e}")
            await asyncio.sleep(1)

    logger.info("Thread de Chat Analyzer encerrada.")
