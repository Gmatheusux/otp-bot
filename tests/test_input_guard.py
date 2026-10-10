"""
Aceite da E03: nenhuma tecla ou clique sai fora da trava de entrada.

1. Estático: no código do bot (otpbot/ e main.py) só `platform/input_backend.py` chama as APIs que mandam entrada
   ao Windows; `actuation/mouse.py` (Bézier) só é usado por ele. Um módulo novo que apertar tecla direto quebra
   este teste.
2. Dinâmico: em cenários reais da Hunt, da cura e do árbitro, todo envio que chegou ao backend tinha um dono
   válido da trava naquele instante; com a trava revogada nada chega.
"""
import ast
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import Brain, det  # noqa: E402
from otpbot.actuation.action_queue import Click, KeyPress, Wait  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BACKEND = Path("otpbot/platform/input_backend.py")
MOUSE = Path("otpbot/actuation/mouse.py")

# (módulo, função) que mandam entrada; "*" = qualquer função do módulo
FORBIDDEN = {
    "keyboard": {"send", "press", "release", "write", "press_and_release", "play"},
    "pyautogui": {"click", "doubleClick", "rightClick", "moveTo", "moveRel", "move", "dragTo", "drag", "press",
                  "keyDown", "keyUp", "typewrite", "write", "hotkey", "mouseDown", "mouseUp", "scroll"},
    "pydirectinput": {"*"},
    "win32gui": {"PostMessage", "SendMessage", "SendMessageTimeout", "SetForegroundWindow"},
    "win32api": {"PostMessage", "SendMessage", "keybd_event", "mouse_event", "SetCursorPos"},
}
FORBIDDEN_ATTRS = {"SendInput", "keybd_event", "mouse_event", "PostMessageW", "SendMessageW"}


def bot_sources():
    yield ROOT / "main.py"
    yield from (ROOT / "otpbot").rglob("*.py")


def violations(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                found.append(f"{node.attr} (linha {node.lineno})")
            if isinstance(node.value, ast.Name) and node.value.id in FORBIDDEN:
                names = FORBIDDEN[node.value.id]
                if "*" in names or node.attr in names:
                    found.append(f"{node.value.id}.{node.attr} (linha {node.lineno})")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            imported = [a.name for a in node.names]
            if any(m.split(".")[0] == "pydirectinput" for m in modules):
                found.append(f"import pydirectinput (linha {node.lineno})")
            if "MouseController" in imported or any(m == "otpbot.actuation.mouse" for m in modules):
                found.append(f"import do MouseController (linha {node.lineno})")
            if isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN:
                bad = [a.name for a in node.names if "*" in FORBIDDEN[node.module] or a.name in FORBIDDEN[node.module]]
                if bad:
                    found.append(f"from {node.module} import {', '.join(bad)} (linha {node.lineno})")
    return found


def test_so_o_backend_manda_entrada_ao_windows():
    problems = {}
    for path in bot_sources():
        rel = path.relative_to(ROOT)
        if rel == BACKEND:
            continue
        found = violations(path)
        if rel == MOUSE:  # o Bézier usa pydirectinput, mas só o backend de primeiro plano o importa
            found = [f for f in found if "pydirectinput" not in f]
        if found:
            problems[str(rel)] = found
    assert problems == {}


def test_o_detector_pega_uma_tecla_direta(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("import keyboard\nimport win32gui\nkeyboard.send('f1')\nwin32gui.PostMessage(1, 2, 3, 4)\n",
                   encoding="utf-8")
    assert len(violations(bad)) == 2


def all_sent_with_valid_owner(brain):
    return all(owner is not None for _, _, owner in brain.backend.events)


def test_cenarios_reais_so_enviam_com_dono_da_trava():
    async def scenario():
        results = []
        frames = [
            [det(0, 0.5, 0.5), det(1, 0.6, 0.5)],                                   # kite
            [det(0, 0.5, 0.5)] + [det(1, 0.5 + 0.01 * i, 0.5) for i in range(8)],   # cercado
            [det(0, 0.5, 0.5), det(2, 0.25, 0.5)],                                  # captura
        ]
        for detections in frames:
            brain = Brain()
            brain.config["features"]["stance"].update(auto=True, lure="defensive")
            brain.frame(detections, {"stance": "offensive"})
            await brain.tick_and_wait()
            results.append(brain)
        return results

    brains = asyncio.run(scenario())
    assert all(b.backend.events for b in brains)
    assert all(all_sent_with_valid_owner(b) for b in brains)


def test_trava_revogada_nada_chega_ao_backend():
    async def scenario():
        brain = Brain()
        lease = brain.lock.grant("hunt", 3)
        brain.lock.revoke_all()
        sent = [
            await brain.queue.send(lease, KeyPress("f1")),
            await brain.queue.send(lease, Click(1, 1)),
            await brain.queue.send(lease, KeyPress("f4"), Wait(0.1), Click(2, 2)),
            await brain.queue.press_current("f1"),          # sem lease na task
            await brain.queue.click_current((5, 5)),
        ]
        brain.frame([det(0, 0.5, 0.5), det(1, 0.6, 0.5)])
        brain.pause.clear()
        await brain.arbiter.halt()                          # pausado: o árbitro não dá a trava a ninguém
        return brain, sent

    brain, sent = asyncio.run(scenario())
    assert sent == [False] * 5
    assert brain.backend.events == []
