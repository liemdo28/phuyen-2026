from __future__ import annotations

import httpx

from app.core.config import settings


class TelegramAdapter:
    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict | None = None,
        parse_mode: str = "HTML",
    ) -> None:
        if not settings.telegram_bot_token:
            return
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload: dict = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()
            if not body.get("ok", False):
                raise RuntimeError(f"Telegram sendMessage failed: {body}")
