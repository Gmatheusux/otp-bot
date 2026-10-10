"""
otpbot/brain/behaviors/base.py — Contrato de um comportamento do árbitro.

Prioridade fixa (ARQUITETURA §3): número menor = mais importante.
  SAFETY 0 > COMPANION 1 > SURVIVAL 2 > HUNT 3
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from otpbot.actuation.action_queue import ActionQueue
from otpbot.actuation.input_lock import Lease
from otpbot.state.world_state import WorldState, WorldStore

SAFETY, COMPANION, SURVIVAL, HUNT = 0, 1, 2, 3


@dataclass
class BrainContext:
    queue: ActionQueue
    store: WorldStore
    telemetry: dict = field(default_factory=dict)
    navigator: Any = None
    heal_routine: Any = None
    kill: Callable[[], None] = lambda: None


class Behavior:
    name = "base"
    priority = HUNT
    # Quando ESTE comportamento interrompe outro, o interrompido faz a limpeza (ex.: volta ao pokémon de farm)?
    allows_cleanup = True

    def wants(self, ws: WorldState, cfg: dict) -> bool:
        """Quer o controle neste tick?"""
        return False

    async def step(self, ws: WorldState, cfg: dict, lease: Lease) -> None:
        """Um tick. Rotina longa pode ficar aqui dentro: o árbitro roda numa task cancelável."""

    async def cleanup(self, lease: Optional[Lease]) -> None:
        """Chamado depois que a task foi cancelada por um comportamento mais importante."""
