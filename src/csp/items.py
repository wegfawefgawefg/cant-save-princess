from __future__ import annotations

from csp.combat import perform_attack
from csp.state import State


def use_item(state: State, item_name: str) -> None:
    if item_name not in state.player.inventory:
        state.message_log.append(f"You don't have a {item_name}.")
        return

    if item_name == "Sword":
        perform_attack(state, "Sword Slash", 3, 1, "sword")
    elif item_name == "Bow":
        perform_attack(state, "Bow Shot", 2, 2, "bow")
