"""
otpbot/hunts/hunt_model.py — Uma hunt salva: rota, alvos, bolas, equipe com papéis e regras (ARQUITETURA §5).

Cada hunt é um arquivo `%APPDATA%\\OTPBot\\hunts\\<nome>.json` [Q47, Q58]. O gravador (E09) gera o rascunho, o
editor do console (E09) revisa, e a máquina de fases (E10) executa.

Equipe com papéis (preparação da v2, [Q63]): a hunt tem uma lista de pokémons, cada um com um papel. Os quatro papéis
já existem no formato; a v1.0 aceita só `damage` (exatamente 1) e `healer` (no máximo 1). `lure` e `damage2` são da
v2 e a validação recusa por enquanto, sem mudar a estrutura.

Regras: os padrões são os da ESPECIFICACAO §2–§4 (N para parar 8, N mínimo no ponto de matar 5, buff de defesa com
5, cura abaixo de 90%, 3 tentativas de bola).
"""
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from otpbot.app import paths

FORMAT_VERSION = 1

# Tipos de ponto da rota [Q45]: andar, parar e lurar, parar e matar, escada
POINT_KINDS = ("walk", "lure", "kill", "stairs")
ROLES = ("damage", "healer", "lure", "damage2")
ROLES_V1 = ("damage", "healer")
BALL_KINDS = ("shiny", "normal")
_NAME = re.compile(r"^[\w\- ]{1,60}$")


class HuntError(ValueError):
    """Hunt inválida; `errors` tem a lista de problemas em português."""

    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass
class Waypoint:
    x: int
    y: int
    z: int
    kind: str = "walk"
    wait_s: float = 0.0  # tempo parado no ponto, vindo da gravação [Q42]


@dataclass
class Targets:
    species: str = ""                                   # espécie da hunt: nome fora dela = suspeito [Q52, Q54]
    capture: List[str] = field(default_factory=list)    # corpos a capturar (nomes de sprites recortados) [Q20]


@dataclass
class Ball:
    kind: str     # "shiny" ou "normal" [Q21]
    sprite: str   # nome do sprite da bola
    key: str      # hotkey (a bola tem auto use) [Q22]


@dataclass
class TeamMember:
    name: str
    role: str
    key: str = ""                  # hotkey para chamar/trocar [Q34]
    slot: Optional[int] = None     # posição na Pokébar (1..), se usada


@dataclass
class Rules:
    stop_count: int = 8            # para com N juntos [Q9]
    stop_min_at_kill: int = 5      # ponto de matar com pelo menos N [Q11]
    defense_buff_count: int = 5    # buff de defesa com 5+ na tela [Q15]
    heal_below_hp: float = 90.0    # % do HP do jogador [Q31]
    ball_attempts: int = 3         # tentativas de captura [Q23]


@dataclass
class Hunt:
    name: str
    route: List[Waypoint] = field(default_factory=list)
    targets: Targets = field(default_factory=Targets)
    balls: List[Ball] = field(default_factory=list)
    team: List[TeamMember] = field(default_factory=list)
    rules: Rules = field(default_factory=Rules)
    version: int = FORMAT_VERSION

    # ------------------------------------------------------------------ papéis
    def members(self, role: str) -> List[TeamMember]:
        return [m for m in self.team if m.role == role]

    @property
    def damage(self) -> Optional[TeamMember]:
        found = self.members("damage")
        return found[0] if found else None

    @property
    def healer(self) -> Optional[TeamMember]:
        found = self.members("healer")
        return found[0] if found else None

    # ------------------------------------------------------------------ validação
    def problems(self) -> List[str]:
        errors = []
        if not _NAME.match(self.name or ""):
            errors.append("nome: use letras, números, espaço, '-' ou '_' (até 60)")
        for i, p in enumerate(self.route, 1):
            if p.kind not in POINT_KINDS:
                errors.append(f"rota, ponto {i}: tipo '{p.kind}' desconhecido ({', '.join(POINT_KINDS)})")
            if min(p.x, p.y, p.z) < 0:
                errors.append(f"rota, ponto {i}: coordenada negativa")
            if p.wait_s < 0:
                errors.append(f"rota, ponto {i}: espera negativa")
        for b in self.balls:
            if b.kind not in BALL_KINDS:
                errors.append(f"bola '{b.sprite}': tipo '{b.kind}' desconhecido ({', '.join(BALL_KINDS)})")
        for m in self.team:
            if m.role not in ROLES:
                errors.append(f"equipe, '{m.name}': papel '{m.role}' desconhecido")
            elif m.role not in ROLES_V1:
                errors.append(f"equipe, '{m.name}': o papel '{m.role}' só entra na v2")
        if len(self.members("damage")) != 1:
            errors.append("equipe: precisa de exatamente 1 pokémon de dano")
        if len(self.members("healer")) > 1:
            errors.append("equipe: no máximo 1 curador")
        r = self.rules
        if not 1 <= r.stop_min_at_kill <= r.stop_count:
            errors.append("regras: o N mínimo no ponto de matar tem que ficar entre 1 e o N para parar")
        if r.defense_buff_count < 1:
            errors.append("regras: N do buff de defesa tem que ser pelo menos 1")
        if not 0 < r.heal_below_hp <= 100:
            errors.append("regras: HP de cura entre 1 e 100%")
        if r.ball_attempts < 1:
            errors.append("regras: pelo menos 1 tentativa de bola")
        return errors

    def validate(self) -> "Hunt":
        errors = self.problems()
        if errors:
            raise HuntError(errors)
        return self

    # ------------------------------------------------------------------ JSON
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hunt":
        try:
            version = int(data.get("version", FORMAT_VERSION))
            if version > FORMAT_VERSION:
                raise HuntError([f"formato {version} é mais novo que este bot ({FORMAT_VERSION})"])
            return cls(
                name=str(data["name"]),
                route=[Waypoint(int(p["x"]), int(p["y"]), int(p["z"]), str(p.get("kind", "walk")),
                                float(p.get("wait_s", 0.0))) for p in data.get("route", [])],
                targets=Targets(**data.get("targets", {})),
                balls=[Ball(**b) for b in data.get("balls", [])],
                team=[TeamMember(**m) for m in data.get("team", [])],
                rules=Rules(**data.get("rules", {})),
                version=FORMAT_VERSION,
            )
        except HuntError:
            raise
        except (KeyError, TypeError, ValueError) as e:
            raise HuntError([f"arquivo de hunt mal formado: {e}"]) from e


# ---------------------------------------------------------------------- arquivos
def _folder(folder: Optional[Path]) -> Path:
    return Path(folder) if folder is not None else paths.hunts_dir()


def hunt_path(name: str, folder: Optional[Path] = None) -> Path:
    if not _NAME.match(name or ""):
        raise HuntError([f"nome de hunt inválido: '{name}'"])
    return _folder(folder) / f"{name}.json"


def save_hunt(hunt: Hunt, folder: Optional[Path] = None) -> Path:
    """Valida e grava (arquivo temporário + troca, para não deixar meio arquivo se o bot cair)."""
    hunt.validate()
    path = hunt_path(hunt.name, folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(hunt.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return path


def load_hunt(name: str, folder: Optional[Path] = None) -> Hunt:
    path = hunt_path(name, folder)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HuntError([f"hunt '{name}' não encontrada em {path.parent}"])
    except json.JSONDecodeError as e:
        raise HuntError([f"{path.name}: JSON inválido ({e})"])
    return Hunt.from_dict(data).validate()


def list_hunts(folder: Optional[Path] = None) -> List[str]:
    folder = _folder(folder)
    return sorted(p.stem for p in folder.glob("*.json")) if folder.exists() else []
