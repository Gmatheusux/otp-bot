import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import fake_window  # noqa: E402
from otpbot.perception.capture import GameLocator  # noqa: E402


def test_janela_e_procurada_no_maximo_uma_vez_por_intervalo():
    calls, now = [], [0.0]

    def locate():
        calls.append(now[0])
        return fake_window()

    locator = GameLocator(locate=locate, refresh_s=1.0, clock=lambda: now[0])
    locator.window(); locator.window()
    now[0] = 1.5
    locator.window()
    assert calls == [0.0, 1.5]


def test_sem_jogo_os_sensores_ficam_sem_frame():
    locator = GameLocator(locate=lambda: None)
    assert locator.capture() == (None, None)


def test_jogo_coberto_por_outra_janela_nao_e_lido():
    locator = GameLocator(locate=fake_window, covered=lambda w: True)
    frame, window = locator.capture()
    assert frame is None and window is not None


def test_detecta_janela_por_cima_em_algum_ponto_do_cliente():
    from otpbot.platform.game_window import is_covered
    window = fake_window()
    assert not is_covered(window, owner_at=lambda x, y: 1)
    assert is_covered(window, owner_at=lambda x, y: 99 if x > 1000 and y < 100 else 1)  # canto superior direito


def test_jogo_minimizado_nao_e_capturado():
    from dataclasses import replace
    window = replace(fake_window(), minimized=True)
    locator = GameLocator(locate=lambda: window)
    assert locator.capture() == (None, window)
