"""
tools/move_test.py — Teste ao vivo das coordenadas e do movimento (E08), pela pilha real do bot:
sensor de coordenadas -> WorldStore -> Mover -> fila -> trava -> backend de segundo plano (PostMessage).

  python tools/move_test.py read [--seconds 10]       só lê a coordenada (nenhuma tecla)
  python tools/move_test.py step n|ne|e|se|s|sw|w|nw [--count 1]
  python tools/move_test.py walk X Y [Z]               anda até X, Y (no andar atual se Z faltar)
  python tools/move_test.py walk --rel DX DY      anda DX, DY sqm a partir de onde está

`step` e `walk` mandam teclas ao jogo: precisam do bot como ADMINISTRADOR (D20) e param se a integridade não bater.
"""
import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from otpbot.actuation.action_queue import ActionQueue  # noqa: E402
from otpbot.actuation.input_lock import InputLock  # noqa: E402
from otpbot.actuation.movement import NAMES, Mover, Walk  # noqa: E402
from otpbot.interface.config_manager import ConfigManager  # noqa: E402
from otpbot.perception.capture import GameLocator  # noqa: E402
from otpbot.perception.coords import Coord, coords_monitor  # noqa: E402
from otpbot.platform import game_window  # noqa: E402
from otpbot.platform.input_backend import BackgroundBackend, check_integrity  # noqa: E402
from otpbot.state.world_state import WorldStore  # noqa: E402

from otpbot.app import paths  # noqa: E402

_LOG_DIR = paths.data_dir() / "e08"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(), logging.FileHandler(_LOG_DIR / "move_test.log", encoding="utf-8")])
log = logging.getLogger("move_test")
log.info(f"--- {' '.join(sys.argv[1:])}")


async def main(args) -> int:
    game_window.enable_dpi_awareness()
    locator = GameLocator()
    window = locator.window()
    if window is None:
        log.error("Janela do jogo não encontrada.")
        return 2
    calibration = ConfigManager().config.get("calibration", {})
    store, kill = WorldStore(), asyncio.Event()
    sensor = asyncio.create_task(coords_monitor(locator, store, lambda: calibration, kill, interval=0.05))

    lock = InputLock()
    queue = ActionQueue(lock, BackgroundBackend(locator.window))
    mover = Mover(queue, store, step_timeout=args.timeout)
    try:
        if args.cmd == "read":
            end, last = time.monotonic() + args.seconds, object()
            readings = bad = 0
            while time.monotonic() < end:
                await store.wait_new(["coords"], 1.0)
                r = store.latest("coords")
                readings += 1
                bad += r is None or r.value is None
                if r is not None and r.value != last:
                    last = r.value
                    log.info(f"coordenada: {r.value} (confiança {r.confidence:.2f})")
            log.info(f"{readings} leituras, {bad} sem coordenada")
            return 0

        integrity = check_integrity(window.hwnd)
        log.info(f"Integridade (D20): {integrity['message']}")
        if not integrity["ok"]:
            log.error("Sem a mesma integridade do jogo as teclas não chegam. Rode como administrador.")
            return 3
        lease = lock.grant("teste_e08", 3)
        start = await mover.position(2.0)
        log.info(f"posição inicial: {start}")
        if start is None:
            return 4

        if args.cmd == "step":
            d = NAMES[args.direction]
            for i in range(args.count):
                r = await mover.step(lease, d)
                log.info(f"passo {i + 1} {args.direction}: {r.status.value} {r.start} -> {r.end} ({r.seconds:.2f}s)")
            return 0

        if args.rel:
            target = Coord(start.x + args.x, start.y + args.y, start.z)
        else:
            target = Coord(args.x, args.y, args.z if args.z is not None else start.z)
        log.info(f"destino: {target}")
        r = await mover.walk_to(lease, target, max_distance=args.max_distance)
        for i, s in enumerate(r.steps, 1):
            log.info(f"  {i:3d} {s.direction}: {s.status.value} {s.start} -> {s.end} ({s.seconds:.2f}s)")
        log.info(f"resultado: {r.status.value} em {r.position} ({len(r.steps)} teclas) {r.reason}")
        return 0 if r.status is Walk.ARRIVED else 1
    finally:
        queue.release_all()
        kill.set()
        sensor.cancel()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeout", type=float, default=1.5, help="espera máxima por passo (s)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("read")
    p.add_argument("--seconds", type=float, default=10)
    p = sub.add_parser("step")
    p.add_argument("direction", choices=sorted(NAMES))
    p.add_argument("--count", type=int, default=1)
    p = sub.add_parser("walk")
    p.add_argument("x", type=int)
    p.add_argument("y", type=int)
    p.add_argument("z", type=int, nargs="?")
    p.add_argument("--max-distance", type=int, default=30)
    p.add_argument("--rel", action="store_true", help="X e Y relativos à posição atual (ex.: --rel 8 -6)")
    sys.exit(asyncio.run(main(ap.parse_args())))
