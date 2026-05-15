from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.civilization.attention_guard import AttentionProtectionDecision, AttentionProtectionEngine
from app.civilization.city_flow import CityFlowEngine, CityFlowState
from app.civilization.collective_rhythm import CollectiveRhythmEngine, CollectiveRhythmState
from app.civilization.emotional_geography import EmotionalGeographyEngine, EmotionalZone
from app.civilization.planetary_model import PlanetaryHumanExperienceModel, PlanetaryHumanExperienceState
from app.emotional.emotional_memory import EmotionalMemoryEngine, EmotionalMemorySnapshot
from app.models.domain import UserContext
from app.orchestration.travel_operating_system import TravelOperatingState, TravelOperatingSystem
from app.personalization.profile_manager import PersonalizationManager, PersonalizationSnapshot
from app.realtime.live_context import LiveTravelContext, build_live_travel_context
from app.realtime.provider_registry import ProviderRegistry
from app.schemas.assistant import AssistantIntent
from app.services.travel_companion import TravelCompanionEngine, TravelCompanionState


@dataclass
class TravelBrainDecision:
    companion: TravelCompanionState
    operating: TravelOperatingState
    emotional: EmotionalMemorySnapshot
    personalization: PersonalizationSnapshot
    live_context: LiveTravelContext
    city_flow: CityFlowState
    attention_protection: AttentionProtectionDecision
    emotional_zone: EmotionalZone
    collective_rhythm: CollectiveRhythmState
    planetary: PlanetaryHumanExperienceState
    option_count: int
    guidance: list[str] = field(default_factory=list)
    preference_updates: dict[str, object] = field(default_factory=dict)


class TravelBrain:
    def __init__(self) -> None:
        self.companion = TravelCompanionEngine()
        self.operating_system = TravelOperatingSystem()
        self.emotional_memory = EmotionalMemoryEngine()
        self.personalization = PersonalizationManager()
        self.providers = ProviderRegistry()
        self.city_flow = CityFlowEngine()
        self.attention_guard = AttentionProtectionEngine()
        self.emotional_geography = EmotionalGeographyEngine()
        self.collective_rhythm = CollectiveRhythmEngine()
        self.planetary_model = PlanetaryHumanExperienceModel()

    async def assess(
        self,
        context: UserContext,
        incoming_text: str,
        intent: AssistantIntent,
        now: datetime | None = None,
    ) -> TravelBrainDecision:
        local_now = now or datetime.now(ZoneInfo(context.timezone))
        companion = self.companion.assess(context, incoming_text, intent=intent, now=local_now)
        operating = self.operating_system.assess(context, incoming_text, companion, intent, now=local_now)
        emotional = self.emotional_memory.build_snapshot(context, companion)
        personalization = self.personalization.build_snapshot(context, operating.profile, emotional, operating)
        provider_signals = await self.providers.collect(incoming_text, local_now)
        live_context = build_live_travel_context(provider_signals)

        transport_pressure = max(operating.world.traffic_pressure, live_context.traffic_pressure)
        crowd_density = max(operating.world.tourist_density, live_context.event_pressure)
        emotional_density = min(
            1.0,
            companion.stress * 0.4 + companion.overwhelm * 0.3 + emotional.burnout_risk * 0.3,
        )
        shade_score = max(0.0, 1.0 - operating.world.heat_pressure)
        scenic_quality = min(1.0, operating.world.beach_quality * 0.7 + operating.world.local_activity * 0.3)
        emotional_zone = self.emotional_geography.classify(
            crowd_density=crowd_density,
            noise_level=transport_pressure,
            shade_score=shade_score,
            scenic_quality=scenic_quality,
        )
        recovery_zone_score = emotional_zone.recovery_score
        city_flow = self.city_flow.assess(
            movement_load=min(
                1.0,
                operating.world.transport_flow * 0.45
                + transport_pressure * 0.35
                + operating.energy.rest_pressure * 0.2,
            ),
            transport_pressure=transport_pressure,
            crowd_density=crowd_density,
            emotional_density=emotional_density,
            recovery_zone_score=recovery_zone_score,
        )
        collective_rhythm = self.collective_rhythm.assess(
            stress_density=min(1.0, city_flow.stress_propagation_risk * 0.6 + emotional.burnout_risk * 0.4),
            recovery_density=recovery_zone_score,
            movement_intensity=city_flow.movement_load,
            social_intensity=min(1.0, operating.group.complexity + (0.15 if operating.group.needs_balance else 0.0)),
        )
        planetary = self.planetary_model.synthesize(
            city=city_flow,
            rhythm=collective_rhythm,
            emotionally_healthy_ratio=min(
                1.0,
                max(
                    0.0,
                    0.55
                    + emotional_zone.calm_score * 0.2
                    + recovery_zone_score * 0.15
                    - emotional.burnout_risk * 0.25,
                ),
            ),
        )
        attention_protection = self.attention_guard.evaluate(
            digital_fragmentation=min(1.0, companion.confusion * 0.45 + live_context.event_pressure * 0.2 + transport_pressure * 0.2),
            overload_risk=min(1.0, emotional.burnout_risk * 0.45 + city_flow.stress_propagation_risk * 0.35 + planetary.overload_score * 0.2),
            user_initiated=True,
        )

        option_count = 3
        if personalization.low_friction_mode or operating.recommendation_posture == "protective":
            option_count = 2
        elif operating.recommendation_posture == "expand":
            option_count = 4
        option_count = min(option_count, max(attention_protection.notification_budget, 1))
        if city_flow.stress_propagation_risk >= 0.55 or collective_rhythm.burnout_accumulation_risk >= 0.55:
            option_count = min(option_count, 2)

        guidance: list[str] = []
        guidance.extend(emotional.notes[:1])
        guidance.extend(personalization.notes[:1])
        guidance.extend(city_flow.notes[:1])
        guidance.extend(emotional_zone.notes[:1])
        guidance.extend(collective_rhythm.observations[:1])
        guidance.extend(attention_protection.recommendations[:1])
        guidance.extend(planetary.summaries[:1])
        if live_context.traffic_pressure >= 0.45:
            guidance.append("Realtime context đang nghiêng về traffic pressure cao, nên ưu tiên chặng ngắn hoặc đi sớm hơn.")
        if live_context.weather_pressure >= 0.45:
            guidance.append("Realtime context cho thấy weather sensitivity cao, nên chuẩn bị plan tránh mưa/nắng gắt.")
        guidance.extend(operating.prediction.warnings[:1])

        preference_updates = {
            **operating.preference_updates,
            **self.emotional_memory.preference_updates(companion),
            "option_count_preference": option_count,
        }
        if live_context.traffic_pressure >= 0.45:
            preference_updates["traffic_sensitive"] = True
        if live_context.weather_pressure >= 0.45:
            preference_updates["weather_sensitive"] = True
        preference_updates["calmness_index"] = round(city_flow.calmness_index, 2)
        preference_updates["attention_noise_risk"] = round(attention_protection.noise_risk, 2)
        preference_updates["recovery_zone"] = emotional_zone.name
        preference_updates["planetary_calmness"] = round(planetary.calmness_score, 2)

        return TravelBrainDecision(
            companion=companion,
            operating=operating,
            emotional=emotional,
            personalization=personalization,
            live_context=live_context,
            city_flow=city_flow,
            attention_protection=attention_protection,
            emotional_zone=emotional_zone,
            collective_rhythm=collective_rhythm,
            planetary=planetary,
            option_count=option_count,
            guidance=guidance[:3],
            preference_updates=preference_updates,
        )
