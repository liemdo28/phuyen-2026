from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AttentionProtectionDecision:
    notification_budget: int = 0
    should_batch: bool = True
    should_interrupt: bool = False
    noise_risk: float = 0.0
    recommendations: list[str] = field(default_factory=list)


class AttentionProtectionEngine:
    def evaluate(
        self,
        *,
        digital_fragmentation: float,
        overload_risk: float,
        user_initiated: bool,
    ) -> AttentionProtectionDecision:
        noise_risk = min(1.0, digital_fragmentation * 0.55 + overload_risk * 0.45)
        budget = 1 if user_initiated else 0
        should_interrupt = False
        should_batch = True
        recommendations: list[str] = []

        if noise_risk >= 0.6:
            budget = 1 if user_initiated else 0
            should_batch = True
            recommendations.append("Collapse outputs into one calm summary.")
        elif noise_risk >= 0.35:
            budget = 2 if user_initiated else 1
            should_batch = True
            recommendations.append("Prefer low-frequency hints over multiple nudges.")
        else:
            budget = 3 if user_initiated else 1
            should_batch = False

        if user_initiated and overload_risk < 0.35:
            should_interrupt = True

        return AttentionProtectionDecision(
            notification_budget=budget,
            should_batch=should_batch,
            should_interrupt=should_interrupt,
            noise_risk=noise_risk,
            recommendations=recommendations,
        )
