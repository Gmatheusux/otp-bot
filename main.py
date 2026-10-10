import argparse
import asyncio
import logging
import logging.handlers
import os
import threading
import time
import keyboard

from otpbot.app import paths
from otpbot.app import runtime as runtime_module
from otpbot.app.runtime import BotRuntime
from otpbot.actuation.action_queue import ActionQueue, Click
from otpbot.actuation.input_lock import InputLock
from otpbot.interface.config_manager import ConfigManager
from otpbot.hunts.navigator import Navigator
from otpbot.brain.arbiter import Arbiter
from otpbot.brain.behaviors.base import BrainContext
from otpbot.brain.behaviors.companion import CompanionBehavior
from otpbot.brain.behaviors.hunt import HuntBehavior
from otpbot.brain.behaviors.safety import SafetyBehavior
from otpbot.brain.behaviors.survival import SurvivalBehavior
from otpbot.brain.heal_routine import PokemonHealRoutine
from otpbot.perception.capture import GameLocator
from otpbot.perception.sprites import SpriteLibrary
from otpbot.perception.bars import read_regions
from otpbot.perception.coords import coords_monitor
from otpbot.platform.input_backend import check_integrity
from otpbot.state.world_state import WorldStore

# Configuração de Logs
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("MainOrchestrator")


def setup_file_log() -> None:
    """Log também em %APPDATA%\\OTPBot\\logs (5 arquivos de 2 MB)."""
    handler = logging.handlers.RotatingFileHandler(paths.logs_dir() / "otpbot.log", maxBytes=2_000_000,
                                                   backupCount=4, encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger().addHandler(handler)

API_HOST = "127.0.0.1"  # Só a própria máquina acessa o console


class MockVision:
    def infer(self, img, conf_threshold=0.5): return []


def load_vision_engine(engine_cfg: dict, telemetry: dict):
    """Carrega o YOLO na GPU quando possível; sem modelo, sobe em modo mock para o console funcionar."""
    model_path = str(paths.resolve_data_path(engine_cfg.get("model_path", "models/otp_yolo.pt")))
    if not os.path.exists(model_path):
        logger.warning(f"Modelo YOLO não encontrado em '{model_path}'. Visão em modo MOCK (nenhuma detecção).")
        telemetry.update(device="mock", model=None)
        return MockVision()
    try:
        from otpbot.perception.vision_engine import VisionEngine
        vision_engine = VisionEngine(model_path)
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível carregar o modelo YOLO, usando mock. Erro: {e}")
        telemetry.update(device="mock", model=None)
        return MockVision()
    telemetry.update(device=vision_engine.device_name, model=os.path.basename(model_path))
    if not vision_engine.use_cuda:
        logger.warning("PyTorch sem CUDA: a inferência está rodando na CPU, não na GPU.")
    logger.info(f"Visão carregada: {model_path} em {vision_engine.device_name}")
    return vision_engine


def describe_window(window) -> str:
    if window is None:
        return None
    monitor = window.monitor.device if window.monitor else "?"
    return f"{window.client.width}x{window.client.height} em {monitor}"


async def perception_thread(vision_engine, locator: GameLocator, store: WorldStore, pause_event: asyncio.Event,
                            kill_event: asyncio.Event, config_mgr: ConfigManager, telemetry: dict) -> None:
    """
    Sensor YOLO: print da área cliente do jogo -> detecções (relativas ao cliente) publicadas no WorldState.
    Cada publicação de "detections" é um tick do árbitro. Respeita Pause e Kill.
    """
    logger.info("Thread de Percepção iniciada.")
    last_frame_at = None

    while not kill_event.is_set():
        await pause_event.wait()
        if kill_event.is_set():
            break

        try:
            engine_cfg = config_mgr.get_engine_config()
            fps_target = engine_cfg.get("fps_target", 30)
            frame_time = 1.0 / fps_target if fps_target > 0 else 0.033
            frame, window = await asyncio.to_thread(locator.capture)
            store.publish("window", window)
            telemetry["game_window"] = describe_window(window)
            if frame is None:
                store.publish("detections", None, confidence=0.0)  # sem jogo: ninguém age
                await asyncio.sleep(0.5)
                continue
            detections = await asyncio.to_thread(vision_engine.infer, frame, engine_cfg.get("confidence", 0.5))

            now = time.perf_counter()
            if last_frame_at is not None:
                # Média móvel para o FPS não ficar pulando no console
                instant_fps = 1.0 / max(now - last_frame_at, 1e-6)
                telemetry["fps"] = round(telemetry["fps"] * 0.9 + instant_fps * 0.1, 1)
            last_frame_at = now
            telemetry["detections"] = len(detections)

            store.publish("detections", detections)
            await asyncio.sleep(frame_time)
        except Exception as e:
            logger.error(f"Erro na thread de percepção: {e}")
            await asyncio.sleep(1)

    logger.info("Thread de Percepção encerrada (Kill Event).")


async def calibration_monitor(config_mgr: ConfigManager, locator: GameLocator, store: WorldStore,
                              kill_event: asyncio.Event, telemetry: dict) -> None:
    """
    Sensor das barras: HP, EXP, Pokébar e postura 2x por segundo, na área cliente do jogo. Só observa a tela,
    por isso roda mesmo pausado. Também confere a integridade do bot x jogo (D20) quando a janela aparece.
    """
    checked_hwnd = None
    while not kill_event.is_set():
        try:
            frame, window = await asyncio.to_thread(locator.capture)
            telemetry["game_window"] = describe_window(window)
            if window is not None and window.hwnd != checked_hwnd:
                checked_hwnd = window.hwnd
                integrity = await asyncio.to_thread(check_integrity, window.hwnd)
                telemetry["integrity"] = integrity
                (logger.info if integrity["ok"] else logger.warning)(f"Integridade (D20): {integrity['message']}")
            if frame is None:
                telemetry["readings"] = {}
                store.publish("bars", None, confidence=0.0)
                await asyncio.sleep(1)
                continue
            readings = await asyncio.to_thread(read_regions, frame, config_mgr.config.get("calibration", {}))
            telemetry["readings"] = readings
            store.publish("bars", readings)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Erro na leitura da calibração: {e}")
            await asyncio.sleep(2)


async def run_bot(port: int, ready: threading.Event) -> None:
    logger.info("Iniciando Bot Poketibia (Utility AI) - Inicialização do Core...")

    config_mgr = ConfigManager()
    engine_cfg = config_mgr.get_engine_config()

    # Percepção -> WorldState -> Árbitro -> Fila -> Trava -> Backend (ARQUITETURA §3)
    store = WorldStore()
    lock = InputLock()
    queue = ActionQueue(lock)
    locator = GameLocator()
    arbiter = None  # criado abaixo; o clique da rota usa o lease da Hunt

    async def route_click(screen_point):
        """O cavebot gravou pixels da tela; o backend quer pixels da área cliente."""
        window = locator.window()
        if window is None or arbiter is None:
            return
        x, y = screen_point[0] - window.client.left, screen_point[1] - window.client.top
        await queue.send(arbiter.lease_of("hunt"), Click(x, y))

    navigator = Navigator(route_click)

    # Registro Dinâmico de Cooldowns (os defaults do ConfigManager já cobrem o combo Try-Hard)
    queue.sync_cooldowns(config_mgr.get_cooldowns())
    logger.info("Cooldowns: " + ", ".join(f"{a}={s}s" for a, s in config_mgr.get_cooldowns().items()))

    # Preparação dos Eventos de Controle (o bot abre PAUSADO: dê play pelo console ou pela hotkey)
    loop = asyncio.get_running_loop()
    pause_event = asyncio.Event()
    kill_event = asyncio.Event()

    rt = BotRuntime(loop, pause_event, kill_event, config_mgr, navigator, SpriteLibrary())
    rt.locator, rt.queue = locator, queue
    runtime_module.runtime = rt

    heal_routine = PokemonHealRoutine(queue.press_current, queue.click_current, telemetry=rt.telemetry)
    rt.heal_routine = heal_routine
    ctx = BrainContext(queue=queue, store=store, telemetry=rt.telemetry, navigator=navigator,
                       heal_routine=heal_routine, kill=rt.stop)
    arbiter = Arbiter([SafetyBehavior(ctx), CompanionBehavior(), SurvivalBehavior(), HuntBehavior(ctx)],
                      store, lock, queue, lambda: config_mgr.config, pause_event, kill_event, rt.telemetry)
    rt.arbiter = arbiter

    # API do console + stream de logs no mesmo loop
    import uvicorn
    from otpbot.interface.api_server import app, WebSocketLogHandler
    logging.getLogger().addHandler(WebSocketLogHandler(loop))
    server = uvicorn.Server(uvicorn.Config(app, host=API_HOST, port=port, log_level="warning", timeout_graceful_shutdown=1))
    api_task = asyncio.create_task(server.serve())
    while not server.started and not api_task.done():
        await asyncio.sleep(0.05)
    if api_task.done():
        logger.error(f"Não foi possível abrir o console na porta {port} (já está em uso?).")
    ready.set()

    vision_engine = await asyncio.to_thread(load_vision_engine, engine_cfg, rt.telemetry)

    # Hotkeys globais (pause/kill/gravar/tocar rota), reaplicadas a cada mudança no console
    rt.config_changed()
    logger.info("Bot PAUSADO. Use o botão Play do console ou a hotkey de pause para começar.")

    # Sensor do chat (GM -> gm_alert no WorldState; a Segurança decide); liga/desliga na aba Segurança
    from otpbot.perception.chat import ChatAnalyzer, chat_monitor_thread
    chat_analyzer = ChatAnalyzer()

    # Loop Concorrente
    perception_task = asyncio.create_task(perception_thread(vision_engine, locator, store, pause_event, kill_event, config_mgr, rt.telemetry))
    arbiter_task = asyncio.create_task(arbiter.run())
    chat_task = asyncio.create_task(chat_monitor_thread(chat_analyzer, kill_event, pause_event, lambda: config_mgr.config,
                                                        locator.capture, lambda gm: store.publish("gm_alert", gm)))
    calibration_task = asyncio.create_task(calibration_monitor(config_mgr, locator, store, kill_event, rt.telemetry))
    # Sensor das coordenadas x, y, z (dígitos-modelo); o movimento confere cada passo por ele
    coords_task = asyncio.create_task(coords_monitor(locator, store, lambda: config_mgr.config.get("calibration", {}),
                                                     kill_event, rt.telemetry))

    # Aguarda o sinal de Kill ser processado e encerrar as threads
    await asyncio.gather(perception_task, arbiter_task, chat_task, calibration_task, coords_task)

    navigator.stop_playback()
    navigator.stop_recording()
    queue.release_all()
    keyboard.unhook_all()
    server.should_exit = True
    try:
        await asyncio.wait_for(api_task, timeout=5)
    except asyncio.TimeoutError:
        logger.warning("API do console não encerrou a tempo.")
    logger.info("Desligamento limpo concluído. Threads sincronizadas.")


def main() -> None:
    parser = argparse.ArgumentParser(description="OTP Bot - console local")
    parser.add_argument("--port", type=int, default=8000, help="Porta local da API/console (padrão 8000)")
    parser.add_argument("--no-window", action="store_true", help="Não abre a janela; use o link impresso no navegador")
    args = parser.parse_args()

    paths.prepare()
    setup_file_log()
    logger.info(f"Dados em {paths.data_dir()}")

    try:
        import webview
    except ImportError:
        webview = None
        if not args.no_window:
            logger.warning("pywebview não instalado: abrindo sem janela própria (pip install pywebview).")

    ready = threading.Event()

    def bot_thread():
        try:
            asyncio.run(run_bot(args.port, ready))
        except Exception:
            logger.exception("Falha fatal no bot.")
        finally:
            ready.set()
            if webview is not None:
                for window in list(webview.windows):
                    window.destroy()

    thread = threading.Thread(target=bot_thread, name="BotLoop", daemon=True)
    thread.start()
    ready.wait(timeout=30)

    from otpbot.interface.api_server import SESSION_TOKEN
    url = f"http://{API_HOST}:{args.port}/?token={SESSION_TOKEN}"

    try:
        if webview is not None and not args.no_window:
            webview.create_window("OTP Bot", url, width=1100, height=780, min_size=(420, 600), background_color="#0b0c0e")
            webview.start()
        else:
            logger.info(f"Console: {url}")
            logger.info(f"Console em modo dev (npm run dev): http://127.0.0.1:5173/?token={SESSION_TOKEN}")
            while thread.is_alive():
                thread.join(timeout=0.5)
    except KeyboardInterrupt:
        logger.info("Bot Poketibia encerrado via SIGINT (Ctrl+C).")
    finally:
        # Fechar a janela (ou Ctrl+C) desliga o bot
        if runtime_module.runtime is not None:
            runtime_module.runtime.stop()
        thread.join(timeout=10)


if __name__ == "__main__":
    main()
