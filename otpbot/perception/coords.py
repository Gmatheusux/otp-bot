"""
otpbot/perception/coords.py — Posição x, y, z do personagem pela caixinha do minimapa (ex.: "433, 1501, 7").

Leitura por dígitos-modelo (risco R3), sem Tesseract: a fonte do jogo é fixa e o texto sai sempre com os mesmos
pixels (branco com contorno preto, conferido nos prints da E01 em 1920 e 3440). Então:

  1. recorte da região `coords` da calibração;
  2. pixels claros (cinza >= LIT) viram máscara;
  3. colunas vazias separam os caracteres; a linha começa na primeira linha acesa;
  4. cada caractere é comparado com os modelos (`defaults/coords/*.png`) por Jaccard;
  5. o texto tem que casar com "x, y, z".

Confiança = a pior nota entre os caracteres. Caractere desconhecido, nota baixa ou formato errado = None (ninguém
age sobre posição incerta, ARQUITETURA §3).
"""
import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np

from otpbot.app.paths import DEFAULTS_DIR
from otpbot.perception.bars import pick_profile, scaled_rect

logger = logging.getLogger("Coords")

GLYPHS_DIR = DEFAULTS_DIR / "coords"
LIT = 120          # cinza mínimo de um pixel do texto (o fundo da caixinha fica abaixo de 80)
LINE_H = 10        # 8 linhas do dígito + 2 da cauda da vírgula
# A fonte sai sempre com os mesmos pixels: o certo dá 1.00 nos prints reais. Os mais parecidos entre si (6 e 9)
# dão 0.82, então exigimos nota alta E folga sobre o segundo colocado.
MIN_SCORE = 0.92   # nota mínima de cada caractere
MIN_MARGIN = 0.08  # o melhor modelo tem que ganhar do segundo por isto
GLYPH_NAMES = {"comma": ","}  # nome do arquivo -> caractere (dígitos usam o próprio nome)
_FORMAT = re.compile(r"^(\d{1,5}),(\d{1,5}),(\d{1,2})$")


@dataclass(frozen=True)
class Coord:
    x: int
    y: int
    z: int

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __str__(self) -> str:
        return f"{self.x}, {self.y}, {self.z}"


@dataclass(frozen=True)
class CoordReading:
    coord: Optional[Coord]
    confidence: float
    text: str  # o que foi lido ("?" no caractere desconhecido), para log e diagnóstico


def text_mask(crop: np.ndarray) -> np.ndarray:
    gray = crop if crop.ndim == 2 else cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return gray >= LIT


def segment(mask: np.ndarray) -> List[np.ndarray]:
    """Máscaras dos caracteres, da esquerda para a direita, todas com LINE_H linhas a partir do topo do texto."""
    rows = np.flatnonzero(mask.any(axis=1))
    if rows.size == 0:
        return []
    top = rows[0]
    band = mask[top:top + LINE_H]
    if band.shape[0] < LINE_H:
        band = np.pad(band, ((0, LINE_H - band.shape[0]), (0, 0)))
    cols = band.any(axis=0)
    glyphs, start = [], None
    for x, on in enumerate(list(cols) + [False]):
        if on and start is None:
            start = x
        elif not on and start is not None:
            glyphs.append(band[:, start:x])
            start = None
    return glyphs


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Jaccard das duas máscaras alinhadas à esquerda (largura diferente conta como erro)."""
    w = max(a.shape[1], b.shape[1])
    a = np.pad(a, ((0, 0), (0, w - a.shape[1])))
    b = np.pad(b, ((0, 0), (0, w - b.shape[1])))
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / union) if union else 0.0


def load_glyphs(folder: Path = GLYPHS_DIR) -> Dict[str, np.ndarray]:
    glyphs = {}
    for f in sorted(Path(folder).glob("*.png")):
        img = cv2.imdecode(np.fromfile(str(f), np.uint8), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        glyphs[GLYPH_NAMES.get(f.stem, f.stem)] = img > 127
    return glyphs


def save_glyph(mask: np.ndarray, char: str, folder: Path = GLYPHS_DIR) -> Path:
    name = next((k for k, v in GLYPH_NAMES.items() if v == char), char)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.png"
    cv2.imencode(".png", mask.astype(np.uint8) * 255)[1].tofile(str(path))
    return path


def classify(glyph: np.ndarray, glyphs: Dict[str, np.ndarray]) -> Tuple[str, float]:
    """(caractere, nota). '?' se a nota é baixa ou se dois modelos empatam."""
    ranked = sorted(((similarity(glyph, model), char) for char, model in glyphs.items()), reverse=True)
    if not ranked:
        return "?", 0.0
    score, best = ranked[0]
    second = ranked[1][0] if len(ranked) > 1 else 0.0
    if score < MIN_SCORE or score - second < MIN_MARGIN:
        return "?", score
    return best, score


def read_crop(crop: np.ndarray, glyphs: Dict[str, np.ndarray]) -> CoordReading:
    parts = segment(text_mask(crop))
    if not parts or not glyphs:
        return CoordReading(None, 0.0, "")
    chars, scores = zip(*(classify(g, glyphs) for g in parts))
    text = "".join(chars)
    conf = min(scores)
    m = _FORMAT.match(text)
    if m is None:
        return CoordReading(None, 0.0, text)
    return CoordReading(Coord(*(int(v) for v in m.groups())), conf, text)


def coords_rect(calibration: Dict, frame_shape) -> Optional[Tuple[int, int, int, int]]:
    """(x, y, w, h) da região `coords` do perfil do frame, cortada nos limites do frame."""
    h, w = frame_shape[:2]
    _, profile, scale = pick_profile(calibration, w, h)
    region = (profile or {}).get("regions", {}).get("coords")
    if not region:
        return None
    return scaled_rect(region, scale, frame_shape)


def read_live(locator, calibration: Dict, reader: "CoordReader") -> Optional[CoordReading]:
    """Copia só a caixinha da tela e lê. None = jogo fechado, minimizado, coberto ou sem região."""
    window = locator.window()
    if window is None or window.minimized:
        return None
    rect = coords_rect(calibration, (window.client.height, window.client.width))
    if rect is None:
        return None
    crop, _ = locator.capture(rect)
    if crop is None:
        return None
    return read_crop(crop, reader.glyphs)


async def coords_monitor(locator, store, calibration: Callable[[], Dict], kill_event, telemetry: Optional[dict] = None,
                         interval: float = 0.1, reader: Optional["CoordReader"] = None) -> None:
    """
    Sensor das coordenadas: publica `coords` (Coord) no WorldState ~10x/s, com a confiança da leitura. Só observa a
    tela, então roda mesmo pausado (o movimento confere cada passo por ele).
    """
    reader = reader or CoordReader()
    last_text = None
    while not kill_event.is_set():
        try:
            reading = await asyncio.to_thread(read_live, locator, calibration(), reader)
            if reading is None or reading.coord is None:
                store.publish("coords", None, confidence=0.0)
                if reading is not None and reading.text != last_text:
                    logger.debug(f"Coordenada ilegível: '{reading.text}'")
            else:
                store.publish("coords", reading.coord, confidence=reading.confidence)
            last_text = reading.text if reading else None
            if telemetry is not None:
                telemetry["coords"] = str(reading.coord) if reading and reading.coord else None
            await asyncio.sleep(interval if reading is not None else 1.0)
        except Exception as e:
            logger.error(f"Erro na leitura das coordenadas: {e}")
            await asyncio.sleep(2)


class CoordReader:
    """Lê a posição de um frame da área cliente. Os modelos são carregados uma vez."""

    def __init__(self, glyphs: Optional[Dict[str, np.ndarray]] = None):
        self.glyphs = load_glyphs() if glyphs is None else glyphs
        if not self.glyphs:
            logger.warning(f"Nenhum dígito-modelo em {GLYPHS_DIR}: coordenadas sem leitura.")

    def read(self, frame: np.ndarray, calibration: Dict) -> CoordReading:
        rect = coords_rect(calibration, frame.shape)
        if rect is None:
            return CoordReading(None, 0.0, "")
        x, y, w, h = rect
        return read_crop(frame[y:y + h, x:x + w], self.glyphs)
