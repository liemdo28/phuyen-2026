from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CalmTechnologyDecision:
    should_interrupt: bool
    urgency: str = "low"
    allowed_surface: str = "chat_only"
    max_option_count: int = 3
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
    ) -> CalmTechnologyDecision:
        rationale: list[str] = []
        urgency = "low"
        should_interrupt = False
        allowed_surface = "chat_only"
        max_option_count = min(max(option_count, 1), 4)

        if safety_risk >= 0.55:
            should_interrupt = True
            urgency = "high"
            allowed_surface = "priority_alert"
            max_option_count = 1
            rationale.append("Safety risk high enough to justify interruption.")
        elif future_stress >= 0.55 or burnout_risk >= 0.55:
            should_interrupt = user_initiated
            urgency = "medium"
            max_option_count = 2
            rationale.append("Reduce cognitive load because projected stress/recovery risk is elevated.")
        else:
            should_interrupt = False
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
            rationale=rationale,
        )
