"""
otpbot/app/paths.py — Onde ficam os dados do usuário (D7): %APPDATA%\\OTPBot.

Nada de dado fica na pasta do código. Na primeira execução os arquivos que antes ficavam ao lado do código
(config.json, route.json, assets/, models/) são COPIADOS para cá; a origem nunca é apagada. Arquivo que já existe
no destino não é sobrescrito. Depois entram os padrões do programa (defaults/), só onde faltar.

OTPBOT_DATA_DIR troca a pasta de dados (testes e instalações portáteis).
"""
import filecmp
import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger("Paths")

APP_NAME = "OTPBot"
# Raiz do código: main.py, frontend/, defaults/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULTS_DIR = PROJECT_ROOT / "defaults"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

# (origem relativa à raiz do código antiga, destino relativo à pasta de dados)
LEGACY_ITEMS = (
    ("config.json", "config.json"),
    ("route.json", "route.json"),
    ("assets/sprites", "sprites"),
    ("assets/calibration", "calibration"),
    ("models", "models"),
)


def data_dir() -> Path:
    override = os.environ.get("OTPBOT_DATA_DIR")
    if override:
        return Path(override)
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / APP_NAME


def config_file() -> Path:
    return data_dir() / "config.json"


def route_file() -> Path:
    return data_dir() / "route.json"


def sprites_dir() -> Path:
    return data_dir() / "sprites"


def calibration_dir() -> Path:
    return data_dir() / "calibration"


def models_dir() -> Path:
    return data_dir() / "models"


def logs_dir() -> Path:
    return data_dir() / "logs"


def resolve_data_path(path: str) -> Path:
    """Caminho relativo do config (ex: models/otp_yolo.pt) vale a partir da pasta de dados."""
    p = Path(path)
    return p if p.is_absolute() else data_dir() / p


def _copy_missing(src: Path, dst: Path, copied: List[Tuple[Path, Path]]) -> None:
    if src.is_dir():
        for child in sorted(src.iterdir()):
            _copy_missing(child, dst / child.name, copied)
        return
    if dst.exists() or src.suffix == ".pyc":
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if not filecmp.cmp(src, dst, shallow=False):
        raise OSError(f"Cópia diferente da origem: {src} -> {dst}")
    copied.append((src, dst))


def migrate_legacy(legacy_root: Optional[Path] = None) -> List[Tuple[Path, Path]]:
    """Copia os dados do lugar antigo (ao lado do código) para a pasta de dados. Nunca apaga a origem."""
    root = Path(legacy_root) if legacy_root else PROJECT_ROOT
    target = data_dir()
    copied: List[Tuple[Path, Path]] = []
    for src_rel, dst_rel in LEGACY_ITEMS:
        src = root / src_rel
        if src.exists():
            _copy_missing(src, target / dst_rel, copied)
    for src, dst in copied:
        logger.info(f"Migrado: {src} -> {dst} (o original continua no lugar)")
    return copied


def install_defaults() -> List[Tuple[Path, Path]]:
    """Padrões do programa (prints de referência da calibração) onde ainda não houver nada."""
    copied: List[Tuple[Path, Path]] = []
    if (DEFAULTS_DIR / "calibration").exists():
        _copy_missing(DEFAULTS_DIR / "calibration", calibration_dir(), copied)
    return copied


def prepare() -> Path:
    """Cria as pastas de dados, migra os arquivos antigos e completa com os padrões."""
    for folder in (data_dir(), sprites_dir(), calibration_dir(), models_dir(), logs_dir()):
        folder.mkdir(parents=True, exist_ok=True)
    migrate_legacy()
    install_defaults()
    return data_dir()
