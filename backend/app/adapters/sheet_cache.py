from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    data: list[dict[str, Any]]
    fetched_at: float


class SheetCache:
    """In-memory TTL cache for Google Sheet reads."""

    def __init__(self, ttl_seconds: int = 30) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> list[dict[str, Any]] | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() - entry.fetched_at > self._ttl:
            self._store.pop(key, None)
            return None
        return entry.data

    def set(self, key: str, data: list[dict[str, Any]]) -> None:
        self._store[key] = CacheEntry(data=data, fetched_at=time.monotonic())

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self._store.clear()
        else:
            self._store.pop(key, None)
