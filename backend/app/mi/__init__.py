"""
Mi — Human-like Vietnamese AI Companion Civilization System

NOT a chatbot. NOT a travel assistant.
A living, emotionally intelligent Vietnamese friend.

Exports:
  MiEngine — the single integration point for Mi's full system
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.mi.identity import MI_NAME, MI_SELF_PRONOUN, MI_DEFAULT_USER_PRONOUN
from app.mi.slang_engine import normalize_slang, detect_dialect
from app.mi.pronoun_engine import detect_pronoun_context, build_pronoun_guidance, PronounContext
from app.mi.emotion_engine import detect_emotion, build_emotion_guidance, EmotionState
from app.mi.response_engine import shape_response, get_dialect_warmth, MiResponse

logger = logging.getLogger(__name__)

__all__ = [
    "MiEngine",
    "MiContext",
    "MI_NAME",
]


@dataclass
class MiContext:
    """Full Mi context for a single message turn."""
    normalized_text: str
    dialect: str
    pronoun: PronounContext
    emotion: EmotionState
    pronoun_guidance: str
    emotion_guidance: str
    memory_context: str = ""

    def full_interaction_guidance(self) -> str:
        """Combined guidance block to inject into LLM system prompt."""
        parts = [self.pronoun_guidance, self.emotion_guidance]
        if self.memory_context:
            parts.append(self.memory_context)
        return "\n\n".join(p for p in parts if p)


class MiEngine:
    """
    Single integration point for Mi's full personality system.

    Usage:
        engine = MiEngine()
        ctx = engine.analyze("met vl, gan thoi nhen")
        # ctx.full_interaction_guidance() → inject into LLM system prompt
        # ctx.emotion.response_mode → drive response length
    """

    def __init__(self) -> None:
        logger.info("MiEngine initialized — Mi is alive 💫")

    def analyze(
        self,
        text: str,
        memory_context: str = "",
    ) -> MiContext:
        """
        Full analysis pipeline for a single user message.
        Returns MiContext with all adaptation signals ready.
        """
        # 1. Normalize slang / typos / no-accent
        normalized = normalize_slang(text)

        # 2. Detect dialect
        dialect = detect_dialect(text)  # use original (preserve miền Tây markers)

        # 3. Detect pronouns
        pronoun = detect_pronoun_context(text)

        # 4. Detect emotion
        emotion = detect_emotion(normalized)

        # 5. Build guidance strings for LLM injection
        pronoun_guidance = build_pronoun_guidance(pronoun)
        emotion_guidance = build_emotion_guidance(emotion)

        return MiContext(
            normalized_text=normalized,
            dialect=dialect,
            pronoun=pronoun,
            emotion=emotion,
            pronoun_guidance=pronoun_guidance,
            emotion_guidance=emotion_guidance,
            memory_context=memory_context,
        )

    def shape(
        self,
        raw_reply: str,
        ctx: MiContext,
        user_lat: float | None = None,
        user_lon: float | None = None,
        place_name: str | None = None,
        place_lat: float | None = None,
        place_lon: float | None = None,
    ) -> MiResponse:
        """
        Shape a raw LLM reply through Mi's response engine:
        - Enforce length limits
        - Add dialect warmth
        - Add Telegram buttons
        """
        response = shape_response(
            raw_reply=raw_reply,
            emotion=ctx.emotion,
            pronoun=ctx.pronoun,
            user_lat=user_lat,
            user_lon=user_lon,
            place_name=place_name,
            place_lat=place_lat,
            place_lon=place_lon,
        )
        # Apply dialect warmth
        response.text = get_dialect_warmth(ctx.dialect, response.text)
        return response

    def heuristic_reply(self, text: str) -> str:
        """
        Mi's built-in response when LLM is unavailable.
        Always warm, always Vietnamese, always Mi.
        """
        from app.adapters.llm import _heuristic_companion_reply
        return _heuristic_companion_reply(text)
