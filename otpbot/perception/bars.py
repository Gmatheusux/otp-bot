"""
otpbot/perception/bars.py — Regiões fixas da interface do jogo e leitura das barras por cor.

A interface do cliente NÃO cresce com o monitor: os painéis têm o mesmo tamanho em pixels em
qualquer resolução; o que muda é a área do jogo e a posição do que fica à direita/embaixo.
Por isso há um perfil de regiões por resolução (em pixels reais da tela), escolhido pelo
tamanho do frame. Uma resolução sem perfil usa o mais próximo, escalado pela largura.
"""
import copy
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# Faixas HSV (OpenCV: H 0-180) das barras do cliente
COLOR_RANGES = {
    "green": [((35, 90, 90), (85, 255, 255))],
    "yellow": [((10, 90, 110), (35, 255, 255))],
    "red": [((0, 90, 90), (9, 255, 255)), ((170, 90, 90), (180, 255, 255))],
    "blue": [((95, 90, 90), (130, 255, 255))],
}

# Como cada região é lida
REGION_KINDS = {
    "player_hp": ("bar", "red"),      # painel Pokémon: barra vermelha = HP do jogador
    "pokemon_hp": ("bar", "blue"),    # painel Pokémon: barra azul = HP do pokémon
    "exp_bar": ("bar", "yellow"),
    "team": ("slots", "green"),
    "stance": ("stance", None),
}

# Ordem das mãos no painel, da esquerda para a direita
STANCES = ("offensive", "neutral", "defensive")


def _scaled(regions: Dict, factor: float) -> Dict:
    out = {}
    for name, region in regions.items():
        r = dict(region)
        for k in ("x", "y", "w", "h"):
            r[k] = int(round(region[k] * factor))
        out[name] = r
    return out


# 3440x1440: medido no print do jogador, que veio reduzido para 2000px de largura (fator 1.72)
_REGIONS_3440_AT_2000 = {
    "game_area": {"x": 318, "y": 2, "w": 1360, "h": 714},
    "player_hp": {"x": 45, "y": 36, "w": 60, "h": 10},
    "pokemon_hp": {"x": 45, "y": 49, "w": 61, "h": 9},
    "stance": {"x": 46, "y": 63, "w": 56, "h": 18, "slots": 3},
    "exp_bar": {"x": 726, "y": 685, "w": 718, "h": 7},
    "team": {"x": 22, "y": 104, "w": 71, "h": 144, "slots": 5},
    "battle_list": {"x": 0, "y": 290, "w": 105, "h": 160},
    "skills": {"x": 668, "y": 425, "w": 185, "h": 22},
    "hotbar": {"x": 545, "y": 693, "w": 910, "h": 22},
    "minimap": {"x": 1776, "y": 22, "w": 208, "h": 146},
    "coords": {"x": 1775, "y": 18, "w": 62, "h": 12},
    "chat": {"x": 240, "y": 740, "w": 800, "h": 38},
}

# 1920x1080: medido em escala 1:1 no print do jogador
_REGIONS_1920 = {
    "game_area": {"x": 398, "y": 138, "w": 1124, "h": 588},
    "player_hp": {"x": 84, "y": 54, "w": 102, "h": 17},
    "pokemon_hp": {"x": 84, "y": 76, "w": 102, "h": 18},
    "stance": {"x": 88, "y": 103, "w": 93, "h": 30, "slots": 3},
    "exp_bar": {"x": 728, "y": 810, "w": 758, "h": 12},
    "team": {"x": 44, "y": 172, "w": 125, "h": 196, "slots": 4},
    "battle_list": {"x": 8, "y": 440, "w": 180, "h": 280},
    "hotbar": {"x": 415, "y": 825, "w": 1095, "h": 36},
    "minimap": {"x": 1536, "y": 30, "w": 372, "h": 256},
    "coords": {"x": 1537, "y": 26, "w": 80, "h": 16},
    "chat": {"x": 412, "y": 900, "w": 1096, "h": 70},
}

# Área CLIENTE da janela maximizada com barra de título [E01]: os sensores capturam só ela desde a E03.
# Medido na E03 nas capturas do cliente (1920: print ao vivo; 3440: docs/e01/captura_3440_janela.png).
# Os painéis da esquerda ficam nas mesmas coordenadas do cliente nas duas resoluções.
_CLIENT_LEFT_PANEL = {
    "player_hp": {"x": 84, "y": 58, "w": 102, "h": 17},
    "pokemon_hp": {"x": 84, "y": 81, "w": 102, "h": 17},
    "stance": {"x": 88, "y": 107, "w": 93, "h": 30, "slots": 3},
    "team": {"x": 44, "y": 186, "w": 125, "h": 245, "slots": 5},
}

# O painel de baixo e a Battle mudam de altura conforme o jogador arruma a interface: confira na Calibração.
_REGIONS_1920_CLIENT = {
    **_CLIENT_LEFT_PANEL,
    "game_area": {"x": 398, "y": 133, "w": 1124, "h": 588},
    "exp_bar": {"x": 728, "y": 796, "w": 758, "h": 12},
    "battle_list": {"x": 8, "y": 460, "w": 180, "h": 300},
    "hotbar": {"x": 415, "y": 812, "w": 1095, "h": 36},
    "minimap": {"x": 1536, "y": 34, "w": 372, "h": 256},
    # Caixinha "x, y, z" do minimapa: dentro da borda dela [E08], 386 px antes da borda direita nas duas resoluções
    "coords": {"x": 1920 - 386, "y": 31, "w": 88, "h": 18},
    "chat": {"x": 412, "y": 893, "w": 1096, "h": 75},
}

_REGIONS_3440_CLIENT = {
    **_scaled(_REGIONS_3440_AT_2000, 3440 / 2000),
    **_CLIENT_LEFT_PANEL,
    "game_area": {"x": 552, "y": 4, "w": 2336, "h": 1224},
    "exp_bar": {"x": 1249, "y": 1175, "w": 1235, "h": 12},
    "battle_list": {"x": 8, "y": 455, "w": 180, "h": 280},
    "hotbar": {"x": 939, "y": 1190, "w": 1565, "h": 38},
    "coords": {"x": 3440 - 386, "y": 31, "w": 88, "h": 18},
    "chat": {"x": 413, "y": 1270, "w": 1376, "h": 60},
}

DEFAULT_CALIBRATION = {
    "summon_name": "Megaclefable",
    "profiles": {
        "3440x1440": {"width": 3440, "height": 1440, "regions": _scaled(_REGIONS_3440_AT_2000, 3440 / 2000)},
        "1920x1080": {"width": 1920, "height": 1080, "regions": _REGIONS_1920},
        "3440x1369": {"width": 3440, "height": 1369, "regions": _REGIONS_3440_CLIENT},
        "1920x1009": {"width": 1920, "height": 1009, "regions": _REGIONS_1920_CLIENT},
    },
}


def migrate_calibration(calibration: Dict) -> Dict:
    """Formato antigo ({base_width, regions} escalado pela largura) -> perfil 3440x1440."""
    if "regions" not in calibration or "profiles" in calibration:
        return calibration
    base = float(calibration.get("base_width") or 2000)
    migrated = copy.deepcopy(DEFAULT_CALIBRATION)
    migrated["summon_name"] = calibration.get("summon_name", migrated["summon_name"])
    migrated["profiles"]["3440x1440"]["regions"] = _scaled(calibration["regions"], 3440 / base)
    return migrated


def pick_profile(calibration: Dict, width: int, height: int,
                 forced: Optional[str] = None) -> Tuple[Optional[str], Optional[Dict], float]:
    """Perfil da resolução exata; senão o de largura mais próxima. Retorna (chave, perfil, escala)."""
    profiles = calibration.get("profiles", {})
    if not profiles:
        return None, None, 1.0
    key = forced if forced in profiles else f"{width}x{height}"
    if key not in profiles:
        same_width = [k for k, p in profiles.items() if p.get("width") == width]
        key = same_width[0] if same_width else min(profiles, key=lambda k: abs(profiles[k].get("width", 0) - width))
    profile = profiles[key]
    return key, profile, width / float(profile.get("width") or width)


def scaled_rect(region: Dict, scale: float, frame_shape) -> Optional[tuple]:
    """Converte a região do perfil para pixels do frame, recortando nas bordas."""
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


def region_point(calibration: Dict, name: str, screen_width: int, screen_height: int,
                 slot: int = 0) -> Optional[tuple]:
    """Centro da região (ou de um dos seus botões) em pixels da tela real, para clicar."""
    _, profile, scale = pick_profile(calibration, screen_width, screen_height)
    region = (profile or {}).get("regions", {}).get(name)
    if not region:
        return None
    slots = int(region.get("slots", 1))
    if REGION_KINDS.get(name, (None,))[0] == "slots":
        # Pokébar: um pokémon embaixo do outro
        x = (region["x"] + region["w"] / 2) * scale
        y = (region["y"] + region["h"] * (slot + 0.5) / slots) * scale
    else:
        # Mãos de postura e afins: lado a lado
        x = (region["x"] + region["w"] * (slot + 0.5) / slots) * scale
        y = (region["y"] + region["h"] / 2) * scale
    return int(round(x)), int(round(y))


def read_regions(frame: np.ndarray, calibration: Dict, profile_key: Optional[str] = None) -> Dict:
    """Lê todas as barras calibradas no frame. Barra não encontrada vira None."""
    fh, fw = frame.shape[:2]
    key, profile, scale = pick_profile(calibration, fw, fh, forced=profile_key)
    readings: Dict[str, object] = {"profile": key}
    regions = (profile or {}).get("regions", {})
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
