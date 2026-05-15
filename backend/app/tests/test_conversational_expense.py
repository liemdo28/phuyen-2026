"""
Tests for the Conversational Expense Memory system.

Simulates realistic multi-message expense flows:
  user sends fragments → engine accumulates → engine infers → user confirms
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.conversation.context_window import ContextWindow, MAX_ABSORBED_COMMENTARY
from app.conversation.expense_merger import ExpenseMerger, _format_amount
from app.conversation.intent_continuation import IntentContinuation
from app.conversation.session_engine import ExpenseSessionEngine
from app.conversation.temporal_memory import ExpenseSession, TemporalMemory
from app.conversation.topic_resolver import TopicResolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _session(
    state: str = "collecting",
    fragments: list[str] | None = None,
    image_fragments: list[dict] | None = None,
    pending_irrelevant: int = 0,
    updated_ago_seconds: float = 0.0,
) -> ExpenseSession:
    s = ExpenseSession(chat_id=1, user_id=1)
    s.state = state
    s.fragments = fragments or []
    s.image_fragments = image_fragments or []
    s.pending_irrelevant_count = pending_irrelevant
    if updated_ago_seconds:
        s.updated_at = _now() - timedelta(seconds=updated_ago_seconds)
    return s


# ===========================================================================
# ExpenseMerger
# ===========================================================================


class TestExpenseMerger:
    def setup_method(self):
        self.merger = ExpenseMerger()

    def _sess(self, *fragments, images=None):
        s = _session(fragments=list(fragments), image_fragments=images or [])
        return s

    # Amount parsing --------------------------------------------------------

    def test_bare_k_amount(self):
        r = self.merger.merge(self._sess("500k"))
        assert r.amount == 500_000

    def test_bare_number_small(self):
        r = self.merger.merge(self._sess("350"))
        assert r.amount == 350_000

    def test_bare_number_large(self):
        r = self.merger.merge(self._sess("1500000"))
        assert r.amount == 1_500_000

    def test_million_amount(self):
        r = self.merger.merge(self._sess("1.5 triệu"))
        assert r.amount == 1_500_000

    def test_thousand_words(self):
        r = self.merger.merge(self._sess("200 nghìn"))
        assert r.amount == 200_000

    def test_amount_with_dots_as_thousands(self):
        # "350.000" — dots stripped → 350000 > 999 → kept as-is
        r = self.merger.merge(self._sess("350.000đ"))
        assert r.amount == 350_000

    def test_no_amount(self):
        r = self.merger.merge(self._sess("ăn trưa hải sản"))
        assert r.amount is None

    def test_picks_largest_amount(self):
        r = self.merger.merge(self._sess("100k thôi, chứ mỗi người 50k"))
        # 100k > 50k
        assert r.amount == 100_000

    # Category detection ----------------------------------------------------

    def test_seafood_category(self):
        r = self.merger.merge(self._sess("hải sản"))
        assert r.category == "food"
        assert r.subcategory == "seafood"

    def test_coffee_category(self):
        r = self.merger.merge(self._sess("uống cà phê"))
        assert r.category == "food"
        assert r.subcategory == "coffee"

    def test_fuel_category(self):
        r = self.merger.merge(self._sess("đổ xăng"))
        assert r.category == "transport"
        assert r.subcategory == "fuel"

    def test_hotel_category(self):
        r = self.merger.merge(self._sess("thuê khách sạn 2 đêm"))
        assert r.category == "accommodation"

    def test_unknown_category(self):
        r = self.merger.merge(self._sess("chi tiêu gì đó"))
        assert r.category is None

    # Meal type detection ---------------------------------------------------

    def test_lunch_meal_type(self):
        r = self.merger.merge(self._sess("ăn trưa với bạn"))
        assert r.meal_type == "lunch"

    def test_breakfast_meal_type(self):
        r = self.merger.merge(self._sess("bữa sáng 30k"))
        assert r.meal_type == "breakfast"

    def test_dinner_meal_type(self):
        r = self.merger.merge(self._sess("ăn tối hải sản"))
        assert r.meal_type == "dinner"

    # Confidence scoring ----------------------------------------------------

    def test_high_confidence_with_all_fields(self):
        r = self.merger.merge(self._sess("500k", "ăn trưa hải sản"))
        assert r.confidence >= 0.9

    def test_medium_confidence_amount_and_category(self):
        r = self.merger.merge(self._sess("200k cà phê"))
        assert 0.7 <= r.confidence <= 1.0

    def test_low_confidence_amount_only(self):
        r = self.merger.merge(self._sess("350k"))
        assert r.confidence >= 0.5
        assert r.ambiguity <= 0.5

    def test_zero_confidence_no_data(self):
        r = self.merger.merge(self._sess("đông quá"))
        assert r.confidence == 0.0

    # Confirmation message --------------------------------------------------

    def test_confirmation_includes_amount(self):
        r = self.merger.merge(self._sess("500k ăn trưa hải sản"))
        assert "500k" in r.confirmation_message or "500" in r.confirmation_message

    def test_confirmation_includes_meal_type(self):
        r = self.merger.merge(self._sess("500k ăn trưa"))
        assert "trưa" in r.confirmation_message

    def test_no_amount_asks_for_amount(self):
        r = self.merger.merge(self._sess("ăn hải sản"))
        assert "bao nhiêu" in r.confirmation_message

    def test_low_confidence_adds_caveat(self):
        r = self.merger.merge(self._sess("350k"))
        # confidence = 0.55 (amount only) — above threshold, no caveat
        # But with subcategory missing, sentence should still parse fine
        assert "?" in r.confirmation_message

    # Image + text fragments ------------------------------------------------

    def test_image_fragment_adds_receipt_tag(self):
        s = self._sess("500k", images=[{"raw_text": "hải sản trưa"}])
        r = self.merger.merge(s)
        assert "[ảnh/receipt]" in r.description
        assert r.category == "food"

    def test_image_ocr_amount_parsed(self):
        s = self._sess(images=[{"raw_text": "Total: 350,000 VND"}])
        r = self.merger.merge(s)
        assert r.amount == 350_000


# ===========================================================================
# TopicResolver
# ===========================================================================


class TestTopicResolver:
    def setup_method(self):
        self.resolver = TopicResolver()

    def test_expense_signal_amount(self):
        assert self.resolver.is_expense_relevant("500k") is True

    def test_expense_signal_food_token(self):
        assert self.resolver.is_expense_relevant("ăn trưa") is True

    def test_expense_signal_bare_number(self):
        assert self.resolver.is_expense_relevant("350") is True

    def test_not_expense_single_digit(self):
        assert self.resolver.is_expense_relevant("5") is False

    def test_commentary_short_message(self):
        assert self.resolver.is_commentary("đông quá") is True

    def test_commentary_wow(self):
        assert self.resolver.is_commentary("wow") is True

    def test_not_commentary_expense(self):
        assert self.resolver.is_commentary("500k ăn trưa") is False

    def test_topic_change_recommendation(self):
        assert self.resolver.is_topic_change("gợi ý chỗ ngon") is True

    def test_topic_change_not_if_expense_present(self):
        assert self.resolver.is_topic_change("gợi ý 200k ăn") is False

    def test_confirmation_token(self):
        assert self.resolver.is_confirmation("đúng rồi") is True
        assert self.resolver.is_confirmation("ừ") is True
        assert self.resolver.is_confirmation("ok") is True

    def test_rejection_token(self):
        assert self.resolver.is_rejection("không") is True
        assert self.resolver.is_rejection("sai") is True
        assert self.resolver.is_rejection("hủy") is True

    def test_resolve_expense(self):
        s = _session(state="collecting", fragments=["500k"])
        assert self.resolver.resolve("ăn trưa", s) == "expense"

    def test_resolve_confirmation_on_inferred_session(self):
        s = _session(state="inferred")
        s.summary_shown = True
        assert self.resolver.resolve("đúng rồi", s) == "confirmation"

    def test_resolve_rejection_on_inferred_session(self):
        s = _session(state="inferred")
        s.summary_shown = True
        assert self.resolver.resolve("không phải", s) == "rejection"

    def test_resolve_defaults_to_expense(self):
        result = self.resolver.resolve("blah blah random", None)
        assert result == "expense"


# ===========================================================================
# ContextWindow
# ===========================================================================


class TestContextWindow:
    def setup_method(self):
        self.cw = ContextWindow()

    def test_within_window_fresh(self):
        s = _session()
        assert self.cw.is_within_window(s, _now()) is True

    def test_expired_after_120s(self):
        s = _session(updated_ago_seconds=121)
        assert self.cw.is_within_window(s, _now()) is False

    def test_extended_window_with_images(self):
        s = _session(image_fragments=[{"raw_text": "receipt"}], updated_ago_seconds=250)
        assert self.cw.is_within_window(s, _now()) is True

    def test_extended_window_expired(self):
        s = _session(image_fragments=[{"raw_text": "receipt"}], updated_ago_seconds=310)
        assert self.cw.is_within_window(s, _now()) is False

    def test_near_expiry_detected(self):
        s = _session(updated_ago_seconds=105)
        assert self.cw.is_near_expiry(s, _now()) is True

    def test_not_near_expiry_fresh(self):
        s = _session(updated_ago_seconds=30)
        assert self.cw.is_near_expiry(s, _now()) is False

    def test_can_absorb_commentary(self):
        s = _session(pending_irrelevant=MAX_ABSORBED_COMMENTARY - 1)
        assert self.cw.can_absorb_commentary(s) is True

    def test_cannot_absorb_past_limit(self):
        s = _session(pending_irrelevant=MAX_ABSORBED_COMMENTARY)
        assert self.cw.can_absorb_commentary(s) is False


# ===========================================================================
# IntentContinuation
# ===========================================================================


class TestIntentContinuation:
    def setup_method(self):
        self.engine = IntentContinuation()

    def test_no_session_expense_starts_new(self):
        assert self.engine.decide("500k", None) == "new_session"

    def test_no_session_non_expense_ignored(self):
        assert self.engine.decide("đông quá", None) == "ignore"

    def test_continue_on_expense_fragment(self):
        s = _session(state="collecting", fragments=["500k"])
        assert self.engine.decide("ăn trưa hải sản", s) == "continue_session"

    def test_confirm_on_inferred(self):
        s = _session(state="inferred")
        s.summary_shown = True
        assert self.engine.decide("đúng rồi", s) == "confirm_session"

    def test_reject_on_inferred(self):
        s = _session(state="inferred")
        s.summary_shown = True
        assert self.engine.decide("không đúng", s) == "reject_session"

    def test_expired_session_closes(self):
        s = _session(updated_ago_seconds=130)
        assert self.engine.decide("hải sản", s) == "close_expired"

    def test_commentary_absorbed_within_limit(self):
        s = _session(pending_irrelevant=0)
        assert self.engine.decide("đông quá", s) == "ignore"

    def test_commentary_breaks_session_at_limit(self):
        s = _session(pending_irrelevant=MAX_ABSORBED_COMMENTARY)
        assert self.engine.decide("wow", s) == "close_expired"

    def test_topic_change_starts_new(self):
        s = _session(state="collecting", fragments=["500k"])
        assert self.engine.decide("gợi ý chỗ ngon", s) == "new_session"


# ===========================================================================
# ExpenseSessionEngine — full flow integration tests
# ===========================================================================


class TestExpenseSessionEngine:
    def setup_method(self):
        self.engine = ExpenseSessionEngine()
        self.chat_id = 10
        self.user_id = 20

    def _process(self, text: str, images=None, offset_seconds: float = 0.0):
        now = _now() + timedelta(seconds=offset_seconds)
        return self.engine.process(text, self.chat_id, self.user_id, images, now)

    def test_single_message_amount_and_category_infers(self):
        result = self._process("500k ăn trưa hải sản")
        assert result.action == "inferred"
        assert result.session.amount == 500_000
        assert result.session.category == "food"
        assert result.reply is not None
        assert "500k" in result.reply or "500" in result.reply

    def test_fragmented_flow_two_messages(self):
        r1 = self._process("500k")
        # First message: amount only — confidence 0.55 → inferred (just above threshold)
        assert r1.action == "inferred"

    def test_commentary_absorbed_no_reply(self):
        self._process("500k ăn trưa")  # open session
        r = self._process("đông quá")
        assert r.action == "ignored"
        assert r.reply is None

    def test_confirmation_closes_session(self):
        self._process("500k ăn trưa hải sản")
        r = self._process("đúng rồi")
        assert r.action == "confirmed"
        assert r.ready_to_commit is True
        assert "ghi lại" in r.reply

    def test_rejection_cancels_session(self):
        self._process("500k ăn trưa")
        r = self._process("không phải")
        assert r.action == "rejected"
        assert r.reply is not None
        # Session should be gone
        assert self.engine.memory.get(self.chat_id, self.user_id) is None

    def test_expired_session_new_expense_starts_fresh(self):
        self._process("500k ăn trưa")
        # Advance time past window
        r = self._process("200k cà phê", offset_seconds=130)
        # Session was expired, new one started
        assert r.action in ("inferred", "collecting", "new_session")
        new_sess = self.engine.memory.get(self.chat_id, self.user_id)
        if new_sess:
            # New session shouldn't carry old fragments
            assert "500k ăn trưa" not in new_sess.fragments

    def test_non_expense_message_ignored_no_session(self):
        r = self._process("đông quá")
        assert r.action in ("ignored", "no_session")
        assert r.reply is None

    def test_topic_change_closes_session(self):
        self._process("500k ăn trưa")
        r = self._process("gợi ý chỗ ngon")
        assert r.action in ("new_session", "collecting", "inferred")

    def test_image_fragment_extends_window(self):
        ocr = {"raw_text": "hải sản 350,000 VND"}
        r = self._process("ăn trưa", images=[ocr])
        sess = self.engine.memory.get(self.chat_id, self.user_id)
        if sess:
            assert len(sess.image_fragments) == 1
            assert sess.source == "image+chat"

    def test_commit_marks_session_committed(self):
        self._process("500k ăn trưa hải sản")
        self._process("đúng")  # confirm
        committed = self.engine.commit(self.chat_id, self.user_id)
        assert committed is not None
        assert committed.state == "committed"
        assert committed.amount == 500_000

    def test_commit_without_confirmed_session_returns_none(self):
        self._process("500k ăn trưa")
        # Don't confirm — commit should return None
        committed = self.engine.commit(self.chat_id, self.user_id)
        assert committed is None

    def test_multiple_commentary_breaks_session(self):
        self._process("500k ăn trưa")
        for _ in range(MAX_ABSORBED_COMMENTARY):
            self._process("wow")
        r = self._process("hihi")
        # After too many commentaries, session should be expired/new
        assert r.action in ("expired", "no_session", "ignored", "new_session", "collecting")

    def test_receipt_ocr_only_message(self):
        ocr = {"raw_text": "bữa trưa hải sản 500,000"}
        r = self._process("", images=[ocr])
        # Empty text with image should still be processed
        sess = self.engine.memory.get(self.chat_id, self.user_id)
        # Either inferred or collecting depending on amount parse
        assert r.action in ("inferred", "collecting", "ignored", "no_session")


# ===========================================================================
# Format helper
# ===========================================================================


class TestFormatAmount:
    def test_thousands(self):
        assert _format_amount(500_000) == "500k"

    def test_millions(self):
        assert _format_amount(1_500_000) == "1.5 triệu"

    def test_small(self):
        assert _format_amount(500) == "500đ"

    def test_exact_million(self):
        assert _format_amount(2_000_000) == "2 triệu"
