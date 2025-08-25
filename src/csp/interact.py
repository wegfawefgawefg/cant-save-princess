from __future__ import annotations

from typing import Optional

from csp.common import Direction, is_adjacent
from csp.state import State, all_entities, GameMode
from csp.dialogue import initial_dialogues
from csp.flags import has_flag
from csp.commerce import trade_with_trapper, open_item_shop, do_shop


def handle_interact(state: State, preferred: Optional[Direction] = None) -> None:
    # Gather adjacent interactables
    candidates = []
    px, py = state.player.x, state.player.y
    for e in all_entities(state):
        if e is state.player:
            continue
        if is_adjacent(state.player, e):
            candidates.append(e)

    if not candidates:
        state.message_log.append("Nothing here to interact with.")
        return

    # Direction preference filter if provided: prioritize entities in that primary direction
    def primary_dir(dx: int, dy: int) -> Direction | None:
        if dx == 0 and dy == 0:
            return None
        if abs(dx) >= abs(dy):
            return Direction.RIGHT if dx > 0 else Direction.LEFT
        else:
            return Direction.DOWN if dy > 0 else Direction.UP

    if preferred is not None:
        filtered = [e for e in candidates if primary_dir(e.x - px, e.y - py) == preferred]
        if filtered:
            candidates = filtered

    # Choose nearest by Manhattan distance (stable tie-break by name)
    candidates.sort(key=lambda e: (abs(e.x - px) + abs(e.y - py), e.name))
    e = candidates[0]

    # Behavior handling
    if e.behavior == "chest" and not e.opened:
        e.opened = True
        from csp.messages import log
        state.player.gold += 10000
        log(state, "You opened the chest and found 10,000 gold!")
        e.char = "o"
        e.color = (180, 180, 90)
        return
    if e.behavior == "sign":
        from csp.messages import log
        log(state, "Sign: North → Town Shop")
        log(state, "Sign: East → Woods")
        log(state, "Sign: South → Sea")
        return
    if e.behavior == "trader":
        trade_with_trapper(state)
        return
    if e.behavior == "shop":
        # For now, open the default item shop
        do_shop(state, "item_shop")
        return
    if e.behavior == "sage":
        if has_flag(state, "riddle_solved"):
            state.message_log.append("Sage: The western path is already open, seeker.")
            return
        # Start riddle dialogue
        state.dialogue_id = "riddle1"
        tree = state.dialogues.get(state.dialogue_id, {})
        state.dialogue_node = str(tree.get("start", ""))
        state.menu_dialogue_index = 0
        state.mode = GameMode.DIALOGUE
        return
    if e.behavior in ("switch", "door"):
        from csp.messages import log
        log(state, "Nothing to toggle yet.")
        return
    if e.behavior == "gold" and not getattr(e, "opened", False):
        e.opened = True
        state.player.gold += 100
        from csp.messages import log
        log(state, "You collected 100 gold!")
        e.char = "."
        e.color = (120, 120, 120)
        return
    # Fallback
    from csp.messages import log
    log(state, "Nothing here to interact with.")
