"""
Mi Miền Tây Intelligence System

A living Southern Vietnamese human communication & emotional culture system.
NOT a dictionary — understands wording, rhythm, emotional tone, social softness,
humor, hidden intent, regional slang, and cultural warmth.

Usage:
    engine = MienTayEngine()
    ctx = engine.analyze("mèn đét ơi nóng dữ thần")
    guidance = ctx.build_guidance()    # inject into LLM system prompt
    reply = engine.shape(raw_reply, ctx)  # shape Mi's response
"""
from __future__ import annotations

import logging

from app.mi.mien_tay.analyzer import MienTayContext, analyze, normalize_mien_tay
from app.mi.mien_tay.response import shape, build_response_examples
from app.mi.mien_tay.data import (
    DIALECT_MARKERS, SLANG, REACTIONS, SOFT_NEGOTIATION,
    HUMOR_MARKERS, SOCIAL_WARMTH, FOOD_CULTURE,
    EmotionalSignal, ResponseTone,
)

logger = logging.getLogger(__name__)

__all__ = [
    "MienTayEngine",
    "MienTayContext",
]


class MienTayEngine:
    """
    Single integration point for Miền Tây cultural intelligence.

    Covers:
    - Dialect detection (score 0.0–1.0)
    - Emotional graph (surprise, fatigue, humor, warmth, soft-negotiation...)
    - Exaggeration detection (don't interpret literally)
    - Response tone shaping (empathetic, playful, soft, warm)
    - Authentic Southern warmth suffix injection
    - LLM guidance string generation
    """

    def __init__(self) -> None:
        logger.info(
            "MienTayEngine initialized — %d slang entries, %d reactions, "
            "%d soft-negotiation patterns, %d humor markers",
            len(SLANG), len(REACTIONS), len(SOFT_NEGOTIATION), len(HUMOR_MARKERS),
        )

    def analyze(self, text: str) -> MienTayContext:
        """
        Full analysis pipeline for a user message.

        Returns MienTayContext. If is_mien_tay=False, no Southern dialect detected.

        Examples:
            "mèn đét ơi nóng dữ thần"
            → is_mien_tay=True, is_reaction=True, is_exaggeration=True,
              dominant_signal=SURPRISE, emotional_intensity=0.85

            "hông ấy mình đi cafe hông"
            → is_mien_tay=True, is_soft_negotiation=True,
              response_tone=SOFT, desired_pace=slow

            "hay vầy đi"
            → is_mien_tay=True, is_soft_negotiation=True,
              response_tone=SOFT
        """
        ctx = analyze(text)
        if ctx.is_mien_tay:
            logger.debug(
                "MienTay detected: score=%.0f%% intensity=%.0f%% "
                "signals=%s tone=%s exaggeration=%s",
                ctx.dialect_score * 100,
                ctx.emotional_intensity * 100,
                [s.value for s in ctx.signals],
                ctx.response_tone.value,
                ctx.is_exaggeration,
            )
        return ctx

    def shape(self, raw_reply: str, ctx: MienTayContext) -> str:
        """
        Shape a raw LLM reply through Miền Tây warmth engine.
        - Enforces length limits for fatigue/soft-negotiation
        - Adds authentic Southern warmth suffix
        - Applies tone prefix for high-intensity emotional states
        """
        return shape(raw_reply, ctx)

    def build_llm_guidance(self, ctx: MienTayContext) -> str:
        """
        Full guidance string for LLM injection (system prompt layer).
        Includes emotional graph interpretation + response examples.
        """
        guidance = ctx.build_guidance()
        examples = build_response_examples(ctx)
        parts = [p for p in [guidance, examples] if p]
        return "\n\n".join(parts)

    def normalize(self, text: str) -> str:
        """Normalize Miền Tây text for intent detection."""
        return normalize_mien_tay(text)
