from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.domain import MemoryTurn, UserContext
from app.schemas.assistant import AssistantIntent
from app.services.travel_companion import TravelCompanionEngine
from app.services.workflow_engine import WorkflowEngine


def build_context() -> UserContext:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 5, 15, 22, 30, tzinfo=tz)
    return UserContext(
        chat_id=1,
        user_id=1,
        conversation=[
            MemoryTurn(role="user", text="mệt quá, không biết đi đâu", timestamp=now - timedelta(minutes=8)),
            MemoryTurn(role="assistant", text="...", timestamp=now - timedelta(minutes=7)),
            MemoryTurn(role="user", text="mệt quá, không biết đi đâu", timestamp=now - timedelta(minutes=4)),
        ],
    )


def test_assess_detects_stress_and_overwhelm() -> None:
    engine = TravelCompanionEngine()
    context = build_context()
    now = datetime(2026, 5, 15, 22, 35, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    state = engine.assess(
        context,
        "mệt quá, không biết đi đâu giờ nhiều quá",
        intent=AssistantIntent(domain="travel", intent_type="query"),
        now=now,
    )

    assert state.mood in {"stressed", "fatigued"}
    assert state.response_mode == "comfort"
    assert state.stress >= 0.35
    assert "late_night_rapid_searches" in state.signals
    assert state.proactive_hints


def test_adapt_reply_compresses_for_stressed_user() -> None:
    engine = TravelCompanionEngine()
    context = build_context()
    now = datetime(2026, 5, 15, 18, 10, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    state = engine.assess(context, "mệt quá không biết ăn gì", intent=AssistantIntent(domain="travel", intent_type="query"), now=now)

    reply = engine.adapt_reply(
        "Dòng 1\nDòng 2\nDòng 3\nDòng 4\nDòng 5\nDòng 6",
        state,
        intent=AssistantIntent(domain="travel", intent_type="query"),
    )

    assert "Mình chốt gọn cho đỡ rối nhé." in reply
    assert "Gợi ý nhanh:" in reply


class DummySheets:
    """Minimal async stub matching GoogleSheetsAdapter's interface for unit tests."""

    async def create_record(self, domain: str, payload: dict) -> object:
        from app.adapters.google_sheets import SheetsActionResult
        return SheetsActionResult(success=True, message="stub", rows=[payload])

    async def update_latest_record(self, domain: str, payload: dict) -> object:
        from app.adapters.google_sheets import SheetsActionResult
        return SheetsActionResult(success=False, message="stub")

    async def delete_record(self, domain: str, payload: dict) -> object:
        from app.adapters.google_sheets import SheetsActionResult
        return SheetsActionResult(success=False, message="stub")

    async def query_records(self, domain: str, filters: dict) -> object:
        from app.adapters.google_sheets import SheetsActionResult
        return SheetsActionResult(success=True, message="stub", rows=[])


def test_workflow_engine_travel_reply_changes_with_mood() -> None:
    engine = WorkflowEngine(DummySheets())
    companion = TravelCompanionEngine()
    context = UserContext(chat_id=1, user_id=1)
    now = datetime(2026, 5, 15, 17, 15, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    state = companion.assess(context, "cafe chill ngắm hoàng hôn ở đâu", intent=AssistantIntent(domain="travel", intent_type="query"), now=now)

    reply = engine._travel_reply(AssistantIntent(domain="travel", intent_type="query"), state)

    assert "hidden spot" in reply or "gợi ý thêm" in reply
