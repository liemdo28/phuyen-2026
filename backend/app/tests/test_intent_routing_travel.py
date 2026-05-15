from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.domain import UserContext
from app.schemas.telegram import TelegramUpdate
from app.services.orchestrator import TelegramOrchestrator
from app.services.nlu import classify_travel_intent


@pytest.mark.parametrize(
    "text,expected_intent",
    [
        ("lịch ngày mai có gì", "itinerary"),
        ("ăn gì gần resort", "food"),
        ("ngân sách còn bao nhiêu", "budget"),
        ("ai đã góp tiền", "contribution"),
        ("trời mưa không", "weather"),
        ("phải đem những gì", "packing"),
        ("xem chi tiêu hôm nay", "expense_query"),
        ("chào claude", None),
        ("kể chuyện vui đi", None),
    ],
)
def test_classify_travel_intent(text: str, expected_intent: str | None) -> None:
    assert classify_travel_intent(text) == expected_intent


def _build_update(text: str) -> TelegramUpdate:
    return TelegramUpdate.model_validate(
        {
            "update_id": 2001,
            "message": {
                "message_id": 301,
                "date": 1_778_000_000,
                "chat": {"id": 8654136346, "type": "private"},
                "from": {
                    "id": 8654136346,
                    "is_bot": False,
                    "first_name": "Liem",
                },
                "text": text,
            },
        }
    )


def test_travel_intent_routes_before_llm() -> None:
    orchestrator = TelegramOrchestrator()
    orchestrator.loop_guard = SimpleNamespace(
        evaluate=lambda **_: SimpleNamespace(
            allow_processing=True,
            allow_reply=True,
            reason="ok",
        )
    )
    orchestrator.memory = SimpleNamespace(
        get_context=AsyncMock(return_value=UserContext(chat_id=8654136346, user_id=8654136346))
    )
    orchestrator.action_logger = SimpleNamespace(log=AsyncMock())
    orchestrator.telegram = SimpleNamespace(send_message=AsyncMock())
    orchestrator.llm = SimpleNamespace(detect_intent=AsyncMock(side_effect=AssertionError("LLM should not run")))
    orchestrator.commands = SimpleNamespace(handle=AsyncMock(return_value=None))
    orchestrator.write_flow = SimpleNamespace(handle=AsyncMock(return_value=None))
    orchestrator.sheets = SimpleNamespace(
        read_sheet_cached_with_meta=AsyncMock(
            return_value=(
                [{"_kind": "metadata", "Ngân sách": "30,000,000", "Tổng": "21,600,000", "Còn": "8,400,000"}],
                False,
            )
        )
    )
    orchestrator._default_sheet_url = lambda: "https://docs.google.com/spreadsheets/d/demo/edit"

    asyncio.run(orchestrator.handle_update(_build_update("ngân sách còn bao nhiêu")))

    orchestrator.telegram.send_message.assert_awaited_once()
    sent_text = orchestrator.telegram.send_message.await_args.args[1]
    assert "Ngân sách chuyến đi" in sent_text
