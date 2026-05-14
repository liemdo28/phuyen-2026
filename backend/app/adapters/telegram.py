from __future__ import annotations

from app.core.config import settings


class TelegramAdapter:
    async def send_message(self, chat_id: int, text: str) -> None:
        # Production integration should call Telegram sendMessage here.
        if not settings.telegram_bot_token:
            return
        # Intentionally left as a no-op scaffold to avoid accidental outbound calls during development.
        _ = (chat_id, text)

