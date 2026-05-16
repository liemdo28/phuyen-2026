"""
Nightlife Engine — Simulates late-night users, drunk communication,
social drinking behavior, and nightlife routing scenarios.
"""

import random
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class NightlifeState(Enum):
    SOBER_PLANNING = "sober_planning"
    TIPSY = "tipsy"
    DRUNK = "drunk"
    VERY_DRUNK = "very_drunk"
    POST_DRINKING = "post_drinking"
    LATE_NIGHT_SOBER = "late_night_sober"
    HUNGOVER = "hungover"


@dataclass
class NightlifeProfile:
    state: NightlifeState
    typo_rate: float
    coherence: float  # 0.0 = incoherent, 1.0 = coherent
    message_length: str
    emoji_rate: float
    repeat_rate: float  # rate of repeating words
    caps_rate: float


NIGHTLIFE_PROFILES = {
    NightlifeState.SOBER_PLANNING: NightlifeProfile(
        state=NightlifeState.SOBER_PLANNING,
        typo_rate=0.1, coherence=0.9,
        message_length="medium", emoji_rate=0.2,
        repeat_rate=0.0, caps_rate=0.0,
    ),
    NightlifeState.TIPSY: NightlifeProfile(
        state=NightlifeState.TIPSY,
        typo_rate=0.3, coherence=0.7,
        message_length="short", emoji_rate=0.5,
        repeat_rate=0.1, caps_rate=0.1,
    ),
    NightlifeState.DRUNK: NightlifeProfile(
        state=NightlifeState.DRUNK,
        typo_rate=0.6, coherence=0.4,
        message_length="very_short", emoji_rate=0.7,
        repeat_rate=0.3, caps_rate=0.2,
    ),
    NightlifeState.VERY_DRUNK: NightlifeProfile(
        state=NightlifeState.VERY_DRUNK,
        typo_rate=0.85, coherence=0.15,
        message_length="very_short", emoji_rate=0.8,
        repeat_rate=0.5, caps_rate=0.3,
    ),
    NightlifeState.POST_DRINKING: NightlifeProfile(
        state=NightlifeState.POST_DRINKING,
        typo_rate=0.4, coherence=0.5,
        message_length="short", emoji_rate=0.4,
        repeat_rate=0.2, caps_rate=0.1,
    ),
    NightlifeState.LATE_NIGHT_SOBER: NightlifeProfile(
        state=NightlifeState.LATE_NIGHT_SOBER,
        typo_rate=0.2, coherence=0.8,
        message_length="short", emoji_rate=0.2,
        repeat_rate=0.0, caps_rate=0.0,
    ),
    NightlifeState.HUNGOVER: NightlifeProfile(
        state=NightlifeState.HUNGOVER,
        typo_rate=0.15, coherence=0.7,
        message_length="very_short", emoji_rate=0.1,
        repeat_rate=0.0, caps_rate=0.0,
    ),
}


# Message pools by nightlife state
NIGHTLIFE_MESSAGES = {
    NightlifeState.SOBER_PLANNING: [
        "Tối nay mọi người muốn đi đâu?",
        "Bar nào có view biển?",
        "Quán nhậu nào ngon và không quá ồn?",
        "Có chỗ nào nghe nhạc live không?",
        "Nên đặt trước hay cứ đến?",
        "Cần chi phí tầm bao nhiêu tối nay?",
        "Chỗ nào phù hợp cho nhóm 7 người?",
    ],
    NightlifeState.TIPSY: [
        "còn chỗ nào tiếp theo không 🍺",
        "lon tiếp theo đi mọi người",
        "đi đâu vui hơn đây",
        "chỗ này oke đấy nhỉ haha",
        "còn sớm mà đi đâu nữa đi",
        "shot đi mọi người 🥂",
        "ai biết bar nào không 🍻",
    ],
    NightlifeState.DRUNK: [
        "dau tiep theo di",
        "uong them ko may",
        "di di di di",
        "ngon vl luon ay",
        "tiep theo dau nao",
        "hehe vui qua",
        "ai biet quan nao ko 🍺🍺",
        "may oi dau tiep",
        "lon cuoi roi nha",
    ],
    NightlifeState.VERY_DRUNK: [
        "di di 🍺🍺🍺",
        "hehehe",
        "oi oi oi",
        "ngon ngon ngon",
        "dau dau dau",
        "🍺🍺🍺🍺",
        "tiep tiep tiep",
        "may oi may oi",
        "ha ha ha",
    ],
    NightlifeState.POST_DRINKING: [
        "đói quá về đâu ăn được không",
        "mì tôm ở đâu giờ này",
        "cần đồ ăn khuya",
        "bún gì đó dc không",
        "đồ ăn khuya gần đây",
        "bánh mì không",
        "cần gì đó để tỉnh dậy",
        "trà đá giờ này còn không",
    ],
    NightlifeState.LATE_NIGHT_SOBER: [
        "2am còn gì mở không",
        "quán 24h ở đây không",
        "giờ này đi đâu",
        "mất ngủ đi đâu ngồi",
        "cafe khuya nào còn mở",
        "convenience store gần đây",
        "đi dạo biển khuya có an toàn không",
    ],
    NightlifeState.HUNGOVER: [
        "đầu đau quá",
        "cần cháo hoặc gì đó nhẹ",
        "chanh muối đâu",
        "không muốn đi đâu xa",
        "gần đây thôi",
        "ăn gì cho đỡ say",
        "nước dừa đâu có không",
        "nghỉ ngơi thôi",
        "mệt vl",
    ],
}


# Expected AI behaviors for each state
NIGHTLIFE_AI_EXPECTATIONS = {
    NightlifeState.DRUNK: {
        "must_do": [
            "Keep response very short",
            "Don't give safety lectures",
            "Suggest nearby spots only",
            "Match casual energy",
        ],
        "must_not": [
            "Give long formal response",
            "Lecture about alcohol",
            "Suggest far locations",
            "Be robotic",
            "Ignore slurred/typo messages",
        ],
    },
    NightlifeState.POST_DRINKING: {
        "must_do": [
            "Suggest nearby late-night food",
            "Know what's open at 1-3am",
            "Keep it simple",
            "Understand they want comfort food",
        ],
        "must_not": [
            "Suggest gourmet restaurants",
            "Give lengthy food descriptions",
            "Recommend closed establishments",
        ],
    },
    NightlifeState.HUNGOVER: {
        "must_do": [
            "Suggest hangover recovery food",
            "Nearby only",
            "Simple, gentle tone",
            "Understand low energy state",
        ],
        "must_not": [
            "Suggest spicy/heavy food",
            "Recommend activities",
            "Give enthusiastic response",
            "Ignore the suffering",
        ],
    },
}


class NightlifeEngine:
    """Generates nightlife and late-night scenario messages."""

    def get_random_state(self) -> NightlifeState:
        """Get weighted random nightlife state."""
        weights = {
            NightlifeState.SOBER_PLANNING: 20,
            NightlifeState.TIPSY: 25,
            NightlifeState.DRUNK: 20,
            NightlifeState.VERY_DRUNK: 10,
            NightlifeState.POST_DRINKING: 15,
            NightlifeState.LATE_NIGHT_SOBER: 5,
            NightlifeState.HUNGOVER: 5,
        }
        states = list(weights.keys())
        probs = [weights[s] for s in states]
        total = sum(probs)
        probs = [p / total for p in probs]
        return random.choices(states, weights=probs, k=1)[0]

    def get_message(self, state: NightlifeState) -> str:
        """Get a random message for the given state."""
        messages = NIGHTLIFE_MESSAGES.get(state, ["đi đâu đây"])
        return random.choice(messages)

    def apply_drunk_transform(self, text: str, state: NightlifeState) -> str:
        """Apply drunk-appropriate transformations to text."""
        profile = NIGHTLIFE_PROFILES.get(state)
        if not profile:
            return text

        # Strip accents partially based on coherence
        if profile.coherence < 0.5:
            from ..no_accent.no_accent_engine import NoAccentEngine
            text = NoAccentEngine().strip_accents(text).lower()

        # Apply typos
        if profile.typo_rate > 0.3:
            from ..typo.typo_engine import TypoEngine
            text = TypoEngine().apply(text, profile.typo_rate)

        # Word repetition
        if profile.repeat_rate > 0 and random.random() < profile.repeat_rate:
            words = text.split()
            if words:
                repeat_word = random.choice(words)
                words.append(repeat_word)
                text = " ".join(words)

        # Emoji injection
        if random.random() < profile.emoji_rate:
            drunk_emojis = ["🍺", "🍻", "🥂", "😅", "😂", "🎉", "🥴", "😵"]
            text += " " + random.choice(drunk_emojis)

        # Caps
        if profile.caps_rate > 0 and random.random() < profile.caps_rate:
            text = text.upper()

        return text

    def generate_nightlife_session(self) -> List[dict]:
        """Generate a full nightlife conversation arc."""
        arc = []
        states = [
            NightlifeState.SOBER_PLANNING,
            NightlifeState.TIPSY,
            NightlifeState.DRUNK,
            NightlifeState.POST_DRINKING,
        ]

        for state in states:
            msg = self.get_message(state)
            transformed = self.apply_drunk_transform(msg, state)
            arc.append({
                "state": state.value,
                "original": msg,
                "transformed": transformed,
                "profile": NIGHTLIFE_PROFILES[state],
                "expectations": NIGHTLIFE_AI_EXPECTATIONS.get(state, {}),
            })

        return arc

    def audit_nightlife_response(self, state: NightlifeState, response: str) -> dict:
        """Audit an AI response for nightlife appropriateness."""
        expectations = NIGHTLIFE_AI_EXPECTATIONS.get(state, {})
        violations = []
        passed = []

        profile = NIGHTLIFE_PROFILES.get(state)
        if not profile:
            return {"violations": [], "passed": ["no_nightlife_profile"]}

        # Check response length
        if state in [NightlifeState.DRUNK, NightlifeState.VERY_DRUNK]:
            if len(response) > 200:
                violations.append({
                    "rule": "response_too_long_for_drunk_user",
                    "severity": "HIGH",
                    "detail": "Drunk user needs ultra-short response",
                })
            else:
                passed.append("length_appropriate")

        # Check for alcohol lecturing
        lecture_patterns = [
            "uống rượu có hại", "không nên uống", "cẩn thận với rượu",
            "drinking is dangerous", "alcohol is harmful",
        ]
        if any(p in response.lower() for p in lecture_patterns):
            violations.append({
                "rule": "unsolicited_alcohol_lecture",
                "severity": "MEDIUM",
                "detail": "AI lectured user about alcohol when they just want help",
            })
        else:
            passed.append("no_unsolicited_lecture")

        # Check for hangover food appropriateness
        if state == NightlifeState.HUNGOVER:
            spicy_food = ["cay", "tiêu", "ớt", "kimchi", "lẩu"]
            if any(f in response.lower() for f in spicy_food):
                violations.append({
                    "rule": "spicy_food_for_hangover",
                    "severity": "HIGH",
                    "detail": "AI suggested spicy/heavy food for hungover user",
                })
            else:
                passed.append("hangover_appropriate_food")

        return {
            "nightlife_state": state.value,
            "violations": violations,
            "passed": passed,
            "nightlife_score": max(0.0, 1.0 - len(violations) * 0.3),
        }
