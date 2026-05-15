from __future__ import annotations

from app.models.domain import MemoryTurn, UserContext
from app.services.orchestrator import TelegramOrchestrator


def test_sheet_link_request_returns_google_sheet_url(monkeypatch) -> None:
    orchestrator = object.__new__(TelegramOrchestrator)
    context = UserContext(chat_id=1, user_id=1)

    monkeypatch.setattr(
        TelegramOrchestrator,
        "_default_sheet_url",
        lambda self: "https://docs.google.com/spreadsheets/d/sheet123/edit",
    )

    response = TelegramOrchestrator._direct_link_response(orchestrator, "gửi link file gg sheet", context)

    assert response is not None
    assert "docs.google.com/spreadsheets/d/sheet123/edit" in response.text


def test_default_sheet_url_falls_back_to_default_spreadsheet_url(monkeypatch) -> None:
    orchestrator = object.__new__(TelegramOrchestrator)

    monkeypatch.setattr(
        TelegramOrchestrator,
        "_default_sheet_id",
        lambda self: "abc123",
    )

    assert (
        TelegramOrchestrator._default_sheet_url(orchestrator)
        == "https://docs.google.com/spreadsheets/d/abc123/edit"
    )


def test_maps_request_uses_recent_place_context() -> None:
    orchestrator = object.__new__(TelegramOrchestrator)
    context = UserContext(
        chat_id=1,
        user_id=1,
        conversation=[
            MemoryTurn(role="assistant", text="Bãi Xép đang đẹp đó"),
        ],
    )

    response = TelegramOrchestrator._direct_link_response(orchestrator, "có maps ko", context)

    assert response is not None
    assert response.reply_markup is not None
    assert "Bãi Xép" in response.text
