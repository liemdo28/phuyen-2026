from __future__ import annotations

import time

from app.adapters.sheet_cache import SheetCache


def test_cache_hit_within_ttl() -> None:
    cache = SheetCache(ttl_seconds=30)
    cache.set("k", [{"a": 1}])
    assert cache.get("k") == [{"a": 1}]


def test_cache_miss_after_ttl() -> None:
    cache = SheetCache(ttl_seconds=1)
    cache.set("k", [{"a": 1}])
    time.sleep(1.1)
    assert cache.get("k") is None


def test_invalidate_clears_all() -> None:
    cache = SheetCache()
    cache.set("k1", [])
    cache.set("k2", [])
    cache.invalidate()
    assert cache.get("k1") is None
    assert cache.get("k2") is None
