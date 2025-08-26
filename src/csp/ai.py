from __future__ import annotations

import random

from csp.graphics import COLS, ROWS
from csp.movement import move_entity
from csp.gameplay import damage_player
from csp.state import State


def enemy_ai(state: State) -> None:
    movers = [e for e in state.npcs if getattr(e, "behavior", None) in ("random", "chase", "phase", "pig", "bear_sleep", "bear")]
    for enemy in list(movers):
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
        elif enemy.behavior == "pig":
            # If within 10 tiles (Manhattan), charge toward player (up to 2 steps)
            dist = abs(state.player.x - enemy.x) + abs(state.player.y - enemy.y)
            if dist <= 10:
                for _ in range(2):
                    dx = 1 if state.player.x > enemy.x else (-1 if state.player.x < enemy.x else 0)
                    dy = 1 if state.player.y > enemy.y else (-1 if state.player.y < enemy.y else 0)
                    if abs(state.player.x - enemy.x) >= abs(state.player.y - enemy.y):
                        if not move_entity(state, enemy, dx, 0):
                            move_entity(state, enemy, 0, dy)
                    else:
                        if not move_entity(state, enemy, 0, dy):
                            move_entity(state, enemy, dx, 0)
                # Bite if adjacent
                if abs(state.player.x - enemy.x) + abs(state.player.y - enemy.y) == 1:
                    damage_player(state, 1, source=f"{enemy.name} bite")
        elif enemy.behavior in ("bear_sleep", "bear"):
            if enemy.behavior == "bear_sleep":
                # Do nothing until woken by noise
                continue
            # Bear is awake: slow chase (1 step)
            dx = 1 if state.player.x > enemy.x else (-1 if state.player.x < enemy.x else 0)
            dy = 1 if state.player.y > enemy.y else (-1 if state.player.y < enemy.y else 0)
            if abs(state.player.x - enemy.x) >= abs(state.player.y - enemy.y):
                if not move_entity(state, enemy, dx, 0):
                    move_entity(state, enemy, 0, dy)
            else:
                if not move_entity(state, enemy, 0, dy):
                    move_entity(state, enemy, dx, 0)
            if abs(state.player.x - enemy.x) + abs(state.player.y - enemy.y) == 1:
                damage_player(state, 2, source=f"{enemy.name} swipe")


def append_debug_shapes(state: State) -> None:
    """Append per-frame debug shapes to state.debug_shapes.

    Example: for pigs, draw a yellow detection AABB representing their charge range.
    """
    # Pig detection radius (Manhattan) is 10; show a bounding rect for quick visualization
    for e in state.npcs:
        if getattr(e, "behavior", None) == "pig":
            r = 10
            x1, y1 = e.x - r, e.y - r
            x2, y2 = e.x + r, e.y + r
            state.debug_shapes.append(
                {
                    "type": "rect",
                    "aabb": ((x1, y1), (x2, y2)),
                    "color": (255, 255, 0),
                    "label": "pig range",
                }
            )
