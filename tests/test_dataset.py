import json

import cv2
import numpy as np
import pytest

from otpbot.learning import dataset as ds
from otpbot.learning.dataset import CLASSES, AutoCollector, Dataset, crop_game_area, split_for_group
from otpbot.perception.bars import DEFAULT_CALIBRATION


def frame(w=200, h=100, value=0):
    img = np.full((h, w, 3), value, dtype=np.uint8)
    cv2.rectangle(img, (10, 10), (40, 30), (0, 0, 255), -1)
    return img


def test_classes_sao_exatamente_as_cinco_da_v1():
    assert CLASSES == ("meu_pokemon", "selvagem", "selvagem_shiny", "corpo", "corpo_shiny")


def test_pasta_padrao_fica_na_pasta_de_dados(isolated_data_dir):
    d = Dataset()
    assert d.root == isolated_data_dir / "dataset"
    for sub in ("pending", "images/train", "images/val", "labels/train", "labels/val"):
        assert (d.root / sub).is_dir()


def test_data_yaml_no_formato_do_yolo(tmp_path):
    d = Dataset(tmp_path / "ds")
    text = (d.root / "data.yaml").read_text(encoding="utf-8")
    assert "train: images/train" in text and "val: images/val" in text
    for i, name in enumerate(CLASSES):
        assert f"  {i}: {name}" in text


def test_print_novo_fica_pendente_e_fora_do_treino(tmp_path):
    d = Dataset(tmp_path / "ds")
    image_id = d.add(frame(), source="live", group="live:1")
    assert (d.root / "pending" / f"{image_id}.png").exists()
    assert not any((d.root / "images").rglob("*.png"))
    assert d.list("pending")[0]["id"] == image_id
    assert d.list("labeled") == []
    assert d.load_labels(image_id)["boxes"] == []


def test_salvar_e_reabrir_rotulos(tmp_path):
    d = Dataset(tmp_path / "ds")
    image_id = d.add(frame(), source="live", group="live:1")
    boxes = [{"cls": 1, "x": 10, "y": 20, "w": 40, "h": 30}, {"cls": 4, "x": 100, "y": 50, "w": 20, "h": 20}]
    saved = d.save_labels(image_id, boxes)
    split = saved["split"]
    assert split in ("train", "val")
    assert (d.root / "images" / split / f"{image_id}.png").exists()
    assert not (d.root / "pending" / f"{image_id}.png").exists()
    lines = (d.root / "labels" / split / f"{image_id}.txt").read_text().splitlines()
    assert lines[0] == "1 0.150000 0.350000 0.200000 0.300000"

    reopened = Dataset(tmp_path / "ds").load_labels(image_id)  # instância nova: lê do disco
    assert reopened["labeled"] and reopened["split"] == split
    assert reopened["boxes"] == [{"cls": 1, "x": 10.0, "y": 20.0, "w": 40.0, "h": 30.0},
                                 {"cls": 4, "x": 100.0, "y": 50.0, "w": 20.0, "h": 20.0}]


def test_regravar_mantem_a_divisao_e_troca_as_caixas(tmp_path):
    d = Dataset(tmp_path / "ds")
    image_id = d.add(frame(), source="live", group="live:1")
    split = d.save_labels(image_id, [{"cls": 0, "x": 1, "y": 1, "w": 10, "h": 10}])["split"]
    again = d.save_labels(image_id, [])
    assert again["split"] == split and again["boxes"] == []
    assert (d.root / "labels" / split / f"{image_id}.txt").read_text() == ""  # revisada, sem nada = negativo


def test_caixa_fora_da_imagem_e_recortada_e_classe_invalida_recusada(tmp_path):
    d = Dataset(tmp_path / "ds")
    image_id = d.add(frame(), source="live", group="g")
    out = d.save_labels(image_id, [{"cls": 2, "x": -10, "y": -10, "w": 30, "h": 30}])
    assert out["boxes"] == [{"cls": 2, "x": 0.0, "y": 0.0, "w": 20.0, "h": 20.0}]
    with pytest.raises(ValueError):
        d.save_labels(image_id, [{"cls": 5, "x": 1, "y": 1, "w": 10, "h": 10}])
    with pytest.raises(ValueError):
        d.save_labels(image_id, [{"cls": 0, "x": 500, "y": 1, "w": 10, "h": 10}])


def test_divisao_por_grupo_e_estavel():
    assert split_for_group("video-x:3") == split_for_group("video-x:3")
    groups = [f"g:{i}" for i in range(1000)]
    val = sum(split_for_group(g) == "val" for g in groups)
    assert 150 < val < 250  # ~20%


def test_mesmo_grupo_cai_todo_do_mesmo_lado(tmp_path):
    d = Dataset(tmp_path / "ds")
    splits = set()
    for _ in range(5):
        image_id = d.add(frame(), source="video-a", group="video-a:7")
        splits.add(d.save_labels(image_id, [])["split"])
    assert len(splits) == 1


def test_descartar_apaga_e_nao_volta(tmp_path):
    d = Dataset(tmp_path / "ds")
    image_id = d.add(frame(), source="v", group="g", image_id="v_t0001.0")
    d.save_labels(image_id, [{"cls": 3, "x": 1, "y": 1, "w": 10, "h": 10}])
    d.delete(image_id)
    assert not any(d.root.rglob("v_t0001.0.*"))
    assert d.exists(image_id)  # lembrado como descartado
    with pytest.raises(KeyError):
        d.load_labels(image_id)


def test_id_com_caminho_e_recusado(tmp_path):
    d = Dataset(tmp_path / "ds")
    with pytest.raises(KeyError):
        d.image_bytes("../manifest")


def test_estatisticas_por_classe(tmp_path):
    d = Dataset(tmp_path / "ds")
    a = d.add(frame(), source="s", group="g1")
    d.add(frame(), source="s", group="g2")
    d.save_labels(a, [{"cls": 1, "x": 1, "y": 1, "w": 10, "h": 10}, {"cls": 1, "x": 50, "y": 1, "w": 10, "h": 10},
                      {"cls": 0, "x": 1, "y": 50, "w": 10, "h": 10}])
    stats = d.stats()
    assert stats["images"]["pending"] == 1
    assert stats["images"]["train"] + stats["images"]["val"] == 1
    assert stats["boxes"]["selvagem"] == 2 and stats["boxes"]["meu_pokemon"] == 1


def test_manifest_guarda_origem_e_perfil(tmp_path):
    d = Dataset(tmp_path / "ds")
    image_id = d.add(frame(), source="video-x", group="video-x:0", profile="1920x1009", extra={"video_time_s": 3.0})
    data = json.loads((d.root / "manifest.json").read_text(encoding="utf-8"))
    entry = data["images"][image_id]
    assert entry["profile"] == "1920x1009" and entry["video_time_s"] == 3.0 and entry["split"] is None


def test_recorte_da_area_do_jogo_pelo_perfil():
    img = np.zeros((1009, 1920, 3), dtype=np.uint8)
    crop, key = crop_game_area(img, DEFAULT_CALIBRATION)
    assert key == "1920x1009" and crop.shape[:2] == (588, 1124)
    crop, key = crop_game_area(np.zeros((1369, 3440, 3), dtype=np.uint8), DEFAULT_CALIBRATION)
    assert key == "3440x1369" and crop.shape[:2] == (1224, 2336)


def test_coletor_pula_print_repetido_e_jogo_invisivel(tmp_path):
    d = Dataset(tmp_path / "ds")
    frames = [None, np.zeros((1009, 1920, 3), np.uint8), np.zeros((1009, 1920, 3), np.uint8),
              np.full((1009, 1920, 3), 120, np.uint8)]
    collector = AutoCollector(d, lambda: (frames.pop(0), None), lambda: DEFAULT_CALIBRATION)
    assert collector.capture_once(skip_similar=True) is None and "não visível" in collector.last_error
    assert collector.capture_once(skip_similar=True) is not None
    assert collector.capture_once(skip_similar=True) is None and collector.skipped == 1
    assert collector.capture_once(skip_similar=True) is not None
    assert d.stats()["images"]["pending"] == 2
    assert all(e["profile"] == "1920x1009" for e in d.list())


def test_extracao_de_video(tmp_path):
    from tools.extrair_frames_video import extract, source_name
    from pathlib import Path
    video = tmp_path / "Service 2026-10-09 20-41-41.avi"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 10, (1920, 1009))
    for i in range(40):  # 4 s; muda de cena no segundo 2
        writer.write(np.full((1009, 1920, 3), 40 if i < 20 else 200, np.uint8))
    writer.release()
    d = Dataset(tmp_path / "ds")
    result = extract(video, 1.0, dataset=d, calibration=DEFAULT_CALIBRATION)
    assert source_name(Path(video)) == "video-20261009-204141"
    assert result["profile"] == "1920x1009" and result["saved"] == 2 and result["skipped"] == 2
    again = extract(video, 1.0, dataset=d, calibration=DEFAULT_CALIBRATION)
    assert again["saved"] == 0 and again["existing"] == 2  # rodar de novo não duplica
    assert all(e["width"] == 1124 for e in d.list())


def test_rotas_do_dataset(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from otpbot.interface import api_server, dataset_api

    monkeypatch.setattr(dataset_api, "_dataset", Dataset(tmp_path / "ds"))
    image_id = dataset_api._dataset.add(frame(), source="live", group="g")
    client = TestClient(api_server.app)
    headers = {"X-OTP-Token": api_server.SESSION_TOKEN}

    assert client.get("/api/dataset").status_code == 401
    body = client.get("/api/dataset", headers=headers).json()
    assert body["stats"]["images"]["pending"] == 1 and body["images"][0]["id"] == image_id
    assert client.get(f"/api/dataset/{image_id}/image", headers=headers).content[:4] == b"\x89PNG"
    r = client.put(f"/api/dataset/{image_id}/labels", headers=headers,
                   json={"boxes": [{"cls": 1, "x": 10, "y": 20, "w": 40, "h": 30}]})
    assert r.status_code == 200 and r.json()["labeled"]
    assert client.get(f"/api/dataset/{image_id}/labels", headers=headers).json()["boxes"][0]["cls"] == 1
    bad = client.put(f"/api/dataset/{image_id}/labels", headers=headers,
                     json={"boxes": [{"cls": 9, "x": 1, "y": 1, "w": 5, "h": 5}]})
    assert bad.status_code == 422
    assert client.get("/api/dataset/nao-existe/labels", headers=headers).status_code == 404
    assert client.delete(f"/api/dataset/{image_id}", headers=headers).status_code == 200


def test_dois_processos_nao_apagam_o_que_o_outro_gravou(tmp_path):
    console = Dataset(tmp_path / "ds")       # o console aberto
    a = console.add(frame(), source="live", group="g")
    extrator = Dataset(tmp_path / "ds")      # a extração de vídeo rodando por fora
    b = extrator.add(frame(), source="video-x", group="video-x:0", image_id="video-x_t0003.0")
    console.save_labels(a, [])                # antes sobrescrevia o manifest sem o "b"
    again = Dataset(tmp_path / "ds")
    assert again.exists(a) and again.exists(b)
    assert {e["id"] for e in console.list()} == {a, b}


def test_png_fora_do_manifest_e_recuperado(tmp_path):
    d = Dataset(tmp_path / "ds")
    a = d.add(frame(w=120, h=80), source="video-x", group="video-x:0", image_id="video-x_t0090.0")
    d.save_labels(a, [{"cls": 1, "x": 1, "y": 1, "w": 10, "h": 10}])
    d.add(frame(w=120, h=80), source="video-x", group="video-x:0", image_id="video-x_t0093.0")
    (d.root / "manifest.json").unlink()
    again = Dataset(tmp_path / "ds")
    items = {e["id"]: e for e in again.list()}
    assert set(items) == {"video-x_t0090.0", "video-x_t0093.0"}
    assert items["video-x_t0090.0"]["labeled"] and items["video-x_t0090.0"]["boxes"] == 1
    assert items["video-x_t0093.0"]["width"] == 120 and items["video-x_t0093.0"]["height"] == 80
    assert items["video-x_t0093.0"]["group"] == "video-x:3"  # 93 s // 30
