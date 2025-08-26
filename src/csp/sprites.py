from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

from csp.assets import asset_path
from csp.graphics import CELL_SIZE


def _slug(name: str) -> str:
    s = name.strip().lower()
    out = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_"):
            out.append(ch)
        elif ch.isspace():
            out.append("_")
        else:
            out.append("_")
    # collapse repeats
    slug = "".join(out)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "sprite"


@lru_cache(maxsize=256)
def load_sprite_for_name(name: str) -> pygame.Surface | None:
    """Load a sprite by entity or asset name.

    Looks for sprites/<slug>.png; returns a Surface scaled to CELL_SIZE, or None if missing.
    """
    slug = _slug(name)
    path: Path = asset_path(f"sprites/{slug}.png")
    try:
        surf = pygame.image.load(str(path)).convert_alpha()
    except Exception:
        return None
    if surf.get_width() != CELL_SIZE or surf.get_height() != CELL_SIZE:
        surf = pygame.transform.scale(surf, (CELL_SIZE, CELL_SIZE))
    return surf


def load_sprite_for_entity(entity) -> pygame.Surface | None:
    # Prefer an explicit sprite_name attribute if present, else use name
    name = getattr(entity, "sprite_name", None) or getattr(entity, "name", "")
    return load_sprite_for_name(name)

