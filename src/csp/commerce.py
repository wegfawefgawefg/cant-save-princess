from __future__ import annotations

from csp.common import is_adjacent
from csp.state import State


def handle_commerce(state: State) -> None:
    trapper = state.world.trapper
    shop = state.world.item_shop
    if is_adjacent(state.player, trapper):
        trade_with_trapper(state)
    elif is_adjacent(state.player, shop):
        open_item_shop(state)
    else:
        state.message_log.append("Not near any vendor.")


def trade_with_trapper(state: State) -> None:
    if state.player.meat > 0:
        amt = state.player.meat
        state.player.gold += amt
        state.player.meat = 0
        state.message_log.append(f"Traded {amt} meat for {amt} gold.")
    else:
        state.message_log.append("You have no meat to trade.")


def open_item_shop(state: State) -> None:
    for item in state.shop_items:
        cost = int(item["cost"])  # typing help
        name = str(item["name"])  # typing help
        if state.player.gold >= cost:
            state.player.gold -= cost
            state.message_log.append(f"You bought a {name}!")
            state.player.inventory[name] = True
        else:
            state.message_log.append(f"Not enough gold for {name} ({cost}g).")
