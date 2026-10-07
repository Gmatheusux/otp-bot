"""
modules/vision.py — "Os Olhos" do bot.

Responsabilidade única: capturar a tela do cliente (~30 FPS), recortar as
Regions of Interest (ROI) e converter pixels em dados estruturados.
Este módulo NÃO toma decisões: ele publica um `PerceptionSnapshot` imutável
que a Thread de Decisão consome via `VisionEngine.get_latest()`.

Regras aplicadas:
  * Captura com `mss` (DXGI/GDI via BitBlt, ~2-5 ms por frame) e localização
    opcional da janela com `win32gui`.
  * ZERO OCR. Vida/energia são lidas por Color Masking em HSV + projeção por
    coluna (percentual = largura preenchida / largura total da barra).
  * Todas as coordenadas e faixas de cor ficam no topo do arquivo para
    calibração.

Calibração rápida:
    python -m modules.vision --image print.png      # gera vision_debug.png
    python -m modules.vision --live --window "PokeTibia"   # FPS + leituras

Dependências: numpy, opencv-python, mss (pywin32 opcional, só no Windows).
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Final, Literal, Optional, Sequence

import cv2
import numpy as np
import numpy.typing as npt

try:  # mss é obrigatório apenas para captura ao vivo (o modo --image funciona sem ele)
    import mss
    import mss.tools  # noqa: F401
except ImportError:  # pragma: no cover
    mss = None  # type: ignore[assignment]

try:  # win32gui é opcional: sem ele, captura o monitor inteiro
    import win32gui  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    win32gui = None  # type: ignore[assignment]

logger = logging.getLogger("vision")

Frame = npt.NDArray[np.uint8]  # imagem BGR (H, W, 3)
Mask = npt.NDArray[np.uint8]   # máscara binária (H, W) com 0/255


# =============================================================================
# CALIBRAÇÃO — edite esta seção para a sua tela
# =============================================================================
# Coordenadas medidas no print de referência (área do cliente 1914x1009).
# Todas são relativas ao canto superior esquerdo da ÁREA DO CLIENTE do jogo
# (sem barra de título). Os painéis do OTClient não escalam com a janela: eles
# ficam ancorados nas bordas. Por isso cada ROI tem uma âncora: se a janela
# mudar de tamanho, ROIs ancoradas à direita/baixo se deslocam junto com a
# borda, sem precisar recalibrar.

REFERENCE_CLIENT_SIZE: Final[tuple[int, int]] = (1914, 1009)  # (largura, altura)

TARGET_FPS: Final[float] = 30.0

# Título (ou parte dele) da janela do cliente. None = captura o monitor 1 inteiro.
WINDOW_TITLE_HINT: Final[Optional[str]] = None

AnchorX = Literal["left", "right"]
AnchorY = Literal["top", "bottom"]


@dataclass(frozen=True, slots=True)
class ROI:
    """Retângulo de interesse em coordenadas do frame de referência."""

    name: str
    x: int
    y: int
    w: int
    h: int
    anchor_x: AnchorX = "left"
    anchor_y: AnchorY = "top"

    def resolve(self, frame_w: int, frame_h: int) -> tuple[int, int, int, int]:
        """Converte para (x0, y0, x1, y1) no frame atual, aplicando âncora e clamp."""
        ref_w, ref_h = REFERENCE_CLIENT_SIZE
        x = self.x + (frame_w - ref_w if self.anchor_x == "right" else 0)
        y = self.y + (frame_h - ref_h if self.anchor_y == "bottom" else 0)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(frame_w, x + self.w), min(frame_h, y + self.h)
        if x1 <= x0 or y1 <= y0:
            raise ROIError(f"ROI '{self.name}' fora do frame ({frame_w}x{frame_h}): {self}")
        return x0, y0, x1, y1


@dataclass(frozen=True, slots=True)
class HSVRange:
    """Faixa HSV no padrão OpenCV (H: 0-179, S/V: 0-255)."""

    lower: tuple[int, int, int]
    upper: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class BarSpec:
    """Barra horizontal que enche da esquerda para a direita.

    roi             : retângulo que cobre EXATAMENTE a trilha da barra (100%).
    colors          : faixas HSV que contam como "preenchido" (OR entre elas).
    column_coverage : fração mínima de pixels da coluna que precisa casar com a
                      cor para a coluna contar como cheia. Baixa (0.2) porque o
                      texto "5550 / 5550" desenhado por cima cobre parte da altura.
    max_gap_px      : buracos horizontais tolerados (dígitos do texto, serrilhado).
    """

    roi: ROI
    colors: tuple[HSVRange, ...]
    column_coverage: float = 0.20
    max_gap_px: int = 6


# --- Faixas de cor (medidas no print: vermelho ~(213,61,52) RGB, verde ~(6,248,8),
#     amarelo ~(255,202,11), azul ~(82,133,184); trilha vazia ~(56,71,71)/(24,26,29),
#     que tem saturação baixa e por isso é rejeitada pelo S mínimo). -------------
HSV_RED: Final[tuple[HSVRange, ...]] = (
    HSVRange((0, 110, 90), (10, 255, 255)),
    HSVRange((170, 110, 90), (179, 255, 255)),  # vermelho dá a volta no H
)
HSV_GREEN: Final[tuple[HSVRange, ...]] = (HSVRange((45, 120, 90), (80, 255, 255)),)
HSV_YELLOW: Final[tuple[HSVRange, ...]] = (HSVRange((18, 120, 120), (35, 255, 255)),)
HSV_BLUE: Final[tuple[HSVRange, ...]] = (HSVRange((95, 70, 110), (125, 255, 255)),)
HSV_CYAN: Final[tuple[HSVRange, ...]] = (HSVRange((80, 120, 120), (100, 255, 255)),)
# Battle list: a cor muda com a vida do bicho (verde → amarelo → laranja → vermelho).
# Qualquer cor saturada e clara conta como preenchido.
HSV_ANY_HP: Final[tuple[HSVRange, ...]] = (HSVRange((0, 110, 70), (179, 255, 255)),)

# --- Barras do Pokémon ativo ----------------------------------------------------
# Painel "Pokémon" (topo-esquerda): barra vermelha (vida) e azul (abaixo dela).
POKEMON_PANEL_HP_BAR: Final[BarSpec] = BarSpec(
    roi=ROI("pokemon_panel_hp", x=285, y=62, w=93, h=14), colors=HSV_RED
)
POKEMON_PANEL_BLUE_BAR: Final[BarSpec] = BarSpec(
    roi=ROI("pokemon_panel_blue", x=285, y=84, w=93, h=14), colors=HSV_BLUE
)
# Barras inferiores (acima dos atalhos F1..F14): verde = vida, amarela = energia.
BOTTOM_HP_BAR: Final[BarSpec] = BarSpec(
    roi=ROI("bottom_hp", x=464, y=819, w=196, h=8), colors=HSV_GREEN, column_coverage=0.4
)
BOTTOM_ENERGY_BAR: Final[BarSpec] = BarSpec(
    roi=ROI("bottom_energy", x=721, y=819, w=758, h=8), colors=HSV_YELLOW, column_coverage=0.4
)

# --- Battle List (painel "Batalha") ---------------------------------------------
# ROI cobre só a área das entradas (abaixo do cabeçalho com os filtros).
BATTLE_LIST_ROI: Final[ROI] = ROI("battle_list", x=198, y=505, w=174, h=172)
# Dentro da ROI acima (coordenadas relativas a ela):
BATTLE_BAR_X0: Final[int] = 34          # início da trilha da barra de vida (x=232 absoluto)
BATTLE_BAR_WIDTH: Final[int] = 128      # largura da barra cheia (232..359)
BATTLE_BAR_MIN_HEIGHT: Final[int] = 3   # barras com menos linhas que isso = ruído
BATTLE_BAR_MAX_HEIGHT: Final[int] = 9
BATTLE_ROW_MIN_PIXELS: Final[int] = 6   # pixels coloridos mínimos para a linha contar
BATTLE_ENTRY_PITCH: Final[int] = 30     # distância vertical entre entradas (informativo)

# --- Minimapa ---------------------------------------------------------------------
# Só a área do mapa (sem o título "Minimapa", coordenadas e botões de navegação).
MINIMAP_ROI: Final[ROI] = ROI("minimap", x=1531, y=50, w=374, h=222, anchor_x="right")


# =============================================================================
# Exceções
# =============================================================================
class VisionError(Exception):
    """Erro base do módulo de visão."""


class CaptureError(VisionError):
    """Falha ao capturar a tela."""


class WindowNotFoundError(VisionError):
    """A janela do cliente não foi encontrada."""


class ROIError(VisionError):
    """ROI inválida para o frame atual (fora dos limites)."""


# =============================================================================
# Estruturas de saída (imutáveis = seguras para ler de outra thread)
# =============================================================================
@dataclass(frozen=True, slots=True)
class BarReading:
    percent: float      # 0.0 – 100.0
    confidence: float   # 0.0 – 1.0 (fração das colunas preenchidas que casaram de fato com a cor)


@dataclass(frozen=True, slots=True)
class BattleEntry:
    slot: int                  # 0 = primeira entrada da lista
    hp_percent: float          # 0.0 – 100.0
    center: tuple[int, int]    # centro da barra em coordenadas do frame (para clicar/mirar)


@dataclass(frozen=True, slots=True)
class PerceptionSnapshot:
    frame_id: int
    timestamp: float                       # time.perf_counter() da captura
    capture_ms: float
    process_ms: float
    pokemon_hp: Optional[BarReading]       # barra verde inferior (fonte principal)
    pokemon_energy: Optional[BarReading]   # barra amarela inferior
    panel_hp: Optional[BarReading]         # barra vermelha do painel (redundância)
    panel_blue: Optional[BarReading]       # barra azul do painel
    battle_list: tuple[BattleEntry, ...]
    minimap: Optional[Frame] = field(default=None, repr=False)

    @property
    def monster_count(self) -> int:
        return len(self.battle_list)


# =============================================================================
# Leitura de pixels (funções puras, testáveis isoladamente)
# =============================================================================
def crop(frame: Frame, roi: ROI) -> Frame:
    """Recorta a ROI do frame (view sem cópia)."""
    x0, y0, x1, y1 = roi.resolve(frame.shape[1], frame.shape[0])
    return frame[y0:y1, x0:x1]


def color_mask(bgr: Frame, ranges: Sequence[HSVRange]) -> Mask:
    """Máscara binária com os pixels que caem em qualquer uma das faixas HSV."""
    if bgr.size == 0:
        raise ROIError("Recorte vazio ao gerar máscara de cor")
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(ranges[0].lower, np.uint8), np.array(ranges[0].upper, np.uint8))
    for r in ranges[1:]:
        mask |= cv2.inRange(hsv, np.array(r.lower, np.uint8), np.array(r.upper, np.uint8))
    return mask


def _close_gaps(filled: npt.NDArray[np.bool_], max_gap: int) -> npt.NDArray[np.bool_]:
    """Preenche buracos de até `max_gap` colunas entre colunas preenchidas (1D closing)."""
    if max_gap <= 0 or not filled.any():
        return filled
    out = filled.copy()
    idx = np.flatnonzero(filled)
    gaps = np.diff(idx)
    for start, gap in zip(idx[:-1], gaps):
        if 1 < gap <= max_gap + 1:
            out[start + 1 : start + gap] = True
    return out


def bar_fill_ratio(mask: Mask, column_coverage: float, max_gap_px: int) -> BarReading:
    """Calcula o preenchimento de uma barra a partir da sua máscara.

    1. Projeção vertical: cada coluna vira True se >= column_coverage dos seus
       pixels casaram com a cor (robusto a texto sobreposto).
    2. Fecha buracos pequenos (dígitos, serrilhado).
    3. A barra enche da esquerda: mede o run contínuo que começa na borda esquerda.
       Pixels soltos da mesma cor mais à direita (ex.: texto colorido) são ignorados.
    """
    h, w = mask.shape
    if w == 0 or h == 0:
        return BarReading(0.0, 0.0)
    coverage = (mask > 0).sum(axis=0) / float(h)
    raw = coverage >= column_coverage
    closed = _close_gaps(raw, max_gap_px)

    # O run precisa começar perto da borda esquerda; senão a barra está vazia.
    first = int(np.argmax(closed)) if closed.any() else w
    if first > max_gap_px:
        return BarReading(0.0, 1.0 if not raw.any() else 0.5)

    empties = np.flatnonzero(~closed[first:])
    end = first + (int(empties[0]) if empties.size else w - first)
    percent = 100.0 * end / w
    confidence = float(raw[:end].mean()) if end else 1.0
    return BarReading(round(min(100.0, max(0.0, percent)), 1), round(confidence, 3))


def read_bar(frame: Frame, spec: BarSpec) -> Optional[BarReading]:
    """Lê uma barra; retorna None (e loga) se a ROI estiver inválida."""
    try:
        roi_img = crop(frame, spec.roi)
        return bar_fill_ratio(color_mask(roi_img, spec.colors), spec.column_coverage, spec.max_gap_px)
    except (ROIError, cv2.error) as exc:
        logger.debug("Falha lendo barra %s: %s", spec.roi.name, exc)
        return None


def read_battle_list(frame: Frame) -> tuple[BattleEntry, ...]:
    """Detecta as entradas da Battle List pelas barras de vida (sem OCR).

    Varre só a faixa horizontal das barras (o sprite à esquerda é colorido e
    geraria falso positivo), agrupa linhas consecutivas com pixels coloridos em
    barras e mede o preenchimento de cada uma contra BATTLE_BAR_WIDTH.
    """
    try:
        x0, y0, x1, y1 = BATTLE_LIST_ROI.resolve(frame.shape[1], frame.shape[0])
    except ROIError as exc:
        logger.debug("Battle list: %s", exc)
        return ()

    bx0 = x0 + BATTLE_BAR_X0
    bx1 = min(x1, bx0 + BATTLE_BAR_WIDTH)
    strip = frame[y0:y1, bx0:bx1]
    if strip.size == 0:
        return ()
    mask = color_mask(strip, HSV_ANY_HP)
    row_hits = (mask > 0).sum(axis=1) >= BATTLE_ROW_MIN_PIXELS

    entries: list[BattleEntry] = []
    y = 0
    n_rows = row_hits.shape[0]
    while y < n_rows:
        if not row_hits[y]:
            y += 1
            continue
        start = y
        while y < n_rows and row_hits[y]:
            y += 1
        height = y - start
        if not (BATTLE_BAR_MIN_HEIGHT <= height <= BATTLE_BAR_MAX_HEIGHT):
            continue  # texto colorido / borda de seleção / ruído
        reading = bar_fill_ratio(mask[start:y], column_coverage=0.5, max_gap_px=2)
        center = (bx0 + BATTLE_BAR_WIDTH // 2, y0 + start + height // 2)
        entries.append(BattleEntry(slot=len(entries), hp_percent=reading.percent, center=center))
    return tuple(entries)


def read_minimap(frame: Frame) -> Optional[Frame]:
    """Retorna uma CÓPIA do recorte do minimapa (cópia = seguro entre threads)."""
    try:
        return crop(frame, MINIMAP_ROI).copy()
    except ROIError as exc:
        logger.debug("Minimapa: %s", exc)
        return None


# =============================================================================
# Captura de tela
# =============================================================================
@dataclass(frozen=True, slots=True)
class CaptureRegion:
    left: int
    top: int
    width: int
    height: int

    def as_mss(self) -> dict[str, int]:
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


def find_client_region(title_hint: str) -> CaptureRegion:
    """Localiza a área do cliente da janela cujo título contém `title_hint` (Windows)."""
    if win32gui is None:
        raise WindowNotFoundError("pywin32 não instalado; use WINDOW_TITLE_HINT=None ou instale pywin32")

    found: list[int] = []

    def _enum(hwnd: int, _: object) -> None:
        if win32gui.IsWindowVisible(hwnd) and title_hint.lower() in win32gui.GetWindowText(hwnd).lower():
            found.append(hwnd)

    win32gui.EnumWindows(_enum, None)
    if not found:
        raise WindowNotFoundError(f"Nenhuma janela visível contendo '{title_hint}'")

    hwnd = found[0]
    _, _, w, h = win32gui.GetClientRect(hwnd)
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    if w <= 0 or h <= 0:
        raise WindowNotFoundError(f"Janela '{title_hint}' minimizada (área do cliente {w}x{h})")
    return CaptureRegion(left, top, w, h)


class ScreenCapturer:
    """Wrapper fino sobre `mss`. NÃO compartilhe entre threads: mss guarda
    handles GDI por thread, então crie a instância dentro da thread que captura."""

    def __init__(self, title_hint: Optional[str] = WINDOW_TITLE_HINT) -> None:
        if mss is None:
            raise CaptureError("Pacote 'mss' não instalado (pip install mss)")
        self._title_hint = title_hint
        self._sct = mss.mss()
        self._region = self._locate()

    def _locate(self) -> CaptureRegion:
        if self._title_hint:
            return find_client_region(self._title_hint)
        mon = self._sct.monitors[1]
        return CaptureRegion(mon["left"], mon["top"], mon["width"], mon["height"])

    def refresh_region(self) -> None:
        """Re-localiza a janela (chame se o usuário mover/redimensionar o cliente)."""
        self._region = self._locate()

    def grab(self) -> Frame:
        """Captura um frame BGR contíguo."""
        try:
            raw = self._sct.grab(self._region.as_mss())
        except Exception as exc:  # mss lança ScreenShotError e erros de OS variados
            raise CaptureError(f"Falha no grab: {exc}") from exc
        # BGRA -> BGR. np.asarray é zero-copy; o slice + ascontiguousarray faz 1 cópia.
        return np.ascontiguousarray(np.asarray(raw, dtype=np.uint8)[:, :, :3])

    def close(self) -> None:
        try:
            self._sct.close()
        except Exception:  # pragma: no cover
            pass


# =============================================================================
# Processamento de um frame -> snapshot
# =============================================================================
def analyze_frame(frame: Frame, frame_id: int = 0, capture_ms: float = 0.0) -> PerceptionSnapshot:
    """Converte um frame BGR em PerceptionSnapshot. Função pura (sem estado)."""
    t0 = time.perf_counter()
    snapshot_ts = t0
    pokemon_hp = read_bar(frame, BOTTOM_HP_BAR)
    pokemon_energy = read_bar(frame, BOTTOM_ENERGY_BAR)
    panel_hp = read_bar(frame, POKEMON_PANEL_HP_BAR)
    panel_blue = read_bar(frame, POKEMON_PANEL_BLUE_BAR)
    battle = read_battle_list(frame)
    minimap = read_minimap(frame)
    return PerceptionSnapshot(
        frame_id=frame_id,
        timestamp=snapshot_ts,
        capture_ms=capture_ms,
        process_ms=(time.perf_counter() - t0) * 1000.0,
        pokemon_hp=pokemon_hp,
        pokemon_energy=pokemon_energy,
        panel_hp=panel_hp,
        panel_blue=panel_blue,
        battle_list=battle,
        minimap=minimap,
    )


# =============================================================================
# Thread de Percepção
# =============================================================================
class VisionEngine:
    """Loop de percepção em thread própria.

    Publica sempre o snapshot MAIS RECENTE (latest-value, sem fila): a Thread
    de Decisão nunca processa frames velhos acumulados.

        engine = VisionEngine(title_hint="PokeTibia")
        engine.start()
        snap = engine.get_latest()   # na thread de decisão
        engine.stop()

    Obs.: o pacing do loop usa sleep do tempo restante do frame. A regra de
    "delays randômicos" do DESIGN.md vale para INPUTS (mouse/teclado); a
    percepção não gera input e por isso pode ter ritmo fixo.
    """

    def __init__(
        self,
        title_hint: Optional[str] = WINDOW_TITLE_HINT,
        target_fps: float = TARGET_FPS,
        max_consecutive_errors: int = 30,
    ) -> None:
        if target_fps <= 0:
            raise ValueError("target_fps deve ser > 0")
        self._title_hint = title_hint
        self._frame_period = 1.0 / target_fps
        self._max_errors = max_consecutive_errors
        self._lock = threading.Lock()
        self._latest: Optional[PerceptionSnapshot] = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._fatal: Optional[BaseException] = None
        self._fps = 0.0

    # --- API pública ---------------------------------------------------------
    def start(self, wait_first_frame: float = 2.0) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._ready.clear()
        self._fatal = None
        self._thread = threading.Thread(target=self._run, name="PerceptionThread", daemon=True)
        self._thread.start()
        if wait_first_frame > 0 and not self._ready.wait(wait_first_frame):
            logger.warning("Nenhum frame após %.1fs", wait_first_frame)
        if self._fatal:
            raise VisionError("Percepção falhou ao iniciar") from self._fatal

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout)
            self._thread = None

    def get_latest(self) -> Optional[PerceptionSnapshot]:
        with self._lock:
            return self._latest

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    # --- Loop interno --------------------------------------------------------
    def _run(self) -> None:
        try:
            capturer = ScreenCapturer(self._title_hint)
        except VisionError as exc:
            logger.error("Não foi possível iniciar a captura: %s", exc)
            self._fatal = exc
            self._ready.set()
            return

        frame_id = 0
        errors = 0
        fps_window_start = time.perf_counter()
        fps_frames = 0
        try:
            while not self._stop.is_set():
                loop_start = time.perf_counter()
                try:
                    frame = capturer.grab()
                    capture_ms = (time.perf_counter() - loop_start) * 1000.0
                    snap = analyze_frame(frame, frame_id, capture_ms)
                    with self._lock:
                        self._latest = snap
                    self._ready.set()
                    frame_id += 1
                    fps_frames += 1
                    errors = 0
                except CaptureError as exc:
                    errors += 1
                    logger.warning("Captura falhou (%d/%d): %s", errors, self._max_errors, exc)
                    if errors % 5 == 0 and self._title_hint:
                        self._try_relocate(capturer)
                    if errors >= self._max_errors:
                        logger.error("Muitas falhas seguidas; encerrando percepção")
                        self._fatal = exc
                        break
                except Exception:  # nunca deixa a thread morrer em silêncio
                    errors += 1
                    logger.exception("Erro inesperado no frame %d", frame_id)
                    if errors >= self._max_errors:
                        break

                now = time.perf_counter()
                if now - fps_window_start >= 1.0:
                    self._fps = fps_frames / (now - fps_window_start)
                    fps_window_start, fps_frames = now, 0

                remaining = self._frame_period - (now - loop_start)
                if remaining > 0:
                    self._stop.wait(remaining)
        finally:
            capturer.close()

    @staticmethod
    def _try_relocate(capturer: ScreenCapturer) -> None:
        try:
            capturer.refresh_region()
            logger.info("Janela re-localizada")
        except WindowNotFoundError as exc:
            logger.warning("Re-localização falhou: %s", exc)


# =============================================================================
# Ferramentas de calibração
# =============================================================================
ALL_ROIS: Final[tuple[ROI, ...]] = (
    POKEMON_PANEL_HP_BAR.roi,
    POKEMON_PANEL_BLUE_BAR.roi,
    BOTTOM_HP_BAR.roi,
    BOTTOM_ENERGY_BAR.roi,
    BATTLE_LIST_ROI,
    MINIMAP_ROI,
)


def draw_debug_overlay(frame: Frame, snap: PerceptionSnapshot) -> Frame:
    """Desenha todas as ROIs e leituras sobre uma cópia do frame."""
    out = frame.copy()
    for roi in ALL_ROIS:
        try:
            x0, y0, x1, y1 = roi.resolve(frame.shape[1], frame.shape[0])
        except ROIError:
            continue
        cv2.rectangle(out, (x0, y0), (x1 - 1, y1 - 1), (255, 0, 255), 1)
        cv2.putText(out, roi.name, (x0, max(10, y0 - 3)), cv2.FONT_HERSHEY_PLAIN, 0.9, (255, 0, 255), 1)
    for e in snap.battle_list:
        cv2.circle(out, e.center, 3, (0, 255, 255), -1)
        cv2.putText(out, f"{e.hp_percent:.0f}%", (e.center[0] + 70, e.center[1] + 4),
                    cv2.FONT_HERSHEY_PLAIN, 0.9, (0, 255, 255), 1)
    return out


def _fmt(b: Optional[BarReading]) -> str:
    return "N/A" if b is None else f"{b.percent:5.1f}% (conf {b.confidence:.2f})"


def _print_snapshot(snap: PerceptionSnapshot) -> None:
    print(f"frame {snap.frame_id} | captura {snap.capture_ms:.1f} ms | processamento {snap.process_ms:.1f} ms")
    print(f"  HP (barra inferior)    : {_fmt(snap.pokemon_hp)}")
    print(f"  Energia (inferior)     : {_fmt(snap.pokemon_energy)}")
    print(f"  HP (painel vermelho)   : {_fmt(snap.panel_hp)}")
    print(f"  Azul (painel)          : {_fmt(snap.panel_blue)}")
    print(f"  Battle list ({snap.monster_count}): " + ", ".join(f"{e.hp_percent:.0f}%" for e in snap.battle_list))
    if snap.minimap is not None:
        print(f"  Minimapa               : {snap.minimap.shape[1]}x{snap.minimap.shape[0]} px")


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Calibração/teste do módulo de visão")
    parser.add_argument("--image", help="Analisa um print salvo e gera vision_debug.png")
    parser.add_argument("--live", action="store_true", help="Captura ao vivo e imprime leituras")
    parser.add_argument("--window", default=WINDOW_TITLE_HINT, help="Parte do título da janela do jogo")
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(threadName)s %(levelname)s %(message)s")

    if args.image:
        frame = cv2.imread(args.image, cv2.IMREAD_COLOR)
        if frame is None:
            print(f"Não foi possível abrir {args.image}", file=sys.stderr)
            return 1
        snap = analyze_frame(frame)
        _print_snapshot(snap)
        cv2.imwrite("vision_debug.png", draw_debug_overlay(frame, snap))
        print("Overlay salvo em vision_debug.png (retângulos magenta = ROIs)")
        return 0

    if args.live:
        engine = VisionEngine(title_hint=args.window)
        try:
            engine.start()
        except VisionError as exc:
            print(f"Erro: {exc}", file=sys.stderr)
            return 1
        end = time.perf_counter() + args.seconds
        try:
            while time.perf_counter() < end and engine.is_running:
                snap = engine.get_latest()
                if snap:
                    print(f"[{engine.fps:4.1f} FPS] ", end="")
                    _print_snapshot(snap)
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass
        finally:
            engine.stop()
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
