"""
Fatigue Engine — Simulates traveler exhaustion states and validates
that AI gives fatigue-aware, low-effort recommendations.
"""

import random
from dataclasses import dataclass
from typing import List
from enum import Enum


class FatigueLevel(Enum):
    FRESH = "fresh"
    SLIGHTLY_TIRED = "slightly_tired"
    TIRED = "tired"
    EXHAUSTED = "exhausted"
    COMPLETELY_DONE = "completely_done"
    CHILD_EXHAUSTED = "child_exhausted"


@dataclass
class FatigueProfile:
    level: FatigueLevel
    max_distance_km: float  # max acceptable travel distance
    max_walking_min: int    # max acceptable walking minutes
    response_length_tolerance: int  # max response chars they'll read
    needs_quiet: bool
    needs_rest: bool
    needs_food_first: bool
    child_priority: bool


FATIGUE_PROFILES = {
    FatigueLevel.FRESH: FatigueProfile(
        level=FatigueLevel.FRESH,
        max_distance_km=50, max_walking_min=60,
        response_length_tolerance=800,
        needs_quiet=False, needs_rest=False,
        needs_food_first=False, child_priority=False,
    ),
    FatigueLevel.SLIGHTLY_TIRED: FatigueProfile(
        level=FatigueLevel.SLIGHTLY_TIRED,
        max_distance_km=20, max_walking_min=30,
        response_length_tolerance=500,
        needs_quiet=False, needs_rest=False,
        needs_food_first=False, child_priority=False,
    ),
    FatigueLevel.TIRED: FatigueProfile(
        level=FatigueLevel.TIRED,
        max_distance_km=10, max_walking_min=15,
        response_length_tolerance=300,
        needs_quiet=True, needs_rest=False,
        needs_food_first=True, child_priority=True,
    ),
    FatigueLevel.EXHAUSTED: FatigueProfile(
        level=FatigueLevel.EXHAUSTED,
        max_distance_km=3, max_walking_min=5,
        response_length_tolerance=200,
        needs_quiet=True, needs_rest=True,
        needs_food_first=True, child_priority=True,
    ),
    FatigueLevel.COMPLETELY_DONE: FatigueProfile(
        level=FatigueLevel.COMPLETELY_DONE,
        max_distance_km=1, max_walking_min=2,
        response_length_tolerance=100,
        needs_quiet=True, needs_rest=True,
        needs_food_first=True, child_priority=True,
    ),
    FatigueLevel.CHILD_EXHAUSTED: FatigueProfile(
        level=FatigueLevel.CHILD_EXHAUSTED,
        max_distance_km=2, max_walking_min=3,
        response_length_tolerance=150,
        needs_quiet=True, needs_rest=True,
        needs_food_first=True, child_priority=True,
    ),
}


FATIGUE_MESSAGES = {
    FatigueLevel.SLIGHTLY_TIRED: [
        "hơi mệt rồi nhưng còn đi được",
        "nghỉ một tí rồi đi tiếp nhé",
        "cafe gần đây không",
        "ngồi nghỉ đâu đó đi",
    ],
    FatigueLevel.TIRED: [
        "mệt rồi",
        "chân đau quá",
        "không muốn đi xa nữa",
        "gần thôi nha",
        "cần ăn và nghỉ",
        "bé bắt đầu nhõng nhẽo rồi",
    ],
    FatigueLevel.EXHAUSTED: [
        "mệt vl",
        "không đi nổi rồi",
        "chỉ muốn nằm",
        "gần thôi không đi đâu xa",
        "bé ngủ gật rồi",
        "kiệt sức",
        "về khách sạn thôi",
        "cần chỗ ngồi ngay",
    ],
    FatigueLevel.COMPLETELY_DONE: [
        "chịu không nổi nữa rồi",
        "về thôi",
        "không đi đâu được nữa",
        "xong rồi cho hôm nay",
        "mọi người đều mệt",
        "...",
        "bé khóc rồi",
    ],
    FatigueLevel.CHILD_EXHAUSTED: [
        "bé mệt rồi cần nghỉ",
        "con buồn ngủ",
        "bé hay xỉu",
        "cần chỗ cho bé nghỉ",
        "bé không chịu đi nữa",
        "con quấy rối rồi",
        "bé cần ngủ trưa",
    ],
}


RECOVERY_SUGGESTIONS = {
    "cafe_quiet": [
        "Cafe yên tĩnh gần đây",
        "Chỗ ngồi có điều hòa, wifi",
        "View đẹp, không ồn",
    ],
    "rest_spot": [
        "Lobby khách sạn",
        "Ghế trong mall",
        "Bóng mát ven đường",
        "Nhà hàng có ghế thoải mái",
    ],
    "recovery_food": [
        "Chè mát",
        "Nước dừa",
        "Cháo",
        "Cơm nhẹ",
        "Bánh mì",
        "Sinh tố",
    ],
    "child_rest": [
        "Resort/khách sạn có giường",
        "Nơi có điều hòa",
        "Không có tiếng ồn lớn",
        "Chỗ trẻ em có thể nằm",
    ],
}


class FatigueEngine:
    """Generates and validates fatigue-aware travel scenarios."""

    def detect_fatigue_level(self, message: str) -> FatigueLevel:
        """Detect fatigue level from message content."""
        msg_lower = message.lower()

        critical_signals = ["không đi nổi", "kiệt sức", "chịu không nổi", "về thôi", "xong rồi"]
        high_signals = ["mệt vl", "chân đau", "không muốn", "chỉ muốn nằm", "bé khóc"]
        medium_signals = ["mệt rồi", "gần thôi", "cần nghỉ", "bé mệt", "bé ngủ gật"]
        low_signals = ["hơi mệt", "nghỉ một tí", "ngồi nghỉ"]

        if any(s in msg_lower for s in critical_signals):
            return FatigueLevel.COMPLETELY_DONE
        elif any(s in msg_lower for s in high_signals):
            if "bé" in msg_lower:
                return FatigueLevel.CHILD_EXHAUSTED
            return FatigueLevel.EXHAUSTED
        elif any(s in msg_lower for s in medium_signals):
            return FatigueLevel.TIRED
        elif any(s in msg_lower for s in low_signals):
            return FatigueLevel.SLIGHTLY_TIRED
        return FatigueLevel.FRESH

    def get_fatigue_message(self, level: FatigueLevel) -> str:
        """Get a random message matching the fatigue level."""
        messages = FATIGUE_MESSAGES.get(level, ["oke"])
        return random.choice(messages)

    def audit_fatigue_response(self, level: FatigueLevel, response: str) -> dict:
        """Audit if AI response is fatigue-appropriate."""
        profile = FATIGUE_PROFILES.get(level)
        if not profile:
            return {"violations": [], "passed": []}

        violations = []
        passed = []
        response_lower = response.lower()

        # Check response length
        if len(response) > profile.response_length_tolerance:
            violations.append({
                "rule": "response_too_long_for_fatigue_level",
                "severity": "HIGH",
                "detail": f"Fatigue level {level.value}: max {profile.response_length_tolerance} chars, got {len(response)}",
            })
        else:
            passed.append("response_length_ok")

        # Check for far recommendations
        far_indicators = ["km", "cách", "mất khoảng", "đi"]
        distance_numbers = [
            word for word in response.split()
            if any(c.isdigit() for c in word) and
            any(word in response_lower[max(0, response_lower.index(word if word in response_lower else "x") - 20):
                                       response_lower.index(word if word in response_lower else "x") + 5]
                for indicator in far_indicators
                if indicator in response_lower)
        ]

        if profile.max_distance_km <= 3:
            # Very exhausted — must only suggest VERY nearby
            if any(
                kw in response_lower
                for kw in ["cách đây", "km", "phút đi xe"]
            ):
                violations.append({
                    "rule": "recommended_far_location_to_exhausted_user",
                    "severity": "CRITICAL",
                    "detail": "User is critically exhausted. Must not suggest any travel.",
                })
            else:
                passed.append("proximity_appropriate")

        # Check for ambitious activity suggestions
        if level in [FatigueLevel.EXHAUSTED, FatigueLevel.COMPLETELY_DONE]:
            ambitious = ["leo núi", "đi bộ", "tham quan", "ghé", "thêm địa điểm", "tiếp theo"]
            if any(a in response_lower for a in ambitious):
                violations.append({
                    "rule": "ambitious_suggestion_for_exhausted_user",
                    "severity": "HIGH",
                    "detail": "AI suggested sightseeing to exhausted user",
                })
            else:
                passed.append("no_ambitious_suggestions")

        # Check child priority
        if profile.child_priority and "bé" not in response_lower:
            # Might be okay if conversation didn't mention child
            pass
        elif profile.child_priority:
            passed.append("child_acknowledged")

        # Check for rest suggestions
        if profile.needs_rest:
            rest_words = ["nghỉ", "rest", "nằm", "ngủ", "thư giãn", "yên tĩnh"]
            if not any(r in response_lower for r in rest_words):
                violations.append({
                    "rule": "no_rest_suggestion_when_needed",
                    "severity": "MEDIUM",
                    "detail": "User needs rest but AI didn't suggest it",
                })
            else:
                passed.append("rest_suggested")

        return {
            "fatigue_level": level.value,
            "profile": {
                "max_distance_km": profile.max_distance_km,
                "max_response_length": profile.response_length_tolerance,
            },
            "violations": violations,
            "passed": passed,
            "fatigue_score": max(0.0, 1.0 - len(violations) * 0.25),
        }

    def get_recovery_suggestions(self, level: FatigueLevel) -> dict:
        """Get appropriate recovery suggestions for fatigue level."""
        if level in [FatigueLevel.EXHAUSTED, FatigueLevel.COMPLETELY_DONE, FatigueLevel.CHILD_EXHAUSTED]:
            return {
                "priority": "immediate_rest",
                "options": RECOVERY_SUGGESTIONS["rest_spot"],
                "food": RECOVERY_SUGGESTIONS["recovery_food"],
                "child": RECOVERY_SUGGESTIONS["child_rest"] if level == FatigueLevel.CHILD_EXHAUSTED else [],
            }
        elif level == FatigueLevel.TIRED:
            return {
                "priority": "find_cafe",
                "options": RECOVERY_SUGGESTIONS["cafe_quiet"],
                "food": RECOVERY_SUGGESTIONS["recovery_food"],
                "child": [],
            }
        return {"priority": "continue", "options": [], "food": [], "child": []}
