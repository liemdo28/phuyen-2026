from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import sqlite3
import threading

from app.core.config import settings


@dataclass
class LoopGuardDecision:
    allow_processing: bool = True
    allow_reply: bool = True
    reason: str = "ok"


class LoopGuard:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        state_dir = Path(settings.state_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = state_dir / "telegram_loop_guard.sqlite3"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_updates (
                    update_id INTEGER PRIMARY KEY,
                    message_id INTEGER,
                    chat_id INTEGER,
                    user_id INTEGER,
                    text_hash TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS message_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    user_id INTEGER,
                    message_id INTEGER,
                    text_hash TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def evaluate(
        self,
        *,
        update_id: int,
        message_id: int,
        chat_id: int,
        user_id: int,
        text: str,
    ) -> LoopGuardDecision:
        now = datetime.now(timezone.utc)
        text_hash = self._hash_text(text)
        window_start = (now - timedelta(seconds=settings.rate_limit_window_seconds)).isoformat()
        now_text = now.isoformat()

        with self._lock, self._connect() as conn:
            self._cleanup(conn, window_start)

            existing_update = conn.execute(
                "SELECT 1 FROM processed_updates WHERE update_id = ?",
                (update_id,),
            ).fetchone()
            if existing_update:
                return LoopGuardDecision(allow_processing=False, allow_reply=False, reason="duplicate_update_id")

            existing_message = conn.execute(
                """
                SELECT 1 FROM message_events
                WHERE chat_id = ? AND user_id = ? AND message_id = ? AND created_at >= ?
                LIMIT 1
                """,
                (chat_id, user_id, message_id, window_start),
            ).fetchone()
            if existing_message:
                conn.execute(
                    "INSERT OR REPLACE INTO processed_updates(update_id, message_id, chat_id, user_id, text_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (update_id, message_id, chat_id, user_id, text_hash, now_text),
                )
                conn.commit()
                return LoopGuardDecision(allow_processing=False, allow_reply=False, reason="duplicate_message_id")

            recent_count = conn.execute(
                """
                SELECT COUNT(*) FROM message_events
                WHERE chat_id = ? AND user_id = ? AND created_at >= ?
                """,
                (chat_id, user_id, window_start),
            ).fetchone()[0]
            if recent_count >= settings.rate_limit_max_messages:
                conn.execute(
                    "INSERT OR REPLACE INTO processed_updates(update_id, message_id, chat_id, user_id, text_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (update_id, message_id, chat_id, user_id, text_hash, now_text),
                )
                conn.commit()
                return LoopGuardDecision(allow_processing=False, allow_reply=False, reason="rate_limited")

            repeated_text_count = conn.execute(
                """
                SELECT COUNT(*) FROM message_events
                WHERE chat_id = ? AND user_id = ? AND text_hash = ? AND created_at >= ?
                """,
                (chat_id, user_id, text_hash, window_start),
            ).fetchone()[0]

            conn.execute(
                "INSERT INTO message_events(chat_id, user_id, message_id, text_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, user_id, message_id, text_hash, now_text),
            )
            conn.execute(
                "INSERT OR REPLACE INTO processed_updates(update_id, message_id, chat_id, user_id, text_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (update_id, message_id, chat_id, user_id, text_hash, now_text),
            )
            conn.commit()

        if repeated_text_count >= settings.repeated_text_limit:
            return LoopGuardDecision(allow_processing=False, allow_reply=False, reason="repeated_text_loop_protection")
        return LoopGuardDecision()

    def _cleanup(self, conn: sqlite3.Connection, window_start: str) -> None:
        conn.execute("DELETE FROM message_events WHERE created_at < ?", (window_start,))
        old_updates = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        conn.execute("DELETE FROM processed_updates WHERE created_at < ?", (old_updates,))

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256((text or "").strip().lower().encode("utf-8")).hexdigest()
