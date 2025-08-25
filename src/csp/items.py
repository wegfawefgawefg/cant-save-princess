from __future__ import annotations

from csp.combat import perform_attack
from csp.state import State
from csp.messages import log


def use_item(state: State, item_name: str) -> None:
    if item_name not in state.player.inventory:
        log(state, f"You don't have a {item_name}.")
        return

    if item_name == "Sword":
        perform_attack(state, "Sword Slash", 3, 1, "sword")
    elif item_name == "Bow":
        # Require arrows to fire
        arrows = state.owned_items.get("Arrows", 0)
        if arrows <= 0:
            log(state, "No arrows!")
            s = state.sounds.get("grunt")
            if s:
                try:
                    s.play()
                except Exception:
                    pass
            return
        state.owned_items["Arrows"] = arrows - 1
        perform_attack(state, "Bow Shot", 2, 2, "bow")
