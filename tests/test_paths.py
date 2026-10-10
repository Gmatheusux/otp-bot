import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from otpbot.app import paths
from otpbot.interface.config_manager import ConfigManager


def make_legacy(root):
    """Pasta antiga com o layout de antes da E02 (dados ao lado do código), com acento no caminho."""
    (root / "assets" / "sprites").mkdir(parents=True)
    (root / "assets" / "calibration").mkdir(parents=True)
    (root / "models").mkdir()
    (root / "config.json").write_text('{"hotkeys": {"pause": "f7"}}', encoding="utf-8")
    (root / "route.json").write_text('[{"x": 1, "y": 2, "delay": 1.0}]', encoding="utf-8")
    (root / "assets" / "sprites" / "sprites.json").write_text("[]", encoding="utf-8")
    (root / "assets" / "sprites" / "abc.png").write_bytes(b"png")
    (root / "assets" / "calibration" / "reference_1920x1080.png").write_bytes(b"meu print")
    (root / "models" / "otp_yolo.pt").write_bytes(b"pesos")
    return root


def test_data_dir_follows_env(isolated_data_dir):
    assert paths.data_dir() == isolated_data_dir
    assert paths.config_file() == isolated_data_dir / "config.json"
    assert paths.resolve_data_path("models/otp_yolo.pt") == isolated_data_dir / "models" / "otp_yolo.pt"


def test_data_dir_defaults_to_appdata(monkeypatch, tmp_path):
    monkeypatch.delenv("OTPBOT_DATA_DIR")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert paths.data_dir() == tmp_path / "OTPBot"


def test_migration_copies_everything_and_keeps_origin(tmp_path, isolated_data_dir):
    legacy = make_legacy(tmp_path / "automação")
    copied = paths.migrate_legacy(legacy)

    assert len(copied) == 6
    assert json.loads(paths.config_file().read_text(encoding="utf-8")) == {"hotkeys": {"pause": "f7"}}
    assert paths.route_file().exists()
    assert (paths.sprites_dir() / "abc.png").read_bytes() == b"png"
    assert (paths.calibration_dir() / "reference_1920x1080.png").read_bytes() == b"meu print"
    assert (paths.models_dir() / "otp_yolo.pt").read_bytes() == b"pesos"
    # A origem nunca é apagada
    assert (legacy / "config.json").exists() and (legacy / "assets" / "sprites" / "abc.png").exists()


def test_migration_never_overwrites(tmp_path, isolated_data_dir):
    legacy = make_legacy(tmp_path / "antigo")
    isolated_data_dir.mkdir(parents=True)
    paths.config_file().write_text('{"novo": true}', encoding="utf-8")

    copied = paths.migrate_legacy(legacy)

    assert paths.config_file().read_text(encoding="utf-8") == '{"novo": true}'
    assert paths.config_file() not in [dst for _, dst in copied]
    assert paths.migrate_legacy(legacy) == []  # segunda vez não copia nada


def test_defaults_fill_only_missing(tmp_path, isolated_data_dir):
    legacy = make_legacy(tmp_path / "antigo")
    paths.migrate_legacy(legacy)
    paths.install_defaults()

    # O print do usuário vence o padrão; o perfil que faltava vem do padrão do programa
    assert (paths.calibration_dir() / "reference_1920x1080.png").read_bytes() == b"meu print"
    assert (paths.calibration_dir() / "reference_3440x1440.png").exists()


def test_prepare_creates_folders(isolated_data_dir):
    paths.prepare()
    for folder in ("sprites", "calibration", "models", "logs"):
        assert (isolated_data_dir / folder).is_dir()


def test_config_manager_uses_data_dir_and_drops_chat_roi(isolated_data_dir):
    isolated_data_dir.mkdir(parents=True)
    paths.config_file().write_text(json.dumps(
        {"features": {"safety": {"gm_monitor": False, "chat_roi": [10, 600, 400, 30]}}}), encoding="utf-8")

    mgr = ConfigManager()

    assert mgr.config_path == str(paths.config_file())
    assert mgr.config["features"]["safety"] == {"gm_monitor": False}
    assert "chat" in mgr.config["calibration"]["profiles"]["1920x1080"]["regions"]
