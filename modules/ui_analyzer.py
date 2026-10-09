import cv2
import numpy as np
from typing import Dict, List, Tuple
from modules.vision_engine import VisionEngine

class UIAnalyzer:
    def __init__(self, vision_engine: VisionEngine, health_area_roi: Tuple[int, int, int, int] = (100, 50, 300, 100)):
        """
        Inicializa o analisador de Interface de Usuário.
        Abstrai a lógica de negócio visual (ex: onde estão as barras de vida, ícones, buffs).
        
        Args:
            vision_engine: Instância do motor de visão base.
            health_area_roi: Tupla (x, y, w, h) definindo a área da tela onde os debuffs aparecem.
        """
        self.vision = vision_engine
        self.health_area_roi = health_area_roi

    def check_debuff_active(self, frame: np.ndarray, debuff_icon_path: str, threshold: float = 0.8) -> bool:
        """
        Verifica se um ícone de debuff está ativo na área de vida usando Template Matching.
        
        Args:
            frame: Buffer de tela atual (capturado do jogo).
            debuff_icon_path: Caminho para a imagem template do ícone de debuff.
            threshold: Limiar de confiança (0.0 a 1.0).
            
        Returns:
            True se o debuff foi encontrado na ROI, False caso contrário.
        """
        template = cv2.imread(debuff_icon_path)
        if template is None:
            print(f"[UIAnalyzer] Erro: Template não encontrado no caminho {debuff_icon_path}")
            return False
            
        matches = self.vision.match_template(
            img=frame, 
            template=template, 
            roi=self.health_area_roi, 
            threshold=threshold
        )
        
        return len(matches) > 0
