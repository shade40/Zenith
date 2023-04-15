"""A simple implementation for a Least-Recently-Used cache object.

We need this because Python's `lru_cache` doesn't support non-hashable objects,
and adding support (through another decorator) is messy and impossible to read.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Generic, Hashable, TypeVar

__all__ = ["LRUCache"]

CacheItemType = TypeVar("CacheItem")


@dataclass
class LRUCache(Generic[CacheItemType]):
    """A Least-Recently-Used cache.

    Usage:

    ```python3
    cache = LRUCache(1024)

    def cached_function(a: int, b: int) -> float:
        key = please_hash(a, b)

        if key in cache:
            return cache[key]

        # Expensive calculation
        result = ...

        cache[key] = result

        return result
    ```
    """

    _capacity: int
    _cache: OrderedDict[Hashable, CacheItemType] = field(
        init=False, default_factory=OrderedDict
    )

    def __contains__(self, key: Hashable) -> bool:
        return key in self._cache

    def __getitem__(self, key: Hashable) -> CacheItemType:
        if key not in self._cache:
            raise KeyError(f"Key {key!r} not found in cache.")

        self._cache.move_to_end(key)
        return self._cache[key]

    def __setitem__(self, key: Hashable, value: CacheItemType) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)

        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)

    def get(
        self, key: Hashable, default: CacheItemType | None = None
    ) -> CacheItemType | None:
        return self._cache.get(key, default)
