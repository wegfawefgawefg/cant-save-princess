from __future__ import annotations

from csp.graphics import COLS, ROWS
from csp.state import State, all_entities


def can_move_to(state: State, x: int, y: int, ignore_entity: object | None = None) -> bool:
    if not (0 <= x < state.map_cols and 0 <= y < state.map_rows):
        return False
    # Dynamic tile collision
    tile = state.map_tiles.get((x, y)) if hasattr(state, "map_tiles") else None
    if tile is not None and getattr(tile, "collidable", False):
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
