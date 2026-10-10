import json
import time
import os
import threading
import logging
import asyncio
import win32api
import pyautogui
from typing import Awaitable, Callable, List, Dict, Optional
from otpbot.app import paths

logger = logging.getLogger("Navigator")

class Navigator:
    """
    Módulo Core de Navegação (Record & Playback) para Cavebot. Sai na E09.
    Grava cliques reais do usuário no minimapa (pixels da TELA) e os reproduz com `click(ponto_da_tela)`,
    que passa pela fila de ações e pela trava de entrada (E03).
    """
    def __init__(self, click: Callable[[tuple], Awaitable], route_file: Optional[str] = None):
        self.click = click
        self.route_file = route_file or str(paths.route_file())
        self.is_recording = False
        self.is_playing = False
        self.route_points: List[Dict[str, float]] = []
        self.last_click_time = 0.0
        self._record_thread: Optional[threading.Thread] = None

    def toggle_recording(self):
        """Alterna entre iniciar e parar a gravação de rota."""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """Inicia a rotina de Gravação em uma thread dedicada."""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.route_points = []
        self.last_click_time = time.time()
        logger.info("Iniciando gravação de rota (Record). Clique no minimapa para adicionar waypoints.")
        
        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()

    def stop_recording(self):
        """Finaliza a gravação e consolida o route.json."""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.route_points:
            with open(self.route_file, "w", encoding="utf-8") as f:
                json.dump(self.route_points, f, indent=4)
            logger.info(f"Gravação concluída. {len(self.route_points)} waypoints salvos em {self.route_file}.")
        else:
            logger.warning("Gravação finalizada sem nenhum ponto capturado.")

    def _record_loop(self):
        """Loop de polling via win32api para capturar cliques precisos fora da thread principal."""
        state_left = win32api.GetKeyState(0x01)
        
        while self.is_recording:
            current_state = win32api.GetKeyState(0x01)
            
            # Detecta transição de estado (MouseDown)
            if current_state != state_left:
                state_left = current_state
                if current_state < 0: 
                    x, y = pyautogui.position()
                    current_time = time.time()
                    
                    # O primeiro clique não tem delay real, atribuímos um tempo base curto
                    delay = current_time - self.last_click_time if len(self.route_points) > 0 else 1.0
                    self.last_click_time = current_time
                    
                    point = {
                        "x": int(x),
                        "y": int(y),
                        "delay": round(delay, 3)
                    }
                    self.route_points.append(point)
                    logger.info(f"Waypoint gravado: ({x}, {y}) | Deslocamento: {point['delay']}s")
                    
            time.sleep(0.01) # Sleep minúsculo para evitar 100% de CPU

    async def play_route(self):
        """
        Rotina de Repetição (Cavebot).
        Deve ser executada como Task dentro do orquestrador asyncio principal.
        Lê o route.json em loop contínuo simulando os mesmos tempos de deslocamento.
        """
        if not os.path.exists(self.route_file):
            logger.error(f"Arquivo {self.route_file} não encontrado. Grave uma rota antes de dar Play.")
            return

        with open(self.route_file, "r", encoding="utf-8") as f:
            try:
                route = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Erro ao ler {self.route_file}. O arquivo pode estar corrompido.")
                return

        if not route:
            logger.error("A rota carregada está vazia.")
            return

        self.is_playing = True
        logger.info(f"Iniciando repetição (Cavebot) - {len(route)} waypoints carregados da rota.")

        while self.is_playing:
            for i, point in enumerate(route):
                if not self.is_playing:
                    break
                
                delay = point.get("delay", 1.0)
                
                # Cap de segurança: previne travamentos caso o usuário demore minutos entre um clique e outro na gravação
                if delay > 20.0:
                    delay = 3.0

                logger.debug(f"[Waypoint {i+1}/{len(route)}] Aguardando deslocamento: {delay}s...")
                await asyncio.sleep(delay)
                
                if not self.is_playing:
                    break

                target_pos = (point["x"], point["y"])
                logger.info(f"[Waypoint {i+1}/{len(route)}] Caminhando para -> {target_pos}")
                
                await self.click(target_pos)
                
        logger.info("Rotina de Cavebot finalizada.")
        
    def stop_playback(self):
        """Sinaliza a parada amigável do Cavebot."""
        self.is_playing = False
        logger.info("Parando Cavebot (Playback)...")
