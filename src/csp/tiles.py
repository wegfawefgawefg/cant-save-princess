from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Tile:
    name: str
    sprite: str | None = None
    collidable: bool = False
    tag: str | None = None  # semantic tag like 'leaves', 'torch', etc.

