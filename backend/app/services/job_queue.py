from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.telegram import TelegramUpdate


QUEUE_NAME = "telegram_updates"


class JobQueue:
    def __init__(self) -> None:
        self.backend = settings.queue_backend
        self.redis_url = settings.redis_url

    async def enqueue_update(
        self,
        update: TelegramUpdate,
        inline_handler: Callable[[TelegramUpdate], Awaitable[None]],
    ) -> None:
        if self.backend == "redis" and self.redis_url:
            redis = Redis.from_url(self.redis_url, decode_responses=True)
            await redis.rpush(QUEUE_NAME, json.dumps(update.model_dump(by_alias=True)))
            await redis.aclose()
            return
        asyncio.create_task(inline_handler(update))

    async def run_worker(
        self,
        handler: Callable[[TelegramUpdate], Awaitable[None]],
    ) -> None:
        if self.backend != "redis" or not self.redis_url:
            raise RuntimeError("Redis queue backend is not configured.")
        redis = Redis.from_url(self.redis_url, decode_responses=True)
        try:
            while True:
                result = await redis.blpop(QUEUE_NAME, timeout=5)
                if not result:
                    continue
                _, raw_payload = result
                update = TelegramUpdate.model_validate(json.loads(raw_payload))
                await handler(update)
        finally:
            await redis.aclose()
