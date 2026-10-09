"""
otpbot/platform/game_window.py — Acha a janela do cliente, em qual monitor ela está, o retângulo da área
cliente, se está em foco, e captura só essa área.

A janela é achada pela CLASSE (`PokeAllianceV3`): o título ("Service") e o processo ("AudioEngine.exe") são
disfarçados pelo cliente e não servem de chave [E01].

Captura: cópia da região da tela (mss). Funciona com o jogo fora de foco, desde que ele esteja visível no
monitor (sem janela por cima). PrintWindow devolve imagem preta neste cliente DirectX [E01].

Uso: python -m otpbot.platform.game_window [--save caminho.png]
"""
import ctypes
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

GAME_WINDOW_CLASS = "PokeAllianceV3"


@dataclass(frozen=True)
class Rect:
    """Retângulo em pixels físicos da área de trabalho virtual (pode ter x negativo no monitor à esquerda)."""
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def overlap_area(self, other: "Rect") -> int:
        w = min(self.right, other.right) - max(self.left, other.left)
        h = min(self.bottom, other.bottom) - max(self.top, other.top)
        return max(0, w) * max(0, h)

    def as_mss(self) -> Dict[str, int]:
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


@dataclass(frozen=True)
class Monitor:
    device: str
    rect: Rect
    primary: bool


@dataclass(frozen=True)
class GameWindow:
    hwnd: int
    client: Rect            # área cliente, em coordenadas da tela
    monitor: Optional[Monitor]
    foreground: bool
    minimized: bool

    @property
    def size(self) -> Tuple[int, int]:
        return self.client.width, self.client.height


def enable_dpi_awareness() -> None:
    """Coordenadas em pixels físicos em qualquer escala. Idempotente; chamar antes de qualquer janela."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass


def monitor_for(rect: Rect, monitors: Sequence[Monitor]) -> Optional[Monitor]:
    """Monitor com a maior área em comum com o retângulo (janela maximizada passa 8px da borda)."""
    best = max(monitors, key=lambda m: m.rect.overlap_area(rect), default=None)
    if best is None or best.rect.overlap_area(rect) == 0:
        return None
    return best


def list_monitors() -> List[Monitor]:
    import win32api
    out = []
    for handle, _, _ in win32api.EnumDisplayMonitors():
        info = win32api.GetMonitorInfo(handle)
        l, t, r, b = info["Monitor"]
        out.append(Monitor(info["Device"], Rect(l, t, r - l, b - t), bool(info["Flags"] & 1)))
    return out


def find_game_window(class_name: str = GAME_WINDOW_CLASS) -> Optional[int]:
    import win32gui
    hwnd = win32gui.FindWindow(class_name, None)
    return hwnd or None


def describe(hwnd: int, monitors: Optional[Sequence[Monitor]] = None) -> GameWindow:
    import win32gui
    _, _, w, h = win32gui.GetClientRect(hwnd)
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    client = Rect(left, top, w, h)
    return GameWindow(
        hwnd=hwnd,
        client=client,
        monitor=monitor_for(client, monitors if monitors is not None else list_monitors()),
        foreground=win32gui.GetForegroundWindow() == hwnd,
        minimized=bool(win32gui.IsIconic(hwnd)),
    )


def locate(class_name: str = GAME_WINDOW_CLASS) -> Optional[GameWindow]:
    """Janela do jogo agora, ou None se o cliente não estiver aberto."""
    enable_dpi_awareness()
    hwnd = find_game_window(class_name)
    return describe(hwnd) if hwnd else None


def _new_mss():
    import mss
    return (getattr(mss, "MSS", None) or mss.mss)()


def capture_client(window: GameWindow, sct=None) -> np.ndarray:
    """Print (BGR) só da área cliente do jogo. `sct` é uma instância de mss por thread; sem ela, cria uma."""
    if window.minimized or window.client.width <= 0 or window.client.height <= 0:
        raise RuntimeError("Janela do jogo minimizada: não há o que capturar")
    if sct is None:
        with _new_mss() as own:
            raw = own.grab(window.client.as_mss())
    else:
        raw = sct.grab(window.client.as_mss())
    return np.ascontiguousarray(np.array(raw)[:, :, :3])


def save_png(path: str, image: np.ndarray) -> None:
    """cv2.imwrite falha calado em caminhos com acento no Windows ("automação"); imencode + tofile não."""
    import cv2
    ok, buf = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError(f"não consegui codificar o PNG para {path}")
    buf.tofile(path)


def pick_window_profile(calibration: Dict, window: GameWindow):
    """Perfil de calibração escolhido pelo tamanho da área cliente (e não do monitor)."""
    from modules.screen_calibration import pick_profile
    w, h = window.size
    return pick_profile(calibration, w, h)


def _main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Mostra a janela do jogo e salva um print só dela.")
    parser.add_argument("--save", help="caminho do .png")
    args = parser.parse_args()

    window = locate()
    if window is None:
        print(f"Janela do jogo (classe {GAME_WINDOW_CLASS}) não encontrada")
        return
    mon = window.monitor
    print(f"hwnd={window.hwnd:#x} cliente={window.client} foco={window.foreground} minimizada={window.minimized}")
    print(f"monitor={mon.device if mon else '?'} {mon.rect if mon else ''} principal={mon.primary if mon else '?'}")
    if args.save:
        save_png(args.save, capture_client(window))
        print(f"print salvo em {args.save}")


if __name__ == "__main__":
    _main()
