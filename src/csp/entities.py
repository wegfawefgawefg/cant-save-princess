from __future__ import annotations

from csp.graphics import COLORS, COLS, ROWS


class Entity:
    def __init__(
        self,
        x: int,
        y: int,
        char: str,
        color: tuple[int, int, int],
        name: str,
        description: str,
        behavior: str | None = None,
    ) -> None:
        self.x: int = x
        self.y: int = y
        self.char: str = char
        self.color: tuple[int, int, int] = color
        self.name: str = name
        self.description: str = description
        self.behavior: str | None = behavior
        self.health: int = 3
        self.inventory: dict[str, object] = {}
        # For special items/entities
        self.opened: bool = False  # e.g. for chest


class Player(Entity):
    def __init__(self) -> None:
        super().__init__(
            COLS // 2,
            ROWS // 2,
            "@",
            COLORS["player"],
            "The Chrono Exile",
            "Bearer of temporal shards",
        )
        self.health: int = 20
        self.gold: int = 0
        self.meat: int = 0
        # Basic punch remains
        self.actions: dict[str, dict[str, int]] = {"punch": {"damage": 1, "range": 1}}
        self.inventory: dict[str, object] = {"gold": 0, "meat": 0}
