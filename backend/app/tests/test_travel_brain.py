from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.domain import MemoryTurn, UserContext
from app.orchestration.travel_brain import TravelBrain
from app.schemas.assistant import AssistantIntent


async def _assess(text: str, now: datetime, conversation: list[MemoryTurn] | None = None):
    context = UserContext(chat_id=1, user_id=1, conversation=conversation or [])
    intent = AssistantIntent(domain="travel", intent_type="query")
    return await TravelBrain().assess(context, text, intent, now=now)


def test_travel_brain_reduces_option_count_for_stressed_context() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 5, 15, 22, 40, tzinfo=tz)
    conversation = [
        MemoryTurn(role="user", text="mệt quá", timestamp=now - timedelta(minutes=9)),
        MemoryTurn(role="user", text="không biết đi đâu", timestamp=now - timedelta(minutes=3)),
    ]

    decision = __import__("asyncio").run(_assess("mệt quá, không biết đi đâu, kẹt xe nữa", now, conversation))

    assert decision.option_count == 2
    assert decision.personalization.low_friction_mode is True
    assert decision.guidance


def test_travel_brain_expands_for_explorer_window() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 5, 15, 16, 50, tzinfo=tz)
    conversation = [
        MemoryTurn(role="user", text="quán cafe chill view đẹp", timestamp=now - timedelta(minutes=15)),
    ]

    decision = __import__("asyncio").run(_assess("chỗ ngắm hoàng hôn đẹp với hidden spot gần đây", now, conversation))

    assert decision.option_count >= 3
    assert decision.operating.profile.primary_style in {"explorer", "photographer"}


def test_travel_brain_marks_realtime_pressure() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 5, 15, 18, 10, tzinfo=tz)

    decision = __import__("asyncio").run(_assess("mưa không, traffic giờ về khách sạn có kẹt xe không", now))

    assert decision.live_context.traffic_pressure > 0
    assert decision.live_context.weather_pressure > 0
