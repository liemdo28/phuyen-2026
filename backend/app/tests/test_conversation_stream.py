"""
Tests for the Conversation Stream Engine and Context Fusion Engine.

Covers:
- Multi-message expense accumulation with sentiment absorption
- Sentiment signals absorbed into active threads (not new threads)
- Thread timeout and expiry
- Navigation/recommendation/question intent detection
- Topic change detection and interruption recovery
- Context fusion: OCR + text merging, confidence, needs_confirmation, sentiment
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest

from app.conversation.stream_engine import (
    ConversationThread,
    StreamEngine,
    StreamResult,
    _classify_message,
    _detect_sentiment_metadata,
    _is_expense_fragment,
    _is_pure_sentiment_signal,
)
from app.conversation.context_fusion import ContextFusion, FusedContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now() -> datetime:
    return datetime.now(timezone.utc)


def make_session(
    chat_id: int = 1,
    user_id: int = 1,
    amount: float | None = None,
    category: str | None = None,
    meal_type: str | None = None,
    location: str | None = None,
    fragments: list[str] | None = None,
):
    """Build a mock ExpenseSession-like object."""
    @dataclass
    class _MockSession:
        amount: float | None = None
        category: str | None = None
        meal_type: str | None = None
        location: str | None = None
        fragments: list[str] = field(default_factory=list)
        confidence: float = 0.7

    s = _MockSession(
        amount=amount,
        category=category,
        meal_type=meal_type,
        location=location,
        fragments=fragments or [],
    )
    return s


# ---------------------------------------------------------------------------
# 1. Basic expense fragment detection
# ---------------------------------------------------------------------------

class TestExpenseFragmentDetection:
    def test_amount_with_k(self):
        assert _is_expense_fragment("500k") is True

    def test_amount_uppercase_K(self):
        assert _is_expense_fragment("300K") is True

    def test_amount_with_đồng(self):
        assert _is_expense_fragment("150 đồng") is True

    def test_food_keyword(self):
        assert _is_expense_fragment("ăn trưa") is True

    def test_seafood_keyword(self):
        assert _is_expense_fragment("hải sản") is True

    def test_cafe_keyword(self):
        assert _is_expense_fragment("cafe") is True

    def test_transport_keyword(self):
        assert _is_expense_fragment("taxi") is True

    def test_bare_number(self):
        assert _is_expense_fragment("50000") is True

    def test_pure_sentiment_not_expense(self):
        assert _is_expense_fragment("đông ghê") is False

    def test_pure_sentiment_ngon(self):
        # "ngon" alone is NOT an expense token
        assert _is_expense_fragment("ngon") is False


# ---------------------------------------------------------------------------
# 2. Sentiment signal detection
# ---------------------------------------------------------------------------

class TestSentimentSignalDetection:
    def test_crowded_dong_ghe(self):
        meta = _detect_sentiment_metadata("quán đông ghê")
        assert meta.get("crowded") is True

    def test_crowded_dong_qua(self):
        meta = _detect_sentiment_metadata("đông quá")
        assert meta.get("crowded") is True

    def test_crowded_nhieu_nguoi(self):
        meta = _detect_sentiment_metadata("nhiều người")
        assert meta.get("crowded") is True

    def test_positive_ngon(self):
        meta = _detect_sentiment_metadata("mà ngon")
        assert meta.get("positive_sentiment") is True

    def test_positive_tuyet(self):
        meta = _detect_sentiment_metadata("tuyệt vời")
        assert meta.get("positive_sentiment") is True

    def test_positive_thich(self):
        meta = _detect_sentiment_metadata("thích lắm")
        assert meta.get("positive_sentiment") is True

    def test_negative_khong_ngon(self):
        meta = _detect_sentiment_metadata("không ngon")
        assert meta.get("negative_sentiment") is True

    def test_negative_te(self):
        meta = _detect_sentiment_metadata("tệ quá")
        assert meta.get("negative_sentiment") is True

    def test_expensive_mac_qua(self):
        meta = _detect_sentiment_metadata("mắc quá")
        assert meta.get("expensive") is True

    def test_expensive_dat(self):
        meta = _detect_sentiment_metadata("đắt lắm")
        assert meta.get("expensive") is True

    def test_expensive_chat_chem(self):
        meta = _detect_sentiment_metadata("chặt chém")
        assert meta.get("expensive") is True

    def test_cheap_re(self):
        meta = _detect_sentiment_metadata("rẻ quá")
        assert meta.get("cheap") is True

    def test_cheap_hop_ly(self):
        meta = _detect_sentiment_metadata("hợp lý")
        assert meta.get("cheap") is True

    def test_noisy_on(self):
        meta = _detect_sentiment_metadata("ồn quá")
        assert meta.get("noisy") is True

    def test_quiet_chill(self):
        meta = _detect_sentiment_metadata("chill")
        assert meta.get("quiet") is True

    def test_fatigue(self):
        meta = _detect_sentiment_metadata("mệt quá")
        assert meta.get("fatigue_high") is True

    def test_pure_sentiment_crowded(self):
        assert _is_pure_sentiment_signal("đông ghê") is True

    def test_pure_sentiment_ma_ngon(self):
        assert _is_pure_sentiment_signal("mà ngon") is True

    def test_mixed_not_pure(self):
        # "mắc quá" is expensive signal; "hải sản" is expense → not pure sentiment
        assert _is_pure_sentiment_signal("hải sản mắc quá") is False


# ---------------------------------------------------------------------------
# 3. Message classification
# ---------------------------------------------------------------------------

class TestMessageClassification:
    def test_navigation_intent_di_dau(self):
        assert _classify_message("đi đâu giờ", None) == "navigation_intent"

    def test_navigation_intent_gan_day(self):
        assert _classify_message("gần đây có gì", None) == "navigation_intent"

    def test_recommendation_intent_goi_y(self):
        assert _classify_message("gợi ý cafe", None) == "recommendation_intent"

    def test_recommendation_intent_cho_nao_tam_bien(self):
        assert _classify_message("chỗ nào tắm biển", None) == "recommendation_intent"

    def test_recommendation_intent_cho_nao_ngon(self):
        assert _classify_message("chỗ nào ngon", None) == "recommendation_intent"

    def test_question_may_gio(self):
        assert _classify_message("mấy giờ", None) == "question"

    def test_question_bao_nhieu_tien(self):
        assert _classify_message("bao nhiêu tiền", None) == "question"

    def test_question_mark(self):
        assert _classify_message("có ổn không?", None) == "question"

    def test_expense_fragment_amount(self):
        assert _classify_message("500k", None) == "expense_fragment"

    def test_expense_fragment_hai_san(self):
        assert _classify_message("hải sản", None) == "expense_fragment"

    def test_expense_fragment_an_trua(self):
        assert _classify_message("ăn trưa", None) == "expense_fragment"

    def test_sentiment_signal_dong_ghe(self):
        assert _classify_message("quán đông ghê", None) == "sentiment_signal"

    def test_sentiment_signal_ma_ngon(self):
        assert _classify_message("mà ngon", None) == "sentiment_signal"

    def test_confirmation_with_active_thread(self):
        thread = ConversationThread(topic="expense")
        result = _classify_message("đúng rồi", thread)
        assert result == "confirmation"

    def test_rejection_with_active_thread(self):
        thread = ConversationThread(topic="expense")
        result = _classify_message("không phải", thread)
        assert result == "rejection"


# ---------------------------------------------------------------------------
# 4. StreamEngine: multi-message expense accumulation + sentiment absorption
# ---------------------------------------------------------------------------

class TestStreamEngineExpenseAccumulation:
    def setup_method(self):
        self.engine = StreamEngine()
        self.chat_id = 100
        self.user_id = 1
        self.t0 = now()

    def _t(self, seconds: int) -> datetime:
        return self.t0 + timedelta(seconds=seconds)

    def test_first_expense_fragment_creates_thread(self):
        result = self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        assert result.thread is not None
        assert result.thread.topic == "expense"
        assert result.message_type == "expense_fragment"

    def test_second_expense_fragment_accumulates(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("hải sản", self.chat_id, self.user_id, self._t(5))
        assert result.thread is not None
        assert len(result.thread.fragments) == 2
        assert result.thread.topic == "expense"

    def test_three_fragments_same_thread(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        self.engine.process("hải sản", self.chat_id, self.user_id, self._t(5))
        result = self.engine.process("ăn trưa", self.chat_id, self.user_id, self._t(10))
        assert len(result.thread.fragments) == 3

    def test_sentiment_absorbed_into_active_thread(self):
        """'quán đông ghê' must be absorbed into active expense thread."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("quán đông ghê", self.chat_id, self.user_id, self._t(5))
        assert result.absorbed is True
        assert result.thread.topic == "expense"
        assert result.thread.metadata.get("crowded") is True

    def test_ma_ngon_absorbed_as_positive_sentiment(self):
        """'mà ngon' must be absorbed as positive_sentiment metadata."""
        self.engine.process("hải sản", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("mà ngon", self.chat_id, self.user_id, self._t(5))
        assert result.absorbed is True
        assert result.thread.metadata.get("positive_sentiment") is True

    def test_expensive_signal_absorbed(self):
        """'mắc quá' absorbed → expensive=True in thread metadata."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("mắc quá", self.chat_id, self.user_id, self._t(5))
        assert result.absorbed is True
        assert result.thread.metadata.get("expensive") is True

    def test_multiple_sentiments_absorbed(self):
        """Multiple sentiment signals absorbed into same thread."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        self.engine.process("quán đông ghê", self.chat_id, self.user_id, self._t(5))
        self.engine.process("mà ngon", self.chat_id, self.user_id, self._t(10))
        thread = self.engine.get_active_thread(self.chat_id, self.user_id)
        assert thread.metadata.get("crowded") is True
        assert thread.metadata.get("positive_sentiment") is True

    def test_sentiment_signals_list_updated(self):
        """Absorbed sentiment signals appear in thread.sentiment_signals."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        self.engine.process("đông ghê", self.chat_id, self.user_id, self._t(5))
        thread = self.engine.get_active_thread(self.chat_id, self.user_id)
        assert len(thread.sentiment_signals) >= 1

    def test_absorbed_sentiment_no_reply(self):
        """Absorbed sentiment signal should have no reply_hint."""
        self.engine.process("hải sản", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("đông ghê", self.chat_id, self.user_id, self._t(5))
        assert result.reply_hint is None

    def test_full_expense_flow(self):
        """Full spec example: 500k + hải sản + quán đông ghê + mà ngon + ăn trưa."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        self.engine.process("hải sản", self.chat_id, self.user_id, self._t(5))
        self.engine.process("quán đông ghê", self.chat_id, self.user_id, self._t(10))
        self.engine.process("mà ngon", self.chat_id, self.user_id, self._t(15))
        result = self.engine.process("ăn trưa", self.chat_id, self.user_id, self._t(20))
        thread = result.thread
        assert thread.metadata.get("crowded") is True
        assert thread.metadata.get("positive_sentiment") is True
        # fragments should include expense-relevant messages, not pure sentiment
        assert len(thread.fragments) >= 3


# ---------------------------------------------------------------------------
# 5. Thread timeout and expiry
# ---------------------------------------------------------------------------

class TestThreadTimeout:
    def setup_method(self):
        self.engine = StreamEngine()
        self.chat_id = 200
        self.user_id = 2
        self.t0 = now()

    def _t(self, seconds: int) -> datetime:
        return self.t0 + timedelta(seconds=seconds)

    def test_expense_thread_expires_after_180s(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        # 181 seconds later, thread should be expired → new thread created
        result = self.engine.process("hải sản", self.chat_id, self.user_id, self._t(181))
        # A new thread starts (expense thread was expired)
        assert result.thread is not None
        # Only one fragment in the new thread
        assert len(result.thread.fragments) == 1

    def test_expired_thread_not_returned_as_active(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        # Fetch after expiry
        result2 = self.engine.process("check", self.chat_id, self.user_id, self._t(181))
        # The thread retrieved should not be the old expired one with 500k
        thread = self.engine.get_active_thread(self.chat_id, self.user_id)
        # Either None or a fresh thread
        if thread:
            assert "500k" not in thread.fragments or len(thread.fragments) == 1

    def test_thread_still_active_within_timeout(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("hải sản", self.chat_id, self.user_id, self._t(100))
        # Still active, two fragments
        assert len(result.thread.fragments) == 2

    def test_navigation_thread_longer_timeout(self):
        """Navigation threads should last 300s."""
        self.engine.process("gần đây có gì", self.chat_id, self.user_id, self._t(0))
        thread = self.engine.get_active_thread(self.chat_id, self.user_id)
        assert thread is not None
        assert thread.topic == "navigation"
        # At 181s, navigation thread should still be active
        # (process a follow-up navigation message)
        result = self.engine.process("gần đây", self.chat_id, self.user_id, self._t(181))
        assert result.thread is not None
        assert result.thread.topic == "navigation"


# ---------------------------------------------------------------------------
# 6. Navigation and recommendation intent
# ---------------------------------------------------------------------------

class TestNavigationAndRecommendation:
    def setup_method(self):
        self.engine = StreamEngine()
        self.chat_id = 300
        self.user_id = 3
        self.t0 = now()

    def _t(self, seconds: int) -> datetime:
        return self.t0 + timedelta(seconds=seconds)

    def test_navigation_intent_creates_navigation_thread(self):
        result = self.engine.process("đi đâu giờ", self.chat_id, self.user_id, self._t(0))
        assert result.message_type == "navigation_intent"
        assert result.thread.topic == "navigation"

    def test_navigation_reply_hint(self):
        result = self.engine.process("đi đâu giờ", self.chat_id, self.user_id, self._t(0))
        assert result.reply_hint is not None

    def test_recommendation_intent_goi_y_cafe(self):
        result = self.engine.process("gợi ý cafe", self.chat_id, self.user_id, self._t(0))
        assert result.message_type == "recommendation_intent"
        assert result.thread.topic == "recommendation"

    def test_recommendation_reply_hint(self):
        result = self.engine.process("gợi ý cafe", self.chat_id, self.user_id, self._t(0))
        assert result.reply_hint is not None

    def test_cho_nao_tam_bien_recommendation(self):
        result = self.engine.process("chỗ nào tắm biển", self.chat_id, self.user_id, self._t(0))
        assert result.message_type == "recommendation_intent"

    def test_gan_day_co_gi_navigation(self):
        result = self.engine.process("gần đây có gì", self.chat_id, self.user_id, self._t(0))
        assert result.message_type == "navigation_intent"


# ---------------------------------------------------------------------------
# 7. Topic change detection and thread pausing
# ---------------------------------------------------------------------------

class TestTopicChangeAndPausing:
    def setup_method(self):
        self.engine = StreamEngine()
        self.chat_id = 400
        self.user_id = 4
        self.t0 = now()

    def _t(self, seconds: int) -> datetime:
        return self.t0 + timedelta(seconds=seconds)

    def test_topic_change_pauses_expense_thread(self):
        """Switching from expense to navigation should pause expense thread."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        self.engine.process("hải sản", self.chat_id, self.user_id, self._t(5))
        # Switch to navigation
        self.engine.process("đi đâu giờ", self.chat_id, self.user_id, self._t(10))
        paused = self.engine.get_paused_thread(self.chat_id, self.user_id)
        active = self.engine.get_active_thread(self.chat_id, self.user_id)
        assert paused is not None
        assert paused.topic == "expense"
        assert active is not None
        assert active.topic == "navigation"

    def test_interruption_recovery_resumes_expense_thread(self):
        """After navigation interrupt, returning to expense resumes paused thread."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        self.engine.process("hải sản", self.chat_id, self.user_id, self._t(5))
        old_thread_id = self.engine.get_active_thread(self.chat_id, self.user_id).thread_id
        # Interrupt with navigation
        self.engine.process("đi đâu giờ", self.chat_id, self.user_id, self._t(10))
        # Resume expense
        result = self.engine.process("ăn trưa", self.chat_id, self.user_id, self._t(15))
        assert result.thread.topic == "expense"
        assert result.thread.thread_id == old_thread_id

    def test_resumed_thread_accumulates_new_fragment(self):
        """Resumed thread should include the new fragment."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        self.engine.process("đi đâu giờ", self.chat_id, self.user_id, self._t(5))
        result = self.engine.process("ăn trưa", self.chat_id, self.user_id, self._t(10))
        assert "ăn trưa" in result.thread.fragments

    def test_paused_thread_expires_on_recovery_after_timeout(self):
        """If paused thread has expired when we return, a new thread is created."""
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        self.engine.process("đi đâu giờ", self.chat_id, self.user_id, self._t(5))
        # Return after long pause (paused expense thread expired)
        result = self.engine.process("hải sản", self.chat_id, self.user_id, self._t(400))
        # New thread created (paused thread expired)
        assert result.thread is not None
        assert len(result.thread.fragments) == 1


# ---------------------------------------------------------------------------
# 8. Question intent
# ---------------------------------------------------------------------------

class TestQuestionIntent:
    def setup_method(self):
        self.engine = StreamEngine()
        self.chat_id = 500
        self.user_id = 5
        self.t0 = now()

    def _t(self, seconds: int) -> datetime:
        return self.t0 + timedelta(seconds=seconds)

    def test_may_gio_is_question(self):
        result = self.engine.process("mấy giờ", self.chat_id, self.user_id, self._t(0))
        assert result.message_type == "question"

    def test_bao_nhieu_tien_is_question(self):
        result = self.engine.process("bao nhiêu tiền", self.chat_id, self.user_id, self._t(0))
        assert result.message_type == "question"


# ---------------------------------------------------------------------------
# 9. Confirmation and rejection
# ---------------------------------------------------------------------------

class TestConfirmationRejection:
    def setup_method(self):
        self.engine = StreamEngine()
        self.chat_id = 600
        self.user_id = 6
        self.t0 = now()

    def _t(self, seconds: int) -> datetime:
        return self.t0 + timedelta(seconds=seconds)

    def test_confirmation_resolves_thread(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("đúng rồi", self.chat_id, self.user_id, self._t(5))
        assert result.message_type == "confirmation"
        assert result.thread.state == "resolved"

    def test_confirmation_reply_hint(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("đúng rồi", self.chat_id, self.user_id, self._t(5))
        assert result.reply_hint is not None
        assert "ghi" in result.reply_hint.lower() or "Mình" in result.reply_hint

    def test_rejection_resolves_thread(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("không phải", self.chat_id, self.user_id, self._t(5))
        assert result.message_type == "rejection"

    def test_rejection_reply_hint(self):
        self.engine.process("500k", self.chat_id, self.user_id, self._t(0))
        result = self.engine.process("không phải", self.chat_id, self.user_id, self._t(5))
        assert result.reply_hint is not None


# ---------------------------------------------------------------------------
# 10. Context Fusion: basic text
# ---------------------------------------------------------------------------

class TestContextFusionText:
    def setup_method(self):
        self.fusion = ContextFusion()

    def test_amount_extracted_from_text(self):
        ctx = self.fusion.fuse("500k")
        assert ctx.fused_amount == 500_000.0

    def test_category_food_from_hai_san(self):
        ctx = self.fusion.fuse("hải sản")
        assert ctx.fused_category == "food"

    def test_category_transport_from_taxi(self):
        ctx = self.fusion.fuse("taxi 50k")
        assert ctx.fused_category == "transport"

    def test_amount_and_category_high_confidence(self):
        ctx = self.fusion.fuse("ăn trưa 500k")
        assert ctx.confidence >= 0.8

    def test_only_category_medium_confidence(self):
        ctx = self.fusion.fuse("hải sản")
        assert ctx.confidence >= 0.6

    def test_no_signals_low_confidence(self):
        ctx = self.fusion.fuse("chào buổi sáng")
        assert ctx.confidence <= 0.5

    def test_confirmation_hint_contains_category(self):
        ctx = self.fusion.fuse("ăn trưa hải sản 500k")
        assert "ăn" in ctx.confirmation_hint.lower() or "uống" in ctx.confirmation_hint.lower()

    def test_confirmation_hint_contains_amount(self):
        ctx = self.fusion.fuse("500k")
        assert "500" in ctx.confirmation_hint or "k" in ctx.confirmation_hint

    def test_confirmation_hint_ends_with_dung_khong(self):
        ctx = self.fusion.fuse("ăn trưa 200k")
        assert "đúng không" in ctx.confirmation_hint

    def test_confirmation_hint_starts_with_minh(self):
        ctx = self.fusion.fuse("ăn trưa 200k")
        assert ctx.confirmation_hint.startswith("Mình")


# ---------------------------------------------------------------------------
# 11. Context Fusion: OCR + image
# ---------------------------------------------------------------------------

class TestContextFusionOCR:
    def setup_method(self):
        self.fusion = ContextFusion()

    def test_ocr_amount_extracted(self):
        images = [{"raw_text": "Hóa đơn: 350k"}]
        ctx = self.fusion.fuse("ăn tối", images=images)
        assert ctx.fused_amount == 350_000.0

    def test_ocr_uncertain_sets_needs_confirmation(self):
        images = [{"raw_text": "ocr pending"}]
        ctx = self.fusion.fuse("ăn tối", images=images)
        assert ctx.needs_confirmation is True

    def test_ocr_unknown_sets_needs_confirmation(self):
        images = [{"raw_text": "unknown"}]
        ctx = self.fusion.fuse("ăn tối", images=images)
        assert ctx.needs_confirmation is True

    def test_ocr_uncertain_lowers_confidence(self):
        images = [{"raw_text": "ocr pending"}]
        ctx = self.fusion.fuse("ăn tối", images=images)
        assert ctx.confidence <= 0.55

    def test_image_amount_wins_over_session_when_certain(self):
        """Image amount should be preferred over session amount if OCR is certain."""
        session = make_session(amount=300_000, category="food")
        images = [{"raw_text": "500k"}]
        ctx = self.fusion.fuse("ăn trưa", images=images, expense_session=session)
        assert ctx.fused_amount == 500_000.0

    def test_session_amount_wins_when_ocr_uncertain(self):
        session = make_session(amount=300_000, category="food")
        images = [{"raw_text": "ocr pending 500k"}]
        ctx = self.fusion.fuse("ăn trưa", images=images, expense_session=session)
        # OCR uncertain, session amount should win
        assert ctx.fused_amount == 300_000.0

    def test_image_location_used_as_hint(self):
        images = [{"raw_text": "Nhà hàng ABC 200k", "location": "Đà Nẵng"}]
        ctx = self.fusion.fuse("ăn tối", images=images)
        assert ctx.fused_location_hint == "Đà Nẵng"

    def test_no_ocr_no_needs_confirmation(self):
        ctx = self.fusion.fuse("500k ăn trưa")
        assert ctx.needs_confirmation is False

    def test_text_amount_without_image(self):
        ctx = self.fusion.fuse("200k")
        assert ctx.fused_amount == 200_000.0

    def test_amount_and_image_high_confidence(self):
        images = [{"raw_text": "Hóa đơn: 350k"}]
        ctx = self.fusion.fuse("ăn tối", images=images)
        assert ctx.confidence >= 0.6


# ---------------------------------------------------------------------------
# 12. Context Fusion: sentiment
# ---------------------------------------------------------------------------

class TestContextFusionSentiment:
    def setup_method(self):
        self.fusion = ContextFusion()

    def test_positive_sentiment_from_text(self):
        ctx = self.fusion.fuse("ngon quá")
        assert ctx.fused_sentiment == "positive"

    def test_negative_sentiment_from_text(self):
        ctx = self.fusion.fuse("không ngon tệ")
        assert ctx.fused_sentiment == "negative"

    def test_mixed_sentiment(self):
        ctx = self.fusion.fuse("ngon nhưng đắt")
        assert ctx.fused_sentiment == "mixed"

    def test_neutral_no_signals(self):
        ctx = self.fusion.fuse("ăn trưa")
        assert ctx.fused_sentiment == "neutral"

    def test_crowdedness_from_thread_metadata(self):
        @dataclass
        class _MockThread:
            metadata: dict = field(default_factory=dict)
            fragments: list[str] = field(default_factory=list)
            sentiment_signals: list[str] = field(default_factory=list)

        thread = _MockThread(metadata={"crowded": True, "positive_sentiment": True})
        ctx = self.fusion.fuse("ăn trưa", conversation_thread=thread)
        assert ctx.fused_crowdedness is True

    def test_crowdedness_from_text(self):
        ctx = self.fusion.fuse("quán đông ghê hải sản")
        assert ctx.fused_crowdedness is True

    def test_positive_sentiment_from_thread(self):
        @dataclass
        class _MockThread:
            metadata: dict = field(default_factory=dict)
            fragments: list[str] = field(default_factory=list)
            sentiment_signals: list[str] = field(default_factory=list)

        thread = _MockThread(metadata={"positive_sentiment": True})
        ctx = self.fusion.fuse("ăn trưa", conversation_thread=thread)
        assert ctx.fused_sentiment == "positive"

    def test_mixed_signals_thread(self):
        @dataclass
        class _MockThread:
            metadata: dict = field(default_factory=dict)
            fragments: list[str] = field(default_factory=list)
            sentiment_signals: list[str] = field(default_factory=list)

        thread = _MockThread(
            metadata={"positive_sentiment": True, "negative_sentiment": True}
        )
        ctx = self.fusion.fuse("ăn tối", conversation_thread=thread)
        assert ctx.fused_sentiment == "mixed"


# ---------------------------------------------------------------------------
# 13. Context Fusion: session data
# ---------------------------------------------------------------------------

class TestContextFusionSession:
    def setup_method(self):
        self.fusion = ContextFusion()

    def test_session_amount_used(self):
        session = make_session(amount=250_000, category="food")
        ctx = self.fusion.fuse("", expense_session=session)
        assert ctx.fused_amount == 250_000.0

    def test_session_category_used(self):
        session = make_session(category="transport")
        ctx = self.fusion.fuse("", expense_session=session)
        assert ctx.fused_category == "transport"

    def test_session_location_used(self):
        session = make_session(location="Hội An")
        ctx = self.fusion.fuse("", expense_session=session)
        assert ctx.fused_location_hint == "Hội An"

    def test_confirmation_hint_with_location(self):
        session = make_session(amount=200_000, category="food", location="Hội An")
        ctx = self.fusion.fuse("", expense_session=session)
        assert "Hội An" in ctx.confirmation_hint

    def test_confirmation_hint_with_meal_type(self):
        session = make_session(amount=150_000, category="food", meal_type="lunch")
        ctx = self.fusion.fuse("", expense_session=session)
        assert "trưa" in ctx.confirmation_hint


# ---------------------------------------------------------------------------
# 14. FusedContext data integrity
# ---------------------------------------------------------------------------

class TestFusedContextIntegrity:
    def setup_method(self):
        self.fusion = ContextFusion()

    def test_text_fragments_stored(self):
        ctx = self.fusion.fuse("500k hải sản")
        assert "500k hải sản" in ctx.text_fragments

    def test_image_contexts_stored(self):
        images = [{"raw_text": "200k"}]
        ctx = self.fusion.fuse("ăn tối", images=images)
        assert len(ctx.image_contexts) == 1

    def test_trip_context_stored(self):
        trip = {"location": "Đà Lạt", "day": 3}
        ctx = self.fusion.fuse("", trip_context=trip)
        assert ctx.trip_context == trip

    def test_trip_location_as_hint(self):
        trip = {"location": "Đà Lạt"}
        ctx = self.fusion.fuse("ăn trưa 200k", trip_context=trip)
        assert ctx.fused_location_hint == "Đà Lạt"

    def test_world_signals_stored(self):
        wm = {"world_signals": ["rain", "peak_season"]}
        ctx = self.fusion.fuse("", world_model=wm)
        assert "rain" in ctx.world_signals

    def test_emotional_signals_stored(self):
        wm = {"emotional_signals": ["tired", "hungry"]}
        ctx = self.fusion.fuse("", world_model=wm)
        assert "tired" in ctx.emotional_signals

    def test_confidence_range(self):
        ctx = self.fusion.fuse("500k hải sản")
        assert 0.0 <= ctx.confidence <= 1.0

    def test_fused_sentiment_valid_values(self):
        ctx = self.fusion.fuse("ngon quá đắt")
        assert ctx.fused_sentiment in ("positive", "negative", "neutral", "mixed")
