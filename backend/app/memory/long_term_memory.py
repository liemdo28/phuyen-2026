from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.models.domain import UserContext

# Keys in UserContext.preferences that persist long-term learning
_LT_PREFIX = "lt_"


@dataclass
class TripMemorySnapshot:
    trip_id: str
    destination: str
    emotional_highlight: str = ""
    favorite_place_type: str = ""
    pacing_score: float = 0.5        # 0=rushed, 1=leisurely
    avg_stress: float = 0.3
    avg_enjoyment: float = 0.6
    travel_style: str = "balanced"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LongTermMemoryState:
    affinity_places: list[str] = field(default_factory=list)
    travel_style_history: list[str] = field(default_factory=list)
    comfort_baselines: dict[str, float] = field(default_factory=dict)
    exploration_depth: float = 0.5
    avg_pacing_preference: float = 0.5
    repeat_destination_count: int = 0
    emotional_highlight_tags: list[str] = field(default_factory=list)
    memory_insights: list[str] = field(default_factory=list)
    cross_trip_patterns: dict[str, Any] = field(default_factory=dict)
    has_history: bool = False


class LongTermMemoryEngine:
    """
    Cross-trip memory engine: remembers previous trips, emotional highlights,
    favorite environments, and travel style evolution across visits.
    Enables the AI to say: 'Bạn thường thích các địa điểm yên tĩnh gần biển
    giống các chuyến đi trước.'
    """

    def assess(self, context: UserContext) -> LongTermMemoryState:
        prefs = context.preferences
        state = LongTermMemoryState()

        # Retrieve persisted long-term preferences
        affinity_places: list[str] = list(prefs.get(f"{_LT_PREFIX}affinity_places", []))
        style_history: list[str] = list(prefs.get(f"{_LT_PREFIX}style_history", []))
        emotional_tags: list[str] = list(prefs.get(f"{_LT_PREFIX}emotional_tags", []))
        visit_count: int = int(prefs.get(f"{_LT_PREFIX}visit_count", 0))
        avg_pacing: float = float(prefs.get(f"{_LT_PREFIX}avg_pacing", 0.5))
        avg_stress: float = float(prefs.get(f"{_LT_PREFIX}avg_stress", 0.3))
        avg_enjoyment: float = float(prefs.get(f"{_LT_PREFIX}avg_enjoyment", 0.6))
        exploration_depth: float = float(prefs.get(f"{_LT_PREFIX}exploration_depth", 0.5))

        # Comfort baselines from long-term patterns
        comfort_baselines: dict[str, float] = {
            "avg_stress": avg_stress,
            "avg_enjoyment": avg_enjoyment,
            "exploration_depth": exploration_depth,
            "avg_pacing": avg_pacing,
        }

        # Derive cross-trip patterns
        cross_trip_patterns: dict[str, Any] = {}
        if style_history:
            from collections import Counter
            style_counts = Counter(style_history)
            dominant_style = style_counts.most_common(1)[0][0]
            cross_trip_patterns["dominant_style"] = dominant_style
            cross_trip_patterns["style_diversity"] = len(style_counts) / max(1, len(style_history))
        if emotional_tags:
            cross_trip_patterns["top_emotional_tags"] = emotional_tags[:3]
        if affinity_places:
            cross_trip_patterns["favorite_place_types"] = affinity_places[:4]

        # Generate Vietnamese memory insights
        insights: list[str] = []
        has_history = visit_count > 0 or bool(affinity_places) or bool(style_history)

        if has_history:
            if "beach" in affinity_places or "quiet_beach" in affinity_places:
                insights.append(
                    "Bạn thường thích các địa điểm yên tĩnh gần biển giống các chuyến đi trước."
                )
            if avg_pacing < 0.35:
                insights.append(
                    "Nhìn lại các chuyến đi, bạn luôn thích lịch trình thư thả và không vội vã."
                )
            if "relax_traveler" in style_history[-3:] and len(style_history) >= 2:
                insights.append(
                    "Phong cách du lịch của bạn đang dần nghiêng về tận hưởng và thư giãn hơn là khám phá vội."
                )
            if visit_count >= 2:
                insights.append(
                    f"Đây là lần thứ {visit_count + 1} bạn khám phá Phú Yên — mình nhớ bạn thích những góc ít khách du lịch."
                )
            if avg_stress > 0.55:
                insights.append(
                    "Trong các chuyến trước, bạn đôi khi bị quá tải. Lần này mình sẽ cảnh báo sớm hơn."
                )

        state.affinity_places = affinity_places[:6]
        state.travel_style_history = style_history[-5:]
        state.comfort_baselines = comfort_baselines
        state.exploration_depth = exploration_depth
        state.avg_pacing_preference = avg_pacing
        state.repeat_destination_count = visit_count
        state.emotional_highlight_tags = emotional_tags[:5]
        state.memory_insights = insights[:2]
        state.cross_trip_patterns = cross_trip_patterns
        state.has_history = has_history
        return state

    def record_trip_snapshot(self, context: UserContext, snapshot: TripMemorySnapshot) -> dict[str, Any]:
        """Returns updated preferences dict to be merged into UserContext.preferences."""
        prefs = context.preferences
        affinity = list(prefs.get(f"{_LT_PREFIX}affinity_places", []))
        style_history = list(prefs.get(f"{_LT_PREFIX}style_history", []))
        emotional_tags = list(prefs.get(f"{_LT_PREFIX}emotional_tags", []))
        visit_count = int(prefs.get(f"{_LT_PREFIX}visit_count", 0))
        avg_pacing = float(prefs.get(f"{_LT_PREFIX}avg_pacing", 0.5))
        avg_stress = float(prefs.get(f"{_LT_PREFIX}avg_stress", 0.3))
        avg_enjoyment = float(prefs.get(f"{_LT_PREFIX}avg_enjoyment", 0.6))
        exploration_depth = float(prefs.get(f"{_LT_PREFIX}exploration_depth", 0.5))

        # Update rolling averages
        n = visit_count + 1
        avg_pacing = (avg_pacing * visit_count + snapshot.pacing_score) / n
        avg_stress = (avg_stress * visit_count + snapshot.avg_stress) / n
        avg_enjoyment = (avg_enjoyment * visit_count + snapshot.avg_enjoyment) / n

        style_history.append(snapshot.travel_style)
        if snapshot.favorite_place_type and snapshot.favorite_place_type not in affinity:
            affinity.append(snapshot.favorite_place_type)
        if snapshot.emotional_highlight and snapshot.emotional_highlight not in emotional_tags:
            emotional_tags.append(snapshot.emotional_highlight)

        if exploration_depth < 0.5 and snapshot.travel_style == "explorer":
            exploration_depth = min(1.0, exploration_depth + 0.1)

        return {
            f"{_LT_PREFIX}affinity_places": affinity[-8:],
            f"{_LT_PREFIX}style_history": style_history[-10:],
            f"{_LT_PREFIX}emotional_tags": emotional_tags[-8:],
            f"{_LT_PREFIX}visit_count": n,
            f"{_LT_PREFIX}avg_pacing": round(avg_pacing, 3),
            f"{_LT_PREFIX}avg_stress": round(avg_stress, 3),
            f"{_LT_PREFIX}avg_enjoyment": round(avg_enjoyment, 3),
            f"{_LT_PREFIX}exploration_depth": round(exploration_depth, 3),
        }
