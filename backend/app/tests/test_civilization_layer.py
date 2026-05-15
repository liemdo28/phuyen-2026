from app.civilization.attention_guard import AttentionProtectionEngine
from app.civilization.city_flow import CityFlowEngine
from app.civilization.collective_rhythm import CollectiveRhythmEngine
from app.civilization.emotional_geography import EmotionalGeographyEngine
from app.civilization.planetary_model import PlanetaryHumanExperienceModel


def test_city_flow_detects_stress_propagation() -> None:
    state = CityFlowEngine().assess(
        movement_load=0.8,
        transport_pressure=0.75,
        crowd_density=0.7,
        emotional_density=0.65,
        recovery_zone_score=0.2,
    )
    assert state.stress_propagation_risk > 0.5
    assert state.notes


def test_attention_guard_reduces_notification_budget() -> None:
    decision = AttentionProtectionEngine().evaluate(
        digital_fragmentation=0.8,
        overload_risk=0.7,
        user_initiated=False,
    )
    assert decision.notification_budget <= 1
    assert decision.should_batch is True


def test_emotional_geography_finds_recovery_zone() -> None:
    zone = EmotionalGeographyEngine().classify(
        crowd_density=0.2,
        noise_level=0.2,
        shade_score=0.8,
        scenic_quality=0.75,
    )
    assert zone.name in {"recovery_zone", "calming_zone"}


def test_collective_rhythm_flags_burnout() -> None:
    state = CollectiveRhythmEngine().assess(
        stress_density=0.8,
        recovery_density=0.2,
        movement_intensity=0.7,
        social_intensity=0.6,
    )
    assert state.burnout_accumulation_risk > 0.5


def test_planetary_model_synthesizes_calm_flow() -> None:
    city = CityFlowEngine().assess(
        movement_load=0.35,
        transport_pressure=0.3,
        crowd_density=0.25,
        emotional_density=0.25,
        recovery_zone_score=0.75,
    )
    rhythm = CollectiveRhythmEngine().assess(
        stress_density=0.3,
        recovery_density=0.7,
        movement_intensity=0.4,
        social_intensity=0.35,
    )
    model = PlanetaryHumanExperienceModel().synthesize(
        city=city,
        rhythm=rhythm,
        emotionally_healthy_ratio=0.7,
    )
    assert model.calmness_score > 0.5
    assert model.recovery_capacity > 0.5
