from __future__ import annotations

from csp.common import Direction
from csp.maps import Warp
from csp.tiles import Tile
from csp.messages import log
from csp.state import State


def load_map(state: State, map_id: str, spawn_pos: tuple[int, int] | None = None) -> None:
    m = state.maps[map_id]
    state.current_map_id = map_id
    # Solid tiles (walls + additional solids)
    solids = set(m.walls) | set(getattr(m, "solid_tiles", set()))
    state.map_warps = dict(m.warps)
    state.map_cols, state.map_rows = m.size
    # Runtime tiles
    state.map_tiles = {}
    for (x, y) in solids:
        state.map_tiles[(x, y)] = Tile(name="Wall", sprite=None, collidable=True, tag="wall")
    # Deep copy entities positions (simple copy ok for our Entity)
    state.npcs = [_copy_entity(e) for e in m.npcs]
    state.npcs.extend([_copy_entity(e) for e in m.enemies])
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
    # Per-map on-load hook (can add/modify tiles and npcs)
    if getattr(m, "on_load", None):
        try:
            m.on_load(state)  # type: ignore[misc]
        except Exception:
            # Non-fatal; continue
            pass


def _copy_entity(e):
    from csp.entities import Entity

    c = Entity(
        e.x,
        e.y,
        e.char,
        e.color,
        e.name,
        e.description,
        e.behavior,
        alignment=getattr(e, "alignment", "neutral"),
        attackable=getattr(e, "attackable", False),
    )
    c.health = e.health
    c.inventory = dict(e.inventory)
    c.opened = e.opened
    # Optional fields
    if hasattr(e, "sprite_name"):
        c.sprite_name = getattr(e, "sprite_name")
    return c


def check_warp_after_move(state: State, last_dir: Direction | None) -> None:
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


def process_triggers_after_move(state: State) -> None:
    """Process tile triggers on step (player)."""
    px, py = state.player.x, state.player.y
    t = state.map_tiles.get((px, py))
    if t is None:
        return
    if t.tag == "leaves":
        # Consume leaves and wake nearby sleeping bears
        try:
            del state.map_tiles[(px, py)]
        except KeyError:
            pass
        woke = 0
        for be in state.npcs:
            if getattr(be, "behavior", None) == "bear_sleep":
                be.behavior = "bear"
                woke += 1
        if woke:
            log(state, "You step on crunchy leaves. A bear wakes up!")


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
        # Remove wall tile at west gate (make passable)
        try:
            del state.map_tiles[west_gate]
        except KeyError:
            pass
        state.map_warps[west_gate] = start.warps[west_gate]
    from csp.messages import log

    log(state, "You hear a mechanism unlocking to the west.")
