from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.adaptation.rebalancer import ExperienceRebalancer, RebalanceState
from app.behavior.profile_engine import TravelBehaviorEngine, TravelBehaviorProfile
from app.dna.travel_dna import TravelDNAEngine, TravelDNAProfile
from app.emotional.geography_engine import EmotionalGeographyEngine, GeographyState
from app.emotional.journey_modeler import EmotionalJourneyModeler, EmotionalJourneyState
from app.environment.env_monitor import EnvironmentMonitor, EnvironmentState
from app.evolution.evolution_engine import EvolutionEngine, EvolutionState
from app.fatigue.energy_engine import TravelEnergyEngine, TravelEnergyState
from app.intelligence.travel_graph import TravelGraphEngine, TravelGraphState
from app.learning.feedback_engine import FeedbackEngine, FeedbackState
from app.life.context_engine import LifeContextEngine, LifeContextState
from app.life.life_memory import LifeMemoryEngine, LifeMemoryState
from app.life.life_orchestrator import LifeOrchestrator, LifeOrchestrationState
from app.life.rhythm_memory import LifeRhythmMemory, LifeRhythmState
from app.local.local_intelligence import LocalIntelligenceEngine, LocalIntelligenceState
from app.memory.long_term_memory import LongTermMemoryEngine, LongTermMemoryState
from app.models.domain import UserContext
from app.orchestration.travel_flow_orchestrator import TravelFlowOrchestrator, TravelFlowState
from app.personalization.human_rhythm import HumanRhythmEngine, HumanRhythmProfile
from app.prediction.journey_prediction import JourneyPredictionEngine, PredictionState
from app.realtime.world_model import RealtimeWorldModel, RealtimeWorldModelEngine
from app.rhythm.rhythm_engine import RhythmEngine, RhythmState
from app.safety.safety_engine import SafetyEngine, SafetyState
from app.schemas.assistant import AssistantIntent
from app.services.decision_fatigue_reducer import DecisionFatigueReducer, DecisionFatigueState
from app.services.travel_companion import TravelCompanionState
from app.social.group_dynamics import GroupDynamicsEngine, GroupDynamicsState
from app.wellbeing.calm_ux import CalmTechnologyEngine, CalmUXState
from app.wellbeing.optimizer import WellbeingOptimizationState, WellbeingOptimizer


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

    # Phase 8 — AI Life Companion
    life_context: LifeContextState | None = None
    life_rhythm: LifeRhythmState | None = None
    wellbeing: WellbeingOptimizationState | None = None
    travel_dna: TravelDNAProfile | None = None
    calm_ux: CalmUXState | None = None
    life_memory: LifeMemoryState | None = None
    life_orchestration: LifeOrchestrationState | None = None

    # Part 2 — Real-World Human Experience Orchestration
    travel_flow: TravelFlowState | None = None
    geography: GeographyState | None = None
    decision_fatigue: DecisionFatigueState | None = None


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

        # Phase 8 engines
        self.life_context = LifeContextEngine()
        self.life_rhythm = LifeRhythmMemory()
        self.wellbeing_optimizer = WellbeingOptimizer()
        self.travel_dna = TravelDNAEngine()
        self.calm_ux = CalmTechnologyEngine()
        self.life_memory = LifeMemoryEngine()
        self.life_orchestrator = LifeOrchestrator()

        # Part 2 — Real-World Human Experience Orchestration
        self.travel_flow = TravelFlowOrchestrator()
        self.geography = EmotionalGeographyEngine()
        self.decision_fatigue = DecisionFatigueReducer()

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

        # --- Phase 8 assessment ---
        life_context = self.life_context.assess(context, incoming_text)
        life_rhythm = self.life_rhythm.assess(context, local_now)
        wellbeing = self.wellbeing_optimizer.optimize(life_context, life_rhythm, energy, emotional_journey)
        travel_dna = self.travel_dna.assess(context, profile, life_context, human_rhythm)
        calm_ux = self.calm_ux.assess(life_context, emotional_journey, wellbeing, travel_dna)
        life_mem = self.life_memory.assess(context)
        life_orchestration = self.life_orchestrator.orchestrate(
            life_context, life_rhythm, life_mem, emotional_journey,
            energy, wellbeing, calm_ux, travel_dna,
        )

        # --- Part 2: Real-world human experience orchestration ---
        travel_flow = self.travel_flow.assess(
            hour=local_now.hour,
            fatigue=companion_state.fatigue,
            weather_risk=world.weather_risk,
            tourist_density=world.tourist_density,
            incoming_text=incoming_text,
            preferences=context.preferences,
        )
        geography = self.geography.get_state()
        decision_fatigue = self.decision_fatigue.assess(incoming_text, companion_state.fatigue)

        # --- Posture decision (Phase 6 + 8 enhance logic) ---
        posture = "balanced"
        if emotional_journey.emotional_safety_needed or emotional_journey.burnout_risk > 0.65:
            posture = "protective"
        elif life_context.burnout_detected or wellbeing.score.grade == "critical":
            posture = "protective"
        elif energy.rest_pressure >= 0.5 or companion_state.response_mode == "comfort":
            posture = "protective"
        elif life_orchestration.trip_as_therapy:
            posture = "protective"
        elif rebalance.expand_exploration and profile.primary_style in {"explorer", "photographer"}:
            posture = "expand"
        elif profile.primary_style in {"explorer", "photographer"} and energy.exploration_readiness >= 0.45:
            posture = "expand"
        elif life_rhythm.needs_exploration and wellbeing.score.grade in ("good", "thriving"):
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
            life_context=life_context,
            life_rhythm=life_rhythm,
            wellbeing=wellbeing,
            travel_dna=travel_dna,
            calm_ux=calm_ux,
            life_memory=life_mem,
            life_orchestration=life_orchestration,
            travel_flow=travel_flow,
            geography=geography,
            decision_fatigue=decision_fatigue,
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

        # --- Phase 8: Life companion voice (highest priority if present) ---
        if state.life_orchestration and state.life_orchestration.companion_message:
            hints.insert(0, state.life_orchestration.companion_message)

        # --- Phase 8: Wellbeing insights ---
        if state.wellbeing and state.wellbeing.wellbeing_insights:
            hints.extend(state.wellbeing.wellbeing_insights[:1])

        # --- Phase 8: Life context ---
        if state.life_context and state.life_context.life_insights:
            hints.extend(state.life_context.life_insights[:1])

        # --- Phase 8: Life rhythm ---
        if state.life_rhythm and state.life_rhythm.rhythm_insights:
            hints.extend(state.life_rhythm.rhythm_insights[:1])

        # --- Phase 8: Travel DNA personalization ---
        if state.travel_dna and state.travel_dna.personalization_hints:
            hints.extend(state.travel_dna.personalization_hints[:1])

        # --- Phase 8: Life memory continuity ---
        if state.life_memory and state.life_memory.continuity_message and state.life_memory.travel_life_chapter in ("experienced", "reflective"):
            hints.append(state.life_memory.continuity_message)

        # --- Part 2: Travel flow arc hint ---
        if state.travel_flow and state.travel_flow.hint:
            hints.append(state.travel_flow.hint)

        # --- Part 2: Decision fatigue (override max options) ---
        if state.decision_fatigue and state.decision_fatigue.hint:
            hints.insert(0, state.decision_fatigue.hint)

        # --- Part 2: Geography insight ---
        if state.geography and state.geography.hint:
            hints.append(state.geography.hint)

        # --- Legacy hints ---
        hints.extend(state.local.insights[:1])
        hints.extend(state.safety.advisories[:1])
        hints.extend(state.rhythm.adjustments[:1])

        # Determine hint cap from Calm UX (Phase 8)
        hint_cap = state.calm_ux.hint_count_limit if state.calm_ux else 3

        # Dedup and cap
        deduped: list[str] = []
        for hint in hints:
            if hint and hint not in deduped:
                deduped.append(hint)

        if not deduped:
            return base_reply

        hint_block = "\n".join(f"• {hint}" for hint in deduped[:hint_cap])
        return f"{base_reply}\n\nTravel OS:\n{hint_block}"
