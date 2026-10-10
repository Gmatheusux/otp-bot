import asyncio
import base64
import binascii
import json
import logging
import os
import secrets
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from otpbot.app import paths
from otpbot.app import runtime as runtime_module
from otpbot.perception import bars as screen_calibration
from otpbot.perception import sprites as sprite_library
from otpbot.perception.capture import capture_screen

logger = logging.getLogger("APIServer")

# Token gerado a cada execução: só quem abriu o console por esta sessão consegue falar com a API.
SESSION_TOKEN = secrets.token_urlsafe(24)
FRONTEND_DIST = paths.FRONTEND_DIST

# Sem CORS: o console é servido pela própria API (mesma origem) ou pelo proxy do Vite em dev.
app = FastAPI(title="OTP Bot - Console API", version="1.1.0", docs_url=None, redoc_url=None, openapi_url=None)


def require_token(x_otp_token: Optional[str] = Header(default=None)):
    if not x_otp_token or not secrets.compare_digest(x_otp_token, SESSION_TOKEN):
        raise HTTPException(status_code=401, detail="Token de sessão inválido.")


def get_runtime():
    if runtime_module.runtime is None:
        raise HTTPException(status_code=503, detail="Bot ainda inicializando.")
    return runtime_module.runtime


class ConnectionManager:
    """Gerencia as sessões contínuas de WebSocket para envio de telemetria."""
    def __init__(self, history_size: int = 200):
        self.active_connections: List[WebSocket] = []
        self.history: Deque[Dict[str, Any]] = deque(maxlen=history_size)
        self._seq = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        for entry in list(self.history):
            await websocket.send_json(entry)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    def publish(self, entry: Dict[str, Any]):
        """Deve ser chamado dentro do loop asyncio (via call_soon_threadsafe)."""
        self._seq += 1
        entry["id"] = self._seq
        self.history.append(entry)
        if self.active_connections:
            asyncio.create_task(self.broadcast(entry))

    async def broadcast(self, entry: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(entry)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


class WebSocketLogHandler(logging.Handler):
    """Encaminha os logs do bot (de qualquer thread) para o console via WebSocket."""
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__(level=logging.INFO)
        self.loop = loop

    def emit(self, record: logging.LogRecord):
        entry = {
            "time": time.strftime("%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "source": record.name,
            "message": record.getMessage(),
        }
        try:
            self.loop.call_soon_threadsafe(ws_manager.publish, entry)
        except RuntimeError:
            pass  # loop encerrado durante o shutdown


# Mantido para compatibilidade com quem já chamava broadcast_log diretamente
async def broadcast_log(log_message: str):
    ws_manager.publish({"time": time.strftime("%H:%M:%S"), "level": "INFO", "source": "bot", "message": log_message})


class ControlRequest(BaseModel):
    action: Literal["start", "pause", "toggle", "stop", "cavebot_toggle", "record_toggle"]


@app.get("/api/config", dependencies=[Depends(require_token)])
async def get_config(rt=Depends(get_runtime)) -> Dict[str, Any]:
    """Retorna o JSON de configuração atual em tempo real."""
    return rt.config_manager.config


@app.post("/api/config", dependencies=[Depends(require_token)])
async def update_config(new_config: Dict[str, Any], rt=Depends(get_runtime)):
    """Sobrescreve as configurações de cooldowns/hotkeys dinamicamente."""
    rt.config_manager.update_full_config(new_config)
    rt.config_changed()
    return {"status": "success", "message": "Configurações atualizadas no disco."}


@app.get("/api/route", dependencies=[Depends(require_token)])
async def get_route(rt=Depends(get_runtime)) -> Dict[str, Any]:
    """Waypoints da rota gravada (os da gravação em andamento, se houver)."""
    navigator = rt.navigator
    points = list(navigator.route_points) if navigator else []
    if not points and navigator and os.path.exists(navigator.route_file):
        try:
            with open(navigator.route_file, "r", encoding="utf-8") as f:
                points = json.load(f)
        except (OSError, json.JSONDecodeError):
            points = []
    return {"file": navigator.route_file if navigator else None, "points": points}


@app.get("/api/status", dependencies=[Depends(require_token)])
async def get_status(rt=Depends(get_runtime)) -> Dict[str, Any]:
    return rt.status()


@app.post("/api/control", dependencies=[Depends(require_token)])
async def control(req: ControlRequest, rt=Depends(get_runtime)):
    actions = {
        "start": lambda: rt.set_running(True),
        "pause": lambda: rt.set_running(False),
        "toggle": rt.toggle_running,
        "stop": rt.stop,
        "cavebot_toggle": rt.toggle_cavebot,
        "record_toggle": rt.toggle_recording,
    }
    actions[req.action]()
    return {"status": "ok", "action": req.action}


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    """Endpoint vitalício para streaming de decisões lógicas do orquestrador."""
    if not secrets.compare_digest(token, SESSION_TOKEN):
        await websocket.close(code=4401)
        return
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


class HealTestRequest(BaseModel):
    action: Literal["healer", "farm", "full"]
    delay_s: float = Field(default=3.0, ge=0, le=10)


@app.post("/api/heal/test", dependencies=[Depends(require_token)])
async def heal_test(req: HealTestRequest, rt=Depends(get_runtime)):
    """Testa a cura com pokémon no jogo (após alguns segundos para o jogador voltar ao jogo)."""
    if not rt.heal_test(req.action, req.delay_s):
        raise HTTPException(status_code=409, detail="A rotina de cura já está rodando.")
    return {"status": "agendado", "action": req.action}


# ---------------------------------------------------------------- Sprites de itens

# Último print tirado pelo console: o recorte é feito sobre ele, pixel a pixel, no servidor
_last_screenshot = None


class ScreenshotRequest(BaseModel):
    delay_s: float = Field(default=3.0, ge=0, le=10)


class SpriteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    category: str
    key: str = ""
    region: Optional[List[int]] = None       # [x, y, largura, altura] no último print
    image_base64: Optional[str] = None       # alternativa: PNG enviado pelo jogador


class SpriteUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=60)
    category: Optional[str] = None
    key: Optional[str] = None
    threshold: Optional[float] = Field(default=None, ge=0.5, le=0.99)


def get_sprites(rt=Depends(get_runtime)):
    return rt.sprites


@app.post("/api/screenshot", dependencies=[Depends(require_token)])
async def take_screenshot(req: ScreenshotRequest):
    """Espera alguns segundos (para o jogador trocar para o jogo) e devolve o print em PNG."""
    global _last_screenshot
    await asyncio.sleep(req.delay_s)
    frame = await asyncio.to_thread(capture_screen)
    _last_screenshot = frame
    png = await asyncio.to_thread(sprite_library.encode_png, frame)
    return Response(content=png, media_type="image/png")


@app.get("/api/sprites", dependencies=[Depends(require_token)])
async def list_sprites(sprites=Depends(get_sprites)):
    return {"sprites": sprites.list(), "categories": list(sprite_library.CATEGORIES)}


@app.post("/api/sprites", dependencies=[Depends(require_token)])
async def create_sprite(req: SpriteCreate, sprites=Depends(get_sprites)):
    if req.image_base64:
        try:
            image = sprite_library.decode_image(base64.b64decode(req.image_base64.split(",")[-1]))
        except (ValueError, binascii.Error):
            raise HTTPException(status_code=400, detail="Arquivo de imagem inválido.")
    elif req.region:
        if _last_screenshot is None:
            raise HTTPException(status_code=400, detail="Tire um print antes de recortar.")
        if len(req.region) != 4:
            raise HTTPException(status_code=400, detail="Região deve ser [x, y, largura, altura].")
        x, y, w, h = req.region
        fh, fw = _last_screenshot.shape[:2]
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > fw or y + h > fh:
            raise HTTPException(status_code=400, detail="Região fora do print.")
        image = _last_screenshot[y:y + h, x:x + w].copy()
    else:
        raise HTTPException(status_code=400, detail="Envie uma região do print ou uma imagem.")

    try:
        return sprites.add(req.name, req.category, image, key=req.key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sprites/{sprite_id}/image", dependencies=[Depends(require_token)])
async def sprite_image(sprite_id: str, sprites=Depends(get_sprites)):
    try:
        return Response(content=sprites.image_bytes(sprite_id), media_type="image/png")
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprite não encontrado.")


@app.patch("/api/sprites/{sprite_id}", dependencies=[Depends(require_token)])
async def update_sprite(sprite_id: str, req: SpriteUpdate, sprites=Depends(get_sprites)):
    try:
        return sprites.update(sprite_id, **req.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprite não encontrado.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/sprites/{sprite_id}", dependencies=[Depends(require_token)])
async def delete_sprite(sprite_id: str, sprites=Depends(get_sprites)):
    try:
        sprites.remove(sprite_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprite não encontrado.")
    return {"status": "ok"}


@app.post("/api/sprites/{sprite_id}/test", dependencies=[Depends(require_token)])
async def test_sprite(sprite_id: str, req: ScreenshotRequest, sprites=Depends(get_sprites)):
    """Tira um print novo e diz se o bot encontra o item nele."""
    await asyncio.sleep(req.delay_s)
    frame = await asyncio.to_thread(capture_screen)
    try:
        return await asyncio.to_thread(sprites.match, sprite_id, frame)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprite não encontrado.")


# ---------------------------------------------------------------- Calibração da tela

def reference_path(profile_key: str) -> Path:
    # A chave vem da API: só aceita o formato "1920x1080" para não virar caminho arbitrário
    if not profile_key.replace("x", "", 1).isdigit():
        raise HTTPException(status_code=400, detail="Perfil inválido.")
    return paths.calibration_dir() / f"reference_{profile_key}.png"


class CalibrationTest(BaseModel):
    source: Literal["reference", "screen"] = "reference"
    profile: Optional[str] = None
    delay_s: float = Field(default=0, ge=0, le=10)


@app.get("/api/calibration/reference/{profile_key}", dependencies=[Depends(require_token)])
async def calibration_reference(profile_key: str):
    path = reference_path(profile_key)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Este perfil ainda não tem imagem de referência.")
    return Response(content=path.read_bytes(), media_type="image/png")


@app.post("/api/calibration/reference", dependencies=[Depends(require_token)])
async def set_calibration_reference(req: ScreenshotRequest, rt=Depends(get_runtime)):
    """
    Salva um print atual como referência do perfil da resolução da tela.
    Resolução nova vira um perfil novo, copiado do mais próximo e escalado pela largura.
    """
    await asyncio.sleep(req.delay_s)
    frame = await asyncio.to_thread(capture_screen)
    height, width = frame.shape[:2]
    key = f"{width}x{height}"
    paths.calibration_dir().mkdir(parents=True, exist_ok=True)
    reference_path(key).write_bytes(sprite_library.encode_png(frame))

    config = rt.config_manager.config
    profiles = config["calibration"]["profiles"]
    created = key not in profiles
    if created:
        base_key, base, scale = screen_calibration.pick_profile(config["calibration"], width, height)
        regions = screen_calibration._scaled(base["regions"], scale) if base else {}
        profiles[key] = {"width": width, "height": height, "regions": regions}
        logger.info(f"Perfil de calibração {key} criado a partir de {base_key}. Confira as regiões.")
        rt.config_manager.update_full_config(config)
    return {"status": "ok", "profile": key, "created": created}


@app.post("/api/calibration/test", dependencies=[Depends(require_token)])
async def test_calibration(req: CalibrationTest, rt=Depends(get_runtime)):
    """Lê as barras na imagem de referência de um perfil ou num print novo da tela."""
    calibration = rt.config_manager.config["calibration"]
    if req.source == "reference":
        if not req.profile:
            raise HTTPException(status_code=400, detail="Informe o perfil.")
        path = reference_path(req.profile)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Este perfil ainda não tem imagem de referência.")
        frame = sprite_library.decode_image(path.read_bytes())
    else:
        await asyncio.sleep(req.delay_s)
        frame = await asyncio.to_thread(capture_screen)
    readings = await asyncio.to_thread(screen_calibration.read_regions, frame, calibration, req.profile)
    return {"source": req.source, "width": int(frame.shape[1]), "height": int(frame.shape[0]), "readings": readings}


# O console compilado (npm run build) é servido na raiz. Rotas da API acima têm prioridade.
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="console")
else:
    @app.get("/", response_class=HTMLResponse)
    async def console_missing():
        return (
            "<body style='background:#0b0c0e;color:#d6d8dd;font-family:sans-serif;padding:40px'>"
            "<h2>Console não compilado</h2>"
            "<p>Rode <code>npm run build</code> dentro de <code>frontend/</code> e reabra o bot.</p></body>"
        )
