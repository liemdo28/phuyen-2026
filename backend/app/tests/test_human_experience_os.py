from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.ethics.calm_technology import CalmTechnologyPolicy
from app.orchestration.travel_brain import TravelBrain
from app.recovery.recovery_engine import RecoveryEngine
from app.schemas.assistant import AssistantIntent
from app.society.agent_society import TravelAgentSociety
from app.models.domain import UserContext


async def _brain(text: str):
    now = datetime(2026, 5, 15, 18, 15, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    return await TravelBrain().assess(
        UserContext(chat_id=1, user_id=1),
        text,
        AssistantIntent(domain="travel", intent_type="query"),
        now=now,
    )


def test_calm_policy_stays_quiet_when_low_risk() -> None:
    decision = CalmTechnologyPolicy().evaluate(
        future_stress=0.2,
        safety_risk=0.1,
        burnout_risk=0.2,
        option_count=3,
        user_initiated=False,
    )
    assert decision.should_interrupt is False
    assert decision.allowed_surface == "silent_background"


def test_recovery_engine_protects_energy() -> None:
    brain = __import__("asyncio").run(_brain("mệt quá, không biết đi đâu nữa"))
    plan = RecoveryEngine().build_plan(brain.emotional, brain.operating)
    assert plan.level in {"medium", "high", "light"}
    assert plan.actions


def test_agent_society_returns_human_centered_guidance() -> None:
    brain = __import__("asyncio").run(_brain("mưa không, traffic giờ về khách sạn có kẹt xe không"))
    calm = CalmTechnologyPolicy().evaluate(
        future_stress=brain.operating.prediction.future_stress,
        safety_risk=brain.operating.safety.risk_level,
        burnout_risk=brain.emotional.burnout_risk,
        option_count=brain.option_count,
        user_initiated=True,
    )
    recovery = RecoveryEngine().build_plan(brain.emotional, brain.operating)
    society = TravelAgentSociety().coordinate(brain, calm, recovery)

    assert society.top_messages()
