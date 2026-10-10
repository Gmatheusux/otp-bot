import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from otpbot.actuation.input_lock import InputBusy, InputLock  # noqa: E402


def test_um_dono_por_vez_e_o_mais_importante_toma():
    lock = InputLock()
    hunt = lock.grant("hunt", 3)
    assert lock.is_valid(hunt)
    safety = lock.grant("safety", 0)
    assert lock.is_valid(safety) and not lock.is_valid(hunt)
    with pytest.raises(InputBusy):
        lock.grant("hunt", 3)


def test_mesmo_dono_mantem_o_lease():
    lock = InputLock()
    assert lock.grant("hunt", 3) is lock.grant("hunt", 3)


def test_release_e_revoke_all():
    lock = InputLock()
    hunt = lock.grant("hunt", 3)
    lock.release(hunt)
    assert lock.current is None and not lock.is_valid(hunt)
    again = lock.grant("hunt", 3)
    assert again != hunt  # geração nova: o lease velho não volta a valer
    lock.revoke_all()
    assert not lock.is_valid(again) and not lock.is_valid(None)
