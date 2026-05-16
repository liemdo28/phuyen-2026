"""
Mi Pronoun Engine — Full Vietnamese social pronoun adaptation.

Mi dynamically adapts pronouns, tone, warmth, pacing, and energy
based on: age, social hierarchy, relationship distance, region, emotional state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class PronounRole(str, Enum):
    PEER = "peer"           # bạn/mình — same generation, equal
    YOUNGER = "younger"     # em — user treats Mi as older
    OLDER = "older"         # anh/chị/cô/chú/bác — user is older
    CASUAL = "casual"       # tao/mày — very informal
    INTIMATE = "intimate"   # ní/bro — Gen Z intimacy
    UNKNOWN = "unknown"


@dataclass
class PronounContext:
    """Detected pronoun context from a user message."""
    role: PronounRole = PronounRole.UNKNOWN
    user_address: str = "bạn"      # how Mi calls the user
    mi_self: str = "mình"          # how Mi refers to herself
    tone_level: int = 3            # 1=very casual, 3=neutral, 5=formal
    warmth_modifier: float = 1.0   # 1.0=normal, 1.3=warmer, 0.8=cooler
    pace_modifier: float = 1.0     # 1.0=normal, 0.8=slower, 1.2=faster
    dialect_hint: str = "neutral"  # mien_tay | gen_z | older | neutral

    def describe(self) -> str:
        return (
            f"Address user as '{self.user_address}', "
            f"Mi calls herself '{self.mi_self}', "
            f"tone={self.tone_level}/5, "
            f"warmth={'extra' if self.warmth_modifier > 1 else 'normal'}"
        )


# ── Pronoun detection patterns ─────────────────────────────────────────────────
# Each pattern: (regex_pattern, PronounContext)
_PATTERNS: list[tuple[str, PronounContext]] = [
    # Older — respectful hierarchy
    (r"\b(bác|bác ơi)\b", PronounContext(
        role=PronounRole.OLDER, user_address="bác", mi_self="mình",
        tone_level=4, warmth_modifier=1.2, pace_modifier=0.8,
    )),
    (r"\b(cô|cô ơi)\b", PronounContext(
        role=PronounRole.OLDER, user_address="cô", mi_self="mình",
        tone_level=4, warmth_modifier=1.2, pace_modifier=0.8,
    )),
    (r"\b(chú|chú ơi)\b", PronounContext(
        role=PronounRole.OLDER, user_address="chú", mi_self="mình",
        tone_level=4, warmth_modifier=1.2, pace_modifier=0.8,
    )),
    (r"\b(dì|dì ơi)\b", PronounContext(
        role=PronounRole.OLDER, user_address="dì", mi_self="mình",
        tone_level=4, warmth_modifier=1.2, pace_modifier=0.8,
    )),

    # Semi-formal — anh/chị
    (r"\banh\b", PronounContext(
        role=PronounRole.OLDER, user_address="anh", mi_self="mình",
        tone_level=3, warmth_modifier=1.1, pace_modifier=0.9,
    )),
    (r"\bchị\b", PronounContext(
        role=PronounRole.OLDER, user_address="chị", mi_self="mình",
        tone_level=3, warmth_modifier=1.1, pace_modifier=0.9,
    )),

    # Em — user treats Mi as older sister
    (r"\bem\b", PronounContext(
        role=PronounRole.YOUNGER, user_address="em", mi_self="mình",
        tone_level=3, warmth_modifier=1.15, pace_modifier=1.0,
    )),

    # Peer — bạn/mình
    (r"\bbạn\b", PronounContext(
        role=PronounRole.PEER, user_address="bạn", mi_self="mình",
        tone_level=3, warmth_modifier=1.0, pace_modifier=1.0,
    )),

    # Very casual — tao/mày
    (r"\b(tao|tôi|tui)\b", PronounContext(
        role=PronounRole.CASUAL, user_address="bạn", mi_self="mình",
        tone_level=2, warmth_modifier=0.95, pace_modifier=1.1,
    )),
    (r"\bmày\b", PronounContext(
        role=PronounRole.CASUAL, user_address="bạn", mi_self="mình",
        tone_level=1, warmth_modifier=0.9, pace_modifier=1.2,
    )),

    # Gen Z intimate — ní/bro/tụi mình
    (r"\b(ní|ni|bro|chế|tụi mình|tụi)\b", PronounContext(
        role=PronounRole.INTIMATE, user_address="bạn", mi_self="mình",
        tone_level=1, warmth_modifier=1.3, pace_modifier=1.2,
        dialect_hint="gen_z",
    )),

    # Miền Tây pronouns
    (r"\b(tui|mầy)\b", PronounContext(
        role=PronounRole.CASUAL, user_address="bạn", mi_self="mình",
        tone_level=2, warmth_modifier=1.25, pace_modifier=1.0,
        dialect_hint="mien_tay",
    )),
]


def detect_pronoun_context(text: str) -> PronounContext:
    """
    Detect the pronoun/social context from a user message.
    Returns appropriate PronounContext for Mi to use in response.
    """
    t = text.lower()
    for pattern, ctx in _PATTERNS:
        if re.search(pattern, t):
            return ctx
    # Default: peer-level, neutral
    return PronounContext(
        role=PronounRole.UNKNOWN,
        user_address="bạn",
        mi_self="mình",
        tone_level=3,
        warmth_modifier=1.0,
        pace_modifier=1.0,
    )


def build_pronoun_guidance(ctx: PronounContext) -> str:
    """
    Build a short instruction string to inject into Mi's system prompt
    so the LLM knows exactly which pronouns to use.
    """
    lines = [
        f"## Pronoun Adaptation for this conversation",
        f"- Refer to user as: '{ctx.user_address}'",
        f"- Mi refers to herself as: '{ctx.mi_self}'",
    ]
    if ctx.role == PronounRole.OLDER:
        lines.append("- Tone: respectful, slightly slower, more gentle")
        lines.append("- Avoid slang, avoid shortcuts")
    elif ctx.role == PronounRole.INTIMATE:
        lines.append("- Tone: very playful, warm, Gen Z energy OK")
        lines.append("- Emoji OK, shorter sentences OK")
    elif ctx.role == PronounRole.CASUAL:
        lines.append("- Tone: casual and relaxed, match their energy")
    elif ctx.role == PronounRole.PEER:
        lines.append("- Tone: friendly peer, warm but not overly formal")

    if ctx.dialect_hint == "mien_tay":
        lines.append("- User is from miền Tây — warm, soft rhythm, can add 'nhen/hen' endings")
    elif ctx.dialect_hint == "gen_z":
        lines.append("- User is Gen Z — playful OK, keep responses punchy and fun")

    return "\n".join(lines)
