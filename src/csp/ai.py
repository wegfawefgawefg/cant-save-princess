from __future__ import annotations

import random

from csp.graphics import COLS, ROWS
from csp.movement import move_entity
from csp.state import State


def enemy_ai(state: State) -> None:
    for enemy in list(state.enemies):
        if enemy.behavior == "random":
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            move_entity(state, enemy, dx, dy)
        elif enemy.behavior == "chase":
            dx = 1 if state.player.x > enemy.x else -1
            dy = 1 if state.player.y > enemy.y else -1
            # Move in x direction first
            if not move_entity(state, enemy, dx, 0):
                move_entity(state, enemy, 0, dy)
        elif enemy.behavior == "phase":
            # Ignores walls entirely
            enemy.x = (enemy.x + random.choice([-1, 1])) % COLS
            enemy.y = (enemy.y + random.choice([-1, 1])) % ROWS
