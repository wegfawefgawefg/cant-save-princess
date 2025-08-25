from __future__ import annotations

from typing import Optional

from csp.common import Direction
from csp.maps import MapDef, Warp
from csp.state import State


def load_map(state: State, map_id: str, spawn_pos: Optional[tuple[int, int]] = None) -> None:
    m = state.maps[map_id]
    state.current_map_id = map_id
    state.map_walls = set(m.walls)
    state.map_warps = dict(m.warps)
    state.map_cols, state.map_rows = m.size
    # Deep copy entities positions (simple copy ok for our Entity)
    state.npcs = [
        _copy_entity(e) for e in m.npcs
    ]
    state.enemies = [
        _copy_entity(e) for e in m.enemies
    ]
    # Position player
    if spawn_pos is not None:
        state.player.x, state.player.y = spawn_pos
    else:
        # Ensure player within bounds; if not, center them in the map
        if not (0 <= state.player.x < state.map_cols and 0 <= state.player.y < state.map_rows):
            state.player.x = state.map_cols // 2
            state.player.y = state.map_rows // 2
    # Clear per-map debug
    state.debug_shapes = []
    # Clear per-map flags
    state.flags_map.clear()


def _copy_entity(e):
    from csp.entities import Entity

    c = Entity(e.x, e.y, e.char, e.color, e.name, e.description, e.behavior)
    c.health = e.health
    c.inventory = dict(e.inventory)
    c.opened = e.opened
    return c


def check_warp_after_move(state: State, last_dir: Optional[Direction]) -> None:
    pos = (state.player.x, state.player.y)
    warp = state.map_warps.get(pos)
    if not warp:
        return
    # If sideexit_dir is set, require matching input direction
    if warp.sideexit_dir:
        if last_dir is None:
            return
        if not _dir_matches(last_dir, warp.sideexit_dir):
            return
    # Trigger warp
    from csp.map_runtime import load_map

    load_map(state, warp.target_map_id, spawn_pos=warp.target_pos)


def _dir_matches(d: Direction, need: str) -> bool:
    if need == "up":
        return d.value == (0, -1)
    if need == "down":
        return d.value == (0, 1)
    if need == "left":
        return d.value == (-1, 0)
    if need == "right":
        return d.value == (1, 0)
    return False


def open_start_left_path(state: State) -> None:
    # Open west gate in start_area and add warp to riddle_room
    if "start_area" not in state.maps or "riddle_room" not in state.maps:
        from csp.messages import log
        log(state, "[debug] Missing maps for left path.")
        return
    start = state.maps["start_area"]
    s_cols, s_rows = start.size
    west_gate = (0, s_rows // 2)
    # Update map def
    start.walls.discard(west_gate)
    start.warps[west_gate] = Warp(
        target_map_id="riddle_room",
        target_pos=(state.maps["riddle_room"].size[0] - 2, state.maps["riddle_room"].size[1] // 2),
        sideexit_dir="left",
    )
    # If currently in start, update runtime too
    if state.current_map_id == "start_area":
        state.map_walls.discard(west_gate)
        state.map_warps[west_gate] = start.warps[west_gate]
    from csp.messages import log
    log(state, "You hear a mechanism unlocking to the west.")
