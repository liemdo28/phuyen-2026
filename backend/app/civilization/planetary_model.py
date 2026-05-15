from __future__ import annotations

from dataclasses import dataclass, field

from app.civilization.city_flow import CityFlowState
from app.civilization.collective_rhythm import CollectiveRhythmState


@dataclass
class PlanetaryHumanExperienceState:
    calmness_score: float = 0.5
    overload_score: float = 0.5
    recovery_capacity: float = 0.5
    meaningful_experience_potential: float = 0.5
    summaries: list[str] = field(default_factory=list)


class PlanetaryHumanExperienceModel:
    def synthesize(
        self,
        *,
        city: CityFlowState,
        rhythm: CollectiveRhythmState,
        emotionally_healthy_ratio: float,
    ) -> PlanetaryHumanExperienceState:
        state = PlanetaryHumanExperienceState()
        state.calmness_score = min(1.0, max(0.0, city.calmness_index * 0.45 + rhythm.healthy_pacing_score * 0.35 + emotionally_healthy_ratio * 0.2))
        state.overload_score = min(1.0, max(0.0, city.stress_propagation_risk * 0.45 + rhythm.burnout_accumulation_risk * 0.35 + (1 - emotionally_healthy_ratio) * 0.2))
        state.recovery_capacity = min(1.0, max(0.0, city.recovery_zone_score * 0.45 + rhythm.work_recovery_balance * 0.35 + emotionally_healthy_ratio * 0.1))
        state.meaningful_experience_potential = min(
            1.0,
            max(0.0, state.calmness_score * 0.35 + state.recovery_capacity * 0.3 + (1 - state.overload_score) * 0.2),
        )
        if state.overload_score >= 0.55:
            state.summaries.append("System-wide overload is growing faster than recovery capacity.")
        if state.calmness_score >= 0.55:
            state.summaries.append("Calm human flow is achievable if low-noise orchestration is preserved.")
        return state
