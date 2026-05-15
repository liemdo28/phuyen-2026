from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.domain import MemoryTurn, UserContext
from app.orchestration.travel_operating_system import TravelOperatingSystem
from app.schemas.assistant import AssistantIntent
from app.services.travel_companion import TravelCompanionEngine


def test_travel_os_sets_protective_posture_for_stressed_user() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 5, 15, 22, 20, tzinfo=tz)
    context = UserContext(
        chat_id=1,
        user_id=1,
        conversation=[
            MemoryTurn(role="user", text="mệt quá, không biết đi đâu", timestamp=now - timedelta(minutes=12)),
            MemoryTurn(role="user", text="nhiều quá", timestamp=now - timedelta(minutes=4)),
        ],
    )
    companion = TravelCompanionEngine().assess(
        context,
        "mệt quá, không biết đi đâu, kẹt xe nữa",
        intent=AssistantIntent(domain="travel", intent_type="query"),
        now=now,
    )

    state = TravelOperatingSystem().assess(
        context,
        "mệt quá, không biết đi đâu, kẹt xe nữa",
        companion,
        AssistantIntent(domain="travel", intent_type="query"),
        now=now,
    )

    assert state.recommendation_posture == "protective"
    assert state.energy.rest_pressure >= 0.4
    assert state.prediction.traffic_issue_risk > 0


def test_travel_os_expands_for_explorer_photo_window() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 5, 15, 16, 45, tzinfo=tz)
    context = UserContext(
        chat_id=1,
        user_id=1,
        conversation=[
            MemoryTurn(role="user", text="quán cafe chill view đẹp", timestamp=now - timedelta(minutes=20)),
            MemoryTurn(role="user", text="chỗ nào ngắm hoàng hôn đẹp", timestamp=now - timedelta(minutes=7)),
        ],
    )
    companion = TravelCompanionEngine().assess(
        context,
        "cafe chill ngắm hoàng hôn ở đâu",
        intent=AssistantIntent(domain="travel", intent_type="query"),
        now=now,
    )

    state = TravelOperatingSystem().assess(
        context,
        "cafe chill ngắm hoàng hôn ở đâu",
        companion,
        AssistantIntent(domain="travel", intent_type="query"),
        now=now,
    )

    assert state.profile.primary_style in {"photographer", "explorer", "foodie"}
    assert state.local.insights
    assert state.recommendation_posture in {"expand", "balanced"}


def test_travel_os_enhance_reply_appends_operating_guidance() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 5, 15, 18, 5, tzinfo=tz)
    context = UserContext(chat_id=1, user_id=1)
    intent = AssistantIntent(domain="travel", intent_type="query")
    companion = TravelCompanionEngine().assess(context, "ăn gì gần đây", intent=intent, now=now)
    state = TravelOperatingSystem().assess(context, "ăn gì gần đây", companion, intent, now=now)

    reply = TravelOperatingSystem().enhance_reply("Mình có thể chốt 1-2 quán gần bạn.", state, intent)

    assert "Travel OS:" in reply
