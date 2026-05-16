"""
Mi Presence — emotional context memory.
Remembers recent emotional states per chat_id (in-process LRU cache).
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Deque

from app.mi.presence.state import EmotionalSnapshot

_WINDOW = 5  # keep last 5 messages per chat


@dataclass
class EmotionalHistory:
    snapshots: Deque[EmotionalSnapshot] = field(default_factory=lambda: deque(maxlen=_WINDOW))
    _lock: Lock = field(default_factory=Lock, repr=False, compare=False)

    def push(self, snap: EmotionalSnapshot) -> None:
        with self._lock:
            self.snapshots.append(snap)

    @property
    def recent_fatigue_max(self) -> float:
        if not self.snapshots:
            return 0.0
        return max(s.fatigue for s in self.snapshots)

    @property
    def recent_stress_max(self) -> float:
        if not self.snapshots:
            return 0.0
        return max(s.stress for s in self.snapshots)

    @property
    def recent_excitement_avg(self) -> float:
        if not self.snapshots:
            return 0.0
        return sum(s.excitement for s in self.snapshots) / len(self.snapshots)

    @property
    def was_recently_tired(self) -> bool:
        return self.recent_fatigue_max >= 0.4

    @property
    def was_recently_stressed(self) -> bool:
        return self.recent_stress_max >= 0.45

    @property
    def trend_recovering(self) -> bool:
        """True if fatigue is decreasing over last 2 messages."""
        snaps = list(self.snapshots)
        if len(snaps) < 2:
            return False
        return snaps[-1].fatigue < snaps[-2].fatigue


class EmotionalMemoryStore:
    """In-process per-chat emotional history store."""

    _MAX_CHATS = 500

    def __init__(self) -> None:
        self._store: dict[int, EmotionalHistory] = {}
        self._order: deque[int] = deque(maxlen=self._MAX_CHATS)
        self._lock = Lock()

    def push(self, chat_id: int, snap: EmotionalSnapshot) -> None:
        with self._lock:
            if chat_id not in self._store:
                if len(self._store) >= self._MAX_CHATS:
                    oldest = self._order.popleft()
                    self._store.pop(oldest, None)
                self._store[chat_id] = EmotionalHistory()
                self._order.append(chat_id)
            self._store[chat_id].push(snap)

    def get(self, chat_id: int) -> EmotionalHistory:
        with self._lock:
            return self._store.get(chat_id, EmotionalHistory())


# Module-level singleton
_store = EmotionalMemoryStore()


def push(chat_id: int, snap: EmotionalSnapshot) -> None:
    _store.push(chat_id, snap)


def get(chat_id: int) -> EmotionalHistory:
    return _store.get(chat_id)
