from __future__ import annotations

from csp.state import State
from csp.messages import log


def handle_combat(state: State) -> None:
    dmg = state.player.actions["punch"]["damage"]
    rng = state.player.actions["punch"]["range"]
    perform_attack(state, "Punch", dmg, rng, "punch")


def perform_attack(state: State, attack_name: str, dmg: int, rng: int, sound_key: str) -> None:
    targets = []
    for e in state.enemies:
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
                state.player.meat += 1
                log(state, "You collected 1 rabbit corpse.")
            state.enemies.remove(target)
    else:
        log(state, f"No target in range for {attack_name}.")
