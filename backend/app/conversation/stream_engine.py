"""
General multi-topic Conversation Stream Engine for the Vietnamese AI travel companion.

Tracks ALL message types across topics: expense, navigation, recommendation, social.
Sentiment signals (crowded, positive, negative, etc.) are absorbed into the active
thread's metadata rather than creating new threads.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Topic = Literal["expense", "navigation", "recommendation", "social", "unknown"]

MessageType = Literal[
    "expense_fragment",
    "sentiment_signal",
    "topic_change",
    "navigation_intent",
    "recommendation_intent",
    "question",
    "confirmation",
    "rejection",
]

ThreadState = Literal["active", "paused", "resolved"]

# Per-topic timeout in seconds
_THREAD_TIMEOUT: dict[str, int] = {
    "expense": 180,
    "navigation": 300,
    "recommendation": 300,
    "social": 300,
    "unknown": 180,
}

# ---------------------------------------------------------------------------
# Signal lexicons  (Vietnamese-aware)
# ---------------------------------------------------------------------------

_CROWDED_SIGNALS = [
    "đông ghê", "đông thật", "đông vãi", "đông quá", "nhiều người",
    "đông lắm", "chật", "đông người",
]
_POSITIVE_SIGNALS = [
    "mà ngon", "ngon quá", "ngon lắm", "ngon", "tuyệt vời", "tuyệt",
    "hay quá", "hay lắm", "hay", "đẹp quá", "đẹp lắm", "đẹp",
    "thích lắm", "thích", "ok lắm", "ổn lắm", "quán ổn",
]
_NEGATIVE_SIGNALS = [
    "không ngon", "dở quá", "dở lắm", "dở", "tệ quá", "tệ lắm", "tệ",
    "không thích", "chán", "không ổn",
]
_EXPENSIVE_SIGNALS = [
    "mắc quá", "mắc lắm", "mắc", "đắt quá", "đắt lắm", "đắt",
    "chặt chém", "cắt cổ",
]
_CHEAP_SIGNALS = [
    "rẻ quá", "rẻ lắm", "rẻ", "ok giá", "hợp lý", "bình thường",
    "giá ổn", "giá phải chăng",
]
_NOISY_SIGNALS = ["ồn quá", "ồn ào", "ồn lắm", "ồn", "náo nhiệt"]
_QUIET_SIGNALS = ["yên tĩnh", "chill", "thoải mái", "yên", "vắng"]
_FATIGUE_SIGNALS = ["mệt quá", "mệt lắm", "mệt", "mỏi", "kiệt sức"]

# Expense-related tokens (multi-char, safe for substring matching)
_EXPENSE_TOKENS = [
    "đồng", "trăm", "triệu", "vnd", "vnđ",
    "ăn", "uống", "mua", "trả", "thanh toán", "tính tiền",
    "cafe", "cà phê", "hải sản", "cơm", "bún", "phở", "bánh", "trà",
    "xăng", "grab", "taxi", "uber",
    "khách sạn", "resort", "phòng", "thuê",
    "siêu thị", "shop", "mua sắm", "chợ",
    "bill", "hoá đơn", "hóa đơn",
    "bữa sáng", "bữa trưa", "bữa tối", "ăn trưa", "ăn sáng", "ăn tối",
    "nhà hàng",
    "chi phí",
]
# Tokens requiring word-boundary matching to avoid false positives
_EXPENSE_WORD_TOKENS_RE = re.compile(
    r"\b(k|tiền|chi|xe|quán|trưa|tối|sáng|chiều)\b", re.IGNORECASE
)
_CURRENCY_SUFFIX = re.compile(r"\d\s*đ\b", re.IGNORECASE)
# Tokens that flag STRONG expense intent (actions + currency) — used to distinguish
# from pure location/context words like "quán" alone in a sentiment phrase.
_STRONG_EXPENSE_TOKENS = [
    "đồng", "triệu", "vnd", "vnđ",
    "ăn", "uống", "mua", "trả", "thanh toán", "tính tiền",
    "cafe", "cà phê", "hải sản", "cơm", "bún", "phở", "xăng", "grab", "taxi", "uber",
    "khách sạn", "resort", "siêu thị", "bill", "hoá đơn", "hóa đơn", "chi phí",
    "bữa sáng", "bữa trưa", "bữa tối", "ăn trưa", "ăn sáng", "ăn tối",
]
_STRONG_EXPENSE_WORD_RE = re.compile(r"\b(tiền|chi)\b", re.IGNORECASE)
_NUMBER_K_RE = re.compile(r"\d+\s*k\b", re.IGNORECASE)

# Navigation intent tokens
_NAVIGATION_TOKENS = [
    "đi đâu", "đường đến", "cách đi", "gần đây có gì", "gần đây",
    "bản đồ", "chỉ đường", "google map", "map",
    "đi tới", "từ đây đến", "cách bao xa", "mấy km",
    "đi như thế nào", "xe bus", "xe ôm",
]

# Recommendation intent tokens
_RECOMMENDATION_TOKENS = [
    "gợi ý", "recommend", "tư vấn", "chỗ nào ngon", "chỗ nào tắm biển",
    "chỗ nào", "nơi nào", "quán nào", "ăn gì", "uống gì",
    "nên đi đâu", "nên ăn gì", "hay nhất", "nổi tiếng",
    "review", "đánh giá", "top", "best",
]

# Question tokens
_QUESTION_TOKENS = [
    "mấy giờ", "bao nhiêu tiền", "bao nhiêu", "khi nào",
    "tại sao", "vì sao", "làm sao", "như thế nào",
    "là gì", "ở đâu", "ai", "?",
]

# Confirmation tokens
_CONFIRM_TOKENS = [
    "đúng", "đúng rồi", "ừ", "ừm", "ok", "được", "chính xác",
    "vâng", "yes", "y", "đúng vậy", "ghi đi", "save", "xác nhận",
]

# Rejection tokens
_REJECT_TOKENS = [
    "không phải", "sai rồi", "không đúng",
    "không", "sai", "hủy", "cancel", "thôi không", "bỏ", "xóa", "delete",
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ConversationThread:
    thread_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    chat_id: int = 0
    user_id: int = 0
    topic: Topic = "unknown"
    fragments: list[str] = field(default_factory=list)
    sentiment_signals: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: ThreadState = "active"

    def touch(self, now: datetime) -> None:
        self.updated_at = now

    def age_seconds(self, now: datetime) -> float:
        return (now - self.updated_at).total_seconds()

    def is_expired(self, now: datetime) -> bool:
        timeout = _THREAD_TIMEOUT.get(self.topic, 180)
        return self.age_seconds(now) > timeout


@dataclass
class StreamResult:
    thread: ConversationThread | None
    message_type: MessageType
    absorbed: bool           # True when signal was merged into existing thread
    reply_hint: str | None   # suggested Vietnamese reply, may be None


# ---------------------------------------------------------------------------
# Internal thread store (one active + one paused per (chat_id, user_id))
# ---------------------------------------------------------------------------

class _ThreadStore:
    def __init__(self) -> None:
        # active thread
        self._active: dict[tuple[int, int], ConversationThread] = {}
        # paused thread (saves last paused thread for interruption recovery)
        self._paused: dict[tuple[int, int], ConversationThread] = {}

    def key(self, chat_id: int, user_id: int) -> tuple[int, int]:
        return (chat_id, user_id)

    def get_active(self, chat_id: int, user_id: int) -> ConversationThread | None:
        return self._active.get(self.key(chat_id, user_id))

    def get_paused(self, chat_id: int, user_id: int) -> ConversationThread | None:
        return self._paused.get(self.key(chat_id, user_id))

    def set_active(self, thread: ConversationThread) -> None:
        self._active[self.key(thread.chat_id, thread.user_id)] = thread

    def pause_active(self, chat_id: int, user_id: int) -> None:
        t = self._active.pop(self.key(chat_id, user_id), None)
        if t:
            t.state = "paused"
            self._paused[self.key(chat_id, user_id)] = t

    def clear_paused(self, chat_id: int, user_id: int) -> None:
        self._paused.pop(self.key(chat_id, user_id), None)

    def resume_paused(self, chat_id: int, user_id: int) -> ConversationThread | None:
        t = self._paused.pop(self.key(chat_id, user_id), None)
        if t:
            t.state = "active"
            self._active[self.key(chat_id, user_id)] = t
        return t

    def resolve_active(self, chat_id: int, user_id: int) -> None:
        t = self._active.pop(self.key(chat_id, user_id), None)
        if t:
            t.state = "resolved"

    def remove_active(self, chat_id: int, user_id: int) -> None:
        self._active.pop(self.key(chat_id, user_id), None)


# ---------------------------------------------------------------------------
# Signal detection helpers
# ---------------------------------------------------------------------------

def _contains_any(text: str, signals: list[str]) -> bool:
    t = text.lower()
    return any(s in t for s in signals)


def _is_expense_fragment(text: str) -> bool:
    t = text.lower().strip()
    if _contains_any(t, _EXPENSE_TOKENS):
        return True
    if _EXPENSE_WORD_TOKENS_RE.search(t):
        return True
    if _CURRENCY_SUFFIX.search(t):
        return True
    if _NUMBER_K_RE.search(t):
        return True
    # bare number like "500000"
    cleaned = re.sub(r"[,\. ]", "", t)
    if cleaned.isdigit() and len(cleaned) >= 4:
        return True
    return False


def _has_strong_expense_signal(text: str) -> bool:
    """True when text carries unmistakable expense intent beyond location nouns."""
    t = text.lower().strip()
    if _contains_any(t, _STRONG_EXPENSE_TOKENS):
        return True
    if _STRONG_EXPENSE_WORD_RE.search(t):
        return True
    if _NUMBER_K_RE.search(t):
        return True
    if _CURRENCY_SUFFIX.search(t):
        return True
    cleaned = re.sub(r"[,\. ]", "", t)
    if cleaned.isdigit() and len(cleaned) >= 4:
        return True
    return False


def _detect_sentiment_metadata(text: str) -> dict:
    """Return metadata dict for all matched sentiment signals in text."""
    meta: dict = {}
    if _contains_any(text, _CROWDED_SIGNALS):
        meta["crowded"] = True
    if _contains_any(text, _POSITIVE_SIGNALS):
        meta["positive_sentiment"] = True
    if _contains_any(text, _NEGATIVE_SIGNALS):
        meta["negative_sentiment"] = True
    if _contains_any(text, _EXPENSIVE_SIGNALS):
        meta["expensive"] = True
    if _contains_any(text, _CHEAP_SIGNALS):
        meta["cheap"] = True
    if _contains_any(text, _NOISY_SIGNALS):
        meta["noisy"] = True
    if _contains_any(text, _QUIET_SIGNALS):
        meta["quiet"] = True
    if _contains_any(text, _FATIGUE_SIGNALS):
        meta["fatigue_high"] = True
    return meta


def _is_pure_sentiment_signal(text: str) -> bool:
    """True if text contains only sentiment signals and NO strong expense/navigation/etc.

    Weak expense tokens like 'quán' (location noun) by themselves do NOT block
    the pure-sentiment classification — only STRONG expense signals do.
    """
    has_sentiment = bool(_detect_sentiment_metadata(text))
    if not has_sentiment:
        return False
    # If it also carries STRONG expense intent it's an expense fragment, not just sentiment
    if _has_strong_expense_signal(text):
        return False
    return True


def _classify_message(text: str, active_thread: ConversationThread | None) -> MessageType:
    """Classify a message into one of the MessageType literals.

    Priority order (highest → lowest):
      1. Confirmation / rejection (with active thread)
      2. Navigation intent
      3. Recommendation intent  ← before pure sentiment to catch "chỗ nào ngon"
      4. Question               ← before expense to catch "bao nhiêu tiền", "?"
      5. Pure sentiment signal  ← after recommendation so that "chỗ nào ngon" → rec
      6. Expense fragment
      7. Default expense
    """
    t = text.lower().strip()

    # 1. Confirmation/rejection (only meaningful when there's an active thread)
    if active_thread:
        if _contains_any(t, _CONFIRM_TOKENS):
            return "confirmation"
        if _contains_any(t, _REJECT_TOKENS):
            return "rejection"

    # 2. Navigation intent (check before expense as "gần đây" beats expense)
    if _contains_any(t, _NAVIGATION_TOKENS):
        return "navigation_intent"

    # 3. Recommendation intent (before pure sentiment, "chỗ nào ngon" → rec)
    if _contains_any(t, _RECOMMENDATION_TOKENS):
        return "recommendation_intent"

    # 4. Question — before expense to handle "bao nhiêu tiền", "mấy giờ", "?"
    if _contains_any(t, _QUESTION_TOKENS):
        return "question"

    # 5. Pure sentiment signal
    if _is_pure_sentiment_signal(t):
        return "sentiment_signal"

    # 6. Expense fragment
    if _is_expense_fragment(t):
        return "expense_fragment"

    # Topic change — check if it's a shift away from current topic
    if active_thread and active_thread.topic == "expense":
        if _contains_any(t, _NAVIGATION_TOKENS + _RECOMMENDATION_TOKENS):
            return "topic_change"

    # Default: treat as expense fragment if no other signal
    return "expense_fragment"


def _topic_for_message_type(msg_type: MessageType) -> Topic:
    mapping: dict[MessageType, Topic] = {
        "expense_fragment": "expense",
        "navigation_intent": "navigation",
        "recommendation_intent": "recommendation",
        "sentiment_signal": "social",
        "question": "unknown",
        "topic_change": "unknown",
        "confirmation": "unknown",
        "rejection": "unknown",
    }
    return mapping.get(msg_type, "unknown")


def _build_reply_hint(thread: ConversationThread, msg_type: MessageType, absorbed: bool) -> str | None:
    if absorbed:
        return None  # silently absorbed; no reply needed
    if msg_type == "expense_fragment":
        if thread.fragments:
            return None  # accumulating; reply only when inferred
    if msg_type == "confirmation":
        return "Mình đã ghi lại rồi nhé!"
    if msg_type == "rejection":
        return "Ok, mình bỏ qua khoản này nhé."
    if msg_type == "navigation_intent":
        return "Bạn muốn đi đâu vậy?"
    if msg_type == "recommendation_intent":
        return "Mình sẽ gợi ý cho bạn nhé!"
    return None


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class StreamEngine:
    """
    General multi-topic conversation stream.

    Call `process(text, chat_id, user_id, now)` on every incoming message.
    Returns a StreamResult describing what happened.
    """

    def __init__(self) -> None:
        self._store = _ThreadStore()

    def process(
        self,
        text: str,
        chat_id: int,
        user_id: int,
        now: datetime | None = None,
    ) -> StreamResult:
        now = now or datetime.now(timezone.utc)

        active = self._store.get_active(chat_id, user_id)
        paused = self._store.get_paused(chat_id, user_id)

        # Expire active thread if timed out
        if active and active.is_expired(now):
            self._store.remove_active(chat_id, user_id)
            active = None

        msg_type = _classify_message(text, active)

        # --- Sentiment signal on active thread: absorb silently ---
        if msg_type == "sentiment_signal" and active:
            meta = _detect_sentiment_metadata(text)
            active.metadata.update(meta)
            active.sentiment_signals.append(text)
            active.touch(now)
            self._store.set_active(active)
            return StreamResult(
                thread=active,
                message_type=msg_type,
                absorbed=True,
                reply_hint=None,
            )

        # --- Confirmation on active thread ---
        if msg_type == "confirmation" and active:
            active.state = "resolved"
            self._store.resolve_active(chat_id, user_id)
            return StreamResult(
                thread=active,
                message_type=msg_type,
                absorbed=False,
                reply_hint="Mình đã ghi lại rồi nhé!",
            )

        # --- Rejection on active thread ---
        if msg_type == "rejection" and active:
            active.state = "resolved"
            self._store.resolve_active(chat_id, user_id)
            return StreamResult(
                thread=active,
                message_type=msg_type,
                absorbed=False,
                reply_hint="Ok, mình bỏ qua khoản này nhé.",
            )

        # --- Topic matches active thread: continue accumulating ---
        new_topic = _topic_for_message_type(msg_type)
        if active and new_topic == active.topic and new_topic != "unknown":
            meta = _detect_sentiment_metadata(text)
            if meta:
                active.metadata.update(meta)
                active.sentiment_signals.append(text)
            active.fragments.append(text)
            active.touch(now)
            self._store.set_active(active)
            return StreamResult(
                thread=active,
                message_type=msg_type,
                absorbed=False,
                reply_hint=_build_reply_hint(active, msg_type, False),
            )

        # --- Topic changed: check if paused thread matches new topic ---
        if active and new_topic != active.topic and new_topic != "unknown":
            # Check if the paused thread matches the incoming topic FIRST.
            # If so, we resume it directly; the current active thread gets dropped.
            # If not, we pause the current active thread (overwriting any old paused thread).
            if paused and new_topic == paused.topic and not paused.is_expired(now):
                # Drop current active thread (don't save it — it would overwrite paused)
                self._store.remove_active(chat_id, user_id)
                active = None
            else:
                # Pause current active thread (overwrites old paused)
                self._store.pause_active(chat_id, user_id)
                active = None  # reset local ref

        # Check if paused thread matches new topic → resume it
        if paused and new_topic == paused.topic and new_topic != "unknown":
            # Expire check on paused thread too
            if not paused.is_expired(now):
                self._store.resume_paused(chat_id, user_id)
                active = self._store.get_active(chat_id, user_id)
                if active:
                    active.fragments.append(text)
                    active.touch(now)
                    self._store.set_active(active)
                    return StreamResult(
                        thread=active,
                        message_type=msg_type,
                        absorbed=False,
                        reply_hint=_build_reply_hint(active, msg_type, False),
                    )
            else:
                self._store.clear_paused(chat_id, user_id)

        # --- Start a new thread ---
        thread = ConversationThread(
            chat_id=chat_id,
            user_id=user_id,
            topic=new_topic if new_topic != "unknown" else "expense",
            created_at=now,
            updated_at=now,
        )
        meta = _detect_sentiment_metadata(text)
        if meta:
            thread.metadata.update(meta)
            thread.sentiment_signals.append(text)
        thread.fragments.append(text)
        self._store.set_active(thread)

        return StreamResult(
            thread=thread,
            message_type=msg_type,
            absorbed=False,
            reply_hint=_build_reply_hint(thread, msg_type, False),
        )

    def get_active_thread(self, chat_id: int, user_id: int) -> ConversationThread | None:
        return self._store.get_active(chat_id, user_id)

    def get_paused_thread(self, chat_id: int, user_id: int) -> ConversationThread | None:
        return self._store.get_paused(chat_id, user_id)
