from __future__ import annotations

from dataclasses import dataclass, field

from app.civilization.city_flow import CityFlowState
from app.civilization.collective_rhythm import CollectiveRhythmState
from app.civilization.emotional_geography import EmotionalZone
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
        city_flow: CityFlowState | None = None,
        emotional_zone: EmotionalZone | None = None,
        collective_rhythm: CollectiveRhythmState | None = None,
    ) -> RecoveryPlan:
        plan = RecoveryPlan()
        rest_pressure = operating.energy.rest_pressure
        simplify_pressure = operating.energy.simplify_pressure
        city_stress = city_flow.stress_propagation_risk if city_flow else 0.0
        zone_name = emotional_zone.name if emotional_zone else ""
        rhythm_risk = collective_rhythm.burnout_accumulation_risk if collective_rhythm else 0.0

        if emotional.burnout_risk >= 0.6 or rest_pressure >= 0.6 or city_stress >= 0.62 or rhythm_risk >= 0.62:
            plan.level = "high"
            plan.target_minutes = 60
            plan.protect_energy = True
            plan.actions = [
                "Giảm một điểm dừng trong block tiếp theo.",
                "Ưu tiên chỗ ngồi nghỉ yên, mát, ít phải ra quyết định.",
                "Dời các hoạt động view/check-in sang sau khi năng lượng hồi lại.",
            ]
            if zone_name in {"recovery_zone", "calming_zone"}:
                plan.actions.append("Nếu gần đó có recovery/calming zone, ưu tiên ghé nghỉ thay vì cố di chuyển tiếp.")
            return plan

        if emotional.burnout_risk >= 0.4 or simplify_pressure >= 0.45 or city_stress >= 0.48:
            plan.level = "medium"
            plan.target_minutes = 30
            plan.protect_energy = True
            plan.actions = [
                "Chèn một điểm cafe hoặc nghỉ ngắn trước khi đi tiếp.",
                "Rút số lựa chọn ăn/uống xuống còn 1-2 phương án.",
            ]
            if zone_name == "overstimulating_zone":
                plan.actions.append("Tránh ở lại quá lâu trong khu vực overstimulating nếu chưa cần thiết.")
            return plan

        plan.level = "light"
        plan.target_minutes = 15
        plan.actions = [
            "Giữ nhịp hiện tại nhưng tránh cộng thêm quá nhiều micro-decisions.",
        ]
        if zone_name == "calming_zone":
            plan.actions.append("Có thể tận dụng khu vực này như một điểm nghỉ nhẹ để giữ nhịp calm lâu hơn.")
        return plan
