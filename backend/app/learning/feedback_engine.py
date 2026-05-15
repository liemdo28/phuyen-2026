from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.models.domain import UserContext

SKIP_MARKERS = ["thôi", "không", "skip", "bỏ qua", "chán", "không thích", "đừng", "ít thôi"]
ACCEPT_MARKERS = ["ok", "được", "hay đó", "thích", "đúng rồi", "ổn", "tốt", "ok bạn ơi", "đi thôi"]
EXTEND_MARKERS = ["thêm", "tiếp", "nữa", "nhiều hơn", "lại đây", "quay lại", "hơn"]
QUIET_MARKERS = ["yên tĩnh", "vắng", "ít người", "chill", "nhẹ", "nhẹ nhàng", "không đông"]
CROWD_MARKERS = ["đông", "nhộn nhịp", "sầm uất", "nhiều người", "vui", "náo nhiệt"]
SLOW_MARKERS = ["chậm", "thư thả", "từ từ", "nhàn", "nghỉ ngơi", "không vội"]
FAST_MARKERS = ["nhanh", "gấp", "vội", "tiết kiệm thời gian", "nhiều chỗ", "dày"]


@dataclass
class RecommendationSignal:
    recommendation_type: str
    outcome: str  # accepted | skipped | extended | ignored
    context_tags: list[str] = field(default_factory=list)
    weight: float = 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BehavioralPattern:
    pattern_name: str
    score: float = 0.0
    confidence: float = 0.0
    trend: str = "stable"  # rising | falling | stable
    sample_count: int = 0


@dataclass
class FeedbackState:
    avoid_types: list[str] = field(default_factory=list)
    amplify_types: list[str] = field(default_factory=list)
    pacing_preference: float = 0.5  # 0=slow, 1=fast
    quiet_preference: float = 0.5   # 0=lively, 1=quiet
    acceptance_rate: float = 0.5
    skip_rate: float = 0.0
    patterns: dict[str, BehavioralPattern] = field(default_factory=dict)
    learning_insights: list[str] = field(default_factory=list)
    evolution_signals: dict[str, Any] = field(default_factory=dict)


class FeedbackEngine:
    """
    Self-learning engine that continuously learns from recommendation outcomes.
    Detects what users accept, skip, extend — and adapts future recommendations.
    """

    _PATTERN_DECAY = 0.85
    _MAX_PREFERENCE_HISTORY = 50

    def assess(self, context: UserContext, incoming_text: str) -> FeedbackState:
        text = incoming_text.lower()
        state = FeedbackState()
        prefs = context.preferences

        # --- Decode outcome signal from current message ---
        skip_score = sum(1 for m in SKIP_MARKERS if m in text) * 0.25
        accept_score = sum(1 for m in ACCEPT_MARKERS if m in text) * 0.2
        extend_score = sum(1 for m in EXTEND_MARKERS if m in text) * 0.22

        # --- Decode environmental preference signals ---
        quiet_score = sum(1 for m in QUIET_MARKERS if m in text) * 0.22
        crowd_score = sum(1 for m in CROWD_MARKERS if m in text) * 0.18
        slow_score = sum(1 for m in SLOW_MARKERS if m in text) * 0.22
        fast_score = sum(1 for m in FAST_MARKERS if m in text) * 0.18

        # --- Retrieve persisted learning state ---
        cumulative_skip = float(prefs.get("learned_skip_rate", 0.0))
        cumulative_accept = float(prefs.get("learned_accept_rate", 0.5))
        cumulative_quiet = float(prefs.get("learned_quiet_pref", 0.5))
        cumulative_pacing = float(prefs.get("learned_pacing_pref", 0.5))
        avoid_list: list[str] = list(prefs.get("learned_avoid_types", []))
        amplify_list: list[str] = list(prefs.get("learned_amplify_types", []))

        # --- Apply exponential moving average update ---
        if skip_score > 0:
            cumulative_skip = min(1.0, cumulative_skip * self._PATTERN_DECAY + skip_score * (1 - self._PATTERN_DECAY))
        if accept_score > 0:
            cumulative_accept = min(1.0, cumulative_accept * self._PATTERN_DECAY + accept_score * (1 - self._PATTERN_DECAY))
        if quiet_score > 0:
            cumulative_quiet = min(1.0, cumulative_quiet * self._PATTERN_DECAY + quiet_score * (1 - self._PATTERN_DECAY))
        elif crowd_score > 0:
            cumulative_quiet = max(0.0, cumulative_quiet * self._PATTERN_DECAY - crowd_score * (1 - self._PATTERN_DECAY))
        if slow_score > 0:
            cumulative_pacing = max(0.0, cumulative_pacing * self._PATTERN_DECAY - slow_score * (1 - self._PATTERN_DECAY))
        elif fast_score > 0:
            cumulative_pacing = min(1.0, cumulative_pacing * self._PATTERN_DECAY + fast_score * (1 - self._PATTERN_DECAY))

        # --- Detect category-level avoidance/amplification ---
        if "đông" in text and skip_score > 0 and "crowded" not in avoid_list:
            avoid_list.append("crowded")
        if "ồn" in text and skip_score > 0 and "noisy" not in avoid_list:
            avoid_list.append("noisy")
        if cumulative_quiet > 0.6 and "noisy" not in avoid_list:
            avoid_list.append("noisy")
        if cumulative_quiet > 0.65 and "crowded" not in avoid_list:
            avoid_list.append("crowded")

        if "biển" in text and extend_score > 0 and "beach" not in amplify_list:
            amplify_list.append("beach")
        if "cafe" in text and accept_score > 0 and "cafe" not in amplify_list:
            amplify_list.append("cafe")
        if "yên tĩnh" in text and accept_score > 0 and "quiet_spots" not in amplify_list:
            amplify_list.append("quiet_spots")

        # --- Build patterns ---
        patterns: dict[str, BehavioralPattern] = {}
        patterns["quiet_preference"] = BehavioralPattern(
            pattern_name="quiet_preference",
            score=cumulative_quiet,
            confidence=min(1.0, len(context.conversation) / 10),
            trend="rising" if quiet_score > 0 else "stable",
            sample_count=len(context.conversation),
        )
        patterns["pacing"] = BehavioralPattern(
            pattern_name="pacing",
            score=cumulative_pacing,
            confidence=min(1.0, len(context.conversation) / 12),
            trend="falling" if slow_score > 0 else ("rising" if fast_score > 0 else "stable"),
            sample_count=len(context.conversation),
        )
        patterns["skip_tendency"] = BehavioralPattern(
            pattern_name="skip_tendency",
            score=cumulative_skip,
            confidence=min(1.0, len(context.conversation) / 8),
            trend="rising" if skip_score > 0 else "stable",
            sample_count=len(context.conversation),
        )

        # --- Learning insights (Vietnamese) ---
        insights: list[str] = []
        if cumulative_skip > 0.45:
            insights.append("Bạn thường bỏ qua các gợi ý đông đúc hoặc ồn ào. Mình sẽ ưu tiên không gian yên hơn.")
        if cumulative_quiet > 0.65:
            insights.append("Bạn có xu hướng thích nơi ít người. Mình ghi nhận để lọc gợi ý phù hợp hơn.")
        if extend_score > 0:
            insights.append("Bạn muốn khám phá thêm — mình sẽ mở rộng gợi ý cho hướng này.")
        if cumulative_pacing < 0.3:
            insights.append("Bạn thích lịch trình thư thả. Mình sẽ tránh nhồi nhét nhiều điểm vào một ngày.")

        state.avoid_types = list(dict.fromkeys(avoid_list))[:6]
        state.amplify_types = list(dict.fromkeys(amplify_list))[:6]
        state.pacing_preference = cumulative_pacing
        state.quiet_preference = cumulative_quiet
        state.acceptance_rate = cumulative_accept
        state.skip_rate = cumulative_skip
        state.patterns = patterns
        state.learning_insights = insights
        state.evolution_signals = {
            "learned_skip_rate": round(cumulative_skip, 3),
            "learned_accept_rate": round(cumulative_accept, 3),
            "learned_quiet_pref": round(cumulative_quiet, 3),
            "learned_pacing_pref": round(cumulative_pacing, 3),
            "learned_avoid_types": state.avoid_types,
            "learned_amplify_types": state.amplify_types,
        }
        return state
