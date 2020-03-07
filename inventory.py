from __future__ import annotations

import itertools
from typing import Iterator, List, TYPE_CHECKING

if TYPE_CHECKING:
    from item import Item


class Inventory:
    symbols = "abcde"
    capacity = len(symbols)

    def __init__(self) -> None:
        self.contents: List[Item] = []

    def take(self, item: Item) -> None:
        """Take an item from its current location and put it in self."""
        assert item.owner is not self
        item.lift()
        self.contents.append(item)
        item.owner = self

    def list_item_descriptions(self) -> Iterator[str]:
        for key, item in itertools.zip_longest(self.symbols, self.contents):
            if item:
                yield f"{key} {item.name}"
            else:
                yield f"{key} -----"

    def is_full(self) -> bool:
        return len(self.contents) >= self.capacity
