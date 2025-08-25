from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from csp.entities import Entity


@dataclass
class Warp:
    target_map_id: str
    target_pos: Tuple[int, int]
    sideexit_dir: Optional[str] = None  # 'up'|'down'|'left'|'right' or None


@dataclass
class MapDef:
    id: str
    name: str
    size: Tuple[int, int]  # (cols, rows)
    walls: set[tuple[int, int]] = field(default_factory=set)
    warps: Dict[Tuple[int, int], Warp] = field(default_factory=dict)
    npcs: List[Entity] = field(default_factory=list)
    enemies: List[Entity] = field(default_factory=list)
    step: Optional[Callable[["State"], None]] = None  # type: ignore[name-defined]


def _border_walls(cols: int, rows: int) -> set[tuple[int, int]]:
    walls: set[tuple[int, int]] = set()
    for x in range(cols):
        walls.add((x, 0))
        walls.add((x, rows - 1))
    for y in range(rows):
        walls.add((0, y))
        walls.add((cols - 1, y))
    return walls


def make_start_area() -> MapDef:
    # Start area with a central sign. East to Woods Entrance. North to Town Shop.
    cols, rows = 24, 16
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))

    # Carve warp tiles in the border
    east_gate = (cols - 1, rows // 2)
    north_gate = (cols // 2, 0)
    # Make them walkable (remove wall) and mark as warp
    walls.discard(east_gate)
    walls.discard(north_gate)

    warps: Dict[Tuple[int, int], Warp] = {
        east_gate: Warp(target_map_id="woods_entrance", target_pos=(1, rows // 2), sideexit_dir="right"),
        north_gate: Warp(target_map_id="town_shop", target_pos=(cols // 2, rows - 2), sideexit_dir="up"),
    }

    # Sign and Sage near the center
    sign = Entity(cols // 2, rows // 2, "?", (200, 200, 100), "Sign", "Directions", behavior="sign")
    sage = Entity(cols // 2 - 2, rows // 2, "S", (200, 200, 255), "Sage", "Riddle giver", behavior="sage")

    return MapDef(
        id="start_area",
        name="Start",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[sign, sage],
        enemies=[],
        step=None,
    )


def make_woods_entrance() -> MapDef:
    cols, rows = 24, 16
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))

    west_gate = (0, rows // 2)
    east_gate = (cols - 1, rows // 2)
    walls.discard(west_gate)
    walls.discard(east_gate)
    warps: Dict[Tuple[int, int], Warp] = {
        west_gate: Warp(target_map_id="start_area", target_pos=(cols - 2, rows // 2), sideexit_dir="left"),
        east_gate: Warp(target_map_id="bunny_area", target_pos=(1, rows // 2), sideexit_dir="right"),
    }

    trapper = Entity(5, rows // 2, "T", (150, 75, 0), "Lazy Trapper", "Trades meat for gold", behavior="trader")

    return MapDef(
        id="woods_entrance",
        name="Woods Entrance",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[trapper],
        enemies=[],
        step=None,
    )


def make_bunny_area() -> MapDef:
    cols, rows = 24, 16
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))

    west_gate = (0, rows // 2)
    walls.discard(west_gate)
    warps: Dict[Tuple[int, int], Warp] = {
        west_gate: Warp(target_map_id="woods_entrance", target_pos=(cols - 2, rows // 2), sideexit_dir="left")
    }

    # Bunny hole (hut) near center-right
    hole = Entity(cols // 2 + 6, rows // 2, "o", (240, 240, 240), "Bunny Hole", "Spawns bunnies", behavior="hut")

    return MapDef(
        id="bunny_area",
        name="Bunny Glade",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[hole],
        enemies=[],
        step=None,
    )


def make_town_shop() -> MapDef:
    cols, rows = 24, 16
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))

    south_gate = (cols // 2, rows - 1)
    walls.discard(south_gate)
    warps: Dict[Tuple[int, int], Warp] = {
        south_gate: Warp(target_map_id="start_area", target_pos=(cols // 2, 1), sideexit_dir="down")
    }

    # One shop in the middle
    shop_npc = Entity(cols // 2, rows // 2, "I", (70, 200, 70), "Item Shop", "Sells powerful gear", behavior="shop")

    return MapDef(
        id="town_shop",
        name="Town Shop",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[shop_npc],
        enemies=[],
        step=None,
    )


def make_riddle_room() -> MapDef:
    cols, rows = 16, 12
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))

    east_gate = (cols - 1, rows // 2)
    walls.discard(east_gate)
    warps: Dict[Tuple[int, int], Warp] = {
        east_gate: Warp(target_map_id="start_area", target_pos=(1, rows // 2), sideexit_dir="right")
    }

    # Gold pickup in center
    gold = Entity(cols // 2, rows // 2, "$", (255, 215, 0), "Gold", "Shiny coin pile", behavior="gold")

    return MapDef(
        id="riddle_room",
        name="Hidden Vault",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[gold],
        enemies=[],
        step=None,
    )


def initial_maps() -> dict[str, MapDef]:
    return {
        "start_area": make_start_area(),
        "woods_entrance": make_woods_entrance(),
        "bunny_area": make_bunny_area(),
        "town_shop": make_town_shop(),
        "riddle_room": make_riddle_room(),
    }
