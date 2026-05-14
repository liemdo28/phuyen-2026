from fastapi import FastAPI

from app.api.telegram import router as telegram_router
from app.core.config import settings


app = FastAPI(
    title="Telegram AI Assistant",
    version="0.1.0",
    description="Vietnamese-first Telegram AI assistant with English internal orchestration.",
)

app.include_router(telegram_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}

