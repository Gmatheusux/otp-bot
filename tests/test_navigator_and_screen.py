import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import humanizer as human
from core.navigator import Navigator
from modules.chat_analyzer import GM_PATTERN
from modules.sprite_library import is_primary, pick_monitor


class FakeMouse:
    def __init__(self):
        self.clicks = []

    def click(self, point, button="left"):
        self.clicks.append(point)


def test_play_duas_vezes_nao_roda_duas_rotas(tmp_path):
    route = tmp_path / "route.json"
    route.write_text(json.dumps([{"x": 10, "y": 10, "delay": 0.01}, {"x": 20, "y": 20, "delay": 0.01}]))
    previous = human.get()
    human.set_humanizer(human.Humanizer.instant())
    mouse = FakeMouse()
    nav = Navigator(mouse, route_file=str(route))

    async def scenario():
        first = asyncio.create_task(nav.play_route())
        await asyncio.sleep(0.005)
        nav.stop_playback()
        # Play de novo enquanto o loop antigo ainda dorme: o antigo tem que morrer
        second = asyncio.create_task(nav.play_route())
        await asyncio.sleep(0.2)
        nav.stop_playback()
        await asyncio.wait_for(asyncio.gather(first, second), timeout=2)

    try:
        asyncio.run(scenario())
    finally:
        human.set_humanizer(previous)
    # Com um loop só, as voltas alternam os pontos; dois loops repetiriam o mesmo ponto em sequência
    assert mouse.clicks
    assert all(a != b for a, b in zip(mouse.clicks, mouse.clicks[1:]))


MONITORS = [
    {"left": -1920, "top": 0, "width": 5360, "height": 1440},   # 0 = todos
    {"left": -1920, "top": 200, "width": 1920, "height": 1080},  # secundário listado primeiro
    {"left": 0, "top": 0, "width": 3440, "height": 1440},        # principal
]


def test_monitor_automatico_e_o_principal():
    assert pick_monitor(MONITORS, 0) is MONITORS[2]
    assert is_primary(pick_monitor(MONITORS, 0))


def test_monitor_escolhido_e_respeitado():
    assert pick_monitor(MONITORS, 1) is MONITORS[1]
    assert not is_primary(MONITORS[1])
    assert pick_monitor(MONITORS, 9) is MONITORS[2]  # índice inválido volta ao automático


def test_gm_so_com_palavra_inteira():
    assert GM_PATTERN.search("[gm] fulano: oi")
    assert GM_PATTERN.search("game master diz: tudo bem?")
    assert not GM_PATTERN.search("voce ganhou um segmento de mapa")
    assert not GM_PATTERN.search("leia o tutorial da cidade")
