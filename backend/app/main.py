import logging
import sys

from fastapi import FastAPI

from app.core.config import settings

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)
logger.info("Starting phuyen-2026 backend (env=%s, db=%s)", settings.app_env, settings.db_path)

from app.api.telegram import router as telegram_router  # noqa: E402 — after logging setup


app = FastAPI(
    title="Telegram AI Assistant",
    version="0.1.0",
    description="Vietnamese-first Telegram AI assistant with English internal orchestration.",
)

app.include_router(telegram_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}

