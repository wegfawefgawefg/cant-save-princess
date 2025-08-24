from __future__ import annotations

from csp.graphics import COLS, ROWS
from csp.state import State, all_entities


def can_move_to(state: State, x: int, y: int, ignore_entity: object | None = None) -> bool:
    if not (0 <= x < COLS and 0 <= y < ROWS):
        return False
    if (x, y) in state.world.walls:
        return False
    for e in all_entities(state):
        if e is ignore_entity:
            continue
        if (e.x, e.y) == (x, y):
            return False
    return True


def move_entity(state: State, entity, dx: int, dy: int) -> bool:
    new_x = entity.x + dx
    new_y = entity.y + dy
    if can_move_to(state, new_x, new_y, ignore_entity=entity):
        entity.x = new_x
        entity.y = new_y
        return True
    return False
