from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CalmTechnologyDecision:
    should_interrupt: bool
    urgency: str = "low"
    allowed_surface: str = "chat_only"
    max_option_count: int = 3
    notification_budget: int = 1
    should_batch: bool = True
    rationale: list[str] = field(default_factory=list)


class CalmTechnologyPolicy:
    """
    Prevents the system from becoming intrusive, addictive, or manipulative.
    """

    def evaluate(
        self,
        *,
        future_stress: float,
        safety_risk: float,
        burnout_risk: float,
        option_count: int,
        user_initiated: bool,
        attention_noise_risk: float = 0.0,
        city_overload_risk: float = 0.0,
    ) -> CalmTechnologyDecision:
        rationale: list[str] = []
        urgency = "low"
        should_interrupt = False
        allowed_surface = "chat_only"
        max_option_count = min(max(option_count, 1), 4)
        notification_budget = 1 if user_initiated else 0
        should_batch = True
        combined_overload = min(1.0, burnout_risk * 0.4 + future_stress * 0.25 + attention_noise_risk * 0.2 + city_overload_risk * 0.15)

        if safety_risk >= 0.55:
            should_interrupt = True
            urgency = "high"
            allowed_surface = "priority_alert"
            max_option_count = 1
            notification_budget = 1
            should_batch = False
            rationale.append("Safety risk high enough to justify interruption.")
        elif combined_overload >= 0.55 or attention_noise_risk >= 0.6:
            should_interrupt = user_initiated
            urgency = "medium"
            max_option_count = 1 if attention_noise_risk >= 0.6 else 2
            notification_budget = 1 if user_initiated else 0
            should_batch = True
            rationale.append("Reduce cognitive load because projected stress/recovery risk is elevated.")
            if attention_noise_risk >= 0.45:
                rationale.append("Attention protection is active, so the system should collapse outputs into one calmer summary.")
        else:
            should_interrupt = False
            notification_budget = 1 if user_initiated else 0
            should_batch = attention_noise_risk >= 0.35
            rationale.append("Remain quiet unless user explicitly engages.")

        if not user_initiated and urgency == "low":
            allowed_surface = "silent_background"
        elif not user_initiated and urgency == "medium":
            allowed_surface = "passive_hint"

        return CalmTechnologyDecision(
            should_interrupt=should_interrupt,
            urgency=urgency,
            allowed_surface=allowed_surface,
            max_option_count=max_option_count,
            notification_budget=notification_budget,
            should_batch=should_batch,
            rationale=rationale,
        )
