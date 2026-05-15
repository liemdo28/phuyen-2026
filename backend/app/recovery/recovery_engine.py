from __future__ import annotations

from dataclasses import dataclass, field

from app.emotional.emotional_memory import EmotionalMemorySnapshot
from app.orchestration.travel_operating_system import TravelOperatingState


@dataclass
class RecoveryPlan:
    level: str = "light"
    actions: list[str] = field(default_factory=list)
    target_minutes: int = 0
    protect_energy: bool = False


class RecoveryEngine:
    def build_plan(
        self,
        emotional: EmotionalMemorySnapshot,
        operating: TravelOperatingState,
    ) -> RecoveryPlan:
        plan = RecoveryPlan()
        rest_pressure = operating.energy.rest_pressure
        simplify_pressure = operating.energy.simplify_pressure

        if emotional.burnout_risk >= 0.6 or rest_pressure >= 0.6:
            plan.level = "high"
            plan.target_minutes = 60
            plan.protect_energy = True
            plan.actions = [
                "Giảm một điểm dừng trong block tiếp theo.",
                "Ưu tiên chỗ ngồi nghỉ yên, mát, ít phải ra quyết định.",
                "Dời các hoạt động view/check-in sang sau khi năng lượng hồi lại.",
            ]
            return plan

        if emotional.burnout_risk >= 0.4 or simplify_pressure >= 0.45:
            plan.level = "medium"
            plan.target_minutes = 30
            plan.protect_energy = True
            plan.actions = [
                "Chèn một điểm cafe hoặc nghỉ ngắn trước khi đi tiếp.",
                "Rút số lựa chọn ăn/uống xuống còn 1-2 phương án.",
            ]
            return plan

        plan.level = "light"
        plan.target_minutes = 15
        plan.actions = [
            "Giữ nhịp hiện tại nhưng tránh cộng thêm quá nhiều micro-decisions.",
        ]
        return plan
