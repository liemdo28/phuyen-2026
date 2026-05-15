from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.behavior.profile_engine import TravelBehaviorEngine, TravelBehaviorProfile
from app.collective.experience_tracker import CollectiveExperienceTracker, CollectiveExperienceState
from app.collective.travel_dna import TravelDNA, TravelDNAEngine
from app.fatigue.energy_engine import TravelEnergyEngine, TravelEnergyState
from app.local.local_intelligence import LocalIntelligenceEngine, LocalIntelligenceState
from app.models.domain import UserContext
from app.prediction.journey_prediction import JourneyPredictionEngine, PredictionState
from app.realtime.world_model import RealtimeWorldModel, RealtimeWorldModelEngine
from app.rhythm.rhythm_engine import RhythmEngine, RhythmState
from app.safety.safety_engine import SafetyEngine, SafetyState
from app.schemas.assistant import AssistantIntent
from app.services.travel_companion import TravelCompanionState
from app.social.group_dynamics import GroupDynamicsEngine, GroupDynamicsState

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


@dataclass
class TravelOperatingState:
    world: RealtimeWorldModel
    energy: TravelEnergyState
    profile: TravelBehaviorProfile
    local: LocalIntelligenceState
    group: GroupDynamicsState
    prediction: PredictionState
    safety: SafetyState
    rhythm: RhythmState
    collective: CollectiveExperienceState | None = None
    travel_dna: TravelDNA | None = None
    recommendation_posture: str = "balanced"
    preference_updates: dict[str, object] = field(default_factory=dict)


class TravelOperatingSystem:
    def __init__(self) -> None:
        self.world_model = RealtimeWorldModelEngine()
        self.energy = TravelEnergyEngine()
        self.behavior = TravelBehaviorEngine()
        self.local = LocalIntelligenceEngine()
        self.group = GroupDynamicsEngine()
        self.prediction = JourneyPredictionEngine()
        self.safety = SafetyEngine()
        self.rhythm = RhythmEngine()
        # Phase 7: Collective Intelligence
        self.collective = CollectiveExperienceTracker()
        self.travel_dna = TravelDNAEngine()

    def assess(
        self,
        context: UserContext,
        incoming_text: str,
        companion_state: TravelCompanionState,
        intent: AssistantIntent,
        now: datetime | None = None,
    ) -> TravelOperatingState:
        local_now = now or datetime.now(VN_TZ)

        # Track experience signal (Phase 7)
        self.collective.track(incoming_text, local_now)

        # Core sub-engines
        world = self.world_model.assess(context, incoming_text, local_now)
        profile = self.behavior.assess(context, incoming_text)
        energy = self.energy.assess(companion_state, world)

        # Phase 7: Collective intelligence
        collective_state = self.collective.assess(local_now)
        user_id = getattr(context, "user_id", 0) or 0
        self.travel_dna.learn_from_behavior_profile(user_id, profile)
        travel_dna = self.travel_dna.get_dna(user_id)

        # Local intelligence with Phase 7 collective + DNA enrichment
        local_state = self.local.assess(
            incoming_text, local_now, world, profile,
            collective_state=collective_state,
            travel_dna=travel_dna,
        )
        group = self.group.assess(incoming_text)
        prediction = self.prediction.assess(world, energy)
        safety = self.safety.assess(world, group)
        rhythm = self.rhythm.assess(energy, profile)

        # Determine recommendation posture
        posture = "balanced"
        if energy.rest_pressure >= 0.5 or companion_state.response_mode == "comfort":
            posture = "protective"
        elif profile.primary_style in {"explorer", "photographer"} and energy.exploration_readiness >= 0.45:
            posture = "expand"
        elif prediction.traffic_issue_risk >= 0.4 or prediction.weather_interruption_risk >= 0.4:
            posture = "predictive"

        # Build preference updates
        preference_updates: dict[str, object] = {
            "travel_primary_style": profile.primary_style,
            "crowd_tolerance": round(profile.crowd_tolerance, 2),
            "comfort_bias": round(profile.comfort_bias, 2),
            "travel_posture": posture,
        }
        if profile.food_bias >= 0.35:
            preference_updates["prefers_food_experiences"] = True
        if profile.photo_bias >= 0.35:
            preference_updates["prefers_photo_spots"] = True

        # Phase 7: add collective and DNA to preferences
        if collective_state.collective_mood != "unknown":
            preference_updates["collective_mood"] = collective_state.collective_mood
        if collective_state.energy_trend:
            preference_updates["energy_trend"] = collective_state.energy_trend

        return TravelOperatingState(
            world=world,
            energy=energy,
            profile=profile,
            local=local_state,
            group=group,
            prediction=prediction,
            safety=safety,
            rhythm=rhythm,
            collective=collective_state,
            travel_dna=travel_dna,
            recommendation_posture=posture,
            preference_updates=preference_updates,
        )

    def enhance_reply(self, base_reply: str, state: TravelOperatingState, intent: AssistantIntent) -> str:
        if intent.domain != "travel":
            return base_reply

        hints: list[str] = []

        # Posture-based hints
        if state.recommendation_posture == "protective":
            hints.append("Mình sẽ ưu tiên phương án ít đổi chỗ, dễ nghỉ và bớt quyết định nhỏ.")
        elif state.recommendation_posture == "expand":
            hints.append("Nếu bạn còn năng lượng, mình có thể mở thêm một lựa chọn local hoặc góc chụp đẹp cùng hướng.")
        elif state.recommendation_posture == "predictive":
            hints.extend(state.prediction.warnings[:1])

        # Phase 7: Collective intelligence hints
        if state.collective is not None:
            if state.collective.timing_insights:
                hints.extend(state.collective.timing_insights[:1])
            if state.collective.energy_trend == "dipping" and state.recommendation_posture != "protective":
                hints.append("Năng lượng nhóm đang giảm — mình sẽ chọn phương án nhẹ hơn.")

        hints.extend(state.local.insights[:1])
        hints.extend(state.safety.advisories[:1])
        hints.extend(state.rhythm.adjustments[:1])

        # De-duplicate
        deduped: list[str] = []
        for hint in hints:
            if hint and hint not in deduped:
                deduped.append(hint)

        if not deduped:
            return base_reply

        hint_block = "\n".join(f"• {hint}" for hint in deduped[:2])
        return f"{base_reply}\n\nTravel OS:\n{hint_block}"