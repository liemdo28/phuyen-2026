from __future__ import annotations

from dataclasses import dataclass, field

from app.ethics.calm_technology import CalmTechnologyDecision
from app.orchestration.travel_brain import TravelBrainDecision
from app.recovery.recovery_engine import RecoveryPlan


@dataclass
class AgentAdvice:
    agent: str
    priority: int
    message: str


@dataclass
class SocietyDecision:
    advice: list[AgentAdvice] = field(default_factory=list)

    def top_messages(self, limit: int = 3) -> list[str]:
        ranked = sorted(self.advice, key=lambda item: (item.priority, item.agent))
        return [item.message for item in ranked[:limit]]


class TravelAgentSociety:
    """
    Cooperative skeleton for a future multi-agent travel ecosystem.
    Keeps agents aligned under calm-technology and human-centered constraints.
    """

    def coordinate(
        self,
        brain: TravelBrainDecision,
        calm: CalmTechnologyDecision,
        recovery: RecoveryPlan,
    ) -> SocietyDecision:
        advice: list[AgentAdvice] = []

        if brain.live_context.traffic_pressure >= 0.45:
            advice.append(
                AgentAdvice(
                    agent="routing_ai",
                    priority=1,
                    message="Routing AI: ưu tiên chặng ngắn hơn hoặc rời đi sớm để né traffic pressure.",
                )
            )
        if brain.live_context.weather_pressure >= 0.45:
            advice.append(
                AgentAdvice(
                    agent="weather_ai",
                    priority=1,
                    message="Weather AI: nghiêng về kế hoạch có chỗ trú hoặc indoor backup.",
                )
            )
        if recovery.protect_energy:
            advice.append(
                AgentAdvice(
                    agent="recovery_ai",
                    priority=0,
                    message=f"Recovery AI: nên chèn {recovery.target_minutes} phút hồi năng lượng trước khi tăng thêm hoạt động.",
                )
            )
        if brain.operating.profile.primary_style in {"explorer", "photographer"} and not recovery.protect_energy:
            advice.append(
                AgentAdvice(
                    agent="exploration_ai",
                    priority=2,
                    message="Exploration AI: có thể thêm một điểm local/hidden spot cùng hướng mà không tăng nhiều friction.",
                )
            )
        if calm.allowed_surface == "priority_alert":
            advice.append(
                AgentAdvice(
                    agent="safety_ai",
                    priority=0,
                    message="Safety AI: chỉ nên hiện cảnh báo ngắn, rõ, và ưu tiên phương án an toàn nhất.",
                )
            )

        if not advice:
            advice.append(
                AgentAdvice(
                    agent="orchestration_ai",
                    priority=3,
                    message="Orchestration AI: giữ hệ ở chế độ yên, chỉ hỗ trợ khi thật sự có giá trị.",
                )
            )

        return SocietyDecision(advice=advice)
