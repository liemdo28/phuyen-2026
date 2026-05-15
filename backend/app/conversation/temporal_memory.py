from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ExpenseSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    chat_id: int = 0
    user_id: int = 0
    state: str = "collecting"   # collecting | inferred | confirmed | committed | cancelled
    fragments: list[str] = field(default_factory=list)
    image_fragments: list[dict] = field(default_factory=list)
    amount: float | None = None
    category: str | None = None
    subcategory: str | None = None
    description: str | None = None
    meal_type: str | None = None
    location: str | None = None
    confidence: float = 0.0
    ambiguity: float = 1.0
    source: str = "chat"        # chat | image+chat | receipt
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confirmation_message: str = ""
    summary_shown: bool = False
    pending_irrelevant_count: int = 0  # commentary messages absorbed without breaking session


class TemporalMemory:
    """
    Short-term in-memory expense session store.
    Holds open sessions per chat while they accumulate fragments.
    Sessions are evicted once committed, cancelled, or expired.
    """

    def __init__(self) -> None:
        # One active session per (chat_id, user_id)
        self._sessions: dict[tuple[int, int], ExpenseSession] = {}

    def get(self, chat_id: int, user_id: int) -> ExpenseSession | None:
        return self._sessions.get((chat_id, user_id))

    def open(self, chat_id: int, user_id: int) -> ExpenseSession:
        session = ExpenseSession(chat_id=chat_id, user_id=user_id)
        self._sessions[(chat_id, user_id)] = session
        return session

    def save(self, session: ExpenseSession) -> None:
        session.updated_at = datetime.now(timezone.utc)
        self._sessions[(session.chat_id, session.user_id)] = session

    def close(self, chat_id: int, user_id: int) -> None:
        self._sessions.pop((chat_id, user_id), None)

    def age_seconds(self, session: ExpenseSession, now: datetime | None = None) -> float:
        ref = now or datetime.now(timezone.utc)
        delta = ref - session.updated_at
        return delta.total_seconds()

    def is_expired(self, session: ExpenseSession, window_seconds: int = 120, now: datetime | None = None) -> bool:
        return self.age_seconds(session, now) > window_seconds
