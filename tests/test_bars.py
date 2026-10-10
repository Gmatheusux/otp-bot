import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from otpbot.perception.bars import active_slot, bar_fill, migrate_calibration, pick_profile, read_regions

GREEN = (0, 200, 0)    # BGR
YELLOW = (0, 190, 240)
RED = (40, 40, 210)
TRACK = (40, 40, 40)


def bar(width, fill_pct, color, height=8):
    img = np.full((height, width, 3), TRACK, dtype=np.uint8)
    img[:, : int(width * fill_pct / 100)] = color
    return img


def test_le_barra_parcial():
    assert abs(bar_fill(bar(200, 74, GREEN), "green") - 74) <= 1


def test_texto_no_meio_da_barra_nao_atrapalha():
    img = bar(200, 74, GREEN)
    img[2:6, 60:90] = (255, 255, 255)  # "74%" escrito por cima
    assert abs(bar_fill(img, "green") - 74) <= 1


def test_barra_vazia_ou_cor_errada_retorna_none():
    assert bar_fill(bar(200, 0, GREEN), "green") is None
    assert bar_fill(bar(200, 80, YELLOW), "green") is None


def stance_buttons(active):
    """3 botões com fundo escuro; o ativo tem fundo claro. Desenhos coloridos no meio."""
    img = np.full((18, 60, 3), 25, dtype=np.uint8)
    img[:, active * 20:(active + 1) * 20] = 55
    for i, color in enumerate([(0, 0, 220), (90, 130, 160), (60, 200, 60)]):
        img[5:13, i * 20 + 6:i * 20 + 14] = color
    return img


def test_detecta_a_mao_ativa():
    assert [active_slot(stance_buttons(i), 3) for i in range(3)] == [0, 1, 2]


def test_sem_destaque_nao_chuta_postura():
    img = np.full((18, 60, 3), 25, dtype=np.uint8)
    assert active_slot(img, 3) is None


def test_escolhe_o_perfil_da_resolucao():
    calibration = {"profiles": {
        "3440x1440": {"width": 3440, "height": 1440, "regions": {}},
        "1920x1080": {"width": 1920, "height": 1080, "regions": {}},
    }}
    assert pick_profile(calibration, 1920, 1080)[:2][0] == "1920x1080"
    assert pick_profile(calibration, 3440, 1440)[0] == "3440x1440"
    key, _, scale = pick_profile(calibration, 2560, 1440)  # sem perfil: o de largura mais próxima
    assert key == "1920x1080" and abs(scale - 2560 / 1920) < 1e-9


def test_migra_calibracao_antiga_para_perfil_3440():
    old = {"base_width": 2000, "summon_name": "Megaclefable",
           "regions": {"player_hp": {"x": 100, "y": 50, "w": 10, "h": 10}}}
    new = migrate_calibration(old)
    assert new["profiles"]["3440x1440"]["regions"]["player_hp"] == {"x": 172, "y": 86, "w": 17, "h": 17}
    assert "1920x1080" in new["profiles"]


def test_escala_quando_nao_ha_perfil_da_resolucao():
    # Perfil de 1000px; frame real com o dobro do tamanho
    calibration = {"profiles": {"1000x500": {"width": 1000, "height": 500, "regions": {
        "player_hp": {"x": 100, "y": 50, "w": 100, "h": 8},
        "team": {"x": 10, "y": 100, "w": 100, "h": 40, "slots": 2},
    }}}}
    frame = np.zeros((400, 2000, 3), dtype=np.uint8)
    frame[100:116, 200:400] = bar(200, 50, RED, height=16)  # HP do jogador é a barra vermelha
    frame[200:240, 20:220] = bar(200, 100, GREEN, height=40)
    frame[240:280, 20:220] = bar(200, 30, GREEN, height=40)

    readings = read_regions(frame, calibration)

    assert abs(readings["player_hp"] - 50) <= 1
    assert [round(v) for v in readings["team"]] == [100, 30]
