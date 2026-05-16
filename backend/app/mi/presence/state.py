"""
Mi Human Presence System — state definitions.
Emotional state, life rhythm, and presence context dataclasses.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class FatigueLevel(Enum):
    FRESH = "fresh"
    MILD = "mild"
    MODERATE = "moderate"
    HIGH = "high"
    EXHAUSTED = "exhausted"


class ResponsePace(Enum):
    MINIMAL = "minimal"    # 1 short sentence, user wants quiet
    SHORT = "short"        # 1-2 sentences, tired
    NORMAL = "normal"      # 2-3 sentences
    ENGAGED = "engaged"    # 2-3 sentences, playful/warm


class SocialMode(Enum):
    QUIET_COMPANION = "quiet_companion"
    CALM_SUPPORTIVE = "calm_supportive"
    CASUAL = "casual"
    PLAYFUL = "playful"
    EMOTIONALLY_SUPPORTIVE = "emotionally_supportive"


class LifePhase(Enum):
    WAKING = "waking"
    HUNGRY = "hungry"
    ACTIVE = "active"
    OVERHEATING = "overheating"
    SUNSET = "sunset"
    SOCIALLY_TIRED = "socially_tired"
    MENTALLY_OVERLOADED = "mentally_overloaded"
    HEALING = "healing"
    REFLECTIVE_NIGHT = "reflective_night"
    NEUTRAL = "neutral"


@dataclass
class EmotionalSnapshot:
    """Single-message emotional state."""
    fatigue: float = 0.0         # 0.0 = fresh, 1.0 = exhausted
    stress: float = 0.0          # 0.0 = calm, 1.0 = overwhelmed
    excitement: float = 0.0      # 0.0 = flat, 1.0 = very excited
    social_battery: float = 1.0  # 0.0 = depleted, 1.0 = full
    wants_quiet: bool = False
    needs_comfort: bool = False
    in_healing: bool = False
    reflective: bool = False
    life_phase: LifePhase = LifePhase.NEUTRAL
    detected_signals: list[str] = field(default_factory=list)

    @property
    def fatigue_level(self) -> FatigueLevel:
        if self.fatigue < 0.2: return FatigueLevel.FRESH
        if self.fatigue < 0.4: return FatigueLevel.MILD
        if self.fatigue < 0.6: return FatigueLevel.MODERATE
        if self.fatigue < 0.8: return FatigueLevel.HIGH
        return FatigueLevel.EXHAUSTED

    @property
    def is_tired(self) -> bool:
        return self.fatigue >= 0.4

    @property
    def is_overwhelmed(self) -> bool:
        return self.stress >= 0.5 or self.social_battery <= 0.3


@dataclass
class PresenceContext:
    """Full context for human presence guidance."""
    current: EmotionalSnapshot = field(default_factory=EmotionalSnapshot)
    recent_was_tired: bool = False
    recent_was_stressed: bool = False
    recent_excitement: float = 0.0
    social_mode: SocialMode = SocialMode.CASUAL
    response_pace: ResponsePace = ResponsePace.NORMAL
    acknowledgment: str = ""
    proactive_note: str = ""
    simplify_choices: bool = False
    max_suggestions: int = 3
    curate_message: str = ""

    def build_guidance(self) -> str:
        parts: list[str] = []

        if self.acknowledgment:
            parts.append(
                f"## Emotional Acknowledgment\n"
                f"Open with this natural acknowledgment (adapt tone slightly if needed): "
                f"\"{self.acknowledgment}\""
            )

        pace_map = {
            ResponsePace.MINIMAL: "1 very short sentence ONLY. User wants quiet — minimal words, maximum warmth.",
            ResponsePace.SHORT: "1–2 sentences MAX. User is tired — keep it simple.",
            ResponsePace.NORMAL: "2–3 sentences. Natural conversational length.",
            ResponsePace.ENGAGED: "2–3 sentences. User has energy — can be slightly warm and playful.",
        }
        parts.append(f"## Response Pacing\n{pace_map[self.response_pace]}")

        mode_guidance = {
            SocialMode.QUIET_COMPANION: (
                "Be a quiet presence. Minimal words, maximum warmth. "
                "Do NOT suggest many things — one gentle option at most."
            ),
            SocialMode.CALM_SUPPORTIVE: (
                "Soft tone, calm pacing. Acknowledge emotional state first, "
                "then offer one gentle suggestion."
            ),
            SocialMode.CASUAL: "Friendly and natural. Like texting a close friend.",
            SocialMode.PLAYFUL: "Warm and slightly playful. User has energy — match it.",
            SocialMode.EMOTIONALLY_SUPPORTIVE: (
                "Lead with empathy. Reduce pressure. Make them feel understood FIRST, "
                "suggestions come second."
            ),
        }
        parts.append(
            f"## Social Mode: {self.social_mode.value}\n"
            f"{mode_guidance[self.social_mode]}"
        )

        if self.simplify_choices:
            curate = self.curate_message or "Mi lọc còn mấy chỗ hợp nhất với trạng thái lúc này cho mình nha 😊"
            parts.append(
                f"## Mental Load Reduction\n"
                f"Do NOT list many options. Pick the {self.max_suggestions} best fits only. "
                f"Say: \"{curate}\""
            )

        if self.recent_was_tired and not self.current.is_tired:
            parts.append(
                "## Emotional Memory\n"
                "User was recently tired. Keep suggestions easy and nearby even if they seem better now. "
                "Do not push ambitious plans."
            )

        if self.proactive_note:
            parts.append(
                f"## Proactive Observation\n"
                f"Naturally weave this in if contextually relevant: \"{self.proactive_note}\""
            )

        parts.append(
            "## Human Presence Core Rules\n"
            "- Emotionally ABSORB stress — do NOT create more pressure\n"
            "- Sound like a calm, caring friend — never like a system\n"
            "- Tired user: acknowledge → simplify → one gentle suggestion\n"
            "- Quiet user: fewer words, softer tone, less density\n"
            "- Never list many options when user is tired/overwhelmed\n"
            "- Conversation should feel: calm, breathable, low-pressure, human"
        )

        return "\n\n".join(parts)
