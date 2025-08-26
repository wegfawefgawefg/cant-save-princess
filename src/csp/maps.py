from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from csp.entities import Entity
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from csp.state import State


@dataclass
class Warp:
    target_map_id: str
    target_pos: tuple[int, int]
    sideexit_dir: str | None = None  # 'up'|'down'|'left'|'right' or None


@dataclass
class MapDef:
    id: str
    name: str
    size: tuple[int, int]  # (cols, rows)
    walls: set[tuple[int, int]] = field(default_factory=set)
    warps: dict[tuple[int, int], Warp] = field(default_factory=dict)
    npcs: list[Entity] = field(default_factory=list)
    enemies: list[Entity] = field(default_factory=list)
    step: Callable[["State"], None] | None = None
    # Optional hook invoked once after a map loads into runtime
    on_load: Callable[["State"], None] | None = None
    # Additional tile metadata
    solid_tiles: set[tuple[int, int]] = field(default_factory=set)  # collidable tiles (like walls)
    noise_tiles: set[tuple[int, int]] = field(default_factory=set)  # non-collidable triggers


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

    warps: dict[tuple[int, int], Warp] = {
        east_gate: Warp(
            target_map_id="woods_entrance", target_pos=(1, rows // 2), sideexit_dir="right"
        ),
        north_gate: Warp(
            target_map_id="town_shop", target_pos=(cols // 2, rows - 2), sideexit_dir="up"
        ),
    }

    # Sign and Sage near the center
    sign = Entity(cols // 2, rows // 2, "?", (200, 200, 100), "Sign", "Directions", behavior="sign")
    sage = Entity(
        cols // 2 - 2, rows // 2, "S", (200, 200, 255), "Sage", "Riddle giver", behavior="sage"
    )

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
    warps: dict[tuple[int, int], Warp] = {
        west_gate: Warp(
            target_map_id="start_area", target_pos=(cols - 2, rows // 2), sideexit_dir="left"
        ),
        east_gate: Warp(
            target_map_id="forest_a", target_pos=(1, rows // 2), sideexit_dir="right"
        ),
    }

    trapper = Entity(
        5, rows // 2, "T", (150, 75, 0), "Lazy Trapper", "Trades meat for gold", behavior="trader"
    )

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
    warps: dict[tuple[int, int], Warp] = {
        west_gate: Warp(
            target_map_id="forest_d", target_pos=(cols - 2, rows // 2), sideexit_dir="left"
        )
    }

    # Bunny hole (hut) near center-right
    hole = Entity(
        cols // 2 + 6,
        rows // 2,
        "o",
        (240, 240, 240),
        "Bunny Hole",
        "Spawns bunnies",
        behavior="hut",
    )

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
    warps: dict[tuple[int, int], Warp] = {
        south_gate: Warp(target_map_id="start_area", target_pos=(cols // 2, 1), sideexit_dir="down")
    }

    # One shop in the middle
    shop_npc = Entity(
        cols // 2,
        rows // 2,
        "I",
        (70, 200, 70),
        "Item Shop",
        "Sells powerful gear",
        behavior="shop",
    )
    # Use the curated shop sprite asset (sprites/shop.png)
    try:
        shop_npc.sprite_name = "shop"
    except Exception:
        pass

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
    # Note: start_area has 16 rows; re-enter centered vertically (y=8)
    warps: dict[tuple[int, int], Warp] = {
        east_gate: Warp(target_map_id="start_area", target_pos=(1, 8), sideexit_dir="right")
    }

    # Gold pickup in center
    gold = Entity(
        cols // 2, rows // 2, "$", (255, 215, 0), "Gold", "Shiny coin pile", behavior="gold"
    )
    # Decorative torches as solid tiles
    solid_tiles = {(3, 2), (cols - 4, 2)}

    def _on_load(state: "State") -> None:
        # If the player already took the gold, do not spawn any gold piles
        from csp.map_helpers import hide_by_behavior_if_flag
        from csp.tiles import Tile
        hide_by_behavior_if_flag(state, behavior="gold", flag="riddle_room.gold_taken")
        # Place torches as collidable tiles with images
        state.map_tiles[(3, 2)] = Tile(name="Torch", sprite="torch", collidable=True, tag="torch")
        state.map_tiles[(cols - 4, 2)] = Tile(name="Torch", sprite="torch", collidable=True, tag="torch")

    return MapDef(
        id="riddle_room",
        name="Hidden Vault",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[gold],
        enemies=[],
        step=None,
        on_load=_on_load,
        solid_tiles=solid_tiles,
    )


def make_forest_a() -> MapDef:
    cols, rows = 24, 16
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))
    west_gate = (0, rows // 2)
    east_gate = (cols - 1, rows // 2)
    north_gate = (cols // 2, 0)
    walls.discard(west_gate)
    walls.discard(east_gate)
    walls.discard(north_gate)
    warps = {
        west_gate: Warp(target_map_id="woods_entrance", target_pos=(cols - 2, rows // 2), sideexit_dir="left"),
        east_gate: Warp(target_map_id="forest_d", target_pos=(1, rows // 2), sideexit_dir="right"),
        north_gate: Warp(target_map_id="forest_b", target_pos=(cols // 2, rows - 2), sideexit_dir="up"),
    }
    return MapDef(
        id="forest_a",
        name="Forest A",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[],
        enemies=[],
        step=None,
    )


def make_forest_b() -> MapDef:
    cols, rows = 24, 16
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))
    south_gate = (cols // 2, rows - 1)
    east_gate = (cols - 1, rows // 2)
    walls.discard(south_gate)
    walls.discard(east_gate)
    warps = {
        south_gate: Warp(target_map_id="forest_a", target_pos=(cols // 2, 1), sideexit_dir="down"),
        east_gate: Warp(target_map_id="forest_c", target_pos=(1, rows // 2), sideexit_dir="right"),
    }
    # One pig that charges
    pig = Entity(cols // 2 - 3, rows // 2, "p", (200, 120, 120), "Pig", "Charges if close", behavior="pig", alignment="hostile", attackable=True)
    pig.health = 3
    def _on_load(state: "State") -> None:
        from csp.map_helpers import hide_by_name_if_flag
        hide_by_name_if_flag(state, names=["Pig"], flag="forest_b.pig_dead")
    return MapDef(
        id="forest_b",
        name="Forest B",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[],
        enemies=[pig],
        step=None,
        on_load=_on_load,
    )


def make_forest_c() -> MapDef:
    cols, rows = 24, 16
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))
    south_gate = (cols // 2, rows - 1)
    west_gate = (0, rows // 2)
    walls.discard(south_gate)
    walls.discard(west_gate)
    warps = {
        south_gate: Warp(target_map_id="forest_d", target_pos=(cols // 2, 1), sideexit_dir="down"),
        west_gate: Warp(target_map_id="forest_b", target_pos=(cols - 2, rows // 2), sideexit_dir="left"),
    }
    # Sleeping bear; noise tiles set in on_load
    bear = Entity(cols // 2 + 3, rows // 2, "B", (120, 80, 40), "Bear", "Do not wake", behavior="bear_sleep", alignment="hostile", attackable=True)
    def _on_load(state: "State") -> None:
        from csp.map_helpers import hide_by_name_if_flag
        from csp.tiles import Tile
        hide_by_name_if_flag(state, names=["Bear"], flag="forest_c.bear_dead")
        leaves = {(5, 5), (8, 7), (12, 4), (6, 9), (10, 6), (14, 8)}
        for pos in leaves:
            state.map_tiles[pos] = Tile(name="Leaves", sprite="leaves", collidable=False, tag="leaves")
    return MapDef(
        id="forest_c",
        name="Forest C",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[],
        enemies=[bear],
        step=None,
        on_load=_on_load,
    )


def make_forest_d() -> MapDef:
    cols, rows = 24, 16
    walls: set[tuple[int, int]] = set()
    walls.update(_border_walls(cols, rows))
    west_gate = (0, rows // 2)
    north_gate = (cols // 2, 0)
    east_gate = (cols - 1, rows // 2)
    walls.discard(west_gate)
    walls.discard(north_gate)
    walls.discard(east_gate)
    warps = {
        west_gate: Warp(target_map_id="forest_a", target_pos=(cols - 2, rows // 2), sideexit_dir="left"),
        north_gate: Warp(target_map_id="forest_c", target_pos=(cols // 2, rows - 2), sideexit_dir="up"),
        east_gate: Warp(target_map_id="bunny_area", target_pos=(1, rows // 2), sideexit_dir="right"),
    }
    return MapDef(
        id="forest_d",
        name="Forest D",
        size=(cols, rows),
        walls=walls,
        warps=warps,
        npcs=[],
        enemies=[],
        step=None,
    )


def initial_maps() -> dict[str, MapDef]:
    return {
        "start_area": make_start_area(),
        "woods_entrance": make_woods_entrance(),
        "forest_a": make_forest_a(),
        "forest_b": make_forest_b(),
        "forest_c": make_forest_c(),
        "forest_d": make_forest_d(),
        "bunny_area": make_bunny_area(),
        "town_shop": make_town_shop(),
        "riddle_room": make_riddle_room(),
    }
