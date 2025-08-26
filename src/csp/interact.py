from __future__ import annotations

from csp.commerce import do_shop, trade_with_trapper
from csp.common import Direction, is_adjacent
from csp.flags import has_flag, set_flag
from csp.state import GameMode, State, all_entities


def handle_interact(state: State, preferred: Direction | None = None) -> None:
    # Gather adjacent interactables
    candidates = []
    px, py = state.player.x, state.player.y
    # Tiles interaction first: choose target position(s)
    def dir_order() -> list[tuple[int, int]]:
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        if preferred is None:
            return [(px + dx, py + dy) for dx, dy in dirs]
        dmap = {
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1),
            Direction.LEFT: (-1, 0),
            Direction.RIGHT: (1, 0),
        }
        first = dmap.get(preferred, (0, 0))
        rest = [d for d in dirs if d != first]
        order = [first] + rest
        return [(px + dx, py + dy) for dx, dy in order]

    # Check tile targets
    for tx, ty in dir_order():
        t = state.map_tiles.get((tx, ty))
        if t is None:
            continue
        # Torch logic
        if t.tag == "torch":
            from csp.messages import log

            # Left torch in riddle room is at (3,2)
            if state.current_map_id == "riddle_room" and (tx, ty) == (3, 2):
                try:
                    del state.map_tiles[(tx, ty)]
                except KeyError:
                    pass
                # Add/augment Torch item with per-item state
                state.owned_items["Torch"] = state.owned_items.get("Torch", 0) + 1
                inv = state.player.inventory.get("Torch")
                default_duration = 1000
                if isinstance(inv, dict):
                    # If torch already exists, refresh duration if lower
                    try:
                        rem = int(inv.get("remaining", 0))
                    except Exception:
                        rem = 0
                    inv["remaining"] = max(rem, default_duration)
                    inv["lit"] = True
                else:
                    state.player.inventory["Torch"] = {"lit": True, "remaining": default_duration, "count": state.owned_items["Torch"]}
                log(state, "You take the torch. It lights your way.")
            else:
                log(state, "The torch won't budge.")
            return

    # Fall back to entity interactions
    for e in all_entities(state):
        if e is state.player:
            continue
        if is_adjacent(state.player, e):
            candidates.append(e)

    if not candidates:
        from csp.messages import log

        log(state, "Nothing here to interact with.")
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
        if has_flag(state, "start_area.riddle_solved"):
            from csp.messages import log

            log(state, "Sage: The western path is already open, seeker.")
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
        set_flag(state, "riddle_room.gold_taken", scope="global", duration_steps=None)
        # Remove this gold from the current runtime map so it disappears immediately
        try:
            state.npcs = [x for x in state.npcs if x is not e]
        except Exception:
            pass
        from csp.messages import log

        log(state, "You collected 100 gold!")
        return
    # Fallback
    from csp.messages import log

    log(state, "Nothing here to interact with.")
