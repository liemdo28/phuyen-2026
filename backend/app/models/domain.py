from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MemoryTurn:
    role: str
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EntityReference:
    entity_type: str
    entity_id: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UserContext:
    chat_id: int
    user_id: int
    locale: str = "vi-VN"
    timezone: str = "Asia/Ho_Chi_Minh"
    conversation: list[MemoryTurn] = field(default_factory=list)
    entities: list[EntityReference] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
