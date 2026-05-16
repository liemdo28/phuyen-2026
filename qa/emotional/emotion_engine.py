"""
Emotional Variation Engine — Simulates real human emotional states
and applies them to message generation and response auditing.
"""

import random
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class EmotionalState(Enum):
    BURNOUT = "burnout"
    STRESSED = "stressed"
    ANGRY = "angry"
    SARCASTIC = "sarcastic"
    LONELY = "lonely"
    EXHAUSTED = "exhausted"
    EXCITED = "excited"
    NIGHTLIFE_ENERGY = "nightlife_energy"
    SOCIAL_FATIGUE = "social_fatigue"
    CALM = "calm"
    HUNGRY_IRRITABLE = "hungry_irritable"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    CONTENT = "content"


@dataclass
class EmotionalProfile:
    state: EmotionalState
    intensity: float  # 0.0 - 1.0
    patience: float
    expected_response_tone: str
    audit_check: str  # what AI must do to pass


EMOTIONAL_PROFILES = {
    EmotionalState.BURNOUT: EmotionalProfile(
        state=EmotionalState.BURNOUT,
        intensity=0.8,
        patience=0.2,
        expected_response_tone="gentle, simple, low effort required from user",
        audit_check="AI must not overwhelm with options or lengthy text",
    ),
    EmotionalState.STRESSED: EmotionalProfile(
        state=EmotionalState.STRESSED,
        intensity=0.7,
        patience=0.3,
        expected_response_tone="calm, reassuring, direct solutions",
        audit_check="AI must acknowledge stress and provide immediate actionable help",
    ),
    EmotionalState.ANGRY: EmotionalProfile(
        state=EmotionalState.ANGRY,
        intensity=0.9,
        patience=0.1,
        expected_response_tone="calm, non-defensive, solution-focused",
        audit_check="AI must not be robotic or dismissive. Must de-escalate.",
    ),
    EmotionalState.SARCASTIC: EmotionalProfile(
        state=EmotionalState.SARCASTIC,
        intensity=0.6,
        patience=0.4,
        expected_response_tone="light, casual, slightly humorous",
        audit_check="AI must read sarcasm correctly and not take bait literally",
    ),
    EmotionalState.EXHAUSTED: EmotionalProfile(
        state=EmotionalState.EXHAUSTED,
        intensity=0.7,
        patience=0.2,
        expected_response_tone="minimal options, nearby only, low energy required",
        audit_check="AI must NOT recommend far or complex destinations when user is exhausted",
    ),
    EmotionalState.EXCITED: EmotionalProfile(
        state=EmotionalState.EXCITED,
        intensity=0.6,
        patience=0.7,
        expected_response_tone="enthusiastic, matching energy",
        audit_check="AI must match excitement level, not be flat/robotic",
    ),
    EmotionalState.NIGHTLIFE_ENERGY: EmotionalProfile(
        state=EmotionalState.NIGHTLIFE_ENERGY,
        intensity=0.7,
        patience=0.5,
        expected_response_tone="fun, social, nightlife-aware",
        audit_check="AI must recommend appropriate nightlife venues, not family restaurants",
    ),
    EmotionalState.LONELY: EmotionalProfile(
        state=EmotionalState.LONELY,
        intensity=0.6,
        patience=0.5,
        expected_response_tone="warm, social suggestions, inclusive",
        audit_check="AI must offer social/group-friendly suggestions",
    ),
    EmotionalState.SOCIAL_FATIGUE: EmotionalProfile(
        state=EmotionalState.SOCIAL_FATIGUE,
        intensity=0.5,
        patience=0.4,
        expected_response_tone="quiet spots, solo-friendly options",
        audit_check="AI must suggest quiet, low-stimulus environments",
    ),
    EmotionalState.HUNGRY_IRRITABLE: EmotionalProfile(
        state=EmotionalState.HUNGRY_IRRITABLE,
        intensity=0.7,
        patience=0.15,
        expected_response_tone="immediate, fast, no-nonsense",
        audit_check="AI must give the fastest food recommendation, no preamble",
    ),
    EmotionalState.FRUSTRATED: EmotionalProfile(
        state=EmotionalState.FRUSTRATED,
        intensity=0.75,
        patience=0.2,
        expected_response_tone="understanding, problem-solving, not defensive",
        audit_check="AI must validate frustration and immediately solve problem",
    ),
    EmotionalState.CALM: EmotionalProfile(
        state=EmotionalState.CALM,
        intensity=0.2,
        patience=0.9,
        expected_response_tone="informative, thorough",
        audit_check="AI can give fuller responses here",
    ),
    EmotionalState.CONFUSED: EmotionalProfile(
        state=EmotionalState.CONFUSED,
        intensity=0.4,
        patience=0.6,
        expected_response_tone="clear, structured, not overwhelming",
        audit_check="AI must simplify and guide clearly",
    ),
    EmotionalState.CONTENT: EmotionalProfile(
        state=EmotionalState.CONTENT,
        intensity=0.1,
        patience=0.9,
        expected_response_tone="friendly, informative",
        audit_check="Standard quality check",
    ),
}


# Emotional state prefix injectors
EMOTION_PREFIXES = {
    EmotionalState.BURNOUT: [
        "mệt quá rồi",
        "hết sức rồi",
        "ừ thôi",
        "mặc kệ",
        "ai lo giúp tôi cái",
    ],
    EmotionalState.STRESSED: [
        "trời ơi",
        "lo quá",
        "không biết phải làm gì",
        "stress vl",
        "panic mode",
    ],
    EmotionalState.ANGRY: [
        "TỨC CHỊU KHÔNG NỔI",
        "Sao lại thế này???",
        "Không thể chấp nhận được",
        "Tôi đã nói rồi mà",
        "lần này là lần cuối",
    ],
    EmotionalState.SARCASTIC: [
        "Ừ đúng rồi",
        "Hay thật đấy",
        "Chắc chắn rồi",
        "Tuyệt vời lắm",
        "Wow cảm ơn nhiều 🙄",
    ],
    EmotionalState.EXHAUSTED: [
        "mệt vl",
        "không đi nổi",
        "chân đau",
        "cần nghỉ",
        "kiệt sức",
    ],
    EmotionalState.EXCITED: [
        "OMG",
        "wow",
        "đỉnh quá",
        "hay vậy",
        "thích mà",
    ],
    EmotionalState.HUNGRY_IRRITABLE: [
        "đói LẮMM",
        "bụng réo rồi",
        "đói quá không chịu nổi",
        "mau lên tôi chết đói",
        "cần ăn ngay",
    ],
    EmotionalState.FRUSTRATED: [
        "hỏi mãi",
        "sao phức tạp vậy",
        "không ai giúp tôi",
        "thất vọng ghê",
        "lại nữa hả",
    ],
}


class EmotionEngine:
    def get_state_from_baseline(self, baseline: float) -> EmotionalState:
        """Map a 0-1 emotional baseline to a state."""
        if baseline < 0.2:
            return random.choice([EmotionalState.CALM, EmotionalState.CONTENT])
        elif baseline < 0.4:
            return random.choice([EmotionalState.CONFUSED, EmotionalState.SOCIAL_FATIGUE])
        elif baseline < 0.6:
            return random.choice([
                EmotionalState.STRESSED, EmotionalState.SARCASTIC,
                EmotionalState.NIGHTLIFE_ENERGY, EmotionalState.EXCITED,
            ])
        elif baseline < 0.8:
            return random.choice([
                EmotionalState.EXHAUSTED, EmotionalState.FRUSTRATED,
                EmotionalState.HUNGRY_IRRITABLE, EmotionalState.BURNOUT,
            ])
        else:
            return random.choice([
                EmotionalState.ANGRY, EmotionalState.STRESSED,
                EmotionalState.EXHAUSTED,
            ])

    def get_state_label(self, baseline: float) -> str:
        return self.get_state_from_baseline(baseline).value

    def get_profile(self, state: EmotionalState) -> EmotionalProfile:
        return EMOTIONAL_PROFILES.get(state, EMOTIONAL_PROFILES[EmotionalState.CALM])

    def colorize(self, text: str, baseline: float, persona_type=None) -> str:
        """Add emotional coloring to text based on baseline."""
        state = self.get_state_from_baseline(baseline)

        # Add prefix with probability proportional to intensity
        profile = self.get_profile(state)
        if random.random() < profile.intensity * 0.4:
            prefixes = EMOTION_PREFIXES.get(state, [])
            if prefixes:
                prefix = random.choice(prefixes)
                if random.random() < 0.5:
                    text = f"{prefix}, {text}"
                else:
                    text = f"{text} {prefix}"

        # Apply punctuation chaos based on emotion
        text = self._apply_emotional_punctuation(text, state, profile.intensity)

        return text

    def _apply_emotional_punctuation(
        self, text: str, state: EmotionalState, intensity: float
    ) -> str:
        """Add emotionally appropriate punctuation."""
        if state == EmotionalState.ANGRY and random.random() < intensity:
            text = text.upper() if random.random() < 0.3 else text + "!!!"
        elif state == EmotionalState.EXHAUSTED and random.random() < intensity:
            text = text.rstrip("!.") + "..."
        elif state == EmotionalState.EXCITED and random.random() < intensity:
            text = text + "!!" if not text.endswith("!") else text
        elif state == EmotionalState.SARCASTIC and random.random() < intensity:
            text = text + " 🙄" if random.random() < 0.3 else text
        elif state == EmotionalState.FRUSTRATED and random.random() < 0.4:
            text = text + "???" if not text.endswith("?") else text + "??"

        return text

    def audit_emotional_response(
        self, user_state: EmotionalState, ai_response: str
    ) -> dict:
        """Check if AI response is appropriate for the user's emotional state."""
        profile = self.get_profile(user_state)
        violations = []
        passed = []

        response_lower = ai_response.lower()
        response_len = len(ai_response)

        # Check: burned out user should not get long responses
        if user_state == EmotionalState.BURNOUT and response_len > 500:
            violations.append({
                "rule": "response_too_long_for_burnout",
                "severity": "MEDIUM",
                "detail": f"Response length {response_len} chars — user is burned out, needs brief answer",
            })
        else:
            passed.append("length_appropriate")

        # Check: angry user response should not be robotic
        if user_state == EmotionalState.ANGRY:
            robotic_phrases = [
                "i understand your concern", "thank you for your feedback",
                "tôi hiểu", "cảm ơn bạn đã phản hồi", "chúng tôi xin lỗi",
            ]
            if any(p in response_lower for p in robotic_phrases):
                violations.append({
                    "rule": "robotic_tone_for_angry_user",
                    "severity": "HIGH",
                    "detail": "AI used corporate/robotic language with angry user",
                })
            else:
                passed.append("tone_appropriate_for_anger")

        # Check: exhausted user should not get far recommendations
        if user_state == EmotionalState.EXHAUSTED:
            far_signals = ["cách đây", "km", "đi khoảng", "mất khoảng"]
            if any(s in response_lower for s in far_signals):
                violations.append({
                    "rule": "distant_recommendation_for_exhausted",
                    "severity": "HIGH",
                    "detail": "AI recommended distant location to exhausted user",
                })
            else:
                passed.append("proximity_aware")

        # Check: hungry + irritable → must give food fast
        if user_state == EmotionalState.HUNGRY_IRRITABLE and response_len > 400:
            violations.append({
                "rule": "too_verbose_for_hungry_user",
                "severity": "MEDIUM",
                "detail": "User is hungry and irritable — response must be direct and fast",
            })
        else:
            passed.append("appropriate_urgency")

        return {
            "emotional_state": user_state.value,
            "expected_tone": profile.expected_response_tone,
            "audit_rule": profile.audit_check,
            "violations": violations,
            "passed": passed,
            "emotional_score": max(0.0, 1.0 - len(violations) * 0.25),
        }
