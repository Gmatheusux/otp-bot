"""
otpbot/platform/input_backend.py — Único lugar do bot que manda tecla ou clique para o jogo (D11).

  BackgroundBackend  (padrão)  PostMessage para a janela do jogo: não rouba foco, não mexe o cursor.
                     Igual ao que o tools/spike_input.py provou na E01: lParam com scan code; numérico com
                     Num Lock desligado sem o bit "extended"; clique = WM_MOUSEMOVE + DOWN/UP em x,y do cliente.
  ForegroundBackend  (alternativa, config `input.backend = "foreground"`): foca o jogo, SendInput por scan code,
                     mouse com Bézier, devolve o foco.

Ninguém chama estas classes direto: tudo passa por `ActionQueue`, que confere a trava antes de cada envio
(teste em tests/test_input_guard.py). Coordenadas de clique são SEMPRE da área cliente do jogo.

D20: o jogo roda como administrador; um bot com integridade menor tem a entrada bloqueada pelo Windows (UIPI).
`check_integrity` compara as duas ao iniciar.
"""
import ctypes
import logging
import time
from ctypes import wintypes
from typing import Callable, List, Optional, Tuple

logger = logging.getLogger("InputBackend")

WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0100, 0x0101, 0x0104, 0x0105
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONDOWN, WM_RBUTTONUP = 0x0201, 0x0202, 0x0204, 0x0205
MK_LBUTTON, MK_RBUTTON = 0x0001, 0x0002

VK_SHIFT, VK_CONTROL, VK_MENU = 0x10, 0x11, 0x12
MODIFIERS = {"ctrl": (VK_CONTROL, 0x1D), "control": (VK_CONTROL, 0x1D), "shift": (VK_SHIFT, 0x2A),
             "alt": (VK_MENU, 0x38)}

# Numérico com Num Lock DESLIGADO [Q43, E01]: teclas de navegação com o scan do numérico, sem "extended"
NUMPAD_OFF = {
    "num7": (0x24, 0x47), "num8": (0x26, 0x48), "num9": (0x21, 0x49),
    "num4": (0x25, 0x4B), "num6": (0x27, 0x4D),
    "num1": (0x23, 0x4F), "num2": (0x28, 0x50), "num3": (0x22, 0x51),
}
_F_SCANS = (0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44, 0x57, 0x58,
            0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x76)
FKEYS = {f"f{i}": (0x70 + i - 1, sc) for i, sc in zip(range(1, 25), _F_SCANS)}
# Numérico com Num Lock LIGADO: o console grava "num 8" (nome da lib keyboard)
NUMPAD_ON = {f"num {d}": (0x60 + d, sc) for d, sc in
             zip(range(10), (0x52, 0x4F, 0x50, 0x51, 0x4B, 0x4C, 0x4D, 0x47, 0x48, 0x49))}
NAMED = {"space": (0x20, 0x39), "enter": (0x0D, 0x1C), "esc": (0x1B, 0x01), "escape": (0x1B, 0x01),
         "tab": (0x09, 0x0F), "backspace": (0x08, 0x0E)}
# Teclas dedicadas de navegação: mesmo scan do numérico, mas COM o bit "extended"
EXTENDED = {"up": (0x26, 0x48), "down": (0x28, 0x50), "left": (0x25, 0x4B), "right": (0x27, 0x4D),
            "home": (0x24, 0x47), "end": (0x23, 0x4F), "page up": (0x21, 0x49), "page down": (0x22, 0x51),
            "insert": (0x2D, 0x52), "delete": (0x2E, 0x53)}
KEYS = {**NUMPAD_OFF, **NUMPAD_ON, **FKEYS, **NAMED}

Stroke = Tuple[int, int, bool]  # (vk, scan, extended)


def _char_key(ch: str) -> Optional[Tuple[int, int]]:
    """Um caractere: VK e scan pelo layout de teclado do Windows."""
    if len(ch) != 1:
        return None
    try:
        user32 = ctypes.windll.user32
        vk = user32.VkKeyScanW(ord(ch)) & 0xFF
        if vk == 0xFF:
            return None
        return vk, user32.MapVirtualKeyW(vk, 0)
    except (AttributeError, OSError):
        if ch.isascii() and ch.isalnum():
            return ord(ch.upper()), 0
        return None


def parse_key(name: str) -> Tuple[List[Stroke], Stroke]:
    """'ctrl+f1' -> ([ctrl], f1). ValueError se o bot não sabe mandar a tecla."""
    parts = [p.strip().lower() for p in name.split("+") if p.strip()]
    if not parts:
        raise ValueError("tecla vazia")
    mods = []
    for p in parts[:-1]:
        if p not in MODIFIERS:
            raise ValueError(f"modificador desconhecido: '{p}'")
        mods.append((*MODIFIERS[p], False))
    last = parts[-1]
    if last in EXTENDED:
        return mods, (*EXTENDED[last], True)
    main = KEYS.get(last) or _char_key(last)
    if main is None:
        raise ValueError(f"tecla desconhecida: '{last}'")
    return mods, (*main, False)


def key_lparam(scan: int, up: bool, extended: bool = False, alt: bool = False) -> int:
    lp = 1 | (scan << 16) | (int(extended) << 24) | (int(alt) << 29)
    if up:
        lp |= (1 << 30) | (1 << 31)
    return lp


def mouse_lparam(x: int, y: int) -> int:
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


class InputBackend:
    name = "base"

    def key(self, name: str, hold: float = 0.08) -> None:
        raise NotImplementedError

    def click(self, x: int, y: int, button: str = "left") -> None:
        raise NotImplementedError

    def release_all(self) -> None:
        pass


class BackgroundBackend(InputBackend):
    """PostMessage para a janela do jogo. `window` devolve o GameWindow atual (ou None)."""
    name = "background"

    def __init__(self, window: Callable[[], object], post: Optional[Callable] = None, sleep=time.sleep):
        self._window = window
        self._post = post
        self._sleep = sleep
        self._held: List[Tuple[int, int, int]] = []  # (hwnd, vk, scan) apertadas e ainda não soltas

    def _hwnd(self) -> int:
        win = self._window()
        if win is None:
            raise RuntimeError("janela do jogo não encontrada")
        return win.hwnd

    def _send(self, hwnd: int, msg: int, wparam: int, lparam: int) -> None:
        post = self._post
        if post is None:
            import win32gui
            post = win32gui.PostMessage
        post(hwnd, msg, wparam, lparam)

    def key(self, name: str, hold: float = 0.08) -> None:
        mods, (vk, scan, ext) = parse_key(name)
        hwnd = self._hwnd()
        alt = any(m[0] == VK_MENU for m in mods)
        down, up = (WM_SYSKEYDOWN, WM_SYSKEYUP) if alt else (WM_KEYDOWN, WM_KEYUP)
        for mvk, msc, _ in mods:
            self._send(hwnd, down, mvk, key_lparam(msc, False, alt=alt))
            self._held.append((hwnd, mvk, msc))
        self._send(hwnd, down, vk, key_lparam(scan, False, ext, alt))
        self._held.append((hwnd, vk, scan))
        self._sleep(hold)
        self._send(hwnd, up, vk, key_lparam(scan, True, ext, alt))
        self._held.remove((hwnd, vk, scan))
        for mvk, msc, _ in reversed(mods):
            self._send(hwnd, up, mvk, key_lparam(msc, True, alt=alt))
            self._held.remove((hwnd, mvk, msc))

    def click(self, x: int, y: int, button: str = "left") -> None:
        hwnd = self._hwnd()
        down, up, mk = ((WM_LBUTTONDOWN, WM_LBUTTONUP, MK_LBUTTON) if button == "left"
                        else (WM_RBUTTONDOWN, WM_RBUTTONUP, MK_RBUTTON))
        lp = mouse_lparam(int(x), int(y))
        self._send(hwnd, WM_MOUSEMOVE, 0, lp)
        self._sleep(0.05)
        self._send(hwnd, down, mk, lp)
        self._sleep(0.08)
        self._send(hwnd, up, 0, lp)

    def release_all(self) -> None:
        for hwnd, vk, scan in reversed(self._held):
            try:
                self._send(hwnd, WM_KEYUP, vk, key_lparam(scan, True))
            except Exception as e:  # janela fechou: nada a soltar
                logger.debug(f"release_all: {e}")
        self._held.clear()


# --- primeiro plano (plano B) ----------------------------------------------------------------------------
class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _U(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _send_scan(scan: int, up: bool, extended: bool = False) -> None:
    flags = 0x0008 | (0x0002 if up else 0) | (0x0001 if extended else 0)  # SCANCODE | KEYUP | EXTENDEDKEY
    inp = _INPUT(type=1, u=_U(ki=_KEYBDINPUT(0, scan, flags, 0, 0)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))


class ForegroundBackend(InputBackend):
    """Foca o jogo, manda por SendInput (scan code) e mouse com Bézier, e devolve o foco a quem tinha."""
    name = "foreground"

    def __init__(self, window: Callable[[], object], mouse=None, sleep=time.sleep):
        self._window = window
        self._mouse = mouse
        self._sleep = sleep
        self._held: List[int] = []

    def _with_focus(self, action: Callable[[object], None]) -> None:
        import win32api
        import win32con
        import win32gui
        win = self._window()
        if win is None:
            raise RuntimeError("janela do jogo não encontrada")
        before = win32gui.GetForegroundWindow()

        def focus(hwnd):
            # Truque do ALT: o Windows só deixa trocar o foco se o processo "recebeu entrada" por último
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32gui.SetForegroundWindow(hwnd)

        if before != win.hwnd:
            focus(win.hwnd)
            self._sleep(0.15)
        try:
            action(win)
        finally:
            if before and before != win.hwnd:
                self._sleep(0.1)
                focus(before)

    def key(self, name: str, hold: float = 0.08) -> None:
        mods, (_, scan, ext) = parse_key(name)

        def press(_win):
            for _, msc, _ in mods:
                _send_scan(msc, False); self._held.append(msc)
            _send_scan(scan, False, ext); self._held.append(scan)
            self._sleep(hold)
            _send_scan(scan, True, ext); self._held.remove(scan)
            for _, msc, _ in reversed(mods):
                _send_scan(msc, True); self._held.remove(msc)

        self._with_focus(press)

    def click(self, x: int, y: int, button: str = "left") -> None:
        if self._mouse is None:
            from otpbot.actuation.mouse import MouseController
            self._mouse = MouseController()

        def press(win):
            self._mouse.click((win.client.left + int(x), win.client.top + int(y)), button)

        self._with_focus(press)

    def release_all(self) -> None:
        for scan in reversed(self._held):
            _send_scan(scan, True)
        self._held.clear()


BACKENDS = {"background": BackgroundBackend, "foreground": ForegroundBackend}
DEFAULT_BACKEND = "background"  # aprovado pelo spike da E01 (D11)


def make_backend(name: str, window: Callable[[], object]) -> InputBackend:
    cls = BACKENDS.get(name)
    if cls is None:
        logger.warning(f"Backend de entrada '{name}' desconhecido; usando '{DEFAULT_BACKEND}'.")
        cls = BACKENDS[DEFAULT_BACKEND]
    return cls(window)


# --- D20: integridade do processo ------------------------------------------------------------------------
INTEGRITY_NAMES = {0x0000: "não confiável", 0x1000: "baixa", 0x2000: "média", 0x3000: "alta", 0x4000: "sistema"}


def _process_integrity(handle) -> int:
    import win32security
    token = win32security.OpenProcessToken(handle, win32security.TOKEN_QUERY)
    sid, _ = win32security.GetTokenInformation(token, win32security.TokenIntegrityLevel)
    return sid.GetSubAuthority(sid.GetSubAuthorityCount() - 1)


def own_integrity() -> int:
    import win32api
    return _process_integrity(win32api.GetCurrentProcess())


def window_integrity(hwnd: int) -> int:
    import win32api
    import win32process
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    handle = win32api.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    try:
        return _process_integrity(handle)
    finally:
        win32api.CloseHandle(handle)


def integrity_name(level: Optional[int]) -> str:
    if level is None:
        return "desconhecida"
    return INTEGRITY_NAMES.get(level - level % 0x1000, hex(level))


def check_integrity(game_hwnd: Optional[int], own: Optional[Callable[[], int]] = None,
                    game: Optional[Callable[[int], int]] = None) -> dict:
    """{'ok', 'bot', 'game', 'message'}. ok=False quando o bot está abaixo do jogo (a entrada seria bloqueada)."""
    own = own or own_integrity
    game = game or window_integrity
    try:
        bot_level = own()
    except Exception as e:
        return {"ok": None, "bot": None, "game": None, "message": f"não consegui ler a integridade do bot: {e}"}
    if not game_hwnd:
        return {"ok": None, "bot": integrity_name(bot_level), "game": None,
                "message": "jogo não encontrado: integridade não conferida"}
    try:
        game_level = game(game_hwnd)
    except Exception as e:
        return {"ok": None, "bot": integrity_name(bot_level), "game": None,
                "message": f"não consegui ler a integridade do jogo: {e}"}
    ok = bot_level >= game_level
    msg = (f"bot com integridade {integrity_name(bot_level)}, jogo {integrity_name(game_level)}"
           + ("" if ok else ": o Windows vai bloquear as teclas e cliques. Abra o bot como administrador (D20)."))
    return {"ok": ok, "bot": integrity_name(bot_level), "game": integrity_name(game_level), "message": msg}
