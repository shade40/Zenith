import pytest

from zenith.lru_cache import LRUCache


def test_lru_cache():
    cache = LRUCache(2)

    cache[0] = "something"

    assert 0 in cache
    assert cache[0] == "something"

    cache[1] = "something else"

    assert 1 in cache
    assert cache[1] == "something else"

    cache[2] = "third item"
    assert 1 in cache and 2 in cache and not 0 in cache

    with pytest.raises(KeyError):
        cache[4]
