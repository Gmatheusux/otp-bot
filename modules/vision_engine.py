"""
modules/vision_engine.py — Inferência GPU para detectores YOLO serializados em TensorRT.

Responsabilidade única: receber um frame numpy (H, W, 3) BGR uint8, executar
o grafo na GPU via um engine `.engine` (TensorRT) e devolver uma matriz densa
de detecções pós-NMS, normalizadas (0.0 - 1.0) em relação ao frame de entrada:

    [x_center, y_center, width, height, confidence, class_id]

Zero-Context Abstraction: este módulo não sabe o que está detectando. Não há
nomes de classes, ROIs ou regras de negócio — apenas tensores, thresholds e
geometria. A interpretação semântica das detecções é responsabilidade de quem
chama `process_frame()`.

Dependências: numpy, opencv-python, tensorrt (>=8.5, API `execute_async_v3`),
pycuda. Requer um engine com exatamente 1 binding de entrada (NCHW, shape
estática) e 1 binding de saída no layout padrão de export do YOLOv8
((1, 4+nc, N) ou (1, N, 4+nc)).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import numpy.typing as npt

try:
    import tensorrt as trt
except ImportError as exc:  # pragma: no cover
    raise ImportError("Pacote 'tensorrt' não instalado") from exc

try:
    import pycuda.autoinit  # noqa: F401 — inicializa o contexto CUDA da thread atual
    import pycuda.driver as cuda
except ImportError as exc:  # pragma: no cover
    raise ImportError("Pacote 'pycuda' não instalado") from exc

logger = logging.getLogger("vision_engine")

Frame = npt.NDArray[np.uint8]            # (H, W, 3) BGR
Detections = npt.NDArray[np.float32]     # (N, 6) = [cx, cy, w, h, conf, class_id], normalizado


class VisionEngineError(Exception):
    """Erro base do motor de inferência."""


class EngineLoadError(VisionEngineError):
    """Falha ao carregar ou desserializar o engine TensorRT."""


class InferenceError(VisionEngineError):
    """Falha durante a execução do grafo ou no shape da saída."""


@dataclass(slots=True)
class _Binding:
    """Par de buffers (host pinned + device) para um tensor de entrada/saída."""

    name: str
    shape: tuple[int, ...]
    dtype: np.dtype
    host: np.ndarray
    device: "cuda.DeviceAllocation"
    is_input: bool


class VisionEngine:
    """Carrega um engine `.engine` (YOLOv8/TensorRT) e expõe `process_frame()`.

        engine = VisionEngine("model.engine", num_classes=80)
        dets = engine.process_frame(frame_bgr)   # (N, 6) float32 normalizado
        engine.close()

    A classe é stateful (contexto de execução CUDA + buffers alocados uma
    única vez) e não é thread-safe: use uma instância por thread/processo
    que fizer inferência.
    """

    def __init__(
        self,
        engine_path: str | Path,
        num_classes: int,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        max_detections: int = 300,
    ) -> None:
        if num_classes <= 0:
            raise ValueError("num_classes deve ser > 0")
        if not (0.0 < conf_threshold < 1.0):
            raise ValueError("conf_threshold deve estar em (0, 1)")
        if not (0.0 < iou_threshold < 1.0):
            raise ValueError("iou_threshold deve estar em (0, 1)")

        self._num_classes = num_classes
        self._conf_threshold = conf_threshold
        self._iou_threshold = iou_threshold
        self._max_detections = max_detections

        self._trt_logger = trt.Logger(trt.Logger.ERROR)
        self._runtime = trt.Runtime(self._trt_logger)
        self._engine = self._load_engine(Path(engine_path))
        self._context = self._engine.create_execution_context()
        if self._context is None:
            raise EngineLoadError("Falha ao criar o execution context do engine")
        self._stream = cuda.Stream()

        self._input, self._output = self._allocate_bindings()
        _, _, self._input_h, self._input_w = self._input.shape

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def _load_engine(self, path: Path) -> "trt.ICudaEngine":
        if not path.is_file():
            raise EngineLoadError(f"Engine não encontrado: {path}")
        engine = self._runtime.deserialize_cuda_engine(path.read_bytes())
        if engine is None:
            raise EngineLoadError(f"Falha ao desserializar engine: {path}")
        return engine

    def _allocate_bindings(self) -> tuple[_Binding, _Binding]:
        input_binding: Optional[_Binding] = None
        output_binding: Optional[_Binding] = None

        for name in self._engine:
            shape = tuple(self._context.get_tensor_shape(name))
            if any(dim < 0 for dim in shape):
                raise EngineLoadError(
                    f"Binding '{name}' tem shape dinâmica {shape}; "
                    "VisionEngine requer um engine com shape de entrada estática"
                )
            dtype = trt.nptype(self._engine.get_tensor_dtype(name))
            host_mem = cuda.pagelocked_empty(int(np.prod(shape)), dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            self._context.set_tensor_address(name, int(device_mem))

            is_input = self._engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT
            binding = _Binding(name, shape, dtype, host_mem, device_mem, is_input)
            if is_input:
                input_binding = binding
            else:
                output_binding = binding

        if input_binding is None or output_binding is None:
            raise EngineLoadError("Engine precisa de exatamente 1 binding de entrada e 1 de saída")
        return input_binding, output_binding

    def close(self) -> None:
        for binding in (self._input, self._output):
            try:
                binding.device.free()
            except Exception:  # pragma: no cover
                pass

    def __enter__(self) -> "VisionEngine":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Pipeline público
    # ------------------------------------------------------------------
    def process_frame(self, frame: Frame) -> Detections:
        """Executa a inferência completa de um frame e devolve as detecções.

        Fluxo: letterbox -> upload GPU -> execução -> download -> NMS ->
        desnormalização das coordenadas do letterbox para o frame original.
        """
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(f"Frame inválido, esperado (H, W, 3), recebido {frame.shape}")

        chw, scale, pad_x, pad_y = self._preprocess(frame)
        np.copyto(self._input.host.reshape(self._input.shape), chw[np.newaxis, ...])

        cuda.memcpy_htod_async(self._input.device, self._input.host, self._stream)
        if not self._context.execute_async_v3(self._stream.handle):
            raise InferenceError("execute_async_v3 retornou falha")
        cuda.memcpy_dtoh_async(self._output.host, self._output.device, self._stream)
        self._stream.synchronize()

        raw = self._output.host.reshape(self._output.shape)
        frame_h, frame_w = frame.shape[:2]
        return self._post_process(raw, scale, pad_x, pad_y, frame_w, frame_h)

    # ------------------------------------------------------------------
    # Pré-processamento
    # ------------------------------------------------------------------
    def _preprocess(self, frame: Frame) -> tuple[np.ndarray, float, int, int]:
        """Letterbox (resize com aspect ratio preservado + padding cinza) e
        normalização para CHW float32 [0, 1]. Retorna também o fator de
        escala e o padding aplicado, necessários para desfazer a transformação
        em `_post_process`."""
        h, w = frame.shape[:2]
        scale = min(self._input_w / w, self._input_h / h)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))

        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((self._input_h, self._input_w, 3), 114, dtype=np.uint8)
        pad_x, pad_y = (self._input_w - new_w) // 2, (self._input_h - new_h) // 2
        canvas[pad_y : pad_y + new_h, pad_x : pad_x + new_w] = resized

        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB).astype(np.float32) * (1.0 / 255.0)
        chw = np.ascontiguousarray(np.transpose(rgb, (2, 0, 1)))
        return chw, scale, pad_x, pad_y

    # ------------------------------------------------------------------
    # Pós-processamento (estritamente matemático)
    # ------------------------------------------------------------------
    def _post_process(
        self,
        raw: np.ndarray,
        scale: float,
        pad_x: int,
        pad_y: int,
        frame_w: int,
        frame_h: int,
    ) -> Detections:
        predictions = self._to_prediction_matrix(raw)
        if predictions.size == 0:
            return np.empty((0, 6), dtype=np.float32)

        boxes_xywh = predictions[:, :4].copy()
        class_scores = predictions[:, 4 : 4 + self._num_classes]
        class_ids = np.argmax(class_scores, axis=1)
        confidences = class_scores[np.arange(class_scores.shape[0]), class_ids]

        keep = confidences >= self._conf_threshold
        if not np.any(keep):
            return np.empty((0, 6), dtype=np.float32)
        boxes_xywh = boxes_xywh[keep]
        confidences = confidences[keep]
        class_ids = class_ids[keep].astype(np.float32)

        boxes_xyxy = self._xywh_to_xyxy(boxes_xywh)
        order = self._nms(boxes_xyxy, confidences, class_ids, self._iou_threshold)
        order = order[: self._max_detections]

        boxes_xywh = boxes_xywh[order]
        confidences = confidences[order]
        class_ids = class_ids[order]

        # Desfaz o letterbox (padding + escala) e normaliza pelo frame original.
        boxes_xywh[:, 0] = (boxes_xywh[:, 0] - pad_x) / scale / frame_w
        boxes_xywh[:, 1] = (boxes_xywh[:, 1] - pad_y) / scale / frame_h
        boxes_xywh[:, 2] = boxes_xywh[:, 2] / scale / frame_w
        boxes_xywh[:, 3] = boxes_xywh[:, 3] / scale / frame_h
        np.clip(boxes_xywh, 0.0, 1.0, out=boxes_xywh)

        return np.concatenate(
            [boxes_xywh, confidences[:, None], class_ids[:, None]], axis=1
        ).astype(np.float32)

    def _to_prediction_matrix(self, raw: np.ndarray) -> np.ndarray:
        """Normaliza a saída do engine para (N, 4+num_classes).

        O export padrão do YOLOv8 pode sair transposto ((1, 4+nc, N), o mais
        comum) ou não ((1, N, 4+nc)); detecta o layout pelo eixo cujo tamanho
        bate com `4 + num_classes`.
        """
        arr = np.squeeze(raw, axis=0) if raw.shape[0] == 1 else raw
        expected = 4 + self._num_classes
        if arr.shape[0] == expected:
            arr = arr.T
        elif arr.shape[-1] != expected:
            raise InferenceError(
                f"Saída do engine incompatível com num_classes={self._num_classes}: shape={raw.shape}"
            )
        return np.ascontiguousarray(arr, dtype=np.float32)

    @staticmethod
    def _xywh_to_xyxy(boxes: np.ndarray) -> np.ndarray:
        xyxy = np.empty_like(boxes)
        half_w, half_h = boxes[:, 2] * 0.5, boxes[:, 3] * 0.5
        xyxy[:, 0] = boxes[:, 0] - half_w
        xyxy[:, 1] = boxes[:, 1] - half_h
        xyxy[:, 2] = boxes[:, 0] + half_w
        xyxy[:, 3] = boxes[:, 1] + half_h
        return xyxy

    @staticmethod
    def _nms(
        boxes_xyxy: np.ndarray,
        scores: np.ndarray,
        class_ids: np.ndarray,
        iou_threshold: float,
    ) -> npt.NDArray[np.int64]:
        """NMS greedy em numpy, independente por classe.

        Usa o truque de `torchvision.ops.batched_nms`: desloca cada caixa por
        `class_id * (maior_coordenada + 1)` antes de calcular IoU, separando
        espacialmente classes diferentes sem precisar de um loop por classe.
        """
        if boxes_xyxy.shape[0] == 0:
            return np.empty((0,), dtype=np.int64)

        offset = class_ids * (boxes_xyxy.max() + 1.0)
        shifted = boxes_xyxy + offset[:, None]

        x1, y1, x2, y2 = shifted[:, 0], shifted[:, 1], shifted[:, 2], shifted[:, 3]
        areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
        order = scores.argsort()[::-1]

        keep: list[int] = []
        while order.size > 0:
            i = order[0]
            keep.append(int(i))
            rest = order[1:]
            xx1 = np.maximum(x1[i], x1[rest])
            yy1 = np.maximum(y1[i], y1[rest])
            xx2 = np.minimum(x2[i], x2[rest])
            yy2 = np.minimum(y2[i], y2[rest])
            inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
            union = areas[i] + areas[rest] - inter
            iou = np.where(union > 0, inter / union, 0.0)
            order = rest[iou <= iou_threshold]

        return np.array(keep, dtype=np.int64)
