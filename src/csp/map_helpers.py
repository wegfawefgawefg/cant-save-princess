from __future__ import annotations

from typing import Iterable

from csp.flags import has_flag


def hide_by_behavior_if_flag(state, behavior: str, flag: str) -> None:
    """Remove entities with a behavior when a flag is set (global or map).

    Operates on the current runtime lists (state.npcs/state.enemies).
    """
    if not has_flag(state, flag):
        return
    state.npcs = [e for e in state.npcs if getattr(e, "behavior", None) != behavior]


def hide_by_name_if_flag(state, names: Iterable[str], flag: str) -> None:
    """Remove entities by name when a flag is set.

    Names are matched case-sensitively against `entity.name`.
    """
    if not has_flag(state, flag):
        return
    names = set(names)
    state.npcs = [e for e in state.npcs if e.name not in names]
