from __future__ import annotations

from typing import Optional, TypedDict


class ShopItem(TypedDict):
    name: str
    cost: int
    desc: str
    max_qty: Optional[int]
    purchased: int

