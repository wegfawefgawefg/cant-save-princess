from __future__ import annotations

from csp.state import State
from csp.flags import set_flag
from csp.messages import log


def handle_combat(state: State) -> None:
    dmg = state.player.actions["punch"]["damage"]
    rng = state.player.actions["punch"]["range"]
    perform_attack(state, "Punch", dmg, rng, "punch")


def perform_attack(state: State, attack_name: str, dmg: int, rng: int, sound_key: str) -> None:
    targets = []
    for e in state.npcs:
        if not getattr(e, "attackable", False):
            continue
        if getattr(e, "alignment", "neutral") == "ally":
            continue
        if abs(e.x - state.player.x) <= rng and abs(e.y - state.player.y) <= rng:
            targets.append(e)
    if targets:
        target = targets[0]
        target.health -= dmg
        if sound_key in state.sounds:
            try:
                state.sounds[sound_key].play()
            except Exception:
                pass
        log(state, f"You used {attack_name} on {target.name} for {dmg} damage!")
        if target.health <= 0:
            log(state, f"You killed the {target.name}!")
            if target.name == "Bunny":
                state.owned_items["Rabbit Meat"] = state.owned_items.get("Rabbit Meat", 0) + 1
                log(state, "+1 Rabbit Meat.")
            elif target.name == "Pig":
                state.owned_items["Pig Meat"] = state.owned_items.get("Pig Meat", 0) + 1
                log(state, "+1 Pig Meat.")
            elif target.name == "Bear":
                state.owned_items["Bear Meat"] = state.owned_items.get("Bear Meat", 0) + 1
                log(state, "+1 Bear Meat.")
            # Persistently remove unique enemies via flags
            if target.name == "Pig":
                set_flag(state, "forest_b.pig_dead", scope="global", duration_steps=None)
            if target.name == "Bear":
                set_flag(state, "forest_c.bear_dead", scope="global", duration_steps=None)
            try:
                state.npcs.remove(target)
            except ValueError:
                pass
    else:
        log(state, f"No target in range for {attack_name}.")
