import pytest


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Nenhum teste lê ou grava em %APPDATA%\\OTPBot de verdade."""
    data = tmp_path / "dados"
    monkeypatch.setenv("OTPBOT_DATA_DIR", str(data))
    return data
