from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto

import pygame

from csp.assets import asset_path
from csp.tiles import Tile
from csp.common import Direction
from csp.dialogue import DialogueTree, initial_dialogues
from csp.entities import Entity, Player
from csp.maps import MapDef, Warp, initial_maps
from csp.shops import ShopItem


class GameMode(Enum):
    MAIN_MENU = auto()
    SETTINGS = auto()
    PLAYING = auto()
    SHOP = auto()
    INVENTORY = auto()
    DIALOGUE = auto()
    DEAD = auto()


def create_enemies() -> list[Entity]:
    return [
        Entity(
            10,
            10,
            "S",
            (120, 80, 200),
            "Shardling Slime",
            "Seeps through cracks",
            behavior="random",
        ),
        Entity(
            15,
            15,
            "B",
            (200, 60, 60),
            "Bloodsteel Bandit",
            "Hunts the living",
            behavior="chase",
        ),
        Entity(
            20,
            20,
            "G",
            (160, 30, 160),
            "Gloom Specter",
            "Phases through walls",
            behavior="phase",
        ),
    ]


@dataclass
class State:
    clock: pygame.time.Clock = field(default_factory=pygame.time.Clock)
    player: Player = field(default_factory=Player)
    # Current map runtime data
    current_map_id: str | None = None
    map_warps: dict[tuple[int, int], Warp] = field(default_factory=dict)
    map_cols: int = 0
    map_rows: int = 0
    npcs: list[Entity] = field(default_factory=list)
    turn_count: int = 0

    # Toggles
    show_help: bool = False
    show_labels: bool = True

    # Basic in-game messages: list of (text, turn_when_added)
    message_log: deque[tuple[str, int]] = field(default_factory=lambda: deque(maxlen=50))

    # Legacy simple shop items (unused by new shop view but kept for reference)
    shop_items: list[dict[str, object]] = field(default_factory=list)

    # Sounds
    sounds: dict[str, pygame.mixer.Sound] = field(default_factory=dict)

    # High-level mode
    mode: GameMode = GameMode.MAIN_MENU

    # Menu selections
    menu_main_index: int = 0
    menu_settings_index: int = 0
    menu_shop_index: int = 0
    menu_inventory_index: int = 0

    # Shop system
    # Map shop id -> list of items (name, cost, desc, max_qty or None, purchased)
    shop_inventories: dict[str, list[ShopItem]] = field(
        default_factory=lambda: {
            "item_shop": [
                {
                    "name": "Sword",
                    "cost": 5,
                    "desc": "Enable Sword Slash (melee).",
                    "max_qty": 1,
                    "purchased": 0,
                },
                {
                    "name": "Bow",
                    "cost": 8,
                    "desc": "Enable Bow Shot (ranged).",
                    "max_qty": 1,
                    "purchased": 0,
                },
                {
                    "name": "Arrows",
                    "cost": 1,
                    "desc": "Ammo for the Bow.",
                    "max_qty": None,  # unlimited
                    "purchased": 0,
                },
            ]
        }
    )
    active_shop_id: str | None = None

    # Owned items and hotkey binds
    owned_items: dict[str, int] = field(default_factory=dict)  # item -> qty
    binds: dict[str, str] = field(default_factory=dict)  # key ('1'..'0') -> item name

    # Maps registry
    maps: dict[str, MapDef] = field(default_factory=initial_maps)

    # Debug shapes
    debug_shapes_on: bool = False
    debug_shapes: list[dict[str, object]] = field(default_factory=list)
    # Runtime tiles for current map
    map_tiles: dict[tuple[int, int], Tile] = field(default_factory=dict)

    # Movement repeat (only in PLAYING mode)
    move_repeat_interval_ms: int = 100  # ~10x per second
    move_repeat_last_time_ms: int = 0
    move_repeat_last_dir: tuple[int, int] | None = None
    run_active: bool = False
    last_dir_key: Direction | None = None
    # Global spawn counters
    bunnies_spawned: int = 0
    # Track timed effects
    has_torch_lit: bool = False

    # Dialogue system
    dialogues: dict[str, DialogueTree] = field(default_factory=initial_dialogues)
    dialogue_id: str | None = None
    dialogue_node: str | None = None
    menu_dialogue_index: int = 0

    # Flags system
    # Global flags: name -> remaining steps (None = permanent until unset)
    flags_global: dict[str, int | None] = field(default_factory=dict)
    # Current map flags: name -> remaining steps (cleared on map load)
    flags_map: dict[str, int | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Load sounds (optional)
        try:
            self.sounds = {
                "punch": pygame.mixer.Sound(str(asset_path("sounds/punch.mp3"))),
                "grunt": pygame.mixer.Sound(str(asset_path("sounds/grunt.mp3"))),
                "sword": pygame.mixer.Sound(str(asset_path("sounds/sword.mp3"))),
                "bow": pygame.mixer.Sound(str(asset_path("sounds/bow.mp3"))),
            }
        except Exception:
            # In headless or missing files, proceed without sounds
            self.sounds = {}


def all_entities(state: State) -> list[Entity]:
    return [*state.npcs, state.player]
