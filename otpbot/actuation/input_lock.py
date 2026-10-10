"""
otpbot/actuation/input_lock.py — Trava de entrada: um dono por vez (D3).

Quem quer apertar tecla ou clicar recebe um `Lease` do árbitro. A fila de ações confere o lease no instante do
envio: lease revogado (outro dono entrou, pausa, kill) = nada sai. Número de prioridade menor = mais importante
(Segurança 0 … Hunt 3).
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("InputLock")


@dataclass(frozen=True)
class Lease:
    owner: str
    priority: int
    generation: int


class InputBusy(Exception):
    """Pedido de trava por alguém menos importante que o dono atual."""


class InputLock:
    def __init__(self):
        self._current: Optional[Lease] = None
        self._generation = 0

    @property
    def current(self) -> Optional[Lease]:
        return self._current

    def grant(self, owner: str, priority: int) -> Lease:
        """Entrega a trava. O dono atual perde o lease, a não ser que seja mais importante (aí InputBusy)."""
        cur = self._current
        if cur is not None and cur.owner == owner and cur.priority == priority:
            return cur
        if cur is not None and cur.priority < priority:
            raise InputBusy(f"trava com '{cur.owner}' (prioridade {cur.priority}); '{owner}' pediu {priority}")
        self._generation += 1
        self._current = Lease(owner, priority, self._generation)
        if cur is not None:
            logger.debug(f"Trava: {cur.owner} -> {owner}")
        return self._current

    def is_valid(self, lease: Optional[Lease]) -> bool:
        return lease is not None and lease == self._current

    def release(self, lease: Optional[Lease]) -> None:
        if self.is_valid(lease):
            self._current = None

    def revoke_all(self) -> None:
        self._generation += 1
        self._current = None
