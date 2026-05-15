from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from app.conversation.context_window import ContextWindow
from app.conversation.temporal_memory import ExpenseSession, TemporalMemory
from app.conversation.topic_resolver import TopicResolver

ContinuationDecision = Literal[
    "continue_session",   # add fragment to existing session
    "new_session",        # close old session, start fresh
    "ignore",             # commentary — absorb without breaking
    "confirm_session",    # user confirmed the inferred expense
    "reject_session",     # user rejected the inferred expense
    "close_expired",      # session timed out
]


class IntentContinuation:
    """
    Decides what to do with an incoming message relative to the active session:
    - Is this a continuation of the current expense thread?
    - Should we start a new session?
    - Is this confirmation/rejection of a pending summary?
    - Is the session expired and should be closed silently?
    """

    def __init__(self) -> None:
        self.resolver = TopicResolver()
        self.context_window = ContextWindow()
        self.memory = TemporalMemory()

    def decide(
        self,
        text: str,
        session: ExpenseSession | None,
        now: datetime | None = None,
    ) -> ContinuationDecision:
        now = now or datetime.now(timezone.utc)

        # No active session → only start one if text is expense-relevant
        if session is None:
            if self.resolver.is_expense_relevant(text):
                return "new_session"
            return "ignore"

        # Check session expiry first
        if not self.context_window.is_within_window(session, now):
            return "close_expired"

        # Resolve what kind of message this is
        topic = self.resolver.resolve(text, session)

        if topic == "confirmation":
            return "confirm_session"

        if topic == "rejection":
            return "reject_session"

        if topic == "expense":
            return "continue_session"

        if topic == "commentary":
            if self.context_window.can_absorb_commentary(session):
                return "ignore"
            # Too many ignored messages → treat as topic change
            return "close_expired"

        if topic == "topic_change":
            return "new_session"

        # Default: keep accumulating
        return "continue_session"
