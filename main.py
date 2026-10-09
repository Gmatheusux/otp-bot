import argparse
import asyncio
import logging
import os
import threading
import time
import keyboard

from core import runtime as runtime_module
from core.runtime import BotRuntime
from core.action_orchestrator import UtilityOrchestrator
from core.mouse_controller import MouseController
from core.config_manager import ConfigManager
from core.navigator import Navigator
from core.decision_thread import decision_thread, press_key_action, click_action
from core.heal_routine import PokemonHealRoutine
from modules.sprite_library import SpriteLibrary, capture_screen
from modules.screen_calibration import read_regions

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MainOrchestrator")

API_HOST = "127.0.0.1"  # Só a própria máquina acessa o console


class MockVision:
    def process_frame(self, **kwargs): return []


def load_vision_engine(engine_cfg: dict, telemetry: dict):
    """Carrega o YOLO na GPU quando possível; sem modelo, sobe em modo mock para o console funcionar."""
    model_path = engine_cfg.get("model_path", "models/otp_yolo.pt")
    if not os.path.exists(model_path):
        logger.warning(f"Modelo YOLO não encontrado em '{model_path}'. Visão em modo MOCK (nenhuma detecção).")
        telemetry.update(device="mock", model=None)
        return MockVision()
    try:
        from modules.vision_engine import VisionEngine
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


async def perception_thread(vision_engine, state_queue: asyncio.Queue, pause_event: asyncio.Event, kill_event: asyncio.Event, config_mgr: ConfigManager, telemetry: dict) -> None:
    """
    Thread de Percepção: Lê o buffer de tela e envia o estado da inferência.
    Respeita eventos de Pause e Kill de forma limpa.
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
            detections = await asyncio.to_thread(vision_engine.process_frame, conf_threshold=engine_cfg.get("confidence", 0.5))

            now = time.perf_counter()
            if last_frame_at is not None:
                # Média móvel para o FPS não ficar pulando no console
                instant_fps = 1.0 / max(now - last_frame_at, 1e-6)
                telemetry["fps"] = round(telemetry["fps"] * 0.9 + instant_fps * 0.1, 1)
            last_frame_at = now
            telemetry["detections"] = len(detections)

            if state_queue.full():
                try:
                    state_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            await state_queue.put(detections)
            await asyncio.sleep(frame_time)
        except Exception as e:
            logger.error(f"Erro na thread de percepção: {e}")
            await asyncio.sleep(1)

    logger.info("Thread de Percepção encerrada (Kill Event).")


async def calibration_monitor(config_mgr: ConfigManager, kill_event: asyncio.Event, telemetry: dict) -> None:
    """Lê HP, EXP e o time 2x por segundo. Só observa a tela, por isso roda mesmo pausado."""
    while not kill_event.is_set():
        try:
            frame = await asyncio.to_thread(capture_screen)
            telemetry["readings"] = await asyncio.to_thread(read_regions, frame, config_mgr.config.get("calibration", {}))
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Erro na leitura da calibração: {e}")
            await asyncio.sleep(2)


async def run_bot(port: int, ready: threading.Event) -> None:
    logger.info("Iniciando Bot Poketibia (Utility AI) - Inicialização do Core...")

    config_mgr = ConfigManager()
    engine_cfg = config_mgr.get_engine_config()

    orchestrator = UtilityOrchestrator()
    mouse_controller = MouseController()
    navigator = Navigator(mouse_controller)

    # Registro Dinâmico de Cooldowns (os defaults do ConfigManager já cobrem o combo Try-Hard)
    orchestrator.sync_cooldowns(config_mgr.get_cooldowns())
    logger.info("Cooldowns: " + ", ".join(f"{a}={s}s" for a, s in config_mgr.get_cooldowns().items()))

    # Preparação dos Eventos de Controle (o bot abre PAUSADO: dê play pelo console ou pela hotkey)
    loop = asyncio.get_running_loop()
    pause_event = asyncio.Event()
    kill_event = asyncio.Event()

    rt = BotRuntime(loop, pause_event, kill_event, config_mgr, navigator, SpriteLibrary())
    runtime_module.runtime = rt

    # API do console + stream de logs no mesmo loop
    import uvicorn
    from core.api_server import app, WebSocketLogHandler
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

    # 4. Fila de Comunicação Inter-Thread
    state_queue = asyncio.Queue(maxsize=1)

    # Setup Chat Analyzer (Kill Event); ROI e liga/desliga vêm da aba Segurança
    from modules.chat_analyzer import ChatAnalyzer, chat_monitor_thread
    chat_analyzer = ChatAnalyzer(roi=tuple(config_mgr.get_features()["safety"]["chat_roi"]))

    # 5. Loop Concorrente
    perception_task = asyncio.create_task(perception_thread(vision_engine, state_queue, pause_event, kill_event, config_mgr, rt.telemetry))
    heal_routine = PokemonHealRoutine(press_key_action, lambda point: click_action(mouse_controller, point), telemetry=rt.telemetry)
    rt.heal_routine = heal_routine
    decision_task = asyncio.create_task(decision_thread(orchestrator, navigator, mouse_controller, lambda: config_mgr.config, state_queue, pause_event, kill_event, rt.telemetry, heal_routine))
    chat_task = asyncio.create_task(chat_monitor_thread(chat_analyzer, kill_event, pause_event, lambda: config_mgr.get_features().get("safety", {})))

    calibration_task = asyncio.create_task(calibration_monitor(config_mgr, kill_event, rt.telemetry))

    # Aguarda o sinal de Kill ser processado e encerrar as threads
    await asyncio.gather(perception_task, decision_task, chat_task, calibration_task)

    navigator.stop_playback()
    navigator.stop_recording()
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

    from core.api_server import SESSION_TOKEN
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
