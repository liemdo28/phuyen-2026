from __future__ import annotations

from dataclasses import dataclass, field

from app.fatigue.energy_engine import TravelEnergyState
from app.realtime.world_model import RealtimeWorldModel


@dataclass
class PredictionState:
    future_stress: float = 0.0
    traffic_issue_risk: float = 0.0
    weather_interruption_risk: float = 0.0
    exhaustion_risk: float = 0.0
    overcrowding_risk: float = 0.0
    missed_timing_risk: float = 0.0
    warnings: list[str] = field(default_factory=list)


class JourneyPredictionEngine:
    def assess(self, world: RealtimeWorldModel, energy: TravelEnergyState) -> PredictionState:
        state = PredictionState()
        state.traffic_issue_risk = min(1.0, world.traffic_pressure * 0.75 + world.transport_flow * 0.2)
        state.weather_interruption_risk = min(1.0, world.weather_risk * 0.85 + world.heat_pressure * 0.15)
        state.exhaustion_risk = min(1.0, energy.rest_pressure * 0.75 + world.heat_pressure * 0.15)
        state.overcrowding_risk = min(1.0, world.tourist_density * 0.8 + world.local_activity * 0.1)
        state.future_stress = min(1.0, energy.simplify_pressure * 0.45 + state.traffic_issue_risk * 0.2 + state.overcrowding_risk * 0.2)
        state.missed_timing_risk = min(1.0, state.traffic_issue_risk * 0.4 + state.overcrowding_risk * 0.3 + world.event_intensity * 0.2)

        if state.traffic_issue_risk >= 0.4:
            state.warnings.append("Khoảng 1 tiếng nữa di chuyển có thể chậm hơn, nếu muốn thoải mái hơn thì nên đi sớm hơn một nhịp.")
        if state.weather_interruption_risk >= 0.4:
            state.warnings.append("Mình thấy rủi ro mưa/nóng khá cao, nên ưu tiên phương án có chỗ nghỉ và dễ trú hơn.")
        if state.exhaustion_risk >= 0.45:
            state.warnings.append("Năng lượng hôm nay có dấu hiệu tụt, nghỉ cafe hoặc giảm một điểm dừng sẽ dễ chịu hơn.")
        return state
