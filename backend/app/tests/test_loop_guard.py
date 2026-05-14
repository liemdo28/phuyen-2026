from pathlib import Path
import tempfile

from app.core import config as config_module
from app.services.loop_guard import LoopGuard


def build_guard() -> LoopGuard:
    temp_dir = tempfile.mkdtemp(prefix="loop-guard-")
    object.__setattr__(config_module.settings, "state_dir", temp_dir)
    object.__setattr__(config_module.settings, "rate_limit_window_seconds", 10)
    object.__setattr__(config_module.settings, "rate_limit_max_messages", 4)
    object.__setattr__(config_module.settings, "repeated_text_limit", 2)
    return LoopGuard()


def test_duplicate_update_is_blocked() -> None:
    guard = build_guard()
    first = guard.evaluate(update_id=1001, message_id=11, chat_id=1, user_id=2, text="/start")
    second = guard.evaluate(update_id=1001, message_id=11, chat_id=1, user_id=2, text="/start")
    assert first.allow_processing is True
    assert second.allow_processing is False
    assert second.reason == "duplicate_update_id"


def test_repeated_text_is_suppressed() -> None:
    guard = build_guard()
    first = guard.evaluate(update_id=2001, message_id=21, chat_id=1, user_id=2, text="/start")
    second = guard.evaluate(update_id=2002, message_id=22, chat_id=1, user_id=2, text="/start")
    third = guard.evaluate(update_id=2003, message_id=23, chat_id=1, user_id=2, text="/start")
    assert first.allow_processing is True
    assert second.allow_processing is True
    assert third.allow_processing is False
    assert third.reason == "repeated_text_loop_protection"
