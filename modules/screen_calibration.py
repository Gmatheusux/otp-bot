"""
modules/screen_calibration.py — Regiões fixas da interface do jogo e leitura das barras por cor.

As regiões são guardadas em pixels de uma imagem de referência (base_width). Na tela real,
tudo é escalado pela largura: o cliente do jogo cresce proporcionalmente a partir do canto
superior esquerdo (ex: referência de 2000px, monitor de 3440px -> escala 1.72).
"""
from typing import Dict, List, Optional

import cv2
import numpy as np

# Faixas HSV (OpenCV: H 0-180) das barras do cliente
COLOR_RANGES = {
    "green": [((35, 90, 90), (85, 255, 255))],
    "yellow": [((10, 90, 110), (35, 255, 255))],
    "red": [((0, 90, 90), (9, 255, 255)), ((170, 90, 90), (180, 255, 255))],
    "blue": [((95, 90, 90), (130, 255, 255))],
}

# Valores medidos no print de referência do jogador (2000x799, Poke Alliance)
DEFAULT_CALIBRATION = {
    "base_width": 2000,
    "summon_name": "Megaclefable",
    "regions": {
        "game_area": {"x": 318, "y": 2, "w": 1360, "h": 714},
        # Painel "Pokémon": vermelha = HP do jogador, azul = HP do pokémon (confirmado pelo jogador)
        "player_hp": {"x": 45, "y": 36, "w": 60, "h": 10},
        "pokemon_hp": {"x": 45, "y": 49, "w": 61, "h": 9},
        # Mãos de postura: vermelha ofensivo, cinza neutro, verde defensivo
        "stance": {"x": 46, "y": 63, "w": 56, "h": 18, "slots": 3},
        "exp_bar": {"x": 726, "y": 685, "w": 718, "h": 7},
        "team": {"x": 22, "y": 104, "w": 71, "h": 144, "slots": 5},
        "battle_list": {"x": 0, "y": 290, "w": 105, "h": 160},
        "skills": {"x": 668, "y": 425, "w": 185, "h": 22},
        "hotbar": {"x": 545, "y": 693, "w": 910, "h": 22},
        "minimap": {"x": 1776, "y": 22, "w": 208, "h": 146},
        "coords": {"x": 1775, "y": 18, "w": 62, "h": 12},
        "chat": {"x": 240, "y": 740, "w": 800, "h": 38},
    },
}

# Como cada região é lida
REGION_KINDS = {
    "player_hp": ("bar", "red"),
    "pokemon_hp": ("bar", "blue"),
    "exp_bar": ("bar", "yellow"),
    "team": ("slots", "green"),
    "stance": ("stance", None),
}

# Ordem das mãos no painel, da esquerda para a direita
STANCES = ("offensive", "neutral", "defensive")


def scaled_rect(region: Dict, scale: float, frame_shape) -> Optional[tuple]:
    """Converte a região da referência para pixels do frame, recortando nas bordas."""
    fh, fw = frame_shape[:2]
    x = int(round(region["x"] * scale))
    y = int(round(region["y"] * scale))
    w = max(1, int(round(region["w"] * scale)))
    h = max(1, int(round(region["h"] * scale)))
    x, y = max(0, x), max(0, y)
    w, h = min(w, fw - x), min(h, fh - y)
    if w <= 0 or h <= 0:
        return None
    return x, y, w, h


def color_mask(crop: np.ndarray, color: str) -> np.ndarray:
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = np.zeros(crop.shape[:2], dtype=bool)
    for low, high in COLOR_RANGES[color]:
        mask |= cv2.inRange(hsv, np.array(low), np.array(high)) > 0
    return mask


def bar_fill(crop: np.ndarray, color: str) -> Optional[float]:
    """
    % preenchido de uma barra horizontal que enche da esquerda para a direita.
    Usa só as linhas onde a cor aparece (a região pode ser um pouco mais alta que a barra)
    e a última coluna colorida (o texto "74%" no meio da barra não atrapalha).
    """
    mask = color_mask(crop, color)
    rows = mask.mean(axis=1) > 0.03
    if not rows.any():
        return None
    cols = np.flatnonzero(mask[rows].mean(axis=0) > 0.4)
    if cols.size == 0:
        return None
    return round(min(100.0, float(cols[-1] + 1) / mask.shape[1] * 100), 1)


def active_slot(crop: np.ndarray, slots: int) -> Optional[int]:
    """
    Qual botão está selecionado: o ativo tem o fundo da caixa mais claro.
    Usa a mediana do brilho dos pixels pouco saturados (o fundo), ignorando o desenho colorido.
    """
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    w = crop.shape[1]
    levels = []
    for i in range(slots):
        part = hsv[:, int(i * w / slots):int((i + 1) * w / slots)]
        background = part[..., 2][part[..., 1] < 60]
        levels.append(float(np.median(background)) if background.size else 0.0)
    best = int(np.argmax(levels))
    others = [v for i, v in enumerate(levels) if i != best]
    # Sem diferença clara (ex: região fora do lugar) é melhor não chutar
    if not others or levels[best] < max(others) * 1.4 + 5:
        return None
    return best


def region_point(calibration: Dict, name: str, screen_width: int, slot: int = 0) -> Optional[tuple]:
    """Centro da região (ou de um dos seus botões) em pixels da tela real, para clicar."""
    region = calibration.get("regions", {}).get(name)
    if not region:
        return None
    scale = screen_width / float(calibration.get("base_width") or screen_width)
    slots = int(region.get("slots", 1))
    x = (region["x"] + region["w"] * (slot + 0.5) / slots) * scale
    y = (region["y"] + region["h"] / 2) * scale
    return int(round(x)), int(round(y))


def read_regions(frame: np.ndarray, calibration: Dict) -> Dict:
    """Lê todas as barras calibradas no frame. Barra não encontrada vira None."""
    scale = frame.shape[1] / float(calibration.get("base_width") or frame.shape[1])
    readings: Dict[str, object] = {}
    regions = calibration.get("regions", {})
    for name, (kind, color) in REGION_KINDS.items():
        region = regions.get(name)
        if not region:
            continue
        rect = scaled_rect(region, scale, frame.shape)
        if rect is None:
            readings[name] = None
            continue
        x, y, w, h = rect
        crop = frame[y:y + h, x:x + w]
        if kind == "bar":
            readings[name] = bar_fill(crop, color)
        elif kind == "stance":
            slot = active_slot(crop, int(region.get("slots", 3)))
            readings[name] = STANCES[slot] if slot is not None and slot < len(STANCES) else None
        else:
            slots = int(region.get("slots", 1))
            bands: List[Optional[float]] = []
            for i in range(slots):
                y0, y1 = int(i * h / slots), int((i + 1) * h / slots)
                bands.append(bar_fill(crop[y0:y1], color))
            readings[name] = bands
    return readings
