from __future__ import annotations

from dataclasses import dataclass, field

from app.realtime.world_model import RealtimeWorldModel
from app.social.group_dynamics import GroupDynamicsState


@dataclass
class SafetyState:
    risk_level: float = 0.0
    advisories: list[str] = field(default_factory=list)


class SafetyEngine:
    def assess(self, world: RealtimeWorldModel, group: GroupDynamicsState) -> SafetyState:
        state = SafetyState()
        state.risk_level = min(1.0, world.safety_risk + (0.1 if group.child_present else 0.0))
        if state.risk_level >= 0.35:
            state.advisories.append("Nếu đi tiếp lúc này, mình sẽ ưu tiên chỗ sáng, dễ quay về và ít phải đổi phương tiện.")
        return state
