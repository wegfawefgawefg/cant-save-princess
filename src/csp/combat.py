from __future__ import annotations

from csp.state import State


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
        state.message_log.append(f"You used {attack_name} on {target.name} for {dmg} damage!")
        if target.health <= 0:
            state.message_log.append(f"You killed the {target.name}!")
            if target.name == "Bunny":
                state.player.meat += 1
                state.message_log.append("You collected 1 meat.")
            state.enemies.remove(target)
    else:
        state.message_log.append(f"No target in range for {attack_name}.")
