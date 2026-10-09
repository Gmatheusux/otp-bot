"""
modules/vision_engine.py — Inferência otimizada para RPA usando Ultralytics YOLOv8 + TensorRT.
"""
import threading
import cv2
import mss
import numpy as np
import torch
from ultralytics import YOLO
from typing import Dict, List

class VisionEngine:
    def __init__(self, model_path: str = "yolov8n.engine"):
        """
        Inicializa o pipeline de inferência RPA.
        Usa a biblioteca ultralytics nativa que suporta TensorRT (.engine) de forma transparente.
        Abstração Zero-Context (sem regras de negócio, apenas processamento visual).
        """
        self.model = YOLO(model_path, task='detect')
        self.use_cuda = torch.cuda.is_available()
        self.device = 0 if self.use_cuda else "cpu"
        self.device_name = torch.cuda.get_device_name(0) if self.use_cuda else "CPU"
        # mss guarda handles do Windows por thread; process_frame roda em threads do pool
        self._local = threading.local()

    @property
    def sct(self):
        if not hasattr(self._local, "sct"):
            self._local.sct = mss.mss()
        return self._local.sct

    def capture_screen(self, monitor_index: int = 1) -> np.ndarray:
        """
        Lê o buffer da tela local usando mss para latência mínima.
        """
        monitor = self.sct.monitors[monitor_index]
        sct_img = self.sct.grab(monitor)
        
        # Converte BGRA (mss) para BGR (padrão OpenCV/YOLO)
        img = np.array(sct_img)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def infer(self, img: np.ndarray, conf_threshold: float = 0.5) -> List[Dict]:
        """
        Executa a detecção e retorna dicionários de bounding boxes relativos (normalizados).
        """
        # verbose=False para não poluir o stdout no modo contínuo
        # FP16 na GPU: ~2x mais rápido nos Tensor Cores da RTX
        results = self.model(img, verbose=False, conf=conf_threshold, device=self.device, half=self.use_cuda)
        
        detections = []
        for result in results:
            for box in result.boxes:
                # Extrai coordenadas relativas (normalizadas de 0.0 a 1.0)
                xywhn = box.xywhn.cpu().numpy()[0]
                conf = float(box.conf.cpu().numpy()[0])
                cls_id = int(box.cls.cpu().numpy()[0])
                
                detections.append({
                    "class_id": cls_id,
                    "confidence": conf,
                    "box_relative": {
                        "x_center": xywhn[0],
                        "y_center": xywhn[1],
                        "width": xywhn[2],
                        "height": xywhn[3]
                    }
                })
                
        return detections

    def process_frame(self, monitor_index: int = 1, conf_threshold: float = 0.5) -> List[Dict]:
        """
        Executa o pipeline completo: leitura de buffer da tela -> inferência -> formatação.
        """
        img = self.capture_screen(monitor_index)
        return self.infer(img, conf_threshold)

    def match_template(self, img: np.ndarray, template: np.ndarray, roi: tuple = None, threshold: float = 0.8) -> List[tuple]:
        """
        Executa Template Matching genérico (Zero-Context).
        
        Args:
            img: Imagem base capturada.
            template: Imagem do template a ser buscado.
            roi: Tupla (x, y, w, h) limitando a Região de Interesse.
            threshold: Limiar de confiança (0.0 a 1.0).
            
        Returns:
            Lista de pontos (x, y) onde o template foi encontrado.
        """
        search_area = img
        offset_x, offset_y = 0, 0
        
        if roi:
            x, y, w, h = roi
            search_area = img[y:y+h, x:x+w]
            offset_x, offset_y = x, y
            
        res = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        
        matches = []
        for pt in zip(*loc[::-1]):
            matches.append((pt[0] + offset_x, pt[1] + offset_y))
            
        return matches

if __name__ == "__main__":
    import time
    
    # Teste unitário rápido e warmup de GPU
    engine = VisionEngine("yolov8n.engine")
    engine.process_frame() # warmup
    
    t0 = time.time()
    dets = engine.process_frame()
    t1 = time.time()
    
    print(f"Tempo de inferência RPA: {(t1 - t0) * 1000:.2f} ms")
    print(f"BBoxes detectados: {len(dets)}")
    for d in dets:
        print(d)
