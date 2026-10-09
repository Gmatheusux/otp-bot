import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.sprite_library import SpriteLibrary


def make_sprite(seed=1, size=24):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, (size, size, 3), dtype=np.uint8)


@pytest.fixture
def library(tmp_path):
    # Pasta com acento, como "03- Projeto de automação": cv2.imwrite quebraria aqui
    return SpriteLibrary(str(tmp_path / "automação" / "sprites"))


def test_adiciona_e_recarrega_do_disco(library):
    sprite = library.add("Ultra Potion", "potion", make_sprite(), key="f5")
    reloaded = SpriteLibrary(str(library.root))
    assert [s["name"] for s in reloaded.list()] == ["Ultra Potion"]
    assert reloaded.template(sprite["id"]).shape == (24, 24, 3)


def test_encontra_o_sprite_nas_posicoes_certas(library):
    templ = make_sprite()
    sprite = library.add("Revive", "revive", templ)
    frame = np.zeros((300, 400, 3), dtype=np.uint8)
    frame[50:74, 100:124] = templ
    frame[200:224, 300:324] = templ

    result = library.match(sprite["id"], frame)

    assert result["found"]
    assert sorted((m["x"], m["y"]) for m in result["matches"]) == [(100, 50), (300, 200)]


def test_nao_encontra_item_ausente(library):
    sprite = library.add("Antídoto", "antidote", make_sprite(seed=1))
    frame = np.zeros((300, 400, 3), dtype=np.uint8)
    frame[50:74, 100:124] = make_sprite(seed=2)
    assert not library.match(sprite["id"], frame)["found"]


def test_remove_apaga_o_arquivo(library):
    sprite = library.add("Buff", "buff", make_sprite())
    library.remove(sprite["id"])
    assert library.list() == []
    assert not (library.root / sprite["file"]).exists()


def test_rejeita_categoria_e_tamanho_invalidos(library):
    with pytest.raises(ValueError):
        library.add("x", "arma", make_sprite())
    with pytest.raises(ValueError):
        library.add("x", "potion", make_sprite(size=3))
