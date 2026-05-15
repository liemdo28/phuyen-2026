from __future__ import annotations

from dataclasses import dataclass, field

from app.behavior.profile_engine import TravelBehaviorProfile
from app.fatigue.energy_engine import TravelEnergyState


@dataclass
class RhythmState:
    pacing_mode: str = "balanced"
    adjustments: list[str] = field(default_factory=list)


class RhythmEngine:
    def assess(self, energy: TravelEnergyState, profile: TravelBehaviorProfile) -> RhythmState:
        state = RhythmState()
        if energy.rest_pressure >= 0.5:
            state.pacing_mode = "slow_down"
            state.adjustments.append("Giảm nhịp: ít điểm dừng hơn, ưu tiên nghỉ và các chặng ngắn.")
        elif energy.exploration_readiness >= 0.45 and profile.primary_style in {"explorer", "photographer", "foodie"}:
            state.pacing_mode = "explore"
            state.adjustments.append("Có thể mở rộng thêm một điểm trải nghiệm nếu cùng hướng và không tăng friction quá nhiều.")
        return state
