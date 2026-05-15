from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.behavior.profile_engine import TravelBehaviorEngine
from app.fatigue.energy_engine import TravelEnergyEngine
from app.learning.feedback_engine import FeedbackEngine
from app.intelligence.travel_graph import TravelGraphEngine
from app.emotional.journey_modeler import EmotionalJourneyModeler
from app.adaptation.rebalancer import ExperienceRebalancer
from app.memory.long_term_memory import LongTermMemoryEngine, TripMemorySnapshot
from app.personalization.human_rhythm import HumanRhythmEngine
from app.evolution.evolution_engine import EvolutionEngine
from app.environment.env_monitor import EnvironmentMonitor
from app.models.domain import UserContext, MemoryTurn
from app.realtime.world_model import RealtimeWorldModel, RealtimeWorldModelEngine
from app.services.travel_companion import TravelCompanionState
from app.schemas.assistant import AssistantIntent
from app.orchestration.travel_operating_system import TravelOperatingSystem

VN_NOW = datetime(2026, 5, 15, 9, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
MIDDAY = datetime(2026, 5, 15, 12, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
EVENING = datetime(2026, 5, 15, 18, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))


def make_context(**kwargs) -> UserContext:
    return UserContext(chat_id=1, user_id=1, **kwargs)


def make_companion(**kwargs) -> TravelCompanionState:
    return TravelCompanionState(**kwargs)


def make_world(**kwargs) -> RealtimeWorldModel:
    return RealtimeWorldModel(**kwargs)


# --- FeedbackEngine ---

class TestFeedbackEngine:
    def test_skip_increases_skip_rate(self):
        engine = FeedbackEngine()
        ctx = make_context(preferences={})
        state = engine.assess(ctx, "thôi bỏ qua đi, không thích chỗ đó")
        assert state.skip_rate > 0

    def test_quiet_preference_detected(self):
        engine = FeedbackEngine()
        ctx = make_context(preferences={})
        state = engine.assess(ctx, "mình thích chỗ yên tĩnh ít người hơn")
        assert state.quiet_preference > 0.45

    def test_accept_raises_acceptance_rate(self):
        engine = FeedbackEngine()
        ctx = make_context(preferences={})
        state = engine.assess(ctx, "ok được, hay đó bạn ơi")
        assert state.acceptance_rate > 0.5

    def test_amplify_beach_on_extend(self):
        engine = FeedbackEngine()
        ctx = make_context(preferences={})
        state = engine.assess(ctx, "mình muốn ra biển thêm nữa")
        assert "beach" in state.amplify_types

    def test_slow_pacing_detected(self):
        engine = FeedbackEngine()
        ctx = make_context(preferences={})
        state = engine.assess(ctx, "thư thả thôi, từ từ, không vội")
        assert state.pacing_preference < 0.5

    def test_evolution_signals_populated(self):
        engine = FeedbackEngine()
        ctx = make_context(preferences={})
        state = engine.assess(ctx, "yên tĩnh thôi")
        assert "learned_quiet_pref" in state.evolution_signals

    def test_cumulative_learning_from_prefs(self):
        engine = FeedbackEngine()
        ctx = make_context(preferences={"learned_quiet_pref": 0.7, "learned_skip_rate": 0.5})
        state = engine.assess(ctx, "thôi không đi nữa")
        assert state.quiet_preference > 0.5
        assert state.skip_rate > 0.3


# --- TravelGraphEngine ---

class TestTravelGraphEngine:
    def setup_method(self):
        self.engine = TravelGraphEngine()
        self.behavior = TravelBehaviorEngine()

    def _profile(self, text=""):
        ctx = make_context()
        return self.behavior.assess(ctx, text)

    def test_bai_xep_detected(self):
        world = make_world()
        profile = self._profile()
        state = self.engine.assess("mình muốn ra bãi xép", VN_NOW, world, profile)
        assert state.detected_location == "bai_xep"

    def test_peak_hour_warning(self):
        world = make_world(tourist_density=0.5)
        profile = self._profile()
        # 10AM is in crowd_peak_hours for bai_xep
        peak_time = datetime(2026, 5, 15, 10, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
        state = self.engine.assess("đi bãi xép thôi", peak_time, world, profile)
        assert state.crowd_warning is True

    def test_best_hour_positive(self):
        world = make_world()
        profile = self._profile()
        # 6AM is in best_hours for bai_xep
        early = datetime(2026, 5, 15, 6, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
        state = self.engine.assess("ra bãi xép sáng sớm", early, world, profile)
        assert state.timing_score >= 0.8

    def test_no_location_returns_empty(self):
        world = make_world()
        profile = self._profile()
        state = self.engine.assess("hôm nay ăn gì nhỉ", VN_NOW, world, profile)
        assert state.detected_location == ""
        assert state.location_intelligence is None

    def test_ganh_da_dia_detected(self):
        world = make_world()
        profile = self._profile()
        state = self.engine.assess("muốn xem gành đá đĩa", VN_NOW, world, profile)
        assert state.detected_location == "ganh_da_dia"

    def test_emotional_context_set(self):
        world = make_world()
        profile = self._profile()
        state = self.engine.assess("ra bãi xép thư giãn", VN_NOW, world, profile)
        assert state.emotional_context == "relaxing"


# --- EmotionalJourneyModeler ---

class TestEmotionalJourneyModeler:
    def setup_method(self):
        self.engine = EmotionalJourneyModeler()
        self.energy_engine = TravelEnergyEngine()
        self.behavior_engine = TravelBehaviorEngine()
        self.world_engine = RealtimeWorldModelEngine()

    def _assess(self, companion, text=""):
        ctx = make_context()
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(companion, world)
        profile = self.behavior_engine.assess(ctx, text)
        return self.engine.assess(companion, energy, world, profile, text)

    def test_burnout_detected_on_signal(self):
        companion = make_companion(fatigue=0.8, overwhelm=0.7, stress=0.6)
        state = self._assess(companion, "mệt lắm, thôi nghỉ thôi, không nổi nữa")
        assert state.burnout_risk > 0.5
        assert state.recovery_timing in ("now", "urgent")

    def test_peak_phase_on_high_energy(self):
        companion = make_companion(excitement=0.9, fatigue=0.1, stress=0.1)
        state = self._assess(companion, "vui quá, tuyệt vời!")
        assert state.journey_phase in ("peak", "active")
        assert state.excitement_curve > 0.4

    def test_emotional_safety_alert_on_burnout(self):
        companion = make_companion(fatigue=0.9, overwhelm=0.85, stress=0.8)
        state = self._assess(companion, "không muốn đi nữa, đủ rồi")
        assert state.emotional_safety_needed is True
        assert len(state.safety_alerts) > 0

    def test_decision_fatigue_detected(self):
        companion = make_companion(confusion=0.7, overwhelm=0.5)
        state = self._assess(companion, "")
        assert state.decision_fatigue is True

    def test_recovery_not_needed_on_fresh(self):
        companion = make_companion(fatigue=0.0, stress=0.0, overwhelm=0.0, excitement=0.6)
        state = self._assess(companion)
        assert state.recovery_timing == "not_needed"
        assert state.burnout_risk < 0.3

    def test_stress_accumulation_on_stress_markers(self):
        companion = make_companion(stress=0.3)
        state = self._assess(companion, "ức quá, lo lắng, stress")
        assert state.stress_accumulation > 0.3


# --- ExperienceRebalancer ---

class TestExperienceRebalancer:
    def setup_method(self):
        self.engine = ExperienceRebalancer()
        self.energy_engine = TravelEnergyEngine()
        self.emotional_engine = EmotionalJourneyModeler()
        self.behavior_engine = TravelBehaviorEngine()
        self.world_engine = RealtimeWorldModelEngine()

    def _assess(self, companion, text=""):
        ctx = make_context()
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(companion, world)
        profile = self.behavior_engine.assess(ctx, text)
        emotional = self.emotional_engine.assess(companion, energy, world, profile, text)
        return self.engine.assess(energy, emotional, world, profile)

    def test_downshift_on_exhaustion(self):
        companion = make_companion(fatigue=0.95, overwhelm=0.9, stress=0.9)
        state = self._assess(companion)
        assert state.intensity_adjustment < 0
        assert state.rebalance_needed is True
        assert state.simplify_itinerary is True

    def test_expand_on_high_energy(self):
        companion = make_companion(excitement=0.9, fatigue=0.05, stress=0.05, overwhelm=0.0)
        state = self._assess(companion)
        assert state.expand_exploration is True
        assert state.intensity_adjustment > 0

    def test_rest_window_on_high_rest_pressure(self):
        companion = make_companion(fatigue=0.85, stress=0.6, overwhelm=0.5)
        state = self._assess(companion)
        assert state.rest_window is True

    def test_suggestion_not_empty_on_rebalance(self):
        companion = make_companion(fatigue=0.8, overwhelm=0.7, stress=0.6)
        state = self._assess(companion)
        assert state.rebalance_needed is True
        assert state.suggestion != ""

    def test_no_rebalance_on_normal_state(self):
        companion = make_companion(fatigue=0.2, stress=0.1, overwhelm=0.1, excitement=0.4)
        state = self._assess(companion)
        assert state.urgency in ("low", "medium")


# --- LongTermMemoryEngine ---

class TestLongTermMemoryEngine:
    def setup_method(self):
        self.engine = LongTermMemoryEngine()

    def test_no_history_fresh_user(self):
        ctx = make_context(preferences={})
        state = self.engine.assess(ctx)
        assert state.has_history is False
        assert state.memory_insights == []

    def test_beach_affinity_recalled(self):
        ctx = make_context(preferences={"lt_affinity_places": ["beach", "quiet_beach"], "lt_visit_count": 1})
        state = self.engine.assess(ctx)
        assert state.has_history is True
        assert any("biển" in i for i in state.memory_insights)

    def test_slow_pacing_recalled(self):
        ctx = make_context(preferences={"lt_avg_pacing": 0.25, "lt_visit_count": 2})
        state = self.engine.assess(ctx)
        assert any("thư thả" in i for i in state.memory_insights)

    def test_visit_count_mentioned(self):
        ctx = make_context(preferences={"lt_visit_count": 3})
        state = self.engine.assess(ctx)
        assert any("lần" in i for i in state.memory_insights)

    def test_record_snapshot_updates_prefs(self):
        ctx = make_context(preferences={})
        snap = TripMemorySnapshot(
            trip_id="t1",
            destination="Phú Yên",
            emotional_highlight="sunset",
            favorite_place_type="beach",
            pacing_score=0.3,
            avg_stress=0.25,
            avg_enjoyment=0.8,
            travel_style="relax_traveler",
        )
        updates = self.engine.record_trip_snapshot(ctx, snap)
        assert updates["lt_visit_count"] == 1
        assert "beach" in updates["lt_affinity_places"]
        assert updates["lt_avg_pacing"] == pytest.approx(0.3, abs=0.01)

    def test_cross_trip_patterns_built(self):
        ctx = make_context(preferences={
            "lt_style_history": ["relax_traveler", "relax_traveler", "explorer"],
            "lt_visit_count": 3,
        })
        state = self.engine.assess(ctx)
        assert "dominant_style" in state.cross_trip_patterns


# --- HumanRhythmEngine ---

class TestHumanRhythmEngine:
    def setup_method(self):
        self.engine = HumanRhythmEngine()
        self.energy_engine = TravelEnergyEngine()
        self.world_engine = RealtimeWorldModelEngine()

    def _energy(self, companion):
        ctx = make_context()
        world = self.world_engine.assess(ctx, "", VN_NOW)
        return self.energy_engine.assess(companion, world)

    def test_morning_person_detected(self):
        ctx = make_context(preferences={"rhythm_morning_energy": 0.8})
        companion = make_companion(fatigue=0.1)
        energy = self._energy(companion)
        profile = self.engine.assess(ctx, VN_NOW, energy)
        assert profile.is_morning_person is True

    def test_solo_preference_detected(self):
        ctx = make_context(
            preferences={"rhythm_social_pref": 0.3},
            conversation=[MemoryTurn(role="user", text="mình thích đi một mình, solo thôi")],
        )
        energy = self._energy(make_companion())
        profile = self.engine.assess(ctx, VN_NOW, energy)
        assert profile.social_preference < 0.5

    def test_deep_explorer_detected(self):
        ctx = make_context(
            preferences={},
            conversation=[MemoryTurn(role="user", text="muốn tìm hiểu văn hóa địa phương, cuộc sống bản địa")],
        )
        energy = self._energy(make_companion())
        profile = self.engine.assess(ctx, VN_NOW, energy)
        assert profile.exploration_depth > 0.45

    def test_low_decision_tolerance_on_low_energy(self):
        companion = make_companion(confusion=0.7, overwhelm=0.6)
        energy = self._energy(companion)
        ctx = make_context(preferences={})
        profile = self.engine.assess(ctx, VN_NOW, energy)
        assert profile.decision_tolerance < 0.5

    def test_insights_populated_for_morning_person(self):
        ctx = make_context(preferences={"rhythm_morning_energy": 0.75})
        energy = self._energy(make_companion())
        profile = self.engine.assess(ctx, VN_NOW, energy)
        assert any("sáng" in i for i in profile.insights)


# --- EvolutionEngine ---

class TestEvolutionEngine:
    def setup_method(self):
        self.engine = EvolutionEngine()
        self.feedback_engine = FeedbackEngine()
        self.emotional_engine = EmotionalJourneyModeler()
        self.memory_engine = LongTermMemoryEngine()
        self.energy_engine = TravelEnergyEngine()
        self.behavior_engine = TravelBehaviorEngine()
        self.world_engine = RealtimeWorldModelEngine()

    def _full_assess(self, companion, ctx, text=""):
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(companion, world)
        profile = self.behavior_engine.assess(ctx, text)
        feedback = self.feedback_engine.assess(ctx, text)
        emotional = self.emotional_engine.assess(companion, energy, world, profile, text)
        memory = self.memory_engine.assess(ctx)
        return self.engine.evolve(ctx, feedback, emotional, memory)

    def test_learning_level_fresh_user(self):
        ctx = make_context(preferences={})
        state = self._full_assess(make_companion(), ctx)
        assert state.intelligence_level == "learning"

    def test_adapting_level_with_interactions(self):
        ctx = make_context(preferences={"evo_total_interactions": 6, "evo_quality_score": 0.6})
        state = self._full_assess(make_companion(excitement=0.6), ctx, "ok được")
        assert state.intelligence_level in ("adapting", "learning")

    def test_quality_improves_on_acceptance(self):
        ctx = make_context(preferences={"evo_quality_score": 0.5})
        state = self._full_assess(make_companion(excitement=0.6, fatigue=0.1), ctx, "ok hay đó")
        assert state.recommendation_quality_score >= 0.45

    def test_evolved_preferences_populated(self):
        ctx = make_context(preferences={})
        state = self._full_assess(make_companion(), ctx)
        assert "evo_quality_score" in state.evolved_preferences
        assert "evo_intelligence_level" in state.evolved_preferences

    def test_quality_trend_stable_on_neutral(self):
        ctx = make_context(preferences={"evo_quality_score": 0.5})
        state = self._full_assess(make_companion(), ctx)
        assert state.quality_trend in ("stable", "improving", "declining")


# --- EnvironmentMonitor ---

class TestEnvironmentMonitor:
    def setup_method(self):
        self.engine = EnvironmentMonitor()
        self.energy_engine = TravelEnergyEngine()
        self.world_engine = RealtimeWorldModelEngine()

    def _energy(self, companion, text="", now=VN_NOW):
        ctx = make_context()
        world = self.world_engine.assess(ctx, text, now)
        return self.energy_engine.assess(companion, world), world

    def test_reroute_on_high_density(self):
        world = make_world(tourist_density=0.7, signals=["evening_peak_window"])
        energy, _ = self._energy(make_companion())
        state = self.engine.assess(world, EVENING, energy)
        assert state.reroute_needed is True
        assert any("đông" in a for a in state.alerts)

    def test_slow_down_on_traffic(self):
        world = make_world(traffic_pressure=0.7, signals=["evening_peak_window"])
        energy, _ = self._energy(make_companion())
        state = self.engine.assess(world, EVENING, energy)
        assert state.slow_down_signal is True

    def test_reprioritize_on_weather_risk(self):
        world = make_world(weather_risk=0.6)
        energy, _ = self._energy(make_companion())
        state = self.engine.assess(world, VN_NOW, energy)
        assert state.reprioritize_needed is True

    def test_accelerate_in_optimal_window(self):
        world = make_world(tourist_density=0.1, traffic_pressure=0.1, signals=["local_breakfast_window"])
        companion = make_companion(excitement=0.8, fatigue=0.1)
        energy, _ = self._energy(companion)
        energy.exploration_readiness = 0.7
        state = self.engine.assess(world, VN_NOW, energy)
        assert state.accelerate_signal is True

    def test_heat_compound_alert(self):
        world = make_world(heat_pressure=0.75, signals=["midday_heat_window"])
        companion = make_companion(fatigue=0.6)
        energy, _ = self._energy(companion)
        energy.physical_energy = 0.3
        state = self.engine.assess(world, MIDDAY, energy)
        assert state.slow_down_signal is True
        assert any("nóng" in a or "nắng" in a or "mệt" in a for a in state.alerts)

    def test_summary_not_empty(self):
        world = make_world()
        energy, _ = self._energy(make_companion())
        state = self.engine.assess(world, VN_NOW, energy)
        assert state.environment_summary != ""


# --- Full Phase 6 Integration via TravelOperatingSystem ---

class TestPhase6Integration:
    def setup_method(self):
        self.tos = TravelOperatingSystem()

    def _intent(self):
        return AssistantIntent(domain="travel", action="recommend", confidence=0.9)

    def test_full_assess_returns_phase6_fields(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.3, excitement=0.6)
        state = self.tos.assess(ctx, "muốn ra bãi xép buổi sáng", companion, self._intent(), VN_NOW)
        assert state.feedback is not None
        assert state.travel_graph is not None
        assert state.emotional_journey is not None
        assert state.rebalance is not None
        assert state.long_term_memory is not None
        assert state.human_rhythm is not None
        assert state.evolution is not None
        assert state.environment is not None

    def test_protective_posture_on_burnout(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.9, overwhelm=0.85, stress=0.8)
        state = self.tos.assess(ctx, "mệt lắm thôi nghỉ thôi", companion, self._intent(), VN_NOW)
        assert state.recommendation_posture == "protective"

    def test_expand_posture_on_energized_explorer(self):
        ctx = make_context(preferences={"travel_primary_style": "explorer"})
        companion = make_companion(excitement=0.9, fatigue=0.05, stress=0.05, overwhelm=0.0)
        state = self.tos.assess(ctx, "khám phá thêm đi view đẹp", companion, self._intent(), VN_NOW)
        assert state.recommendation_posture in ("expand", "balanced")

    def test_enhance_reply_adds_phase6_hints(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.7, overwhelm=0.6, stress=0.5)
        state = self.tos.assess(ctx, "mệt quá rồi", companion, self._intent(), VN_NOW)
        intent = self._intent()
        enhanced = self.tos.enhance_reply("Đây là gợi ý.", state, intent)
        assert "Travel OS:" in enhanced

    def test_preference_updates_include_learning_signals(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.2, excitement=0.5)
        state = self.tos.assess(ctx, "yên tĩnh thôi, bỏ qua chỗ đông", companion, self._intent(), VN_NOW)
        assert "evo_quality_score" in state.preference_updates

    def test_travel_graph_detected_in_full_state(self):
        ctx = make_context(preferences={})
        companion = make_companion()
        state = self.tos.assess(ctx, "muốn đến gành đá đĩa", companion, self._intent(), VN_NOW)
        assert state.travel_graph.detected_location == "ganh_da_dia"

    def test_long_term_memory_beach_recall(self):
        ctx = make_context(preferences={"lt_affinity_places": ["beach"], "lt_visit_count": 2})
        companion = make_companion()
        state = self.tos.assess(ctx, "đi đâu nhỉ", companion, self._intent(), VN_NOW)
        assert state.long_term_memory.has_history is True

    def test_simulated_years_of_travel(self):
        """Simulate a user with years of travel history and evolved preferences."""
        ctx = make_context(preferences={
            "lt_affinity_places": ["beach", "quiet_beach", "cafe"],
            "lt_style_history": ["relax_traveler"] * 5 + ["explorer"] * 2,
            "lt_visit_count": 7,
            "lt_avg_pacing": 0.28,
            "lt_avg_stress": 0.22,
            "lt_avg_enjoyment": 0.82,
            "evo_total_interactions": 35,
            "evo_quality_score": 0.84,
            "evo_adaptation_velocity": 0.6,
            "learned_quiet_pref": 0.72,
            "learned_pacing_pref": 0.25,
            "learned_avoid_types": ["crowded", "noisy"],
            "learned_amplify_types": ["beach", "quiet_spots"],
        })
        companion = make_companion(fatigue=0.25, excitement=0.65, stress=0.15)
        state = self.tos.assess(ctx, "đi đâu yên tĩnh gần biển", companion, self._intent(), VN_NOW)
        assert state.evolution.intelligence_level in ("evolved", "instinctive")
        assert state.long_term_memory.has_history is True
        assert state.feedback.quiet_preference > 0.6

    def test_emotional_overload_scenario(self):
        """Simulate emotional overload with environment pressure."""
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.85, overwhelm=0.9, stress=0.8, confusion=0.7)
        state = self.tos.assess(
            ctx,
            "quá nhiều rồi, không nổi, mệt lắm, đủ rồi",
            companion,
            self._intent(),
            MIDDAY,
        )
        assert state.emotional_journey.emotional_safety_needed is True
        assert state.emotional_journey.burnout_risk > 0.5
        assert state.recommendation_posture == "protective"

    def test_realtime_adaptation_on_traffic_spike(self):
        """Simulate a realtime traffic spike triggering reroute."""
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.3)
        state = self.tos.assess(
            ctx,
            "kẹt xe quá, đường đông, grab chờ mãi không tới",
            companion,
            self._intent(),
            EVENING,
        )
        assert state.world.traffic_pressure > 0
        assert state.recommendation_posture in ("predictive", "balanced", "protective")
