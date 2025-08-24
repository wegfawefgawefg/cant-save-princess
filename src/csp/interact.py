from __future__ import annotations

from csp.common import is_adjacent
from csp.state import State, all_entities


def handle_interact(state: State) -> None:
    for e in all_entities(state):
        if e.behavior == "chest" and not e.opened:
            if is_adjacent(state.player, e):
                e.opened = True
                state.player.gold += 10000
                state.message_log.append("You opened the chest and found 10,000 gold!")
                e.char = "o"
                e.color = (180, 180, 90)
                return
    state.message_log.append("Nothing here to interact with.")
