import asyncio
from pathlib import Path

import cv2
import numpy as np
import pytest

from otpbot.perception import coords
from otpbot.perception.bars import DEFAULT_CALIBRATION
from otpbot.perception.coords import Coord, CoordReader, read_crop
from otpbot.state.world_state import WorldStore
from tests.helpers import fake_window

ROOT = Path(__file__).resolve().parents[1]
E01 = ROOT / "docs" / "e01"

# Prints reais da área cliente (E01): o texto da caixinha conferido a olho no recorte ampliado
REAL = [
    ("captura_1920_janela.png", Coord(433, 1501, 7)),
    ("captura_1920_monitor_secundario.png", Coord(2690, 4170, 2)),
    ("captura_3440_janela.png", Coord(457, 1457, 7)),
]


def load(name):
    return cv2.imdecode(np.fromfile(str(E01 / name), np.uint8), cv2.IMREAD_COLOR)


@pytest.fixture(scope="module")
def reader():
    return CoordReader()


def compose(text, glyphs, gap=2, space=4):
    """Caixinha sintética: os modelos lado a lado sobre o fundo escuro da caixinha."""
    cols = [np.zeros((coords.LINE_H, 3), bool)]
    for ch in text:
        if ch == " ":
            cols.append(np.zeros((coords.LINE_H, space), bool))
            continue
        cols += [glyphs[ch], np.zeros((coords.LINE_H, gap), bool)]
    mask = np.hstack(cols)
    mask = np.pad(mask, ((4, 4), (0, 0)))
    img = np.full(mask.shape + (3,), (47, 38, 28), np.uint8)
    img[mask] = (254, 254, 254)
    return img


@pytest.mark.parametrize("name,expected", REAL)
def test_le_as_coordenadas_dos_prints_reais(reader, name, expected):
    r = reader.read(load(name), DEFAULT_CALIBRATION)
    assert r.coord == expected
    assert r.confidence >= coords.MIN_SCORE


def test_regiao_fica_no_mesmo_lugar_a_partir_da_direita():
    assert coords.coords_rect(DEFAULT_CALIBRATION, (1009, 1920, 3)) == (1534, 31, 88, 18)
    assert coords.coords_rect(DEFAULT_CALIBRATION, (1369, 3440, 3)) == (3054, 31, 88, 18)


def test_todos_os_modelos_se_reconhecem(reader):
    for char, mask in reader.glyphs.items():
        assert coords.classify(mask, reader.glyphs) == (char, 1.0)


def test_texto_sintetico_com_todos_os_digitos_que_temos(reader):
    digits = "".join(sorted(c for c in reader.glyphs if c.isdigit()))
    text = f"{digits[:4]}, {digits[4:8]}, {digits[8:] or '1'}"
    r = read_crop(compose(text, reader.glyphs), reader.glyphs)
    assert r.text == text.replace(" ", "")
    assert r.coord is not None and r.confidence == 1.0


def test_recorte_vazio_ou_ruido_nao_vira_coordenada(reader):
    empty = np.full((18, 88, 3), (47, 38, 28), np.uint8)
    assert read_crop(empty, reader.glyphs).coord is None
    rng = np.random.default_rng(0)
    noise = rng.integers(0, 255, (18, 88, 3), dtype=np.uint8)
    assert read_crop(noise, reader.glyphs).coord is None


def test_caractere_desconhecido_derruba_a_leitura(reader):
    img = compose("433, 1501, 7", reader.glyphs)
    img[6:14, 20:24] = 254  # borrão por cima de um dígito
    r = read_crop(img, reader.glyphs)
    assert r.coord is None and "?" in r.text


def test_formato_errado_nao_vira_coordenada(reader):
    r = read_crop(compose("433, 1501", reader.glyphs), reader.glyphs)
    assert r.coord is None and r.text == "433,1501"


def test_sem_modelos_nao_le(reader):
    assert read_crop(load(REAL[0][0])[31:49, 1534:1622], {}).coord is None


def test_salvar_e_carregar_modelo(tmp_path, reader):
    coords.save_glyph(reader.glyphs[","], ",", tmp_path)
    coords.save_glyph(reader.glyphs["7"], "7", tmp_path)
    assert {p.name for p in tmp_path.iterdir()} == {"comma.png", "7.png"}
    loaded = coords.load_glyphs(tmp_path)
    assert (loaded[","] == reader.glyphs[","]).all() and (loaded["7"] == reader.glyphs["7"]).all()


class FakeLocator:
    """Devolve recortes de um print real, como o GameLocator faz com a região."""

    def __init__(self, frame, window):
        self.frame, self._window, self.regions = frame, window, []

    def window(self):
        return self._window

    def capture(self, region=None):
        self.regions.append(region)
        if self.frame is None:
            return None, self._window
        x, y, w, h = region
        return self.frame[y:y + h, x:x + w], self._window


def test_leitura_ao_vivo_copia_so_a_caixinha(reader):
    loc = FakeLocator(load(REAL[0][0]), fake_window(1920, 1009))
    r = coords.read_live(loc, DEFAULT_CALIBRATION, reader)
    assert r.coord == REAL[0][1] and loc.regions == [(1534, 31, 88, 18)]
    assert coords.read_live(FakeLocator(None, None), DEFAULT_CALIBRATION, reader) is None


def test_sensor_publica_no_worldstate(reader):
    async def scenario():
        store, kill, telemetry = WorldStore(), asyncio.Event(), {}
        loc = FakeLocator(load(REAL[2][0]), fake_window(3440, 1369))
        task = asyncio.create_task(coords.coords_monitor(loc, store, lambda: DEFAULT_CALIBRATION, kill, telemetry,
                                                         interval=0.01, reader=reader))
        await store.wait_new(["coords"], 2)
        kill.set()
        await asyncio.wait_for(task, 2)
        return store.snapshot().get("coords"), telemetry["coords"]

    assert asyncio.run(scenario()) == (REAL[2][1], "457, 1457, 7")


def test_sensor_publica_none_sem_jogo(reader):
    async def scenario():
        store, kill = WorldStore(), asyncio.Event()
        task = asyncio.create_task(coords.coords_monitor(FakeLocator(None, None), store, lambda: DEFAULT_CALIBRATION,
                                                         kill, None, interval=0.01, reader=reader))
        await store.wait_new(["coords"], 2)
        kill.set()
        task.cancel()
        r = store.latest("coords")
        return r.value, r.confidence

    assert asyncio.run(scenario()) == (None, 0.0)
