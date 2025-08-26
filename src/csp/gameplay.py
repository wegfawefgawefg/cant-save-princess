from __future__ import annotations

from csp.messages import log
from csp.state import GameMode


def grant_gold(state, amount: int, source: str | None = None) -> None:
    state.player.gold += max(0, int(amount))
    if source:
        log(state, f"+{amount} gold ({source}).")
    else:
        log(state, f"+{amount} gold.")


def damage_player(state, amount: int, source: str | None = None) -> None:
    dmg = max(0, int(amount))
    state.player.health -= dmg
    if source:
        log(state, f"{source} hits you for {dmg}!")
    else:
        log(state, f"You take {dmg} damage!")
    if state.player.health <= 0:
        log(state, "You have died...")
        # Enter dead mode to block further actions
        state.mode = GameMode.DEAD
        # Stop any ongoing move repeats
        state.move_repeat_last_dir = None


def hit_sfx(state, key: str) -> None:
    s = state.sounds.get(key)
    if s is None:
        return
    try:
        s.play()
    except Exception:
        pass
