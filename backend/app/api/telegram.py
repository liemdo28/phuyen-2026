from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.schemas.telegram import TelegramUpdate
from app.services.orchestrator import TelegramOrchestrator


router = APIRouter(tags=["telegram"])
orchestrator = TelegramOrchestrator()


@router.post("/telegram/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    expected = settings.telegram_webhook_secret
    if expected and x_telegram_bot_api_secret_token != expected:
      raise HTTPException(status_code=401, detail="Invalid webhook secret")

    await orchestrator.handle_update(update)
    return {"ok": True}
