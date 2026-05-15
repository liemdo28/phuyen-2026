from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CityFlowState:
    movement_load: float = 0.0
    transport_pressure: float = 0.0
    crowd_density: float = 0.0
    emotional_density: float = 0.0
    recovery_zone_score: float = 0.0
    stress_propagation_risk: float = 0.0
    calmness_index: float = 0.5
    notes: list[str] = field(default_factory=list)


class CityFlowEngine:
    def assess(
        self,
        *,
        movement_load: float,
        transport_pressure: float,
        crowd_density: float,
        emotional_density: float,
        recovery_zone_score: float,
    ) -> CityFlowState:
        state = CityFlowState(
            movement_load=min(max(movement_load, 0.0), 1.0),
            transport_pressure=min(max(transport_pressure, 0.0), 1.0),
            crowd_density=min(max(crowd_density, 0.0), 1.0),
            emotional_density=min(max(emotional_density, 0.0), 1.0),
            recovery_zone_score=min(max(recovery_zone_score, 0.0), 1.0),
        )
        state.stress_propagation_risk = min(
            1.0,
            state.movement_load * 0.22
            + state.transport_pressure * 0.28
            + state.crowd_density * 0.24
            + state.emotional_density * 0.18
            - state.recovery_zone_score * 0.18,
        )
        state.calmness_index = min(
            1.0,
            max(
                0.0,
                0.85
                - state.movement_load * 0.18
                - state.transport_pressure * 0.2
                - state.crowd_density * 0.16
                - state.emotional_density * 0.14
                + state.recovery_zone_score * 0.25,
            ),
        )
        if state.stress_propagation_risk >= 0.55:
            state.notes.append("City stress is likely to cascade across movement corridors.")
        if state.recovery_zone_score >= 0.55:
            state.notes.append("Recovery environments are strong enough to buffer pressure locally.")
        return state
