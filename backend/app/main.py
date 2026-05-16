import logging
import os
import sys

from fastapi import FastAPI

from app.core.config import settings

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Baked in at Docker build time via ARG GIT_COMMIT
_GIT_COMMIT = os.environ.get("GIT_COMMIT", "unknown")
_BUILD_TIME = os.environ.get("BUILD_TIME", "unknown")

logger.info(
    "Starting phuyen-2026 backend (env=%s, db=%s, commit=%s, built=%s)",
    settings.app_env, settings.db_path, _GIT_COMMIT, _BUILD_TIME,
)

from app.api.telegram import router as telegram_router  # noqa: E402 — after logging setup


app = FastAPI(
    title="Telegram AI Assistant — Mi Companion",
    version="2.0.0",
    description="Mi — Vietnamese AI Companion for Phú Yên 2026 trip.",
)

app.include_router(telegram_router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "env": settings.app_env,
        "mi": "active",
        "commit": _GIT_COMMIT,
        "built": _BUILD_TIME,
    }


@app.get("/version")
async def version() -> dict:
    """Returns runtime version info — use this to verify which code is deployed."""
    return {
        "commit": _GIT_COMMIT,
        "built": _BUILD_TIME,
        "env": settings.app_env,
        "mi_personality": "active",
        "greeting_fastpath": "active",
        "sanitizer": "active",
        "member_registry": "active",
    }

