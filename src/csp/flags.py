from __future__ import annotations

from csp.state import State


def set_flag(
    state: State, name: str, *, scope: str = "global", duration_steps: int | None = None
) -> None:
    if scope == "global":
        state.flags_global[name] = duration_steps
    elif scope == "map":
        state.flags_map[name] = duration_steps
    else:
        raise ValueError("scope must be 'global' or 'map'")


def unset_flag(state: State, name: str, *, scope: str | None = None) -> None:
    if scope is None or scope == "global":
        state.flags_global.pop(name, None)
    if scope is None or scope == "map":
        state.flags_map.pop(name, None)


def has_flag(state: State, name: str) -> bool:
    return name in state.flags_map or name in state.flags_global


def tick_flags(state: State) -> None:
    # Decrement timers; remove flags reaching zero
    for store in (state.flags_global, state.flags_map):
        expired: list[str] = []
        for k, v in list(store.items()):
            if v is None:
                continue
            nv = v - 1
            if nv <= 0:
                expired.append(k)
            else:
                store[k] = nv
        for k in expired:
            store.pop(k, None)


def reset_flags(state: State) -> None:
    state.flags_global.clear()
    state.flags_map.clear()
