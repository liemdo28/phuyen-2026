from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from app.conversation.context_window import ContextWindow
from app.conversation.expense_merger import ExpenseMerger
from app.conversation.intent_continuation import IntentContinuation
from app.conversation.temporal_memory import ExpenseSession, TemporalMemory
from app.conversation.topic_resolver import TopicResolver

SessionAction = Literal[
    "collecting",      # added fragment, still accumulating
    "inferred",        # enough data — show confirmation message
    "confirmed",       # user confirmed → ready to commit
    "rejected",        # user rejected → session cancelled
    "expired",         # window closed — session evicted
    "ignored",         # commentary absorbed, no reply needed
    "new_session",     # old session closed, new one started
    "no_session",      # irrelevant message, nothing to do
]


@dataclass
class SessionResult:
    action: SessionAction
    session: ExpenseSession | None
    reply: str | None           # message to send to user (may be None)
    ready_to_commit: bool = False


_INFER_THRESHOLD = 0.45         # confidence floor to show confirmation
_INFER_FRAGMENTS_MIN = 1        # minimum fragments before trying to infer


class ExpenseSessionEngine:
    """
    Main entry point for the conversational expense memory system.

    Call `process(text, chat_id, user_id, image_fragments)` on every
    incoming message.  Returns a SessionResult that tells the orchestrator
    what happened and whether a reply is needed.
    """

    def __init__(self) -> None:
        self.memory = TemporalMemory()
        self.merger = ExpenseMerger()
        self.continuation = IntentContinuation()
        self.context_window = ContextWindow()
        self.resolver = TopicResolver()

    def process(
        self,
        text: str,
        chat_id: int,
        user_id: int,
        image_fragments: list[dict] | None = None,
        now: datetime | None = None,
    ) -> SessionResult:
        now = now or datetime.now(timezone.utc)
        image_fragments = image_fragments or []

        session = self.memory.get(chat_id, user_id)
        decision = self.continuation.decide(text, session, now)

        # --- expired -------------------------------------------------------
        if decision == "close_expired":
            if session:
                self.memory.close(chat_id, user_id)
            # If the new message is expense-relevant, start fresh
            if self.resolver.is_expense_relevant(text):
                return self._start_new_session(text, chat_id, user_id, image_fragments, now)
            return SessionResult(action="expired", session=None, reply=None)

        # --- ignore (commentary) -------------------------------------------
        if decision == "ignore":
            if session:
                session.pending_irrelevant_count += 1
                self.memory.save(session)
            return SessionResult(action="ignored", session=session, reply=None)

        # --- no active session + non-expense text --------------------------
        if decision == "ignore" and session is None:
            return SessionResult(action="no_session", session=None, reply=None)

        # --- confirmation --------------------------------------------------
        if decision == "confirm_session" and session:
            return self._handle_confirmation(session, chat_id, user_id)

        # --- rejection -----------------------------------------------------
        if decision == "reject_session" and session:
            return self._handle_rejection(session, chat_id, user_id)

        # --- new session (topic changed or nothing active) -----------------
        if decision == "new_session":
            if session:
                self.memory.close(chat_id, user_id)
            return self._start_new_session(text, chat_id, user_id, image_fragments, now)

        # --- continue existing session -------------------------------------
        if decision == "continue_session" and session:
            return self._accumulate(text, session, image_fragments, now)

        # --- first message (no session yet, expense-relevant) --------------
        return self._start_new_session(text, chat_id, user_id, image_fragments, now)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _start_new_session(
        self,
        text: str,
        chat_id: int,
        user_id: int,
        image_fragments: list[dict],
        now: datetime,
    ) -> SessionResult:
        session = self.memory.open(chat_id, user_id)
        session.fragments.append(text)
        session.image_fragments.extend(image_fragments)
        session.source = "image+chat" if image_fragments else "chat"
        self.memory.save(session)

        result = self._try_infer(session)
        if result:
            return result
        return SessionResult(action="collecting", session=session, reply=None)

    def _accumulate(
        self,
        text: str,
        session: ExpenseSession,
        image_fragments: list[dict],
        now: datetime,
    ) -> SessionResult:
        session.fragments.append(text)
        session.image_fragments.extend(image_fragments)
        if image_fragments:
            session.source = "image+chat"
        session.pending_irrelevant_count = 0  # reset on real expense fragment
        self.memory.save(session)

        result = self._try_infer(session)
        if result:
            return result
        return SessionResult(action="collecting", session=session, reply=None)

    def _try_infer(self, session: ExpenseSession) -> SessionResult | None:
        """Attempt to infer a structured expense from current fragments."""
        if len(session.fragments) < _INFER_FRAGMENTS_MIN:
            return None

        merge = self.merger.merge(session)
        session.amount = merge.amount
        session.category = merge.category
        session.subcategory = merge.subcategory
        session.meal_type = merge.meal_type
        session.location = merge.location
        session.description = merge.description
        session.confidence = merge.confidence
        session.ambiguity = merge.ambiguity
        session.confirmation_message = merge.confirmation_message

        if merge.confidence >= _INFER_THRESHOLD:
            session.state = "inferred"
            session.summary_shown = True
            self.memory.save(session)
            return SessionResult(
                action="inferred",
                session=session,
                reply=merge.confirmation_message,
            )

        self.memory.save(session)
        return None

    def _handle_confirmation(self, session: ExpenseSession, chat_id: int, user_id: int) -> SessionResult:
        session.state = "confirmed"
        self.memory.save(session)
        reply = "Mình đã ghi lại rồi nhé! ✓"
        return SessionResult(
            action="confirmed",
            session=session,
            reply=reply,
            ready_to_commit=True,
        )

    def _handle_rejection(self, session: ExpenseSession, chat_id: int, user_id: int) -> SessionResult:
        session.state = "cancelled"
        self.memory.close(chat_id, user_id)
        reply = "Ok, mình bỏ qua khoản này nhé."
        return SessionResult(action="rejected", session=None, reply=reply)

    def commit(self, chat_id: int, user_id: int) -> ExpenseSession | None:
        """Mark the confirmed session as committed and evict it."""
        session = self.memory.get(chat_id, user_id)
        if session and session.state == "confirmed":
            session.state = "committed"
            self.memory.close(chat_id, user_id)
            return session
        return None
