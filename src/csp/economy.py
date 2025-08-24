from __future__ import annotations

import random

from csp.entities import Entity
from csp.graphics import COLORS
from csp.movement import can_move_to
from csp.state import State


def update_economy(state: State) -> None:
    # 5% chance per turn to spawn bunny near the hut
    if random.random() < 0.05:
        spawn_bunny(state)


def spawn_bunny(state: State) -> None:
    hut = state.world.bunny_hut
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
            )
            bunny.health = 1
            state.enemies.append(bunny)
            break
