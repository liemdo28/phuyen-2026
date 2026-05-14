from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any

from app.core.config import settings


@dataclass
class PersistedConversationTurn:
    role: str
    text: str
    created_at: str


@dataclass
class PersistedEntity:
    entity_type: str
    entity_id: str
    payload: dict[str, Any]
    created_at: str


class PersistenceStore:
    def __init__(self) -> None:
        db_path = Path(settings.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def append_turn(self, chat_id: int, user_id: int, role: str, text: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO conversation_turns(chat_id, user_id, role, text, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, user_id, role, text, now),
            )
            conn.execute(
                """
                DELETE FROM conversation_turns
                WHERE id NOT IN (
                    SELECT id FROM conversation_turns
                    WHERE chat_id = ? AND user_id = ?
                    ORDER BY id DESC LIMIT 50
                ) AND chat_id = ? AND user_id = ?
                """,
                (chat_id, user_id, chat_id, user_id),
            )
            conn.commit()

    def get_recent_turns(self, chat_id: int, user_id: int, limit: int = 20) -> list[PersistedConversationTurn]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, text, created_at
                FROM conversation_turns
                WHERE chat_id = ? AND user_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (chat_id, user_id, limit),
            ).fetchall()
        return [PersistedConversationTurn(role=row[0], text=row[1], created_at=row[2]) for row in reversed(rows)]

    def append_entity(self, chat_id: int, user_id: int, entity_type: str, entity_id: str, payload: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO entities(chat_id, user_id, entity_type, entity_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chat_id, user_id, entity_type, entity_id, json.dumps(payload), now),
            )
            conn.commit()

    def get_recent_entities(self, chat_id: int, user_id: int, limit: int = 10) -> list[PersistedEntity]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT entity_type, entity_id, payload_json, created_at
                FROM entities
                WHERE chat_id = ? AND user_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (chat_id, user_id, limit),
            ).fetchall()
        return [
            PersistedEntity(
                entity_type=row[0],
                entity_id=row[1],
                payload=json.loads(row[2]),
                created_at=row[3],
            )
            for row in rows
        ]

    def log_action(self, kind: str, chat_id: int, user_id: int, payload: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO action_logs(kind, chat_id, user_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (kind, chat_id, user_id, json.dumps(payload), now),
            )
            conn.commit()
