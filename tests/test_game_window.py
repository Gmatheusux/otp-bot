import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from otpbot.platform.game_window import (GameWindow, Monitor, Rect, capture_client, monitor_for,
                                         pick_window_profile, save_png)

# Layout real da E01: principal 1920x1080 em (0,0), secundário à esquerda em (-1920,0)
PRINCIPAL = Monitor(r"\\.\DISPLAY1", Rect(0, 0, 1920, 1080), True)
SECUNDARIO = Monitor(r"\\.\DISPLAY2", Rect(-1920, 0, 1920, 1080), False)


def janela(client, monitor=PRINCIPAL, minimized=False):
    return GameWindow(hwnd=1, client=client, monitor=monitor, foreground=False, minimized=minimized)


def test_janela_maximizada_cai_no_monitor_certo():
    # Maximizada, a janela passa 8px de cada borda; o cliente medido foi (0, 23) 1920x1009
    assert monitor_for(Rect(0, 23, 1920, 1009), [SECUNDARIO, PRINCIPAL]) is PRINCIPAL
    assert monitor_for(Rect(-1928, -8, 1936, 1048), [PRINCIPAL, SECUNDARIO]) is SECUNDARIO


def test_janela_entre_dois_monitores_fica_no_de_maior_area():
    assert monitor_for(Rect(-500, 0, 800, 600), [PRINCIPAL, SECUNDARIO]) is SECUNDARIO


def test_janela_fora_de_qualquer_monitor():
    assert monitor_for(Rect(5000, 5000, 100, 100), [PRINCIPAL, SECUNDARIO]) is None
    assert monitor_for(Rect(0, 0, 10, 10), []) is None


class FakeSct:
    def __init__(self):
        self.pedido = None

    def grab(self, region):
        self.pedido = region
        return np.full((region["height"], region["width"], 4), 7, dtype=np.uint8)  # BGRA


def test_captura_so_a_area_cliente_no_monitor_secundario():
    sct = FakeSct()
    img = capture_client(janela(Rect(-1920, 23, 1920, 1009), SECUNDARIO), sct)
    assert sct.pedido == {"left": -1920, "top": 23, "width": 1920, "height": 1009}
    assert img.shape == (1009, 1920, 3)


def test_nao_captura_janela_minimizada():
    with pytest.raises(RuntimeError):
        capture_client(janela(Rect(-32000, -32000, 0, 0), minimized=True), FakeSct())


def test_perfil_escolhido_pelo_tamanho_do_cliente():
    calibration = {"profiles": {
        "3440x1440": {"width": 3440, "height": 1440, "regions": {}},
        "1920x1080": {"width": 1920, "height": 1080, "regions": {}},
    }}
    key, _, scale = pick_window_profile(calibration, janela(Rect(0, 23, 1920, 1009)))
    assert key == "1920x1080" and scale == 1.0
    assert pick_window_profile(calibration, janela(Rect(0, 0, 3440, 1440)))[0] == "3440x1440"


def test_salva_png_em_caminho_com_acento(tmp_path):
    destino = tmp_path / "automação" / "print.png"
    destino.parent.mkdir()
    save_png(str(destino), np.zeros((4, 6, 3), dtype=np.uint8))
    assert destino.stat().st_size > 0
