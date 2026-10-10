import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import fake_window  # noqa: E402
from otpbot.platform import input_backend as ib  # noqa: E402


def make_background(window=fake_window):
    sent = []
    backend = ib.BackgroundBackend(window, post=lambda *msg: sent.append(msg), sleep=lambda _: None)
    return backend, sent


def test_lparam_igual_ao_do_spike_da_e01():
    # tools/spike_input.py: key_lparam(scan, up) = 1 | scan<<16 (+ bits 30 e 31 ao soltar), sem "extended"
    assert ib.key_lparam(0x48, False) == 1 | (0x48 << 16)
    assert ib.key_lparam(0x48, True) == 1 | (0x48 << 16) | (1 << 30) | (1 << 31)
    assert ib.mouse_lparam(1700, 600) == (600 << 16) | 1700


def test_numerico_8_com_num_lock_desligado():
    backend, sent = make_background()
    backend.key("num8")
    assert sent == [(1, ib.WM_KEYDOWN, 0x26, ib.key_lparam(0x48, False)),   # VK_UP + scan 0x48, sem extended
                    (1, ib.WM_KEYUP, 0x26, ib.key_lparam(0x48, True))]


def test_f5_como_no_spike():
    backend, sent = make_background()
    backend.key("f5")
    assert [s[1:3] for s in sent] == [(ib.WM_KEYDOWN, 0x74), (ib.WM_KEYUP, 0x74)]
    assert sent[0][3] == ib.key_lparam(0x3F, False)


def test_ctrl_f1_aperta_o_modificador_em_volta():
    backend, sent = make_background()
    backend.key("ctrl+f1")
    assert [(s[1], s[2]) for s in sent] == [(ib.WM_KEYDOWN, ib.VK_CONTROL), (ib.WM_KEYDOWN, 0x70),
                                           (ib.WM_KEYUP, 0x70), (ib.WM_KEYUP, ib.VK_CONTROL)]
    assert backend._held == []


def test_seta_dedicada_tem_o_bit_extended_e_num_lock_ligado_nao():
    assert ib.parse_key("up") == ([], (0x26, 0x48, True))
    assert ib.parse_key("num8") == ([], (0x26, 0x48, False))
    assert ib.parse_key("num 8") == ([], (0x68, 0x48, False))


def test_clique_em_pixels_do_cliente_sem_mover_o_cursor():
    backend, sent = make_background()
    backend.click(1700, 600)
    lp = ib.mouse_lparam(1700, 600)
    assert sent == [(1, ib.WM_MOUSEMOVE, 0, lp), (1, ib.WM_LBUTTONDOWN, ib.MK_LBUTTON, lp),
                    (1, ib.WM_LBUTTONUP, 0, lp)]


def test_teclas_que_o_bot_nao_sabe_mandar():
    with pytest.raises(ValueError):
        ib.parse_key("")
    with pytest.raises(ValueError):
        ib.parse_key("hyper+f1")
    with pytest.raises(ValueError):
        ib.parse_key("tecla_inventada")


def test_sem_janela_do_jogo_nada_e_enviado():
    backend, sent = make_background(window=lambda: None)
    with pytest.raises(RuntimeError):
        backend.key("f1")
    assert sent == []


def test_backend_padrao_e_o_de_segundo_plano():
    assert ib.DEFAULT_BACKEND == "background"
    assert isinstance(ib.make_backend("background", lambda: None), ib.BackgroundBackend)
    assert isinstance(ib.make_backend("foreground", lambda: None), ib.ForegroundBackend)
    assert isinstance(ib.make_backend("xyz", lambda: None), ib.BackgroundBackend)


def test_d20_bot_abaixo_do_jogo_avisa():
    low = ib.check_integrity(1, own=lambda: 0x2000, game=lambda _: 0x3000)
    assert low["ok"] is False and low["bot"] == "média" and low["game"] == "alta"
    assert "administrador" in low["message"]
    ok = ib.check_integrity(1, own=lambda: 0x3000, game=lambda _: 0x3000)
    assert ok["ok"] is True
    assert ib.check_integrity(None, own=lambda: 0x3000)["ok"] is None
