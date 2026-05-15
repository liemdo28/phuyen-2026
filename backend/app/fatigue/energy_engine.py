from __future__ import annotations

from dataclasses import dataclass, field

from app.realtime.world_model import RealtimeWorldModel
from app.services.travel_companion import TravelCompanionState


@dataclass
class TravelEnergyState:
    physical_energy: float = 0.6
    emotional_energy: float = 0.6
    decision_energy: float = 0.6
    rest_pressure: float = 0.0
    simplify_pressure: float = 0.0
    exploration_readiness: float = 0.0
    signals: list[str] = field(default_factory=list)


class TravelEnergyEngine:
    def assess(self, companion: TravelCompanionState, world: RealtimeWorldModel) -> TravelEnergyState:
        state = TravelEnergyState()
        state.physical_energy = max(0.0, 0.82 - companion.fatigue * 0.55 - world.heat_pressure * 0.18 - world.traffic_pressure * 0.12)
        state.emotional_energy = max(0.0, 0.84 - companion.stress * 0.45 - companion.overwhelm * 0.3 - world.weather_risk * 0.12)
        state.decision_energy = max(0.0, 0.82 - companion.confusion * 0.4 - companion.overwhelm * 0.34 - world.tourist_density * 0.16)
        state.rest_pressure = min(1.0, (1.0 - state.physical_energy) * 0.55 + (1.0 - state.emotional_energy) * 0.45)
        state.simplify_pressure = min(1.0, (1.0 - state.decision_energy) * 0.7 + companion.stress * 0.2)
        state.exploration_readiness = min(1.0, companion.excitement * 0.45 + world.beach_quality * 0.25 + state.physical_energy * 0.2)

        if state.rest_pressure >= 0.5:
            state.signals.append("rest_needed")
        if state.simplify_pressure >= 0.45:
            state.signals.append("simplify_needed")
        if state.exploration_readiness >= 0.45:
            state.signals.append("exploration_window")
        return state
