"""
Mi Human Presence System.

Transforms Mi from "smart AI" into "emotionally present companion".
The user should feel: emotionally accompanied, naturally understood,
mentally lighter, less alone during travel/stress/chaos.
"""
from __future__ import annotations
from app.mi.presence.state import (
    EmotionalSnapshot, PresenceContext, ResponsePace, SocialMode,
    FatigueLevel, LifePhase,
)
from app.mi.presence.orchestrator import build_presence_context
from app.mi.presence import memory as emotional_memory

__all__ = [
    "EmotionalSnapshot",
    "PresenceContext",
    "ResponsePace",
    "SocialMode",
    "FatigueLevel",
    "LifePhase",
    "build_presence_context",
    "emotional_memory",
]
