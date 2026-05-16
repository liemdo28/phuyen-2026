"""
Miền Tây Response Shaper

Takes a raw LLM reply and shapes it with authentic Southern Vietnamese warmth:
- Correct warmth suffixes (nhen, nha, hen, heng)
- Tone calibration based on MienTayContext
- Length enforcement for fatigue/soft-negotiation contexts
- Authentic phrasing injection
"""
from __future__ import annotations

import random
import re

from app.mi.mien_tay.analyzer import MienTayContext
from app.mi.mien_tay.data import ResponseTone, WARMTH_SUFFIXES


# ── Authentic Mi Southern phrases ─────────────────────────────────────────────
# These are natural Southern Vietnamese phrases Mi can use in responses

_EMPATHY_PHRASES = [
    "Nghe có vẻ mệt rồi nhen,",
    "Ừ mệt kiểu đó rồi thì",
    "Thôi nghỉ đi bạn ơi,",
    "Hiểu rồi, kiểu đó mệt thiệt,",
]

_SOFT_RESPONSE_STARTERS = [
    "Hay vầy nhen,",
    "Thử cái này coi,",
    "Hay mình thử",
    "Để coi nhen,",
    "Ừ thì",
]

_PLAYFUL_STARTERS = [
    "Haha",
    "Ừa",
    "Ủa",
    "Trời ơi 😄",
]

_WARMTH_CLOSINGS: dict[str, list[str]] = {
    "casual":     ["nhen 😊", "nha", "hen", "heng"],
    "warm":       ["nhen bạn ơi 😊", "nha nhen", "nhen ơi"],
    "soft":       ["nha", "hen", "nghen"],
    "playful":    ["nhen 😄", "hehe", "nhen ơi 😄"],
    "empathetic": ["nhen", "nha bạn", "nghen"],
}


def _already_has_southern_ending(text: str) -> bool:
    """Check if reply already ends with a Southern warmth particle."""
    t = text.strip().lower()
    southern_endings = [
        "nhen", "nhen 😊", "nhen 😄", "nha", "hen", "heng", "nghen",
        "nhen ơi", "nha bạn", "nhen bạn ơi",
    ]
    for ending in southern_endings:
        if t.endswith(ending):
            return True
    return False


def _add_warmth_suffix(text: str, ctx: MienTayContext) -> str:
    """Add an authentic Southern warmth suffix if not already present."""
    if _already_has_southern_ending(text):
        return text

    text = text.rstrip(".")

    # Pick suffix category based on tone
    tone_map = {
        ResponseTone.WARM_CASUAL:  "casual",
        ResponseTone.PLAYFUL:      "playful",
        ResponseTone.SOFT:         "soft",
        ResponseTone.EMPATHETIC:   "empathetic",
        ResponseTone.LAI_RAI:      "warm",
        ResponseTone.TEASING:      "playful",
    }
    category = tone_map.get(ctx.response_tone, "casual")
    choices = _WARMTH_CLOSINGS.get(category, ["nhen"])
    suffix = random.choice(choices)

    return f"{text} {suffix}"


def _enforce_length_for_fatigue(text: str, ctx: MienTayContext) -> str:
    """
    Shorten response when user is fatigued.
    Miền Tây fatigue = real rest needed, don't overwhelm.
    """
    if not ctx.is_fatigue:
        return text

    if ctx.emotional_intensity > 0.80:
        # Extreme: max 1 sentence
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if sentences:
            return sentences[0]
        return text[:120]

    if ctx.emotional_intensity > 0.60:
        # High: max 2 sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return " ".join(sentences[:2])

    return text


def _enforce_soft_negotiation_length(text: str, ctx: MienTayContext) -> str:
    """
    Soft negotiation = don't overwhelm.
    Keep response brief and option-free.
    """
    if not ctx.is_soft_negotiation:
        return text

    sentences = re.split(r"(?<=[.!?])\s+", text)
    # Max 2 sentences for soft negotiation
    return " ".join(sentences[:2])


def _apply_tone_prefix(text: str, ctx: MienTayContext) -> str:
    """
    Optionally prepend a tone-matching opener for certain emotional states.
    Applied sparingly — only when it adds authenticity.
    """
    if ctx.is_fatigue and ctx.emotional_intensity > 0.70:
        # Only add if text doesn't start with empathy already
        empathy_starters = ["mệt", "nghỉ", "ừ", "thôi", "biết rồi", "hiểu"]
        first_word = text.strip().lower().split()[0] if text.strip() else ""
        if not any(first_word.startswith(s) for s in empathy_starters):
            opener = random.choice(_EMPATHY_PHRASES)
            return f"{opener} {text[0].lower()}{text[1:]}"

    return text


def shape(text: str, ctx: MienTayContext) -> str:
    """
    Full Miền Tây response shaping pipeline.

    1. Length enforcement (fatigue / soft negotiation)
    2. Tone prefix injection
    3. Warmth suffix
    """
    if not ctx.is_mien_tay:
        return text

    text = _enforce_length_for_fatigue(text, ctx)
    text = _enforce_soft_negotiation_length(text, ctx)
    text = _apply_tone_prefix(text, ctx)
    text = _add_warmth_suffix(text, ctx)

    return text


def build_response_examples(ctx: MienTayContext) -> str:
    """
    Build example response guidance for LLM based on detected context.
    Injected into system prompt to show Mi what a good response looks like.
    """
    if not ctx.is_mien_tay:
        return ""

    examples = []

    if ctx.is_fatigue and ctx.emotional_intensity > 0.75:
        examples.append(
            'EXAMPLE — fatigue response: "Mệt dữ rồi thì nghỉ đi, đừng ép. '
            'Cafe gần đây ngồi nhâm nhi cũng được nhen."'
        )
    elif ctx.is_soft_negotiation:
        examples.append(
            'EXAMPLE — soft negotiation: "Hay vầy nhen, mình thử [option] coi. '
            'Bạn thấy sao?"'
        )
    elif ctx.is_humor:
        examples.append(
            'EXAMPLE — humor response: "Haha cái đó lầy thiệt 😄 '
            'Thôi thì [light suggestion] cho đỡ nhen."'
        )
    elif ctx.is_drinking_culture:
        examples.append(
            'EXAMPLE — lai rai: "Ừ lai rai thì [local spot] được lắm — '
            'mồi tươi, giá tốt, ngồi chill nhen."'
        )

    return "\n".join(examples)
