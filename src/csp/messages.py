from __future__ import annotations

from csp.state import State


def log(state: State, text: str) -> None:
    state.message_log.append((text, state.turn_count))

