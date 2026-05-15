from __future__ import annotations

from dataclasses import dataclass, field

# EMA decay for fatigue accumulation
_DECAY = 0.82

# Decision-load signals in Vietnamese
OVERLOAD_SIGNALS = [
    "nhiều quá", "không biết", "khó chọn", "rối quá", "cái nào",
    "chọn cái nào", "cũng được", "mình không biết", "tùy bạn",
    "thôi kệ", "mệt quá rồi", "không muốn nghĩ", "nản",
    "ừ thôi", "cũng ổn", "bạn chọn đi",
]
RECOVERY_SIGNALS = [
    "ok rồi", "được rồi", "ổn rồi", "biết rồi", "hiểu rồi",
    "theo kế hoạch", "cứ vậy đi", "tốt rồi",
]

# Triggers that add to decision load
DECISION_REQUEST_MARKERS = [
    "nên", "hay là", "hay không", "hay", "hoặc", "chọn",
    "đi đâu", "ăn gì", "uống gì", "làm gì giờ", "mấy giờ thì",
]


@dataclass
class DecisionFatigueState:
    fatigue_score: float = 0.0    # 0.0–1.0 accumulated decision load
    overload_detected: bool = False
    simplify_mode: bool = False   # true when should reduce options
    max_options: int = 3          # how many options to offer
    reply_mode: str = "normal"    # normal | simplified | single_choice | defer
    signals: list[str] = field(default_factory=list)
    hint: str = ""


class DecisionFatigueReducer:
    """
    Tracks accumulated decision load across a conversation.
    When the user shows signs of choice overload, the AI should:
    - reduce the number of recommendations
    - make ONE clear suggestion rather than N options
    - stop asking follow-up questions
    - pre-select the obvious best choice

    The goal: think less, stress less, move more smoothly.
    """

    def __init__(self) -> None:
        self._score: float = 0.0
        self._decision_count: int = 0   # how many decisions user made this session
        self._overload_count: int = 0   # consecutive overload signals

    def assess(self, text: str, context_fatigue: float = 0.0) -> DecisionFatigueState:
        t = text.lower().strip()
        state = DecisionFatigueState()

        # Detect overload signals
        overload_hits = sum(1 for s in OVERLOAD_SIGNALS if s in t)
        recovery_hits = sum(1 for s in RECOVERY_SIGNALS if s in t)
        decision_request = sum(1 for m in DECISION_REQUEST_MARKERS if m in t)

        # Update running score
        if overload_hits > 0:
            self._overload_count += 1
            signal_value = min(overload_hits * 0.20 + 0.30, 0.90)
            self._score = _ema(self._score, signal_value)
            state.signals.append("overload_detected")
        elif recovery_hits > 0:
            self._overload_count = 0
            self._score = _ema(self._score, 0.1)
            state.signals.append("recovery_signal")
        elif decision_request > 0:
            self._decision_count += 1
            # Gradual increase from repeated decision-making
            load = min(0.3 + self._decision_count * 0.05, 0.70)
            self._score = _ema(self._score, load)
            state.signals.append("decision_requested")

        # Blend with physiological fatigue
        blended = self._score * 0.7 + context_fatigue * 0.3
        blended = min(max(blended, 0.0), 1.0)

        state.fatigue_score = round(blended, 3)
        state.overload_detected = self._overload_count >= 2 or blended >= 0.45

        # Determine reply mode — overload_detected elevates the floor
        if blended >= 0.55 or (state.overload_detected and blended >= 0.35):
            state.reply_mode = "single_choice"
            state.max_options = 1
            state.simplify_mode = True
            state.hint = "Mình chọn một chỗ cụ thể cho bạn luôn nhé, không cần phải nghĩ thêm."
        elif blended >= 0.35 or state.overload_detected:
            state.reply_mode = "simplified"
            state.max_options = 2
            state.simplify_mode = True
            state.hint = "Mình rút gọn lại còn 2 lựa chọn để dễ quyết định hơn."
        elif blended >= 0.20:
            state.reply_mode = "normal"
            state.max_options = 2
            state.simplify_mode = False
        else:
            state.reply_mode = "normal"
            state.max_options = 3
            state.simplify_mode = False

        return state

    def reset(self) -> None:
        """Call when user confirms a decision successfully."""
        self._score = max(0.0, self._score - 0.25)
        self._overload_count = 0

    @property
    def current_score(self) -> float:
        return round(self._score, 3)

    def to_preference_updates(self) -> dict[str, object]:
        return {
            "df_score": round(self._score, 3),
            "df_decision_count": self._decision_count,
        }

    def load_from_preferences(self, preferences: dict) -> None:
        self._score = float(preferences.get("df_score", 0.0))
        self._decision_count = int(preferences.get("df_decision_count", 0))


def _ema(current: float, signal: float) -> float:
    return current * _DECAY + signal * (1 - _DECAY)


def simplify_reply(text: str, max_options: int, mode: str) -> str:
    """
    Post-process an AI reply to reduce cognitive load.
    - Truncate option lists beyond max_options
    - Remove hedging phrases when in single_choice mode
    - Keep Vietnamese natural language intact
    """
    if mode == "normal":
        return text

    lines = text.split("\n")
    option_lines = [l for l in lines if l.strip().startswith(("•", "-", "1.", "2.", "3.", "4.", "5."))]
    non_option_lines = [l for l in lines if l not in option_lines]

    if len(option_lines) > max_options:
        option_lines = option_lines[:max_options]

    result_lines = non_option_lines + option_lines
    result = "\n".join(l for l in result_lines if l.strip())

    if mode == "single_choice" and option_lines:
        # Extract just the first option as a direct recommendation
        first = option_lines[0].lstrip("•-123456789. ")
        return f"Mình gợi ý: {first}"

    return result
