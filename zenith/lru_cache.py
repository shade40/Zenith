from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Hashable


@dataclass
class LRUCache:
    _capacity: int
    _cache: OrderedDict = field(init=False, default_factory=OrderedDict)

    def __contains__(self, key: str) -> bool:
        return key in self._cache

    def __getitem__(self, key: str) -> int:
        if key not in self._cache:
            raise KeyError(f"Key {key!r} not found in cache.")

        self._cache.move_to_end(key)
        return self._cache[key]

    def __setitem__(self, key: str, value: Hashable | dict) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)

        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)
