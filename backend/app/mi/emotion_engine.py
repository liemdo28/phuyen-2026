"""
Mi Emotion Engine — Structured emotional state detection.

Outputs a rich EmotionState used to drive Mi's response mode,
tone, length, recovery injection, and routing decisions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class EmotionLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseMode(str, Enum):
    ULTRA_SHORT = "ultra_short"     # 1 sentence, <100 chars
    SIMPLIFIED = "simplified"       # 2-3 sentences, 1 option
    BALANCED = "balanced"           # 2-4 sentences, 2-3 options
    EXPANDED = "expanded"           # 4+ sentences, 3+ options


@dataclass
class EmotionState:
    # Primary emotions
    fatigue: EmotionLevel = EmotionLevel.NONE
    stress: EmotionLevel = EmotionLevel.NONE
    hunger: EmotionLevel = EmotionLevel.NONE
    excitement: EmotionLevel = EmotionLevel.NONE
    confusion: EmotionLevel = EmotionLevel.NONE
    loneliness: EmotionLevel = EmotionLevel.NONE
    social_fatigue: EmotionLevel = EmotionLevel.NONE
    burnout: EmotionLevel = EmotionLevel.NONE

    # Mood signals
    hype_mood: bool = False
    healing_mood: bool = False
    sarcasm_detected: bool = False
    recovery_needed: bool = False
    movement_resistance: bool = False

    # Social energy
    social_energy: EmotionLevel = EmotionLevel.MEDIUM

    # Derived
    response_mode: ResponseMode = ResponseMode.BALANCED
    recovery_type: str | None = None  # emotional|social|travel|heat|cognitive

    def to_dict(self) -> dict:
        return {
            "fatigue": self.fatigue.value,
            "stress": self.stress.value,
            "hunger": self.hunger.value,
            "excitement": self.excitement.value,
            "confusion": self.confusion.value,
            "loneliness": self.loneliness.value,
            "social_fatigue": self.social_fatigue.value,
            "burnout": self.burnout.value,
            "hype_mood": self.hype_mood,
            "healing_mood": self.healing_mood,
            "sarcasm_detected": self.sarcasm_detected,
            "recovery_needed": self.recovery_needed,
            "movement_resistance": self.movement_resistance,
            "social_energy": self.social_energy.value,
            "response_mode": self.response_mode.value,
            "recovery_type": self.recovery_type,
        }

    def summary(self) -> str:
        parts = []
        if self.fatigue != EmotionLevel.NONE:
            parts.append(f"fatigue:{self.fatigue.value}")
        if self.stress != EmotionLevel.NONE:
            parts.append(f"stress:{self.stress.value}")
        if self.hunger != EmotionLevel.NONE:
            parts.append(f"hunger:{self.hunger.value}")
        if self.excitement != EmotionLevel.NONE:
            parts.append(f"excitement:{self.excitement.value}")
        if self.hype_mood:
            parts.append("hype")
        if self.healing_mood:
            parts.append("healing")
        if self.sarcasm_detected:
            parts.append("sarcasm")
        if self.recovery_needed:
            parts.append(f"recovery:{self.recovery_type}")
        if self.movement_resistance:
            parts.append("movement_resistance")
        return ", ".join(parts) if parts else "neutral"


# ── Detection rules ────────────────────────────────────────────────────────────

_FATIGUE_CRITICAL = [
    "mệt xỉu", "mệt muốn chết", "kiệt sức rồi", "không còn sức",
    "sắp ngất", "hết pin rồi", "bã người", "rã rời",
    "die rồi", "xỉu mất", "đứng không nổi", "đuối quá rồi",
]
_FATIGUE_HIGH = [
    "mệt lắm", "mệt quá", "mệt rồi", "mét vl", "met vl",
    "kiệt sức", "đuối", "buồn ngủ quá", "ngủ gật rồi", "hết xăng",
]
_FATIGUE_MEDIUM = [
    "mệt", "met", "hơi mệt", "mỏi", "nặng người", "uể oải",
]

_STRESS_HIGH = [
    "stress vãi", "nổ đầu", "loạn não", "rối tung",
    "điên rồi", "bực quá", "tức điên", "ơi trời",
    "chết rồi", "kẹt rồi", "không kịp", "trễ rồi",
]
_STRESS_MEDIUM = [
    "stress", "bực", "khó chịu", "bực mình", "tức",
    "không ổn", "rối", "lo lắng", "lo quá",
]

_HUNGER_HIGH = [
    "đói xỉu", "đói muốn chết", "đói bẹp", "đói cồn cào",
    "bụng kêu", "doi qua", "đói lắm rồi",
]
_HUNGER_MEDIUM = [
    "đói", "đói rồi", "đói quá", "ăn gì", "ăn ở đâu",
    "kiếm gì ăn", "bụng đói", "doi roi", "doi lam",
    "chưa ăn gì", "chưa ăn",
]

_EXCITEMENT = [
    "wow", "đẹp quá", "hào hứng", "phấn khích", "trời ơi đẹp",
    "chill quá", "tan chảy", "đỉnh", "tuyệt", "thích quá",
    "mê quá", "quá đỉnh", "xinh quá",
]
_HYPE = [
    "quẩy", "phê", "hype", "siuuu", "đỉnh kout",
    "xịn sò", "lit", "slay",
]

_CONFUSION = [
    "không biết", "rối quá", "làm sao", "sao bây giờ",
    "giờ này đi đâu", "không biết phải làm sao",
    "rối não", "loạn não", "không hiểu",
]

_SARCASM = [
    "🙄", "ừ đúng rồi", "tuyệt vời lắm", "giỏi thật",
    "hay thật đấy", "ừ ừ chắc vậy", "tất nhiên rồi 🙄",
]

_LONELINESS = [
    "cô đơn", "một mình", "buồn quá", "không có ai",
    "nhớ nhà", "muốn về nhà", "chán",
]

_SOCIAL_FATIGUE = [
    "đông quá", "ồn quá", "không muốn gặp người",
    "muốn yên tĩnh", "không muốn ồn", "tránh đám đông",
    "cần không gian", "cần yên tĩnh",
]

_MOVEMENT_RESISTANCE = [
    "gần thôi", "gan thoi", "gần đây thôi", "không muốn đi xa",
    "lười đi xa", "ngại đi xa", "ngai di xa", "đi bộ thôi",
    "gần gần thôi", "ngại xa", "không xa",
]

_HEALING = [
    "muốn nghỉ", "cần nghỉ", "đi healing", "muốn reset",
    "kiếm chỗ chill", "muốn yên tĩnh", "thư giãn",
    "cần xả hơi", "đầu óc trống", "giải thoát",
]

_HEAT_DISTRESS = [
    "nóng muốn chết", "nóng vãi", "nóng quá", "nắng gắt",
    "oi bức", "nóng chảy mỡ", "mồ hôi", "muốn vào lạnh",
]


def detect_emotion(text: str) -> EmotionState:
    """
    Analyze user message and return a structured EmotionState.
    This drives ALL of Mi's response adaptation.
    """
    t = text.lower()
    state = EmotionState()

    # ── Fatigue ───────────────────────────────────────────────────────────────
    if any(w in t for w in _FATIGUE_CRITICAL):
        state.fatigue = EmotionLevel.CRITICAL
        state.response_mode = ResponseMode.ULTRA_SHORT
        state.recovery_needed = True
        state.recovery_type = "travel"
    elif any(w in t for w in _FATIGUE_HIGH):
        state.fatigue = EmotionLevel.HIGH
        state.response_mode = ResponseMode.SIMPLIFIED
        state.recovery_needed = True
        state.recovery_type = "travel"
    elif any(w in t for w in _FATIGUE_MEDIUM):
        state.fatigue = EmotionLevel.MEDIUM
        state.response_mode = ResponseMode.SIMPLIFIED

    # ── Stress ────────────────────────────────────────────────────────────────
    if any(w in t for w in _STRESS_HIGH):
        state.stress = EmotionLevel.HIGH
        if state.response_mode == ResponseMode.BALANCED:
            state.response_mode = ResponseMode.SIMPLIFIED
        state.recovery_needed = True
        state.recovery_type = state.recovery_type or "emotional"
    elif any(w in t for w in _STRESS_MEDIUM):
        state.stress = EmotionLevel.MEDIUM

    # ── Hunger ────────────────────────────────────────────────────────────────
    if any(w in t for w in _HUNGER_HIGH):
        state.hunger = EmotionLevel.HIGH
        if state.response_mode == ResponseMode.BALANCED:
            state.response_mode = ResponseMode.SIMPLIFIED
    elif any(w in t for w in _HUNGER_MEDIUM):
        state.hunger = EmotionLevel.MEDIUM

    # ── Excitement / Hype ─────────────────────────────────────────────────────
    if any(w in t for w in _HYPE):
        state.hype_mood = True
        state.excitement = EmotionLevel.HIGH
        if state.response_mode == ResponseMode.BALANCED:
            state.response_mode = ResponseMode.EXPANDED
    elif any(w in t for w in _EXCITEMENT):
        state.excitement = EmotionLevel.MEDIUM

    # ── Confusion ─────────────────────────────────────────────────────────────
    if any(w in t for w in _CONFUSION):
        state.confusion = EmotionLevel.MEDIUM
        if state.response_mode == ResponseMode.BALANCED:
            state.response_mode = ResponseMode.SIMPLIFIED

    # ── Sarcasm ───────────────────────────────────────────────────────────────
    if any(w in t for w in _SARCASM):
        state.sarcasm_detected = True

    # ── Loneliness ────────────────────────────────────────────────────────────
    if any(w in t for w in _LONELINESS):
        state.loneliness = EmotionLevel.MEDIUM
        state.recovery_type = state.recovery_type or "emotional"

    # ── Social fatigue ────────────────────────────────────────────────────────
    if any(w in t for w in _SOCIAL_FATIGUE):
        state.social_fatigue = EmotionLevel.HIGH
        state.social_energy = EmotionLevel.LOW
        state.recovery_needed = True
        state.recovery_type = state.recovery_type or "social"

    # ── Movement resistance ───────────────────────────────────────────────────
    if any(w in t for w in _MOVEMENT_RESISTANCE):
        state.movement_resistance = True

    # ── Healing / chill mood ──────────────────────────────────────────────────
    if any(w in t for w in _HEALING):
        state.healing_mood = True
        state.recovery_needed = True
        state.recovery_type = state.recovery_type or "emotional"

    # ── Heat distress ─────────────────────────────────────────────────────────
    if any(w in t for w in _HEAT_DISTRESS):
        state.recovery_needed = True
        state.recovery_type = state.recovery_type or "heat"
        if state.response_mode == ResponseMode.BALANCED:
            state.response_mode = ResponseMode.SIMPLIFIED

    # ── Social energy (default medium unless overridden) ──────────────────────
    if state.fatigue in (EmotionLevel.HIGH, EmotionLevel.CRITICAL):
        state.social_energy = EmotionLevel.LOW
    elif state.hype_mood:
        state.social_energy = EmotionLevel.HIGH

    return state


def build_emotion_guidance(state: EmotionState) -> str:
    """
    Build a short instruction block to inject into Mi's system prompt,
    telling the LLM exactly how to adapt response mode and tone.
    """
    lines = [f"## Emotional State Guidance (live detection)"]
    lines.append(f"Detected: {state.summary()}")
    lines.append(f"Response mode: {state.response_mode.value}")

    if state.response_mode == ResponseMode.ULTRA_SHORT:
        lines.append("→ Max 1 sentence. Acknowledge state + single action. No options. No lists.")
    elif state.response_mode == ResponseMode.SIMPLIFIED:
        lines.append("→ Max 3 sentences. 1 option only. Include comfort element. No lists.")
    elif state.response_mode == ResponseMode.EXPANDED:
        lines.append("→ Can use 4+ sentences. Up to 3 options. Match user energy.")
    else:
        lines.append("→ 2-4 sentences. 2-3 options max.")

    if state.sarcasm_detected:
        lines.append("→ SARCASM: Do NOT agree. Acknowledge complaint, redirect warmly.")
    if state.recovery_needed:
        lines.append(f"→ RECOVERY: User needs {state.recovery_type} recovery. Suggest rest before activity.")
    if state.movement_resistance:
        lines.append("→ MOVEMENT: Nearby only. Ask for current area. Do NOT suggest distant places.")
    if state.loneliness != EmotionLevel.NONE:
        lines.append("→ LONELINESS: Warm acknowledgement. Presence before advice.")

    return "\n".join(lines)
