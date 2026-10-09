import asyncio
import time
import logging
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ActionTimer:
    """
    Gerencia o cooldown independente de uma ação específica.
    Garante que a medição de tempo seja feita de forma matemática (time.time())
    sem bloquear a thread principal.
    """
    def __init__(self, cooldown_seconds: float):
        self.cooldown_seconds = cooldown_seconds
        self.last_execution_time: float = 0.0

    def is_ready(self) -> bool:
        """Verifica de forma não-bloqueante se o tempo de cooldown já passou."""
        return (time.time() - self.last_execution_time) >= self.cooldown_seconds

    def reset(self):
        """Reinicia o timer para o momento atual após a execução da ação."""
        self.last_execution_time = time.time()


class UtilityOrchestrator:
    """
    Orquestrador Híbrido de Utility AI.
    Substitui a Máquina de Estados Finita (FSM) travada por um sistema dinâmico
    onde as ações têm cooldowns próprios e locks assíncronos.
    """
    def __init__(self):
        self._timers: Dict[str, ActionTimer] = {}
        self._action_locks: Dict[str, asyncio.Lock] = {}

    def register_action(self, action_name: str, cooldown_seconds: float):
        """Registra uma nova ação no motor com seu respectivo tempo de recarga."""
        self._timers[action_name] = ActionTimer(cooldown_seconds)
        self._action_locks[action_name] = asyncio.Lock()
        logger.debug(f"Ação registrada: {action_name} | Cooldown: {cooldown_seconds}s")

    def sync_cooldowns(self, cooldowns: Dict[str, float]):
        """Aplica cooldowns vindos do console sem perder o tempo já decorrido de cada ação."""
        for action_name, seconds in cooldowns.items():
            if action_name in self._timers:
                self._timers[action_name].cooldown_seconds = float(seconds)
            else:
                self.register_action(action_name, float(seconds))

    def can_execute(self, action_name: str) -> bool:
        """
        Consulta rápida O(1) não-bloqueante.
        O motor de Utility AI deve usar isso para pular ações em cooldown
        instantaneamente e testar a próxima melhor opção na árvore.
        """
        if action_name not in self._timers:
            logger.warning(f"Tentativa de checagem de ação não registrada: {action_name}")
            return False
        return self._timers[action_name].is_ready()

    async def execute(self, action_name: str, coro: Callable[..., Any], *args, **kwargs) -> Optional[Any]:
        """
        Executa a corrotina da ação de forma assíncrona, protegida por lock.
        Garante que a mesma ação não seja sobreposta acidentalmente por eventos concorrentes.
        """
        if not self.can_execute(action_name):
            return None

        lock = self._action_locks[action_name]
        
        # Fast-fail se outra corrotina já está engatilhando esta ação exata
        if lock.locked():
            return None

        async with lock:
            # Double-check pattern após adquirir o lock
            if not self.can_execute(action_name):
                return None
            
            try:
                # Dispara a ação desejada (ex: mover mouse, apertar atalho de cura)
                result = await coro(*args, **kwargs)
                return result
            finally:
                # O cooldown só é resetado após a ação terminar (ou falhar)
                self._timers[action_name].reset()
                logger.debug(f"Ação executada com sucesso. Cooldown resetado: {action_name}")

    def force_reset_all_timers(self):
        """Zera instantaneamente todos os cooldowns (Cérebro Try-Hard)."""
        for timer in self._timers.values():
            timer.last_execution_time = 0.0
        logger.warning(">>> TIMERS RESETADOS: Todas as magias prontas para uso imediato! <<<")

