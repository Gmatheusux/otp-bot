"""
otpbot/learning/dataset.py — Dataset da visão (E04): prints da área do jogo e rótulos no formato do YOLO.

Pasta: %APPDATA%\\OTPBot\\dataset
    pending/<id>.png            prints ainda não revisados (não entram no treino)
    images/{train,val}/<id>.png prints revisados
    labels/{train,val}/<id>.txt uma linha por caixa: "classe xc yc w h" normalizado (0..1); vazio = sem nada
    data.yaml                   o que o treino YOLO (ultralytics) lê
    manifest.json               origem, resolução e grupo de cada print

Cada imagem é só o recorte da `game_area` do perfil de calibração: os painéis nunca têm estas classes.
A divisão treino/validação é por GRUPO (mesma origem + bloco de 30 s), para frames quase iguais não caírem um em
cada lado; o grupo vira treino ou validação por hash, então imagens novas nunca mudam a divisão das antigas.
"""
import hashlib
import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from otpbot.app import paths
from otpbot.perception.bars import pick_profile, scaled_rect

logger = logging.getLogger("Dataset")

# A ordem define o número da classe no YOLO: não reordenar, só acrescentar no fim (com ok do usuário).
CLASSES = ("meu_pokemon", "selvagem", "selvagem_shiny", "corpo", "corpo_shiny")
SPLITS = ("train", "val")
VAL_PERCENT = 20
GROUP_SECONDS = 30  # 60 s deixava 45 treino / 1 validação no primeiro lote (E04)
MIN_BOX_PX = 3
_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,120}$")


def dataset_dir() -> Path:
    return paths.data_dir() / "dataset"


def split_for_group(group: str) -> str:
    """Treino ou validação pelo hash do grupo (estável entre execuções e máquinas)."""
    bucket = int(hashlib.sha1(group.encode("utf-8")).hexdigest(), 16) % 100
    return "val" if bucket < VAL_PERCENT else "train"


def group_key(source: str, seconds: float) -> str:
    return f"{source}:{int(seconds // GROUP_SECONDS)}"


def crop_game_area(frame: np.ndarray, calibration: Dict,
                   profile_key: Optional[str] = None) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """Recorte da área do jogo pelo perfil da resolução do frame (ou o perfil forçado). (None, chave) sem região."""
    h, w = frame.shape[:2]
    key, profile, scale = pick_profile(calibration, w, h, profile_key)
    region = (profile or {}).get("regions", {}).get("game_area")
    if region is None:
        return None, key
    rect = scaled_rect(region, scale, frame.shape)
    if rect is None:
        return None, key
    x, y, rw, rh = rect
    return frame[y:y + rh, x:x + rw].copy(), key


def similar(a: Optional[np.ndarray], b: Optional[np.ndarray], max_diff: float = 4.0) -> bool:
    """Dois prints quase iguais (diferença média em cinza, reduzido para 160 px de largura)."""
    if a is None or b is None:
        return False

    def small(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        width = 160
        return cv2.resize(gray, (width, max(1, int(gray.shape[0] * width / gray.shape[1]))),
                          interpolation=cv2.INTER_AREA).astype(np.float32)

    sa, sb = small(a), small(b)
    if sa.shape != sb.shape:
        return False
    return float(np.abs(sa - sb).mean()) < max_diff


def boxes_to_yolo(boxes: List[Dict], width: int, height: int) -> List[str]:
    """Caixas em pixels {cls, x, y, w, h} -> linhas do YOLO. Recorta nas bordas; recusa classe inválida."""
    lines = []
    for box in boxes:
        cls = box.get("cls")
        if not isinstance(cls, int) or isinstance(cls, bool) or not 0 <= cls < len(CLASSES):
            raise ValueError(f"Classe inválida: {cls!r}")
        x0 = max(0.0, min(float(width), float(box["x"])))
        y0 = max(0.0, min(float(height), float(box["y"])))
        x1 = max(0.0, min(float(width), float(box["x"]) + float(box["w"])))
        y1 = max(0.0, min(float(height), float(box["y"]) + float(box["h"])))
        if x1 - x0 < MIN_BOX_PX or y1 - y0 < MIN_BOX_PX:
            raise ValueError(f"Caixa pequena demais ou fora da imagem: {box}")
        xc, yc = (x0 + x1) / 2 / width, (y0 + y1) / 2 / height
        bw, bh = (x1 - x0) / width, (y1 - y0) / height
        lines.append(f"{cls} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
    return lines


def yolo_to_boxes(lines: List[str], width: int, height: int) -> List[Dict]:
    boxes = []
    for line in lines:
        parts = line.split()
        if len(parts) != 5:
            continue
        cls = int(parts[0])
        xc, yc, bw, bh = (float(p) for p in parts[1:])
        boxes.append({
            "cls": cls,
            "x": round((xc - bw / 2) * width, 1),
            "y": round((yc - bh / 2) * height, 1),
            "w": round(bw * width, 1),
            "h": round(bh * height, 1),
        })
    return boxes


def _write_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _encode_png(img: np.ndarray) -> bytes:
    # cv2.imwrite falha calado em caminho com acento: sempre por bytes
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ValueError("Falha ao codificar PNG.")
    return buf.tobytes()


class Dataset:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else dataset_dir()
        self._lock = threading.RLock()
        for folder in [self.root / "pending"] + [self.root / kind / split
                                                for kind in ("images", "labels") for split in SPLITS]:
            folder.mkdir(parents=True, exist_ok=True)
        self._mtime = None
        self._manifest = self._load_manifest()
        if self._recover_orphans():
            self._save_manifest()
        self._write_data_yaml()

    # ------------------------------------------------------------------ arquivos
    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    def _load_manifest(self) -> Dict:
        self._mtime = self._manifest_mtime()
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if isinstance(data.get("images"), dict):
                return data
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as e:
            logger.error(f"manifest.json ilegível ({e}); começando um novo (as imagens continuam na pasta).")
        return {"version": 1, "classes": list(CLASSES), "images": {}}

    def _manifest_mtime(self) -> Optional[int]:
        try:
            return self.manifest_path.stat().st_mtime_ns
        except FileNotFoundError:
            return None

    def _sync(self) -> None:
        """
        Outro processo (a extração de vídeo com o console aberto) pode ter gravado o manifest: relê antes de
        qualquer operação, para nunca sobrescrever o que ele acrescentou.
        """
        if self._manifest_mtime() != self._mtime:
            self._manifest = self._load_manifest()
            self._recover_orphans()

    def _recover_orphans(self) -> int:
        """PNG na pasta e fora do manifest (ex.: manifest sobrescrito) volta para a lista. Devolve quantos."""
        known = self._manifest["images"]
        discarded = set(self._manifest.get("discarded", []))
        found = 0
        for split in (None,) + SPLITS:
            folder = self.root / "images" / split if split else self.root / "pending"
            for png in folder.glob("*.png"):
                image_id = png.stem
                if image_id in known or image_id in discarded or not _ID_RE.match(image_id):
                    continue
                header = png.read_bytes()[:24]  # IHDR: largura e altura em big-endian
                source = image_id.split("_")[0]
                stamp = re.search(r"_t(\d+(?:\.\d+)?)$", image_id)
                boxes = 0
                if split:
                    label = self._label_path(image_id, split)
                    boxes = len(label.read_text(encoding="utf-8").splitlines()) if label.exists() else 0
                known[image_id] = {
                    "source": source,
                    "group": group_key(source, float(stamp.group(1))) if stamp else image_id,
                    "profile": None,
                    "width": int.from_bytes(header[16:20], "big"),
                    "height": int.from_bytes(header[20:24], "big"),
                    "created": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(png.stat().st_mtime)),
                    "split": split,
                    "boxes": boxes,
                    "recovered": True,
                }
                found += 1
        if found:
            logger.warning(f"Dataset: {found} imagens fora do manifest recuperadas.")
        return found

    def _save_manifest(self) -> None:
        _write_atomic(self.manifest_path,
                      json.dumps(self._manifest, indent=1, ensure_ascii=False).encode("utf-8"))
        self._mtime = self._manifest_mtime()

    def _write_data_yaml(self) -> None:
        names = "\n".join(f"  {i}: {name}" for i, name in enumerate(CLASSES))
        text = (f"# Gerado pelo OTP Bot (E04). Classes fixas: não editar à mão.\n"
                f"path: {self.root.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n{names}\n")
        _write_atomic(self.root / "data.yaml", text.encode("utf-8"))

    def _check_id(self, image_id: str) -> Dict:
        if not _ID_RE.match(image_id or ""):
            raise KeyError(image_id)
        entry = self._manifest["images"].get(image_id)
        if entry is None:
            raise KeyError(image_id)
        return entry

    def _image_path(self, image_id: str, entry: Dict) -> Path:
        split = entry.get("split")
        return (self.root / "images" / split if split else self.root / "pending") / f"{image_id}.png"

    def _label_path(self, image_id: str, split: str) -> Path:
        return self.root / "labels" / split / f"{image_id}.txt"

    # ------------------------------------------------------------------ operações
    def exists(self, image_id: str) -> bool:
        with self._lock:
            self._sync()
            return image_id in self._manifest["images"] or image_id in self._manifest.get("discarded", [])

    def add(self, image: np.ndarray, source: str, group: str, profile: Optional[str] = None,
            image_id: Optional[str] = None, extra: Optional[Dict] = None) -> str:
        """Guarda um recorte novo em pending/. Devolve o id."""
        with self._lock:
            self._sync()
            if image_id is None:
                stamp = time.strftime("%Y%m%d-%H%M%S")
                image_id = f"{re.sub(r'[^A-Za-z0-9_.-]', '-', source)}_{stamp}_{int(time.time() * 1000) % 1000:03d}"
            base, n = image_id, 1
            while image_id in self._manifest["images"]:
                n += 1
                image_id = f"{base}_{n}"
            if not _ID_RE.match(image_id):
                raise ValueError(f"Id inválido: {image_id}")
            _write_atomic(self.root / "pending" / f"{image_id}.png", _encode_png(image))
            self._manifest["images"][image_id] = {
                "source": source,
                "group": group,
                "profile": profile,
                "width": int(image.shape[1]),
                "height": int(image.shape[0]),
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "split": None,
                "boxes": 0,
                **(extra or {}),
            }
            self._save_manifest()
            return image_id

    def list(self, status: Optional[str] = None) -> List[Dict]:
        """status: 'pending', 'labeled' ou None (todas). Ordem: origem e data."""
        with self._lock:
            self._sync()
            items = []
            for image_id, entry in self._manifest["images"].items():
                labeled = entry.get("split") is not None
                if status == "pending" and labeled or status == "labeled" and not labeled:
                    continue
                items.append({"id": image_id, "labeled": labeled, **entry})
            return sorted(items, key=lambda e: (e.get("source", ""), e.get("created", ""), e["id"]))

    def image_bytes(self, image_id: str) -> bytes:
        with self._lock:
            self._sync()
            entry = self._check_id(image_id)
            return self._image_path(image_id, entry).read_bytes()

    def load_labels(self, image_id: str) -> Dict:
        with self._lock:
            self._sync()
            entry = self._check_id(image_id)
            split = entry.get("split")
            boxes = []
            if split:
                path = self._label_path(image_id, split)
                lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
                boxes = yolo_to_boxes(lines, entry["width"], entry["height"])
            return {"id": image_id, "labeled": split is not None, "split": split,
                    "width": entry["width"], "height": entry["height"], "boxes": boxes}

    def save_labels(self, image_id: str, boxes: List[Dict]) -> Dict:
        """Salva as caixas (lista vazia = revisada, sem nada). Na primeira vez a imagem sai de pending/."""
        with self._lock:
            self._sync()
            entry = self._check_id(image_id)
            lines = boxes_to_yolo(boxes, entry["width"], entry["height"])
            split = entry.get("split") or split_for_group(entry.get("group") or image_id)
            if entry.get("split") is None:
                os.replace(self.root / "pending" / f"{image_id}.png",
                           self.root / "images" / split / f"{image_id}.png")
                entry["split"] = split
            _write_atomic(self._label_path(image_id, split), ("\n".join(lines) + ("\n" if lines else "")).encode())
            entry["boxes"] = len(lines)
            entry["labeled_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self._save_manifest()
            return self.load_labels(image_id)

    def delete(self, image_id: str) -> None:
        """Descarta um print (só a cópia do dataset; nunca toca no vídeo de origem)."""
        with self._lock:
            self._sync()
            entry = self._check_id(image_id)
            self._image_path(image_id, entry).unlink(missing_ok=True)
            if entry.get("split"):
                self._label_path(image_id, entry["split"]).unlink(missing_ok=True)
            del self._manifest["images"][image_id]
            self._manifest.setdefault("discarded", []).append(image_id)  # a extração do vídeo não traz de volta
            self._save_manifest()

    def stats(self) -> Dict:
        with self._lock:
            self._sync()
            per_class = {name: 0 for name in CLASSES}
            images = {"pending": 0, "train": 0, "val": 0}
            for image_id, entry in self._manifest["images"].items():
                split = entry.get("split")
                images[split or "pending"] += 1
                if not split:
                    continue
                path = self._label_path(image_id, split)
                if path.exists():
                    for line in path.read_text(encoding="utf-8").splitlines():
                        parts = line.split()
                        if parts and parts[0].isdigit() and int(parts[0]) < len(CLASSES):
                            per_class[CLASSES[int(parts[0])]] += 1
            return {"root": str(self.root), "classes": list(CLASSES), "images": images, "boxes": per_class}


class AutoCollector:
    """Captura periódica da área do jogo para o dataset. Pula prints quase iguais ao anterior. Só lê a tela."""

    def __init__(self, dataset: Dataset, capture, calibration):
        self.dataset = dataset
        self._capture = capture            # () -> (frame, window)
        self._calibration = calibration    # () -> dict de calibração atual
        self.enabled = False
        self.interval_s = 10.0
        self.saved = 0
        self.skipped = 0
        self.last_error: Optional[str] = None
        self._last: Optional[np.ndarray] = None
        self._session = time.strftime("%Y%m%d-%H%M%S")

    def status(self) -> Dict:
        return {"enabled": self.enabled, "interval_s": self.interval_s, "saved": self.saved,
                "skipped": self.skipped, "last_error": self.last_error}

    def capture_once(self, source: str = "live", skip_similar: bool = False) -> Optional[str]:
        """Um print agora. None se o jogo não está visível ou (com skip_similar) se repetiu o anterior."""
        frame, _ = self._capture()
        if frame is None:
            self.last_error = "Jogo não visível (fechado, minimizado ou com janela por cima)."
            return None
        crop, key = crop_game_area(frame, self._calibration())
        if crop is None:
            self.last_error = f"Perfil {key} sem região game_area."
            return None
        if skip_similar and similar(crop, self._last):
            self.skipped += 1
            return None
        self._last = crop
        self.last_error = None
        group = group_key(f"{source}-{self._session}", time.time())
        image_id = self.dataset.add(crop, source=source, group=group, profile=key)
        self.saved += 1
        return image_id

    async def run(self, stop_event) -> None:
        import asyncio
        while not stop_event.is_set():
            if self.enabled:
                try:
                    image_id = await asyncio.to_thread(self.capture_once, "live", True)
                    if image_id:
                        logger.info(f"Dataset: print {image_id} guardado.")
                except Exception as e:
                    self.last_error = str(e)
                    logger.error(f"Dataset: falha na captura automática: {e}")
            await asyncio.sleep(self.interval_s if self.enabled else 0.5)
