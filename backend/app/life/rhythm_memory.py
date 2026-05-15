from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.models.domain import UserContext

_LR_PREFIX = "lr_"


@dataclass
class LifeRhythmState:
    daily_rhythm: str = "unknown"       # morning_person | night_owl | afternoon_peak | even_energy
    energy_cycle_phase: str = "unknown" # high | building | declining | recovery
    recovery_cycle_days: int = 0        # days since last deep recovery
    social_cycle: str = "balanced"      # craving_social | balanced | needing_solitude
    emotional_cycle: str = "stable"     # high | stable | low | recovering
    yearly_travel_rhythm: str = "unknown"  # frequent | seasonal | rare | first_time
    needs_excitement: bool = False
    needs_calmness: bool = False
    needs_solitude: bool = False
    needs_exploration: bool = False
    rhythm_insights: list[str] = field(default_factory=list)
    wellbeing_signals: dict[str, Any] = field(default_factory=dict)


class LifeRhythmMemory:
    """
    Learns and remembers the traveler's life rhythms across time:
    daily energy cycles, recovery patterns, social cycles, emotional
    cycles, and travel frequency. Enables the AI to understand WHEN
    the user needs excitement, calmness, solitude, or exploration.
    """

    def assess(self, context: UserContext, now: datetime) -> LifeRhythmState:
        prefs = context.preferences
        state = LifeRhythmState()

        # Retrieve persisted rhythm data
        morning_count = int(prefs.get(f"{_LR_PREFIX}morning_activity_count", 0))
        afternoon_count = int(prefs.get(f"{_LR_PREFIX}afternoon_activity_count", 0))
        evening_count = int(prefs.get(f"{_LR_PREFIX}evening_activity_count", 0))
        total_count = morning_count + afternoon_count + evening_count

        last_recovery_ts: str | None = prefs.get(f"{_LR_PREFIX}last_recovery_timestamp")
        cumulative_stress = float(prefs.get(f"{_LR_PREFIX}cumulative_stress", 0.0))
        cumulative_enjoyment = float(prefs.get(f"{_LR_PREFIX}cumulative_enjoyment", 0.5))
        social_interactions = int(prefs.get(f"{_LR_PREFIX}social_interaction_count", 0))
        solo_moments = int(prefs.get(f"{_LR_PREFIX}solo_moment_count", 0))
        trip_count = int(prefs.get(f"{_LR_PREFIX}total_trip_count", 0))

        # Infer daily rhythm
        hour = now.hour
        if total_count > 0:
            if morning_count / max(1, total_count) > 0.5:
                state.daily_rhythm = "morning_person"
            elif evening_count / max(1, total_count) > 0.45:
                state.daily_rhythm = "night_owl"
            elif afternoon_count / max(1, total_count) > 0.45:
                state.daily_rhythm = "afternoon_peak"
            else:
                state.daily_rhythm = "even_energy"
        else:
            # Infer from current hour
            if 5 <= hour <= 9:
                state.daily_rhythm = "morning_person"
            elif hour >= 21:
                state.daily_rhythm = "night_owl"

        # Infer energy cycle phase from cumulative signals
        if cumulative_stress > 0.65:
            state.energy_cycle_phase = "recovery"
        elif cumulative_stress > 0.45:
            state.energy_cycle_phase = "declining"
        elif cumulative_enjoyment > 0.65 and cumulative_stress < 0.3:
            state.energy_cycle_phase = "high"
        else:
            state.energy_cycle_phase = "building"

        # Days since last recovery
        if last_recovery_ts:
            try:
                last_recovery_dt = datetime.fromisoformat(last_recovery_ts)
                delta = now.replace(tzinfo=None) - last_recovery_dt.replace(tzinfo=None)
                state.recovery_cycle_days = delta.days
            except (ValueError, TypeError):
                state.recovery_cycle_days = 0

        # Social cycle
        total_social_signals = social_interactions + solo_moments
        if total_social_signals > 0:
            social_ratio = social_interactions / total_social_signals
            if social_ratio > 0.65:
                state.social_cycle = "craving_social"
            elif social_ratio < 0.35:
                state.social_cycle = "needing_solitude"
            else:
                state.social_cycle = "balanced"

        # Emotional cycle
        if cumulative_enjoyment > 0.7:
            state.emotional_cycle = "high"
        elif cumulative_stress > 0.55:
            state.emotional_cycle = "low"
        elif cumulative_stress > 0.35:
            state.emotional_cycle = "recovering"
        else:
            state.emotional_cycle = "stable"

        # Travel frequency
        if trip_count == 0:
            state.yearly_travel_rhythm = "first_time"
        elif trip_count <= 2:
            state.yearly_travel_rhythm = "rare"
        elif trip_count <= 5:
            state.yearly_travel_rhythm = "seasonal"
        else:
            state.yearly_travel_rhythm = "frequent"

        # Need inference
        state.needs_excitement = (
            state.energy_cycle_phase == "high" and
            state.emotional_cycle == "high" and
            state.social_cycle != "needing_solitude"
        )
        state.needs_calmness = (
            state.energy_cycle_phase in ("recovery", "declining") or
            cumulative_stress > 0.5
        )
        state.needs_solitude = state.social_cycle == "needing_solitude"
        state.needs_exploration = (
            state.energy_cycle_phase == "high" and
            state.yearly_travel_rhythm in ("rare", "first_time") and
            cumulative_enjoyment > 0.5
        )

        # Rhythm insights
        insights: list[str] = []
        if state.needs_calmness:
            insights.append(
                "Chu kỳ năng lượng cho thấy bạn đang cần không gian thở — "
                "chuyến đi lý tưởng sẽ có nhịp chậm và ít quyết định."
            )
        if state.needs_exploration and state.yearly_travel_rhythm in ("rare", "first_time"):
            insights.append("Bạn không đi nhiều — hãy tận dụng chuyến này để khám phá thật sự, không cần vội.")
        if state.needs_excitement:
            insights.append("Bạn đang ở đỉnh năng lượng và cảm xúc — thời điểm tốt để thử những trải nghiệm mới.")
        if state.needs_solitude:
            insights.append("Bạn đang cần không gian riêng — mình sẽ ưu tiên những góc yên tĩnh, ít đông đúc.")
        if state.recovery_cycle_days > 60:
            insights.append("Đã lâu bạn chưa có chuyến nghỉ thật sự. Đây là lúc để dừng lại và tái tạo.")

        state.rhythm_insights = insights[:2]
        state.wellbeing_signals = {
            "energy_phase": state.energy_cycle_phase,
            "needs_calmness": state.needs_calmness,
            "needs_exploration": state.needs_exploration,
            "social_cycle": state.social_cycle,
        }
        return state

    def record_activity(self, context: UserContext, now: datetime, activity_type: str) -> dict:
        """Returns preference updates after recording an activity event."""
        prefs = context.preferences
        hour = now.hour
        updates: dict = {}

        if hour < 12:
            updates[f"{_LR_PREFIX}morning_activity_count"] = int(prefs.get(f"{_LR_PREFIX}morning_activity_count", 0)) + 1
        elif hour < 17:
            updates[f"{_LR_PREFIX}afternoon_activity_count"] = int(prefs.get(f"{_LR_PREFIX}afternoon_activity_count", 0)) + 1
        else:
            updates[f"{_LR_PREFIX}evening_activity_count"] = int(prefs.get(f"{_LR_PREFIX}evening_activity_count", 0)) + 1

        if activity_type == "social":
            updates[f"{_LR_PREFIX}social_interaction_count"] = int(prefs.get(f"{_LR_PREFIX}social_interaction_count", 0)) + 1
        elif activity_type == "solo":
            updates[f"{_LR_PREFIX}solo_moment_count"] = int(prefs.get(f"{_LR_PREFIX}solo_moment_count", 0)) + 1
        elif activity_type == "trip_start":
            updates[f"{_LR_PREFIX}total_trip_count"] = int(prefs.get(f"{_LR_PREFIX}total_trip_count", 0)) + 1
        elif activity_type == "recovery":
            updates[f"{_LR_PREFIX}last_recovery_timestamp"] = now.isoformat()

        return updates
