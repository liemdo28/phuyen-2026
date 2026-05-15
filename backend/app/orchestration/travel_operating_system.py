from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.adaptation.rebalancer import ExperienceRebalancer, RebalanceState
from app.behavior.profile_engine import TravelBehaviorEngine, TravelBehaviorProfile
from app.emotional.journey_modeler import EmotionalJourneyModeler, EmotionalJourneyState
from app.environment.env_monitor import EnvironmentMonitor, EnvironmentState
from app.evolution.evolution_engine import EvolutionEngine, EvolutionState
from app.fatigue.energy_engine import TravelEnergyEngine, TravelEnergyState
from app.intelligence.travel_graph import TravelGraphEngine, TravelGraphState
from app.learning.feedback_engine import FeedbackEngine, FeedbackState
from app.local.local_intelligence import LocalIntelligenceEngine, LocalIntelligenceState
from app.memory.long_term_memory import LongTermMemoryEngine, LongTermMemoryState
from app.models.domain import UserContext
from app.personalization.human_rhythm import HumanRhythmEngine, HumanRhythmProfile
from app.prediction.journey_prediction import JourneyPredictionEngine, PredictionState
from app.realtime.world_model import RealtimeWorldModel, RealtimeWorldModelEngine
from app.rhythm.rhythm_engine import RhythmEngine, RhythmState
from app.safety.safety_engine import SafetyEngine, SafetyState
from app.schemas.assistant import AssistantIntent
from app.services.travel_companion import TravelCompanionState
from app.social.group_dynamics import GroupDynamicsEngine, GroupDynamicsState


@dataclass
class TravelOperatingState:
    # Core engines (Phase 1–5)
    world: RealtimeWorldModel
    energy: TravelEnergyState
    profile: TravelBehaviorProfile
    local: LocalIntelligenceState
    group: GroupDynamicsState
    prediction: PredictionState
    safety: SafetyState
    rhythm: RhythmState
    recommendation_posture: str = "balanced"
    preference_updates: dict[str, object] = field(default_factory=dict)

    # Phase 6 — Self-Evolving AI Travel Intelligence
    feedback: FeedbackState | None = None
    travel_graph: TravelGraphState | None = None
    emotional_journey: EmotionalJourneyState | None = None
    rebalance: RebalanceState | None = None
    long_term_memory: LongTermMemoryState | None = None
    human_rhythm: HumanRhythmProfile | None = None
    evolution: EvolutionState | None = None
    environment: EnvironmentState | None = None


class TravelOperatingSystem:
    def __init__(self) -> None:
        # Phase 1–5 engines
        self.world_model = RealtimeWorldModelEngine()
        self.energy = TravelEnergyEngine()
        self.behavior = TravelBehaviorEngine()
        self.local = LocalIntelligenceEngine()
        self.group = GroupDynamicsEngine()
        self.prediction = JourneyPredictionEngine()
        self.safety = SafetyEngine()
        self.rhythm = RhythmEngine()

        # Phase 6 engines
        self.feedback = FeedbackEngine()
        self.travel_graph = TravelGraphEngine()
        self.emotional_journey = EmotionalJourneyModeler()
        self.rebalancer = ExperienceRebalancer()
        self.long_term_memory = LongTermMemoryEngine()
        self.human_rhythm = HumanRhythmEngine()
        self.evolution = EvolutionEngine()
        self.env_monitor = EnvironmentMonitor()

    def assess(
        self,
        context: UserContext,
        incoming_text: str,
        companion_state: TravelCompanionState,
        intent: AssistantIntent,
        now: datetime | None = None,
    ) -> TravelOperatingState:
        local_now = now or datetime.now(ZoneInfo(context.timezone))

        # --- Phase 1–5 assessment ---
        world = self.world_model.assess(context, incoming_text, local_now)
        profile = self.behavior.assess(context, incoming_text)
        energy = self.energy.assess(companion_state, world)
        local_state = self.local.assess(incoming_text, local_now, world, profile)
        group = self.group.assess(incoming_text)
        prediction = self.prediction.assess(world, energy)
        safety = self.safety.assess(world, group)
        rhythm = self.rhythm.assess(energy, profile)

        # --- Phase 6 assessment ---
        feedback = self.feedback.assess(context, incoming_text)
        travel_graph = self.travel_graph.assess(incoming_text, local_now, world, profile)
        emotional_journey = self.emotional_journey.assess(
            companion_state, energy, world, profile, incoming_text
        )
        rebalance = self.rebalancer.assess(energy, emotional_journey, world, profile)
        long_term_memory = self.long_term_memory.assess(context)
        human_rhythm = self.human_rhythm.assess(context, local_now, energy)
        evolution = self.evolution.evolve(context, feedback, emotional_journey, long_term_memory)
        environment = self.env_monitor.assess(world, local_now, energy)

        # --- Posture decision (Phase 6 enhances original logic) ---
        posture = "balanced"
        if emotional_journey.emotional_safety_needed or emotional_journey.burnout_risk > 0.65:
            posture = "protective"
        elif energy.rest_pressure >= 0.5 or companion_state.response_mode == "comfort":
            posture = "protective"
        elif rebalance.expand_exploration and profile.primary_style in {"explorer", "photographer"}:
            posture = "expand"
        elif profile.primary_style in {"explorer", "photographer"} and energy.exploration_readiness >= 0.45:
            posture = "expand"
        elif prediction.traffic_issue_risk >= 0.4 or prediction.weather_interruption_risk >= 0.4:
            posture = "predictive"
        elif environment.reroute_needed:
            posture = "predictive"

        # --- Preference updates (Phase 6 merges learning signals) ---
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
        if feedback.evolution_signals:
            preference_updates.update(feedback.evolution_signals)
        if evolution.evolved_preferences:
            preference_updates.update(evolution.evolved_preferences)

        return TravelOperatingState(
            world=world,
            energy=energy,
            profile=profile,
            local=local_state,
            group=group,
            prediction=prediction,
            safety=safety,
            rhythm=rhythm,
            recommendation_posture=posture,
            preference_updates=preference_updates,
            feedback=feedback,
            travel_graph=travel_graph,
            emotional_journey=emotional_journey,
            rebalance=rebalance,
            long_term_memory=long_term_memory,
            human_rhythm=human_rhythm,
            evolution=evolution,
            environment=environment,
        )

    def enhance_reply(self, base_reply: str, state: TravelOperatingState, intent: AssistantIntent) -> str:
        if intent.domain != "travel":
            return base_reply

        hints: list[str] = []

        # --- Posture-based hints ---
        if state.recommendation_posture == "protective":
            hints.append("Mình sẽ ưu tiên phương án ít đổi chỗ, dễ nghỉ và bớt quyết định nhỏ.")
        elif state.recommendation_posture == "expand":
            hints.append("Nếu bạn còn năng lượng, mình có thể mở thêm một lựa chọn local hoặc góc chụp đẹp cùng hướng.")
        elif state.recommendation_posture == "predictive":
            hints.extend(state.prediction.warnings[:1])

        # --- Phase 6: Emotional journey insights ---
        if state.emotional_journey:
            if state.emotional_journey.safety_alerts:
                hints.extend(state.emotional_journey.safety_alerts[:1])
            elif state.emotional_journey.insights:
                hints.extend(state.emotional_journey.insights[:1])

        # --- Phase 6: Rebalance suggestion ---
        if state.rebalance and state.rebalance.suggestion and state.rebalance.rebalance_needed:
            hints.append(state.rebalance.suggestion)

        # --- Phase 6: Long-term memory recall ---
        if state.long_term_memory and state.long_term_memory.memory_insights:
            hints.extend(state.long_term_memory.memory_insights[:1])

        # --- Phase 6: Travel graph location timing ---
        if state.travel_graph and state.travel_graph.graph_insights:
            hints.extend(state.travel_graph.graph_insights[:1])

        # --- Phase 6: Environment alerts ---
        if state.environment and state.environment.alerts:
            hints.extend(state.environment.alerts[:1])

        # --- Phase 6: Human rhythm hints ---
        if state.human_rhythm and state.human_rhythm.insights:
            hints.extend(state.human_rhythm.insights[:1])

        # --- Phase 6: Evolution / learning insights ---
        if state.evolution and state.evolution.evolution_insights and state.evolution.intelligence_level in ("evolved", "instinctive"):
            hints.extend(state.evolution.evolution_insights[:1])

        # --- Phase 6: Feedback learning ---
        if state.feedback and state.feedback.learning_insights:
            hints.extend(state.feedback.learning_insights[:1])

        # --- Legacy hints ---
        hints.extend(state.local.insights[:1])
        hints.extend(state.safety.advisories[:1])
        hints.extend(state.rhythm.adjustments[:1])

        # Dedup and cap
        deduped: list[str] = []
        for hint in hints:
            if hint and hint not in deduped:
                deduped.append(hint)

        if not deduped:
            return base_reply

        hint_block = "\n".join(f"• {hint}" for hint in deduped[:3])
        return f"{base_reply}\n\nTravel OS:\n{hint_block}"
