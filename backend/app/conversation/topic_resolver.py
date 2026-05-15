from __future__ import annotations

import re

from app.conversation.temporal_memory import ExpenseSession

# Signals that clearly indicate expense intent (keep session alive)
EXPENSE_SIGNALS = [
    "k", "đồng", "trăm", "triệu", "vnd", "vnđ",
    "ăn", "uống", "mua", "trả", "thanh toán", "tính tiền",
    "cafe", "cà phê", "hải sản", "cơm", "bún", "phở", "bánh", "trà",
    "xăng", "grab", "taxi", "xe", "gỗ", "uber",
    "khách sạn", "resort", "phòng", "thuê",
    "siêu thị", "shop", "mua sắm", "chợ",
    "bill", "hoá đơn", "hóa đơn", "receipt",
    "sáng", "trưa", "tối", "chiều", "đêm",
    "quán", "nhà hàng", "restaurant",
    "tiền", "chi", "chi phí",
]

# Signals that indicate a topic change away from expense
TOPIC_CHANGE_SIGNALS = [
    "đi đâu", "chỗ nào ngon", "thời tiết", "mưa", "nắng",
    "giờ nào", "lịch trình", "kế hoạch", "đặt phòng", "book",
    "gợi ý", "recommend", "bản đồ", "đường",
    "hỏi", "tư vấn", "giúp", "cần biết",
]

# Pure commentary / social filler — irrelevant to expense but shouldn't break session
COMMENTARY_MARKERS = [
    "đông ghê", "đông thật", "đẹp quá", "ngon quá", "đông vãi",
    "nhìn kìa", "ôi trời", "wow", "haha", "lol", "hihi",
    "ok", "ờ", "ừ thì", "thôi", "vậy", "thật à",
    "ý kiến", "bạn nghĩ sao",
]

# Confirmation tokens (user accepts the summary)
CONFIRM_TOKENS = [
    "đúng", "đúng rồi", "ừ", "ừm", "ok", "được", "chính xác",
    "vâng", "yes", "y", "đúng vậy", "ghi đi", "save",
]

# Rejection tokens (user rejects or cancels)
REJECT_TOKENS = [
    "không", "sai", "hủy", "cancel", "thôi không", "bỏ",
    "không phải", "không đúng", "xóa", "delete",
]


class TopicResolver:
    """
    Determines whether a new incoming message:
    - continues the active expense session (expense_relevant)
    - is irrelevant commentary (absorb silently)
    - signals a topic change (close session)
    - confirms or rejects a pending summary
    """

    # Matches currency suffix "đ" only when immediately preceded by a digit
    _CURRENCY_SUFFIX = re.compile(r"\d\s*đ\b", re.IGNORECASE)

    def is_expense_relevant(self, text: str, session: ExpenseSession | None = None) -> bool:
        t = text.lower().strip()
        if any(sig in t for sig in EXPENSE_SIGNALS):
            return True
        # "đ" as currency only when it follows a digit (e.g. "500đ"), not in words like "đông"
        if self._CURRENCY_SUFFIX.search(t):
            return True
        # Pure number message is expense-relevant (e.g. "350" or "350k")
        cleaned = t.replace(",", "").replace(".", "").replace("k", "").replace(" ", "")
        if cleaned.isdigit() and len(cleaned) >= 2:
            return True
        return False

    def is_commentary(self, text: str) -> bool:
        t = text.lower().strip()
        if any(m in t for m in COMMENTARY_MARKERS):
            return True
        # Very short messages with no expense signal are commentary
        if len(t) <= 15 and not self.is_expense_relevant(t):
            return True
        return False

    def is_topic_change(self, text: str) -> bool:
        t = text.lower().strip()
        # Must have explicit travel/non-expense intent AND no expense signals
        has_topic_change = any(sig in t for sig in TOPIC_CHANGE_SIGNALS)
        has_expense = self.is_expense_relevant(t)
        return has_topic_change and not has_expense

    def is_confirmation(self, text: str) -> bool:
        t = text.lower().strip()
        for tok in CONFIRM_TOKENS:
            if tok in t and ("không " + tok) not in t:
                return True
        return False

    def is_rejection(self, text: str) -> bool:
        t = text.lower().strip()
        return any(tok in t for tok in REJECT_TOKENS)

    def resolve(self, text: str, session: ExpenseSession | None) -> str:
        """
        Returns one of: expense | confirmation | rejection | commentary | topic_change | new_expense
        """
        if session and session.state == "inferred" and not session.summary_shown:
            # Session is ready to confirm — check for confirm/reject
            if self.is_confirmation(text):
                return "confirmation"
            if self.is_rejection(text):
                return "rejection"

        if session and session.state == "inferred" and session.summary_shown:
            if self.is_confirmation(text):
                return "confirmation"
            if self.is_rejection(text):
                return "rejection"

        if self.is_expense_relevant(text, session):
            return "expense"
        if self.is_topic_change(text):
            return "topic_change"
        if self.is_commentary(text):
            return "commentary"
        return "expense"  # default: treat as expense signal
