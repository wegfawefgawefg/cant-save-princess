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
    elif item_name == "Torch":
        # Re-light torch if you have remaining fuel
        data = state.player.inventory.get("Torch")
        if isinstance(data, dict):
            rem = int(data.get("remaining", 0))
            if rem <= 0:
                log(state, "The torch has no fuel left.")
                return
            data["lit"] = True
            log(state, "You light the torch.")
        else:
            # If stored differently, just log fallback
            log(state, "You wave the torch around.")


def tick_items_per_turn(state: State) -> None:
    """Advance per-item timers by one step (e.g., torch burn)."""
    tdata = state.player.inventory.get("Torch")
    if isinstance(tdata, dict):
        if tdata.get("lit"):
            try:
                rem = int(tdata.get("remaining", 0))
            except Exception:
                rem = 0
            if rem > 0:
                tdata["remaining"] = rem - 1
                if tdata["remaining"] <= 0:
                    tdata["remaining"] = 0
                    tdata["lit"] = False
                    log(state, "Your torch burns out.")
