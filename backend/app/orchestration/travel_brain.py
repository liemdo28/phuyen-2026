from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

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

        option_count = 3
        if personalization.low_friction_mode or operating.recommendation_posture == "protective":
            option_count = 2
        elif operating.recommendation_posture == "expand":
            option_count = 4

        guidance: list[str] = []
        guidance.extend(emotional.notes[:1])
        guidance.extend(personalization.notes[:1])
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

        return TravelBrainDecision(
            companion=companion,
            operating=operating,
            emotional=emotional,
            personalization=personalization,
            live_context=live_context,
            option_count=option_count,
            guidance=guidance[:3],
            preference_updates=preference_updates,
        )
