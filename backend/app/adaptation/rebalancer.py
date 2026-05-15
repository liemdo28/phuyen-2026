from __future__ import annotations

from dataclasses import dataclass, field

from app.behavior.profile_engine import TravelBehaviorProfile
from app.emotional.journey_modeler import EmotionalJourneyState
from app.fatigue.energy_engine import TravelEnergyState
from app.realtime.world_model import RealtimeWorldModel


@dataclass
class RebalanceState:
    intensity_adjustment: float = 0.0    # -1.0 (reduce a lot) to +1.0 (expand a lot)
    pacing_adjustment: float = 0.0       # -1.0 (slow down) to +1.0 (speed up)
    activity_type_shift: str = "none"    # none | quieter | lighter | bolder | restorative
    urgency: str = "low"                 # low | medium | high | critical
    suggestion: str = ""                 # Vietnamese user-facing suggestion
    rebalance_needed: bool = False
    simplify_itinerary: bool = False
    expand_exploration: bool = False
    rest_window: bool = False
    signals: list[str] = field(default_factory=list)


class ExperienceRebalancer:
    """
    Continuously rebalances trip intensity, movement, activities, and emotional
    pacing throughout the journey. Prevents burnout while maximizing enjoyment.
    """

    def assess(
        self,
        energy: TravelEnergyState,
        emotional: EmotionalJourneyState,
        world: RealtimeWorldModel,
        profile: TravelBehaviorProfile,
    ) -> RebalanceState:
        state = RebalanceState()

        # --- Compute composite pressure ---
        fatigue_pressure = energy.rest_pressure
        stress_pressure = emotional.stress_accumulation
        burnout_pressure = emotional.burnout_risk
        exploration_pull = energy.exploration_readiness

        combined_reduce_pressure = (
            fatigue_pressure * 0.4 + stress_pressure * 0.35 + burnout_pressure * 0.25
        )

        # --- Determine intensity direction ---
        if combined_reduce_pressure > 0.65:
            state.intensity_adjustment = -0.8
            state.pacing_adjustment = -0.7
            state.activity_type_shift = "restorative"
            state.urgency = "high"
            state.rebalance_needed = True
            state.simplify_itinerary = True
            state.signals.append("major_downshift")
        elif combined_reduce_pressure > 0.45:
            state.intensity_adjustment = -0.45
            state.pacing_adjustment = -0.4
            state.activity_type_shift = "lighter"
            state.urgency = "medium"
            state.rebalance_needed = True
            state.signals.append("moderate_downshift")
        elif combined_reduce_pressure > 0.3:
            state.intensity_adjustment = -0.2
            state.pacing_adjustment = -0.15
            state.activity_type_shift = "quieter"
            state.urgency = "low"
            state.rebalance_needed = False
            state.signals.append("mild_downshift")
        elif exploration_pull > 0.55 and combined_reduce_pressure < 0.2:
            state.intensity_adjustment = 0.45
            state.pacing_adjustment = 0.3
            state.activity_type_shift = "bolder"
            state.urgency = "low"
            state.expand_exploration = True
            state.signals.append("expansion_window")

        # --- Rest window detection ---
        if energy.rest_pressure > 0.5 or emotional.recovery_timing in ("now", "urgent"):
            state.rest_window = True
            state.signals.append("rest_window_open")

        # --- Environmental adjustment ---
        if world.heat_pressure > 0.65:
            state.pacing_adjustment = min(0.0, state.pacing_adjustment - 0.2)
            state.signals.append("heat_slowdown")
        if world.traffic_pressure > 0.5:
            state.pacing_adjustment = min(0.0, state.pacing_adjustment - 0.15)
            state.signals.append("traffic_slowdown")
        if world.weather_risk > 0.4:
            state.activity_type_shift = "lighter" if state.activity_type_shift == "none" else state.activity_type_shift
            state.signals.append("weather_adjustment")

        # --- Build Vietnamese suggestion ---
        state.suggestion = self._build_suggestion(state, emotional, energy, profile)

        state.intensity_adjustment = round(max(-1.0, min(1.0, state.intensity_adjustment)), 3)
        state.pacing_adjustment = round(max(-1.0, min(1.0, state.pacing_adjustment)), 3)
        return state

    def _build_suggestion(
        self,
        state: RebalanceState,
        emotional: EmotionalJourneyState,
        energy: TravelEnergyState,
        profile: TravelBehaviorProfile,
    ) -> str:
        if state.urgency == "high" or emotional.burnout_risk > 0.65:
            return (
                "Hôm nay bạn đã di chuyển khá nhiều. "
                "Có thể tối nay nên chọn lịch trình nhẹ hơn để giữ sức cho ngày mai."
            )
        if state.urgency == "medium" and state.activity_type_shift == "lighter":
            return "Mình gợi ý thu hẹp lại kế hoạch buổi chiều — chọn một điểm thay vì hai sẽ dễ thở hơn."
        if state.activity_type_shift == "quieter":
            return "Nếu bạn muốn tiếp tục, hãy chọn những điểm yên tĩnh hơn để tái tạo năng lượng."
        if state.expand_exploration and profile.primary_style in {"explorer", "photographer"}:
            return "Bạn đang có năng lượng tốt. Mình có thể gợi thêm một điểm ít người biết gần đây nếu bạn muốn khám phá thêm."
        if state.rest_window:
            return "Đây là thời điểm tốt để nghỉ ngơi một chút trước khi tiếp tục hành trình."
        return ""
