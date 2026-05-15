from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.domain import UserContext
from app.schemas.telegram import TelegramUpdate
from app.services.orchestrator import TelegramOrchestrator
from app.services.orchestrator import _strip_diacritics


def _build_update(text: str) -> TelegramUpdate:
    return TelegramUpdate.model_validate(
        {
            "update_id": 1001,
            "message": {
                "message_id": 201,
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


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Gửi t link file gg sheet", True),
        ("có file gg sheet chưa", True),
        ("link sheet đâu", True),
        ("cho sheet đi", True),
        ("gửi link file gg sheet", True),
        ("xem sheet được không", True),
        ("mình đói rồi", False),
        ("đi Bãi Xép", False),
    ],
)
def test_sheet_matcher(text: str, expected: bool) -> None:
    orchestrator = object.__new__(TelegramOrchestrator)
    assert TelegramOrchestrator._is_sheet_link_request(orchestrator, text) is expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("có maps ko", True),
        ("mở map đi", True),
        ("chỉ đường tới Gành Đá Đĩa", True),
        ("đói quá", False),
    ],
)
def test_maps_matcher(text: str, expected: bool) -> None:
    orchestrator = object.__new__(TelegramOrchestrator)
    assert TelegramOrchestrator._is_maps_request(orchestrator, text) is expected


def test_strip_diacritics() -> None:
    assert _strip_diacritics("Gửi t link file gg sheet") == "gui t link file gg sheet"
    assert _strip_diacritics("CÓ MAPS KO") == "co maps ko"
    assert _strip_diacritics("Bãi Xép") == "bai xep"


def test_timeout_returns_specific_message() -> None:
    orchestrator = object.__new__(TelegramOrchestrator)
    orchestrator.loop_guard = SimpleNamespace(
        evaluate=lambda **_: SimpleNamespace(
            allow_processing=True,
            allow_reply=True,
            reason="ok",
        )
    )
    orchestrator.action_logger = SimpleNamespace(log=AsyncMock())
    orchestrator.telegram = SimpleNamespace(send_message=AsyncMock())
    orchestrator.memory = SimpleNamespace(get_context=AsyncMock(side_effect=asyncio.TimeoutError()))

    update = _build_update("có file gg sheet chưa")
    asyncio.run(TelegramOrchestrator.handle_update(orchestrator, update))

    orchestrator.telegram.send_message.assert_awaited_once()
    sent_text = orchestrator.telegram.send_message.await_args.args[1]
    assert "suy nghĩ hơi chậm" in sent_text
    assert "Mình vừa gặp lỗi" not in sent_text


def test_direct_link_fast_path_runs_before_commands() -> None:
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
    orchestrator.commands = SimpleNamespace(handle=AsyncMock(side_effect=AssertionError("commands should not run")))
    orchestrator.write_flow = SimpleNamespace(handle=AsyncMock(side_effect=AssertionError("write flow should not run")))
    orchestrator._default_sheet_url = lambda: "https://docs.google.com/spreadsheets/d/sheet123/edit"

    update = _build_update("gửi link file gg sheet")
    asyncio.run(orchestrator.handle_update(update))

    orchestrator.telegram.send_message.assert_awaited_once()
    sent_text = orchestrator.telegram.send_message.await_args.args[1]
    assert "sheet123" in sent_text
