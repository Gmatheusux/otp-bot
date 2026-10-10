"""
otpbot/interface/dataset_api.py — Rotas da aba Visão/IA (E04): coleta de prints e rotulagem.

Ficam num APIRouter à parte para o api_server só incluir (menos conflito com as outras etapas).
Nada aqui envia tecla ou clique ao jogo: só lê a tela.
"""
import asyncio
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from otpbot.app import runtime as runtime_module
from otpbot.learning.dataset import CLASSES, AutoCollector, Dataset

_dataset: Optional[Dataset] = None
_collector: Optional[AutoCollector] = None
_collector_task: Optional[asyncio.Task] = None


def get_dataset() -> Dataset:
    global _dataset
    if _dataset is None:
        _dataset = Dataset()
    return _dataset


def get_collector() -> AutoCollector:
    global _collector
    rt = runtime_module.runtime
    if rt is None or rt.locator is None:
        raise HTTPException(status_code=503, detail="Bot ainda inicializando.")
    if _collector is None:
        _collector = AutoCollector(get_dataset(), rt.locator.capture,
                                   lambda: rt.config_manager.config.get("calibration", {}))
    return _collector


def make_router(require_token) -> APIRouter:
    router = APIRouter(prefix="/api/dataset", dependencies=[Depends(require_token)])

    class Box(BaseModel):
        cls: int = Field(ge=0, lt=len(CLASSES))
        x: float
        y: float
        w: float = Field(gt=0)
        h: float = Field(gt=0)

    class LabelsBody(BaseModel):
        boxes: List[Box]

    class CaptureBody(BaseModel):
        delay_s: float = Field(default=0, ge=0, le=10)

    class AutoBody(BaseModel):
        enabled: bool
        interval_s: float = Field(default=10, ge=2, le=600)

    def not_found():
        return HTTPException(status_code=404, detail="Imagem não encontrada no dataset.")

    @router.get("")
    async def overview(status: Optional[Literal["pending", "labeled"]] = None):
        ds = get_dataset()
        collector = _collector.status() if _collector else {"enabled": False, "interval_s": 10, "saved": 0,
                                                             "skipped": 0, "last_error": None}
        return {"stats": ds.stats(), "images": ds.list(status), "auto": collector}

    @router.get("/{image_id}/image")
    async def image(image_id: str):
        try:
            return Response(content=get_dataset().image_bytes(image_id), media_type="image/png")
        except (KeyError, FileNotFoundError):
            raise not_found()

    @router.get("/{image_id}/labels")
    async def labels(image_id: str):
        try:
            return get_dataset().load_labels(image_id)
        except KeyError:
            raise not_found()

    @router.put("/{image_id}/labels")
    async def save_labels(image_id: str, body: LabelsBody):
        try:
            return await asyncio.to_thread(get_dataset().save_labels, image_id, [b.model_dump() for b in body.boxes])
        except KeyError:
            raise not_found()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.delete("/{image_id}")
    async def delete(image_id: str):
        try:
            get_dataset().delete(image_id)
        except KeyError:
            raise not_found()
        return {"status": "ok"}

    @router.post("/capture")
    async def capture(body: CaptureBody):
        collector = get_collector()
        await asyncio.sleep(body.delay_s)
        image_id = await asyncio.to_thread(collector.capture_once, "live", False)
        if image_id is None:
            raise HTTPException(status_code=409, detail=collector.last_error or "Não foi possível capturar.")
        return {"id": image_id}

    @router.post("/auto")
    async def auto(body: AutoBody):
        global _collector_task
        collector = get_collector()
        collector.enabled, collector.interval_s = body.enabled, body.interval_s
        if body.enabled and (_collector_task is None or _collector_task.done()):
            _collector_task = asyncio.create_task(collector.run(runtime_module.runtime.kill_event))
        return collector.status()

    return router
