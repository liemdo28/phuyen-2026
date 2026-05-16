from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.ethics.calm_technology import CalmTechnologyPolicy
from app.models.domain import UserContext
from app.orchestration.travel_brain import TravelBrain
from app.recovery.recovery_engine import RecoveryEngine
from app.schemas.assistant import AssistantIntent
from app.services.orchestrator import TelegramOrchestrator
from app.society.agent_society import TravelAgentSociety


async def _brain(text: str):
    now = datetime(2026, 5, 15, 18, 20, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    return await TravelBrain().assess(
        UserContext(chat_id=1, user_id=1),
        text,
        AssistantIntent(domain="travel", intent_type="query"),
        now=now,
    )


def test_truncate_option_lines_reduces_bullets() -> None:
    orchestrator = object.__new__(TelegramOrchestrator)
    text = "Gợi ý:\n• Quán A\n• Quán B\n• Quán C\n• Quán D"

    result = TelegramOrchestrator._truncate_option_lines(orchestrator, text, 2)

    assert "• Quán A" in result
    assert "• Quán B" in result
    assert "• Quán C" not in result
    assert "• Nếu cần mình mở thêm lựa chọn sau." in result


def test_compose_live_reply_adds_calm_prefix_and_guidance() -> None:
    orchestrator = object.__new__(TelegramOrchestrator)
    brain = __import__("asyncio").run(_brain("kẹt xe quá, đông quá, mệt và không biết đi đâu"))
    calm = CalmTechnologyPolicy().evaluate(
        future_stress=brain.operating.prediction.future_stress,
        safety_risk=brain.operating.safety.risk_level,
        burnout_risk=brain.emotional.burnout_risk,
        option_count=brain.option_count,
        user_initiated=True,
        attention_noise_risk=brain.attention_protection.noise_risk,
        city_overload_risk=brain.city_flow.stress_propagation_risk,
    )
    recovery = RecoveryEngine().build_plan(
        brain.emotional,
        brain.operating,
        brain.city_flow,
        brain.emotional_zone,
        brain.collective_rhythm,
    )
    society = TravelAgentSociety().coordinate(brain, calm, recovery)

    result = TelegramOrchestrator._compose_live_reply(
        orchestrator,
        "Mình có thể gợi ý vài chỗ:\n• Quán A\n• Quán B\n• Quán C",
        AssistantIntent(domain="travel", intent_type="query"),
        brain,
        calm,
        recovery,
        society,
    )

    assert (
        "Mình chốt gọn" in result
        or "Mình ưu tiên nhịp nhẹ" in result
        or "Mình gom lại ngắn gọn" in result
    )
    # "Giữ nhịp nhẹ:" is internal orchestration guidance — must NOT appear in user-facing reply
    assert "Giữ nhịp nhẹ:" not in result
