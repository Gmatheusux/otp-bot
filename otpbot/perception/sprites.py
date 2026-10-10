"""
otpbot/perception/sprites.py — Biblioteca de sprites de itens escolhidos pelo jogador no console.
Cada sprite é um recorte PNG da tela; o bot localiza o item comparando o recorte com o frame
(Template Matching, TM_CCOEFF_NORMED).
"""
import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

from otpbot.app import paths

logger = logging.getLogger("SpriteLibrary")

CATEGORIES = ("potion", "antidote", "revive", "buff", "ball", "other")
DEFAULT_THRESHOLD = 0.85
MIN_SIDE = 6
MAX_SIDE = 256


def encode_png(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ValueError("Falha ao codificar PNG.")
    return buf.tobytes()


def decode_image(data: bytes) -> np.ndarray:
    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Arquivo de imagem inválido.")
    return img


class SpriteLibrary:
    def __init__(self, root: Optional[str] = None):
        # cv2.imread/imwrite não aceitam acentos no caminho no Windows ("automação");
        # por isso todo I/O de imagem passa por bytes (imencode/imdecode + Path).
        self.root = Path(root) if root else paths.sprites_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "sprites.json"
        self._lock = threading.Lock()
        self._templates: Dict[str, np.ndarray] = {}
        self._sprites: List[Dict] = self._load_index()

    def _load_index(self) -> List[Dict]:
        if not self.index_path.exists():
            return []
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao ler {self.index_path}: {e}")
            return []

    def _save_index(self):
        self.index_path.write_text(json.dumps(self._sprites, indent=4, ensure_ascii=False), encoding="utf-8")

    def _find(self, sprite_id: str) -> Dict:
        for sprite in self._sprites:
            if sprite["id"] == sprite_id:
                return sprite
        raise KeyError(sprite_id)

    def list(self) -> List[Dict]:
        with self._lock:
            return [dict(s) for s in self._sprites]

    def add(self, name: str, category: str, image: np.ndarray, key: str = "",
            threshold: float = DEFAULT_THRESHOLD) -> Dict:
        if category not in CATEGORIES:
            raise ValueError(f"Categoria inválida: {category}")
        h, w = image.shape[:2]
        if min(h, w) < MIN_SIDE or max(h, w) > MAX_SIDE:
            raise ValueError(f"O recorte precisa ter entre {MIN_SIDE} e {MAX_SIDE} pixels de lado (veio {w}x{h}).")

        sprite_id = uuid.uuid4().hex[:10]
        file_name = f"{sprite_id}.png"
        (self.root / file_name).write_bytes(encode_png(image))
        sprite = {
            "id": sprite_id,
            "name": name.strip() or "Item sem nome",
            "category": category,
            "key": key,
            "threshold": float(threshold),
            "file": file_name,
            "width": int(w),
            "height": int(h),
            "created_at": int(time.time()),
        }
        with self._lock:
            self._sprites.append(sprite)
            self._templates[sprite_id] = image
            self._save_index()
        logger.info(f"Sprite adicionado: {sprite['name']} ({category}, {w}x{h})")
        return dict(sprite)

    def update(self, sprite_id: str, **fields) -> Dict:
        allowed = {"name", "category", "key", "threshold"}
        with self._lock:
            sprite = self._find(sprite_id)
            for field, value in fields.items():
                if field not in allowed or value is None:
                    continue
                if field == "category" and value not in CATEGORIES:
                    raise ValueError(f"Categoria inválida: {value}")
                sprite[field] = float(value) if field == "threshold" else value
            self._save_index()
            return dict(sprite)

    def remove(self, sprite_id: str):
        with self._lock:
            sprite = self._find(sprite_id)
            self._sprites.remove(sprite)
            self._templates.pop(sprite_id, None)
            self._save_index()
        (self.root / sprite["file"]).unlink(missing_ok=True)
        logger.info(f"Sprite removido: {sprite['name']}")

    def image_bytes(self, sprite_id: str) -> bytes:
        with self._lock:
            sprite = self._find(sprite_id)
        return (self.root / sprite["file"]).read_bytes()

    def template(self, sprite_id: str) -> np.ndarray:
        with self._lock:
            if sprite_id not in self._templates:
                sprite = self._find(sprite_id)
                self._templates[sprite_id] = decode_image((self.root / sprite["file"]).read_bytes())
            return self._templates[sprite_id]

    def match(self, sprite_id: str, frame: np.ndarray, threshold: Optional[float] = None,
              max_results: int = 20) -> Dict:
        """Procura o sprite no frame. Retorna melhor nota e as posições acima do limiar."""
        with self._lock:
            sprite = dict(self._find(sprite_id))
        templ = self.template(sprite_id)
        limit = sprite["threshold"] if threshold is None else threshold
        th, tw = templ.shape[:2]
        if frame.shape[0] < th or frame.shape[1] < tw:
            return {"found": False, "best_score": 0.0, "matches": []}

        res = cv2.matchTemplate(frame, templ, cv2.TM_CCOEFF_NORMED)
        res = np.nan_to_num(res, nan=0.0)  # áreas de cor sólida geram NaN
        best = float(res.max())

        # Supressão de não-máximos simples: pega o maior pico, apaga a vizinhança, repete
        matches = []
        work = res.copy()
        while len(matches) < max_results:
            _, score, _, (x, y) = cv2.minMaxLoc(work)
            if score < limit:
                break
            matches.append({"x": int(x), "y": int(y), "w": int(tw), "h": int(th), "score": round(float(score), 3)})
            work[max(0, y - th // 2):y + th // 2 + 1, max(0, x - tw // 2):x + tw // 2 + 1] = -1.0

        return {"found": bool(matches), "best_score": round(best, 3), "matches": matches}
