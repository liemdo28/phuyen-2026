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


def test_location_query_without_coordinates_prompts_for_location() -> None:
    orchestrator = TelegramOrchestrator()
    orchestrator.loop_guard = SimpleNamespace(
        evaluate=lambda **_: SimpleNamespace(
            allow_processing=True,
            allow_reply=True,
            reason="ok",
        )
    )
    orchestrator.memory = SimpleNamespace(
        get_context=AsyncMock(
            return_value=UserContext(chat_id=8654136346, user_id=8654136346)
        ),
        update_preferences=AsyncMock(),
    )
    orchestrator.action_logger = SimpleNamespace(log=AsyncMock())
    orchestrator.telegram = SimpleNamespace(send_message=AsyncMock())
    orchestrator.location_intel = SimpleNamespace(
        detect_intent=AsyncMock(
            return_value=SimpleNamespace(
                is_location_intent=True,
                query="mua chè",
                category="",
                user_lat=None,
                user_lon=None,
                on_route=False,
                child_safe=False,
            )
        ),
        parse_location_from_text=lambda _: None,
        search=AsyncMock(side_effect=AssertionError("search should not run")),
    )
    orchestrator.commands = SimpleNamespace(handle=AsyncMock(return_value=None))
    orchestrator.write_flow = SimpleNamespace(handle=AsyncMock(return_value=None))

    update = _build_update("T muốn mua chè")
    asyncio.run(orchestrator.handle_update(update))

    orchestrator.telegram.send_message.assert_awaited_once()
    sent_text = orchestrator.telegram.send_message.await_args.args[1]
    assert "Mình chưa biết bạn đang ở đâu" in sent_text


def test_location_query_uses_last_known_coordinates_from_preferences() -> None:
    orchestrator = TelegramOrchestrator()
    orchestrator.loop_guard = SimpleNamespace(
        evaluate=lambda **_: SimpleNamespace(
            allow_processing=True,
            allow_reply=True,
            reason="ok",
        )
    )
    context = UserContext(chat_id=8654136346, user_id=8654136346)
    context.preferences.update({"last_lat": 13.0955, "last_lon": 109.3028})
    orchestrator.memory = SimpleNamespace(
        get_context=AsyncMock(return_value=context),
        update_preferences=AsyncMock(),
    )
    orchestrator.action_logger = SimpleNamespace(log=AsyncMock())
    orchestrator.telegram = SimpleNamespace(send_message=AsyncMock())
    orchestrator.location_intel = SimpleNamespace(
        detect_intent=AsyncMock(
            return_value=SimpleNamespace(
                is_location_intent=True,
                query="mua chè",
                category="",
                user_lat=None,
                user_lon=None,
                on_route=False,
                child_safe=False,
            )
        ),
        parse_location_from_text=lambda _: None,
        search=AsyncMock(return_value=[]),
        format_multi_result_text=lambda *args, **kwargs: "",
        build_telegram_buttons=lambda *_: None,
    )
    orchestrator.commands = SimpleNamespace(handle=AsyncMock(return_value=None))
    orchestrator.write_flow = SimpleNamespace(handle=AsyncMock(return_value=None))
    orchestrator.llm = SimpleNamespace(
        detect_intent=AsyncMock(
            return_value=SimpleNamespace(
                intent=SimpleNamespace(
                    extracted_fields={},
                    domain="general",
                    intent_type="query",
                    model_dump=lambda: {},
                )
            )
        )
    )
    orchestrator.companion = SimpleNamespace(
        assess=lambda *args, **kwargs: SimpleNamespace(
            mood="neutral",
            stress=0.1,
            excitement=0.1,
            fatigue=0.1,
            confusion=0.1,
            overwhelm=0.1,
            response_mode="balanced",
            signals=[],
            proactive_hints=[],
        ),
        adapt_reply=lambda text, *_args, **_kwargs: text,
    )
    orchestrator._safe_assess_civilization_stack = AsyncMock(
        return_value=orchestrator._neutral_civilization_defaults(
            SimpleNamespace(
                mood="neutral",
                response_mode="balanced",
                signals=[],
                proactive_hints=[],
            )
        )
    )
    orchestrator.workflow = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(text="ok", reply_markup=None, memory_updates=None))
    )
    orchestrator.trip_context = SimpleNamespace(get_state=lambda: None, format_for_prompt=lambda *args, **kwargs: "")
    orchestrator._compose_live_reply = lambda text, *_args, **_kwargs: text
    orchestrator._companion_reply = AsyncMock(return_value=SimpleNamespace(text="ok", reply_markup=None, memory_updates=None))

    update = _build_update("T muốn mua chè")
    asyncio.run(orchestrator.handle_update(update))

    search_call = orchestrator.location_intel.search.await_args.kwargs
    assert search_call["user_lat"] == 13.0955
    assert search_call["user_lon"] == 109.3028
