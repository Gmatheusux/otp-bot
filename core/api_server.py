import asyncio
import json
import logging
import os
import secrets
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import runtime as runtime_module

logger = logging.getLogger("APIServer")

# Token gerado a cada execução: só quem abriu o console por esta sessão consegue falar com a API.
SESSION_TOKEN = secrets.token_urlsafe(24)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

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
