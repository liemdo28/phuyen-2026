from __future__ import annotations

from app.adapters.llm import _build_system_prompt
from app.services.orchestrator import TelegramOrchestrator


def test_build_system_prompt_includes_interaction_guidance() -> None:
    prompt = _build_system_prompt(
        "Trip status: ONGOING",
        "Protect the user's attention.\nCurrent response budget: at most 2 surfaced options.",
    )

    assert "## Current Trip State" in prompt
    assert "## Current Interaction Guidance" in prompt
    assert "Protect the user's attention." in prompt


def test_companion_interaction_guidance_reflects_low_friction_budget() -> None:
    orchestrator = object.__new__(TelegramOrchestrator)

    class _Brain:
        class CityFlow:
            stress_propagation_risk = 0.6

        class Attention:
            noise_risk = 0.55

        class Zone:
            name = "recovery_zone"

        class Operating:
            recommendation_posture = "protective"

        city_flow = CityFlow()
        attention_protection = Attention()
        emotional_zone = Zone()
        operating = Operating()

    class _Calm:
        max_option_count = 2
        should_batch = True

    class _Recovery:
        protect_energy = True

    guidance = TelegramOrchestrator._build_companion_interaction_guidance(
        orchestrator,
        _Brain(),
        _Calm(),
        _Recovery(),
    )

    assert "1-2 options" in guidance
    assert "Protect the user's attention" in guidance
    assert "Prioritize recovery" in guidance
