from __future__ import annotations

from __future__ import annotations

from typing import Iterable

from csp.common import is_adjacent
from csp.state import State, GameMode
from csp.shops import ShopItem
from csp.messages import log
from csp.items import cleanup_zero_qty_items


def handle_commerce(state: State) -> None:
    # Look for adjacent trader or shop NPCs
    trader = next((e for e in state.npcs if e.behavior == "trader"), None)
    shop = next((e for e in state.npcs if e.behavior == "shop"), None)
    if trader and is_adjacent(state.player, trader):
        trade_with_trapper(state)
    elif shop and is_adjacent(state.player, shop):
        open_item_shop(state)
    else:
        log(state, "Not near any vendor.")


def trade_with_trapper(state: State) -> None:
    # Prices
    price_rabbit = 1
    price_pig = 50
    price_bear = 200

    rabbits = int(state.owned_items.get("Rabbit Meat", 0))
    pigs = int(state.owned_items.get("Pig Meat", 0))
    bears = int(state.owned_items.get("Bear Meat", 0))

    total = rabbits * price_rabbit + pigs * price_pig + bears * price_bear
    if total <= 0:
        log(state, "Lazy Trapper: Can't catch any game today... got anything to sell?")
        return
    state.player.gold += total
    # Remove zero-quantity items from inventory to avoid listing them
    if rabbits:
        try:
            del state.owned_items["Rabbit Meat"]
        except KeyError:
            pass
    if pigs:
        try:
            del state.owned_items["Pig Meat"]
        except KeyError:
            pass
    if bears:
        try:
            del state.owned_items["Bear Meat"]
        except KeyError:
            pass
    parts = []
    if rabbits:
        parts.append(f"{rabbits} rabbit")
    if pigs:
        parts.append(f"{pigs} pig")
    if bears:
        parts.append(f"{bears} bear")
    sold = ", ".join(parts)
    log(state, f"Traded {sold} meat for {total} gold.")
    cleanup_zero_qty_items(state)


def do_shop(state: State, shop_id: str) -> None:
    """Open a shop session by id using the registered inventory."""
    state.active_shop_id = shop_id
    state.menu_shop_index = 0
    state.mode = GameMode.SHOP


def register_shop(state: State, shop_id: str, items: Iterable[ShopItem]) -> None:
    """Register or replace a shop inventory in the registry."""
    state.shop_inventories[shop_id] = list(items)


def open_item_shop(state: State) -> None:
    # Generic entry point for the default item shop
    do_shop(state, "item_shop")
