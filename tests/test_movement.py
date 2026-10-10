import asyncio

from otpbot.actuation.action_queue import ActionQueue
from otpbot.actuation.input_lock import InputLock
from otpbot.actuation.movement import KEYS, Mover, Step, Walk, neighbors
from otpbot.perception.coords import Coord
from otpbot.platform.input_backend import NUMPAD_OFF
from otpbot.state.world_state import WorldStore
from tests.helpers import direct, no_sleep

DELTA = {key: d for d, key in KEYS.items()}


class FakeGame:
    """
    Backend falso que é também o mapa: a tecla do numérico move o personagem (8 = y-1), paredes bloqueiam,
    `push` desvia o próximo passo. Um sensor falso publica `coords` a cada 5 ms, como o coords_monitor.
    """
    name = "fake"

    def __init__(self, lock, start, walls=(), push=None, unreadable=False, swallow=0):
        self.lock = lock
        self.swallow = swallow  # quantas teclas seguidas o jogo engole depois de cada passo (fim da animação)
        self._busy = 0
        self.pos = start
        self.walls = set(walls)
        self.push = push or {}
        self.unreadable = unreadable
        self.keys = []
        self.owners = []

    def key(self, name, hold=0.08):
        self.keys.append(name)
        self.owners.append(self.lock.current)
        if self._busy:
            self._busy -= 1
            return
        dx, dy = DELTA[name]
        nxt = Coord(self.pos.x + dx, self.pos.y + dy, self.pos.z)
        if nxt in self.walls:
            return
        self.pos = self.push.pop(nxt, nxt)
        self._busy = self.swallow

    def click(self, x, y, button="left"):
        raise AssertionError("o movimento não clica")

    def release_all(self):
        pass

    async def sensor(self, store):
        while True:
            store.publish("coords", None if self.unreadable else self.pos, confidence=0.0 if self.unreadable else 1.0)
            await asyncio.sleep(0.005)


def run(start, walk, walls=(), push=None, unreadable=False, revoke=False, timeout=0.05, swallow=0, repress=0.0):
    async def scenario():
        lock = InputLock()
        game = FakeGame(lock, start, walls, push, unreadable, swallow)
        queue = ActionQueue(lock, game, sleep=no_sleep, run_blocking=direct)
        store = WorldStore()
        sensor = asyncio.create_task(game.sensor(store))
        lease = lock.grant("hunt", 3)
        if revoke:
            lock.revoke_all()
        mover = Mover(queue, store, step_timeout=timeout, repress_s=repress, settle_s=0)
        try:
            result = await walk(mover, lease)
        finally:
            sensor.cancel()
        return result, game

    return asyncio.run(scenario())


def test_teclas_sao_as_do_numerico_com_num_lock_desligado():
    assert set(KEYS.values()) == set(NUMPAD_OFF)
    assert KEYS[(0, -1)] == "num8" and KEYS[(-1, -1)] == "num7" and KEYS[(1, 1)] == "num3"
    assert neighbors((0, -1)) == [(-1, -1), (1, -1)] and neighbors((1, 1)) == [(1, 0), (0, 1)]


def test_um_passo_em_cada_direcao_confirmado_pela_coordenada():
    for d, key in KEYS.items():
        r, game = run(Coord(100, 100, 7), lambda m, lease, d=d: m.step(lease, d))
        assert r.status is Step.OK, key
        assert r.end == Coord(100 + d[0], 100 + d[1], 7)
        assert game.keys == [key]


def test_passo_bloqueado():
    r, _ = run(Coord(100, 100, 7), lambda m, lease: m.step(lease, (1, 0)), walls={Coord(101, 100, 7)})
    assert r.status is Step.BLOCKED and r.end == Coord(100, 100, 7)


def test_passo_desviado():
    r, _ = run(Coord(100, 100, 7), lambda m, lease: m.step(lease, (1, 0)),
               push={Coord(101, 100, 7): Coord(103, 104, 7)})
    assert r.status is Step.OFF and r.end == Coord(103, 104, 7)


def test_sem_leitura_nao_aperta_nada():
    r, game = run(Coord(100, 100, 7), lambda m, lease: m.step(lease, (1, 0)), unreadable=True)
    assert r.status is Step.NO_READING and game.keys == []


def test_trava_revogada_nao_anda():
    r, game = run(Coord(100, 100, 7), lambda m, lease: m.step(lease, (1, 0)), revoke=True)
    assert r.status is Step.REFUSED and game.keys == []


def test_anda_de_a_ate_b_pela_diagonal_e_depois_reto():
    target = Coord(105, 97, 7)
    r, game = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, target))
    assert r.status is Walk.ARRIVED and r.position == target and game.pos == target
    assert game.keys == ["num9"] * 3 + ["num6"] * 2
    assert all(o is not None and o.owner == "hunt" for o in game.owners)


def test_contorna_parede_pela_vizinha():
    walls = {Coord(101, 100, 7)}
    r, game = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, Coord(103, 100, 7)), walls=walls)
    assert r.status is Walk.ARRIVED
    assert game.keys[:2] == ["num6", "num9"]  # direta bloqueada, depois a vizinha ↗


def test_cercado_fica_perdido():
    start = Coord(100, 100, 7)
    walls = {Coord(100 + dx, 100 + dy, 7) for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - {start}
    r, game = run(start, lambda m, lease: m.walk_to(lease, Coord(105, 100, 7), max_failures=2), walls=walls)
    assert r.status is Walk.LOST and r.position == start and "sem avançar" in r.reason
    assert len(game.keys) == 6  # 2 rodadas de 3 tentativas (direta + 2 vizinhas)


def test_destino_em_outro_andar_ou_longe_demais():
    r, game = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, Coord(101, 100, 6)))
    assert r.status is Walk.LOST and game.keys == []
    r, game = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, Coord(150, 100, 7), max_distance=30))
    assert r.status is Walk.LOST and game.keys == []


def test_empurrado_para_longe_fica_perdido():
    push = {Coord(101, 100, 7): Coord(160, 100, 7)}
    r, _ = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, Coord(105, 100, 7)), push=push)
    assert r.status is Walk.LOST and r.position == Coord(160, 100, 7)


def test_empurrado_perto_recalcula_e_chega():
    push = {Coord(101, 100, 7): Coord(101, 102, 7)}
    r, _ = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, Coord(104, 100, 7)), push=push)
    assert r.status is Walk.ARRIVED and r.steps[0].status is Step.OFF


def test_trava_revogada_no_caminho():
    r, _ = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, Coord(104, 100, 7)), revoke=True)
    assert r.status is Walk.REFUSED


def test_tecla_engolida_no_fim_da_animacao_e_apertada_de_novo():
    """E08 ao vivo: logo depois de um passo o jogo ignora a próxima tecla; sem repetir, o passo dava 'bloqueado'."""
    target = Coord(104, 100, 7)
    r, game = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, target), swallow=1, timeout=0.3,
                  repress=0.02)
    assert r.status is Walk.ARRIVED and r.position == target
    assert all(s.status is Step.OK for s in r.steps) and len(r.steps) == 4
    assert game.keys == ["num6"] + ["num6", "num6"] * 3  # do 2º passo em diante, a 1ª tecla é engolida


def test_sem_repetir_a_tecla_engolida_vira_bloqueio():
    r, _ = run(Coord(100, 100, 7), lambda m, lease: m.walk_to(lease, Coord(104, 100, 7)), swallow=1)
    assert r.steps[1].status is Step.BLOCKED
