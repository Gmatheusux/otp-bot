import json

import pytest

from otpbot.app import paths
from otpbot.hunts.hunt_model import (Ball, Hunt, HuntError, Rules, Targets, TeamMember, Waypoint, list_hunts,
                                     load_hunt, save_hunt)


def sample():
    return Hunt(
        name="Clefairy teste",
        route=[Waypoint(433, 1501, 7), Waypoint(440, 1501, 7, "lure"), Waypoint(445, 1498, 7, "kill", 4.5),
               Waypoint(446, 1498, 7, "stairs")],
        targets=Targets(species="Clefairy", capture=["corpo_clefairy_shiny"]),
        balls=[Ball("shiny", "ultra_ball", "f8"), Ball("normal", "poke_ball", "f9")],
        team=[TeamMember("Megaclefable", "damage", "f5", 1), TeamMember("Blissey", "healer", "f6", 2)],
    )


def test_padroes_das_regras_sao_os_da_especificacao():
    r = Rules()
    assert (r.stop_count, r.stop_min_at_kill, r.defense_buff_count, r.heal_below_hp, r.ball_attempts) == \
        (8, 5, 5, 90.0, 3)


def test_salva_em_appdata_hunts_e_le_igual():
    h = sample()
    path = save_hunt(h)
    assert path == paths.hunts_dir() / "Clefairy teste.json"
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 1
    assert load_hunt("Clefairy teste") == h
    assert list_hunts() == ["Clefairy teste"]


def test_equipe_com_papeis():
    h = sample()
    assert h.damage.name == "Megaclefable" and h.healer.name == "Blissey"
    assert h.members("lure") == []


def test_papeis_da_v2_ja_existem_mas_a_v1_recusa():
    h = sample()
    h.team.append(TeamMember("Wigglytuff", "lure"))
    h.team.append(TeamMember("Clefable", "damage2"))
    errors = h.problems()
    assert any("'lure' só entra na v2" in e for e in errors)
    assert any("'damage2' só entra na v2" in e for e in errors)


def test_equipe_precisa_de_um_dano_e_no_maximo_um_curador():
    h = sample()
    h.team = [TeamMember("Blissey", "healer"), TeamMember("Chansey", "healer")]
    errors = h.problems()
    assert "equipe: precisa de exatamente 1 pokémon de dano" in errors
    assert "equipe: no máximo 1 curador" in errors
    h.team = [TeamMember("Megaclefable", "damage")]  # sem curador é válido
    assert h.problems() == []


def test_erros_de_rota_bola_regras_e_nome():
    h = sample()
    h.name = "../fora"
    h.route.append(Waypoint(1, 2, 7, "voar"))
    h.balls.append(Ball("master", "x", "f1"))
    h.rules = Rules(stop_count=4, stop_min_at_kill=5, heal_below_hp=0, ball_attempts=0)
    with pytest.raises(HuntError) as e:
        h.validate()
    text = " | ".join(e.value.errors)
    for part in ("nome", "tipo 'voar'", "tipo 'master'", "N mínimo", "HP de cura", "tentativa de bola"):
        assert part in text


def test_nao_salva_hunt_invalida():
    h = sample()
    h.team = []
    with pytest.raises(HuntError):
        save_hunt(h)
    assert list_hunts() == []


def test_arquivo_com_campos_faltando_usa_os_padroes(tmp_path):
    (tmp_path / "Minima.json").write_text(json.dumps(
        {"name": "Minima", "team": [{"name": "A", "role": "damage"}], "route": [{"x": 1, "y": 2, "z": 7}]}),
        encoding="utf-8")
    h = load_hunt("Minima", tmp_path)
    assert h.rules == Rules() and h.route[0].kind == "walk" and h.balls == []


def test_arquivo_ruim_vira_erro_legivel(tmp_path):
    (tmp_path / "Ruim.json").write_text("{nada", encoding="utf-8")
    (tmp_path / "Futuro.json").write_text(json.dumps({"name": "Futuro", "version": 99}), encoding="utf-8")
    (tmp_path / "Torto.json").write_text(json.dumps({"name": "Torto", "route": [{"x": 1}]}), encoding="utf-8")
    for name, part in (("Ruim", "JSON inválido"), ("Futuro", "mais novo"), ("Torto", "mal formado"),
                       ("Nenhuma", "não encontrada")):
        with pytest.raises(HuntError) as e:
            load_hunt(name, tmp_path)
        assert part in str(e.value)
