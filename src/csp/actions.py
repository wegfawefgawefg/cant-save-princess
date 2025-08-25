from __future__ import annotations

from csp.map_runtime import open_start_left_path
from csp.flags import set_flag
from csp.state import State


def perform_dialogue_action(state: State, action: str) -> None:
    if action == "open_start_left_path":
        set_flag(state, "riddle_solved", scope="global", duration_steps=None)
        open_start_left_path(state)
    else:
        state.message_log.append(f"[debug] Unknown action: {action}")
