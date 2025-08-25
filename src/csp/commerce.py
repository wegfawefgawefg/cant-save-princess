from __future__ import annotations

from __future__ import annotations

from typing import Iterable

from csp.common import is_adjacent
from csp.state import State, GameMode
from csp.shops import ShopItem
from csp.messages import log


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
    if state.player.meat > 0:
        amt = state.player.meat
        state.player.gold += amt
        state.player.meat = 0
        log(state, f"Traded {amt} rabbit corpses for {amt} gold.")
    else:
        log(state, "Lazy Trapper: Can't catch any rabbits today... got any rabbit corpses?")


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
