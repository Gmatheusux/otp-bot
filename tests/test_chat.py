import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from otpbot.perception.bars import DEFAULT_CALIBRATION
from otpbot.perception.chat import chat_roi


def test_chat_roi_comes_from_calibration_profile():
    assert chat_roi(DEFAULT_CALIBRATION, 1920, 1080) == (412, 900, 1096, 70)


def test_chat_roi_scales_unknown_resolution():
    # 2560 de largura: sem perfil próprio, usa o 1920x1080 (o mais próximo) escalado pela largura
    x, y, w, h = chat_roi(DEFAULT_CALIBRATION, 2560, 1440)
    assert (x, y) == (round(412 * 2560 / 1920), round(900 * 2560 / 1920))


def test_chat_roi_missing_region():
    calibration = {"profiles": {"1920x1080": {"width": 1920, "height": 1080, "regions": {}}}}
    assert chat_roi(calibration, 1920, 1080) is None
