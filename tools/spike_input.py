"""
tools/spike_input.py — Spike R1/D11 [E01]: o cliente aceita entrada com o jogo FORA DE FOCO?

Cada execução manda UMA entrada e salva um print antes e um depois (docs/e01/spike/), para o veredito
ser decidido vendo o jogo, não por suposição. Nada roda em loop.

Métodos:
  post        PostMessage para a janela do jogo (segundo plano: não rouba foco, não move o cursor)
  send        SendMessage (igual, mas síncrono)
  foreground  plano B: foca o jogo, SendInput por scan code, devolve o foco para a janela anterior

Exemplos:
  python tools/spike_input.py key num8 --method post
  python tools/spike_input.py key f5 --method post
  python tools/spike_input.py click 1700 600 --method post        (x, y na área CLIENTE do jogo)
  python tools/spike_input.py click 1700 600 --button right --method post
"""
import argparse
import ctypes
import os
import sys
import time
from ctypes import wintypes

import numpy as np
import win32api
import win32con
import win32gui

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from otpbot.platform.game_window import capture_client, locate, save_png  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'e01', 'spike')

# Teclado numérico com Num Lock DESLIGADO: o Windows entrega as teclas de navegação (VK_UP, VK_HOME...)
# com o scan code do numérico e SEM o bit "extended" (as setas dedicadas têm o bit). [Q43]
NUMPAD_OFF = {
    "num7": (win32con.VK_HOME, 0x47), "num8": (win32con.VK_UP, 0x48), "num9": (win32con.VK_PRIOR, 0x49),
    "num4": (win32con.VK_LEFT, 0x4B), "num6": (win32con.VK_RIGHT, 0x4D),
    "num1": (win32con.VK_END, 0x4F), "num2": (win32con.VK_DOWN, 0x50), "num3": (win32con.VK_NEXT, 0x51),
}
FKEYS = {f"f{i}": (win32con.VK_F1 + i - 1, sc) for i, sc in
         zip(range(1, 13), (0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44, 0x57, 0x58))}
KEYS = {**NUMPAD_OFF, **FKEYS}


def key_lparam(scan: int, up: bool, extended: bool = False) -> int:
    lp = 1 | (scan << 16) | (int(extended) << 24)
    if up:
        lp |= (1 << 30) | (1 << 31)
    return lp


def mouse_lparam(x: int, y: int) -> int:
    return (y << 16) | (x & 0xFFFF)


# --- plano B: SendInput -----------------------------------------------------------------------------
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _U(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _send_scan(scan: int, up: bool) -> None:
    flags = 0x0008 | (0x0002 if up else 0)  # KEYEVENTF_SCANCODE | KEYUP
    inp = INPUT(type=1, u=_U(ki=KEYBDINPUT(0, scan, flags, 0, 0)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _focus(hwnd: int) -> None:
    # Truque do ALT: o Windows só deixa trocar o foco se o processo "recebeu entrada" por último
    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32gui.SetForegroundWindow(hwnd)


# --- envio ------------------------------------------------------------------------------------------
def send_key(hwnd: int, name: str, method: str, hold: float) -> None:
    vk, scan = KEYS[name]
    if method == "foreground":
        before = win32gui.GetForegroundWindow()
        _focus(hwnd)
        time.sleep(0.15)
        _send_scan(scan, False); time.sleep(hold); _send_scan(scan, True)
        time.sleep(0.1)
        if before:
            _focus(before)
        return
    fn = win32gui.PostMessage if method == "post" else win32gui.SendMessage
    fn(hwnd, win32con.WM_KEYDOWN, vk, key_lparam(scan, False))
    time.sleep(hold)
    fn(hwnd, win32con.WM_KEYUP, vk, key_lparam(scan, True))


def send_click(hwnd: int, x: int, y: int, button: str, method: str) -> None:
    if method == "foreground":
        raise SystemExit("clique em primeiro plano não faz parte deste spike (move o seu cursor)")
    down, up, mk = ((win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON) if button == "left"
                    else (win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON))
    fn = win32gui.PostMessage if method == "post" else win32gui.SendMessage
    lp = mouse_lparam(x, y)
    fn(hwnd, win32con.WM_MOUSEMOVE, 0, lp)
    time.sleep(0.05)
    fn(hwnd, down, mk, lp)
    time.sleep(0.08)
    fn(hwnd, up, 0, lp)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="kind", required=True)
    k = sub.add_parser("key"); k.add_argument("name", choices=sorted(KEYS)); k.add_argument("--hold", type=float, default=0.08)
    c = sub.add_parser("click"); c.add_argument("x", type=int); c.add_argument("y", type=int)
    c.add_argument("--button", choices=("left", "right"), default="left")
    for p in (k, c):
        p.add_argument("--method", choices=("post", "send", "foreground"), default="post")
        p.add_argument("--wait", type=float, default=0.8, help="segundos até o print do depois")
    args = ap.parse_args()

    win = locate()
    if win is None:
        raise SystemExit("janela do jogo não encontrada")
    os.makedirs(OUT_DIR, exist_ok=True)
    tag = f"{time.strftime('%H%M%S')}_{args.kind}_{getattr(args, 'name', 'click')}_{args.method}"
    fg_before = win32gui.GetForegroundWindow()
    print(f"jogo hwnd={win.hwnd:#x} cliente={win.client} foco_antes={win.foreground}")

    antes = capture_client(win)
    if args.kind == "key":
        send_key(win.hwnd, args.name, args.method, args.hold)
    else:
        send_click(win.hwnd, args.x, args.y, args.button, args.method)
    time.sleep(args.wait)
    depois = capture_client(win)

    save_png(os.path.join(OUT_DIR, f"{tag}_antes.png"), antes)
    save_png(os.path.join(OUT_DIR, f"{tag}_depois.png"), depois)
    diff = float(np.abs(antes.astype(np.int16) - depois.astype(np.int16)).mean())
    print(f"enviado: {tag}  diferença média dos prints={diff:.2f}  "
          f"foco continuou fora do jogo={win32gui.GetForegroundWindow() != win.hwnd}  "
          f"foco igual ao de antes={win32gui.GetForegroundWindow() == fg_before}")


if __name__ == "__main__":
    main()
