from __future__ import annotations

from datetime import datetime

from app.conversation.temporal_memory import ExpenseSession

# Window lengths in seconds
WINDOW_TIGHT = 30      # consecutive quick messages
WINDOW_DEFAULT = 120   # standard continuation
WINDOW_EXTENDED = 300  # image context extends window

# Max number of irrelevant commentary messages before breaking session
MAX_ABSORBED_COMMENTARY = 3


class ContextWindow:
    """
    Manages the time-based grouping window for expense sessions.
    Groups messages within a rolling time window, adjusting the window
    size based on session state and content type.
    """

    def effective_window(self, session: ExpenseSession) -> int:
        if session.image_fragments:
            return WINDOW_EXTENDED
        if session.state in ("inferred", "confirmed"):
            return WINDOW_DEFAULT
        return WINDOW_DEFAULT

    def is_within_window(self, session: ExpenseSession, now: datetime) -> bool:
        """True if the session is still within its active collection window."""
        window = self.effective_window(session)
        delta = (now - session.updated_at).total_seconds()
        return delta <= window

    def seconds_remaining(self, session: ExpenseSession, now: datetime) -> float:
        window = self.effective_window(session)
        delta = (now - session.updated_at).total_seconds()
        return max(0.0, window - delta)

    def is_near_expiry(self, session: ExpenseSession, now: datetime, threshold: float = 20.0) -> bool:
        """True if the session is about to expire (< threshold seconds remaining)."""
        return self.seconds_remaining(session, now) < threshold

    def can_absorb_commentary(self, session: ExpenseSession) -> bool:
        """True if the session can still absorb irrelevant commentary without breaking."""
        return session.pending_irrelevant_count < MAX_ABSORBED_COMMENTARY
