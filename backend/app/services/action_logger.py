from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.services.persistence import PersistenceStore


logger = get_logger("action_logger")


@dataclass
class ActionEvent:
    kind: str
    chat_id: int
    user_id: int
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ActionLogger:
    def __init__(self) -> None:
        self.events: list[ActionEvent] = []
        self.store = PersistenceStore()

    async def log(self, kind: str, chat_id: int, user_id: int, payload: dict[str, Any]) -> None:
        event = ActionEvent(kind=kind, chat_id=chat_id, user_id=user_id, payload=payload)
        self.events.append(event)
        self.events = self.events[-200:]
        self.store.log_action(kind, chat_id, user_id, payload)
        logger.info("%s chat=%s user=%s payload=%s", kind, chat_id, user_id, payload)
