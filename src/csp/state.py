from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import pygame

from csp.assets import asset_path
from csp.entities import Entity, Player
from csp.world import World


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
    world: World = field(default_factory=World)
    player: Player = field(default_factory=Player)
    enemies: list[Entity] = field(default_factory=create_enemies)
    turn_count: int = 0

    # Toggles
    show_help: bool = False
    show_labels: bool = False

    # Basic in-game messages
    message_log: deque[str] = field(default_factory=lambda: deque(maxlen=10))

    # Possible shop items
    shop_items: list[dict[str, object]] = field(
        default_factory=lambda: [
            {
                "name": "Sword",
                "cost": 5,
                "desc": "Adds a sword to inventory (press 1 to use).",
            },
            {
                "name": "Bow",
                "cost": 8,
                "desc": "Adds a bow to inventory (press 2 to use).",
            },
        ]
    )

    # Sounds
    sounds: dict[str, pygame.mixer.Sound] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Load sounds (optional)
        try:
            self.sounds = {
                "punch": pygame.mixer.Sound(str(asset_path("sounds/punch.mp3"))),
                "sword": pygame.mixer.Sound(str(asset_path("sounds/sword.mp3"))),
                "bow": pygame.mixer.Sound(str(asset_path("sounds/bow.mp3"))),
            }
        except Exception:
            # In headless or missing files, proceed without sounds
            self.sounds = {}


def all_entities(state: State) -> list[Entity]:
    return [
        *state.enemies,
        state.world.trapper,
        state.world.bunny_hut,
        state.world.item_shop,
        state.world.chest,
        state.player,
    ]
