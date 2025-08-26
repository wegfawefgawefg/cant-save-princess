from __future__ import annotations

import random

from csp.entities import Entity
from csp.graphics import COLORS
from csp.movement import can_move_to
from csp.state import State


def update_economy(state: State) -> None:
    # 5% chance per turn to spawn bunny near the hut, up to a global cap
    if getattr(state, "bunnies_spawned", 0) >= 20:
        return
    if random.random() < 0.05:
        if spawn_bunny(state):
            state.bunnies_spawned = getattr(state, "bunnies_spawned", 0) + 1


def spawn_bunny(state: State) -> bool:
    # Find a bunny hut/hole in current map
    hut = next((e for e in state.npcs if e.behavior == "hut" or e.name == "Bunny Hut"), None)
    if hut is None:
        return False
    # Try a few random spots near the hut
    for _ in range(10):
        x = hut.x + random.randint(-2, 2)
        y = hut.y + random.randint(-2, 2)
        if can_move_to(state, x, y):
            bunny = Entity(
                x,
                y,
                "b",
                COLORS["bunny"],
                "Bunny",
                "Harmless fluff",
                behavior="random",
                alignment="neutral",
                attackable=True,
            )
            bunny.health = 1
            state.npcs.append(bunny)
            return True
    return False
