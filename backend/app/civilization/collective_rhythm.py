from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CollectiveRhythmState:
    work_recovery_balance: float = 0.5
    exploration_balance: float = 0.5
    burnout_accumulation_risk: float = 0.0
    healthy_pacing_score: float = 0.5
    observations: list[str] = field(default_factory=list)


class CollectiveRhythmEngine:
    def assess(
        self,
        *,
        stress_density: float,
        recovery_density: float,
        movement_intensity: float,
        social_intensity: float,
    ) -> CollectiveRhythmState:
        state = CollectiveRhythmState()
        state.work_recovery_balance = min(1.0, max(0.0, 0.5 + recovery_density * 0.3 - stress_density * 0.28))
        state.exploration_balance = min(1.0, max(0.0, 0.55 + movement_intensity * 0.12 - social_intensity * 0.08))
        state.burnout_accumulation_risk = min(
            1.0,
            stress_density * 0.35 + movement_intensity * 0.25 + social_intensity * 0.18 - recovery_density * 0.2,
        )
        state.healthy_pacing_score = min(
            1.0,
            max(
                0.0,
                0.8 - state.burnout_accumulation_risk * 0.45 + state.work_recovery_balance * 0.18,
            ),
        )
        if state.burnout_accumulation_risk >= 0.5:
            state.observations.append("Collective rhythm is drifting toward chronic overload.")
        if state.healthy_pacing_score >= 0.6:
            state.observations.append("The system is close to sustainable pacing.")
        return state
