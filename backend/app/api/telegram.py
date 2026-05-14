from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.schemas.telegram import TelegramUpdate
from app.services.job_queue import JobQueue
from app.services.orchestrator import TelegramOrchestrator


router = APIRouter(tags=["telegram"])
orchestrator = TelegramOrchestrator()
job_queue = JobQueue()


@router.post("/telegram/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    expected = settings.telegram_webhook_secret
    if expected and x_telegram_bot_api_secret_token != expected:
      raise HTTPException(status_code=401, detail="Invalid webhook secret")

    await job_queue.enqueue_update(update, orchestrator.handle_update)
    return {"ok": True}
