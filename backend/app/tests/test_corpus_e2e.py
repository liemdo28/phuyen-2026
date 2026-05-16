"""End-to-end test harness for Phú Yên trip corpus (149+ test cases).

Loads `tests/fixtures/user_queries.yaml` and runs each entry through
`classify_travel_intent` (intent-only unit test) and optionally through
`TelegramOrchestrator.handle_update` (full integration test).

Run:
    pytest tests/test_corpus_e2e.py -v
    pytest tests/test_corpus_e2e.py -k "itinerary" --tb=short
    pytest tests/test_corpus_e2e.py --intent-only   # skip slow e2e
    pytest tests/test_corpus_e2e.py --crash-only   # only crash_expected entries
    pytest tests/test_corpus_e2e.py --known-fail   # only known_fail entries

QA tracking columns:
    test_id | text | expected_intent | actual_intent | pass/fail | crash_y_n | notes
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

# Ensure the app package is importable from the backend root.
_BACKEND_ROOT = Path(__file__).parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.models.domain import UserContext
from app.schemas.telegram import TelegramUpdate
from app.services.nlu import classify_travel_intent
from app.services.orchestrator import TelegramOrchestrator

# ALL_CASES is loaded once by conftest.py and re-exported here.
from app.tests.conftest import ALL_CASES


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_update(text: str, update_id: int = 2001, message_id: int = 301) -> TelegramUpdate:
    return TelegramUpdate.model_validate({
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "date": 1_778_000_000,
            "chat": {"id": 8654136346, "type": "private"},
            "from": {
                "id": 8654136346,
                "is_bot": False,
                "first_name": "TestUser",
            },
            "text": text,
        },
    })


def _build_orchestrator() -> TelegramOrchestrator:
    """Return a lightly-mocked TelegramOrchestrator with canned sheet responses."""
    orch = TelegramOrchestrator()
    orch.loop_guard = SimpleNamespace(
        evaluate=lambda **_: SimpleNamespace(
            allow_processing=True,
            allow_reply=True,
            reason="test",
        )
    )
    orch.memory = SimpleNamespace(
        get_context=AsyncMock(
            return_value=UserContext(chat_id=8654136346, user_id=8654136346)
        )
    )
    orch.action_logger = SimpleNamespace(log=AsyncMock())
    orch.telegram = SimpleNamespace(send_message=AsyncMock())
    orch.llm = SimpleNamespace(detect_intent=AsyncMock(return_value=None))
    orch.commands = SimpleNamespace(handle=AsyncMock(return_value=None))
    orch.write_flow = SimpleNamespace(handle=AsyncMock(return_value=None))
    orch.sheets = SimpleNamespace(
        read_sheet_cached_with_meta=AsyncMock(
            return_value=(
                [{"_kind": "metadata", "Ngân sách": "30,000,000",
                  "Tổng": "21,600,000", "Còn": "8,400,000"}],
                False,
            )
        )
    )
    orch._default_sheet_url = lambda: "https://docs.google.com/spreadsheets/d/demo/edit"
    return orch


# ─────────────────────────────────────────────────────────────────────────────
# Intent-only tests (fast, no I/O)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: f"#{c['id']:03d}_{c['text'][:30]!r}")
class TestIntentClassification:
    """Verify classify_travel_intent returns the expected intent for each case."""

    def test_intent(self, case: dict[str, Any]) -> None:
        text = case["text"]
        expected_intent = case.get("intent")
        status = case.get("status", "pass_expected")

        actual = classify_travel_intent(text)

        if status == "known_fail":
            assert actual != expected_intent, (
                f"[#{case['id']}] '{text}' — expected known_fail (intent={actual!r}), "
                f"got expected={expected_intent!r}"
            )
        else:
            assert actual == expected_intent, (
                f"[#{case['id']}] '{text}' — expected intent={expected_intent!r}, got {actual!r}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# E2E crash-resistance tests (slow)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: f"#{c['id']:03d}_{c['text'][:30]!r}")
class TestE2ECrashResistance:
    """Feed each corpus entry through TelegramOrchestrator.handle_update.

    Verify:
    1. No unhandled exceptions / crashes
    2. telegram.send_message was called (bot replied)
    3. Reply does NOT contain error placeholder strings
    """

    @pytest.mark.asyncio
    async def test_no_crash(self, case: dict[str, Any]) -> None:
        text = case["text"]
        expected_no_match: list[str] = case.get("expected_no_match", [])
        status = case.get("status", "pass_expected")

        if status == "crash_expected":
            pytest.skip(f"#{case['id']} is a known crash case (status=crash_expected)")

        orch = _build_orchestrator()

        try:
            await orch.handle_update(_build_update(text, update_id=case["id"] + 10000))
        except Exception as exc:
            pytest.fail(f"[#{case['id']}] '{text}' — bot crashed: {exc}")

        orch.telegram.send_message.assert_awaited_once()
        sent_text: str = orch.telegram.send_message.await_args.args[1]

        for bad in expected_no_match:
            assert bad.lower() not in sent_text.lower(), (
                f"[#{case['id']}] '{text}' — reply contains forbidden string {bad!r}:\n"
                f"  {sent_text[:200]}"
            )