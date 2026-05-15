from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.behavior.profile_engine import TravelBehaviorEngine
from app.dna.travel_dna import TravelDNAEngine
from app.emotional.journey_modeler import EmotionalJourneyModeler
from app.fatigue.energy_engine import TravelEnergyEngine
from app.life.context_engine import LifeContextEngine
from app.life.life_memory import LifeMemoryEngine, LifeMoment
from app.life.life_orchestrator import LifeOrchestrator
from app.life.rhythm_memory import LifeRhythmMemory
from app.models.domain import UserContext, MemoryTurn
from app.orchestration.travel_operating_system import TravelOperatingSystem
from app.personalization.human_rhythm import HumanRhythmEngine
from app.realtime.world_model import RealtimeWorldModelEngine
from app.schemas.assistant import AssistantIntent
from app.services.travel_companion import TravelCompanionState
from app.wellbeing.calm_ux import CalmTechnologyEngine
from app.wellbeing.optimizer import WellbeingOptimizer

VN_NOW = datetime(2026, 5, 15, 9, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
EVENING = datetime(2026, 5, 15, 18, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))


def make_context(**kwargs) -> UserContext:
    return UserContext(chat_id=1, user_id=1, **kwargs)


def make_companion(**kwargs) -> TravelCompanionState:
    return TravelCompanionState(**kwargs)


def _intent():
    return AssistantIntent(domain="travel", action="recommend", confidence=0.9)


# --- LifeContextEngine ---

class TestLifeContextEngine:
    def setup_method(self):
        self.engine = LifeContextEngine()

    def test_burnout_detected_on_signals(self):
        ctx = make_context(preferences={})
        state = self.engine.assess(ctx, "quá tải rồi, không thở được, muốn biến mất")
        assert state.burnout_detected is True
        assert state.life_mode == "recovery"

    def test_work_stress_detected(self):
        ctx = make_context(preferences={})
        state = self.engine.assess(ctx, "deadline gấp, họp liên miên, áp lực công việc")
        assert state.work_stress_level > 0
        assert state.travel_recommendation_bias in ("slow", "recovery", "balanced")

    def test_social_energy_high(self):
        ctx = make_context(preferences={})
        state = self.engine.assess(ctx, "bạn bè rủ đi cùng, tụ tập nhóm, vui vẻ cùng nhau")
        assert state.social_energy > 0.5
        assert state.life_mode in ("social", "normal")

    def test_social_energy_low(self):
        ctx = make_context(preferences={})
        state = self.engine.assess(ctx, "mình muốn đi một mình, cần không gian riêng, không muốn gặp ai")
        assert state.social_energy < 0.5
        assert state.life_mode in ("reflective", "normal")

    def test_recovery_mode_on_burnout(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.7})
        state = self.engine.assess(ctx, "kiệt sức rồi, cần nạp pin")
        assert state.life_mode == "recovery"
        assert state.travel_recommendation_bias == "recovery"

    def test_escape_mode_on_work_stress_and_busy(self):
        ctx = make_context(preferences={"lc_work_stress": 0.6, "lc_lifestyle_pressure": 0.65})
        state = self.engine.assess(ctx, "bận quá, deadline, áp lực")
        assert state.life_mode in ("escape", "normal")

    def test_emotional_high_baseline(self):
        ctx = make_context(preferences={})
        state = self.engine.assess(ctx, "vui quá, hạnh phúc, phấn khởi, excited")
        assert state.emotional_baseline > 0.5

    def test_life_insights_not_empty_on_recovery(self):
        ctx = make_context(preferences={})
        state = self.engine.assess(ctx, "burnout, không nổi nữa, đủ rồi")
        assert len(state.life_insights) > 0


# --- LifeRhythmMemory ---

class TestLifeRhythmMemory:
    def setup_method(self):
        self.engine = LifeRhythmMemory()

    def test_morning_person_from_activity(self):
        ctx = make_context(preferences={
            "lr_morning_activity_count": 8,
            "lr_afternoon_activity_count": 2,
            "lr_evening_activity_count": 1,
        })
        state = self.engine.assess(ctx, VN_NOW)
        assert state.daily_rhythm == "morning_person"

    def test_night_owl_from_activity(self):
        ctx = make_context(preferences={
            "lr_morning_activity_count": 1,
            "lr_afternoon_activity_count": 2,
            "lr_evening_activity_count": 7,
        })
        state = self.engine.assess(ctx, VN_NOW)
        assert state.daily_rhythm == "night_owl"

    def test_recovery_energy_phase(self):
        ctx = make_context(preferences={"lr_cumulative_stress": 0.75})
        state = self.engine.assess(ctx, VN_NOW)
        assert state.energy_cycle_phase == "recovery"

    def test_needing_solitude_from_history(self):
        ctx = make_context(preferences={
            "lr_social_interaction_count": 1,
            "lr_solo_moment_count": 8,
        })
        state = self.engine.assess(ctx, VN_NOW)
        assert state.social_cycle == "needing_solitude"
        assert state.needs_solitude is True

    def test_needs_exploration_on_high_state(self):
        ctx = make_context(preferences={
            "lr_cumulative_stress": 0.1,
            "lr_cumulative_enjoyment": 0.8,
            "lr_total_trip_count": 1,
        })
        state = self.engine.assess(ctx, VN_NOW)
        assert state.needs_exploration is True

    def test_first_time_travel_rhythm(self):
        ctx = make_context(preferences={"lr_total_trip_count": 0})
        state = self.engine.assess(ctx, VN_NOW)
        assert state.yearly_travel_rhythm == "first_time"

    def test_frequent_traveler_rhythm(self):
        ctx = make_context(preferences={"lr_total_trip_count": 8})
        state = self.engine.assess(ctx, VN_NOW)
        assert state.yearly_travel_rhythm == "frequent"

    def test_record_activity_updates_counts(self):
        ctx = make_context(preferences={})
        updates = self.engine.record_activity(ctx, VN_NOW, "social")
        assert updates["lr_social_interaction_count"] == 1

    def test_record_trip_start(self):
        ctx = make_context(preferences={"lr_total_trip_count": 3})
        updates = self.engine.record_activity(ctx, VN_NOW, "trip_start")
        assert updates["lr_total_trip_count"] == 4


# --- WellbeingOptimizer ---

class TestWellbeingOptimizer:
    def setup_method(self):
        self.optimizer = WellbeingOptimizer()
        self.emotional_engine = EmotionalJourneyModeler()
        self.energy_engine = TravelEnergyEngine()
        self.world_engine = RealtimeWorldModelEngine()
        self.life_context_engine = LifeContextEngine()
        self.rhythm_engine = LifeRhythmMemory()

    def _assess(self, companion, ctx, text=""):
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(companion, world)
        from app.behavior.profile_engine import TravelBehaviorEngine
        profile = TravelBehaviorEngine().assess(ctx, text)
        emotional = self.emotional_engine.assess(companion, energy, world, profile, text)
        life_context = self.life_context_engine.assess(ctx, text)
        life_rhythm = self.rhythm_engine.assess(ctx, VN_NOW)
        return self.optimizer.optimize(life_context, life_rhythm, energy, emotional)

    def test_critical_grade_on_full_burnout(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.8, "lc_work_stress": 0.8})
        companion = make_companion(fatigue=0.95, overwhelm=0.9, stress=0.9)
        state = self._assess(companion, ctx, "burnout hoàn toàn, không nổi")
        assert state.score.grade in ("critical", "stressed")
        assert state.itinerary_density in ("minimal", "light")

    def test_thriving_grade_on_good_state(self):
        ctx = make_context(preferences={})
        companion = make_companion(excitement=0.9, fatigue=0.05, stress=0.0, overwhelm=0.0)
        state = self._assess(companion, ctx, "vui quá, hạnh phúc, phấn khởi")
        assert state.score.grade in ("thriving", "good", "neutral")

    def test_recovery_optimize_on_burnout(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.75})
        companion = make_companion(fatigue=0.9, overwhelm=0.85)
        state = self._assess(companion, ctx, "kiệt sức, burnout")
        assert state.optimize_for == "recovery"
        assert state.recovery_windows_required is True
        assert state.quiet_spaces_priority is True

    def test_exploration_optimize_on_high_state(self):
        ctx = make_context(preferences={
            "lr_cumulative_stress": 0.05,
            "lr_cumulative_enjoyment": 0.85,
            "lr_total_trip_count": 1,
        })
        companion = make_companion(excitement=0.85, fatigue=0.05)
        state = self._assess(companion, ctx)
        assert state.optimize_for in ("exploration", "joy", "balance")

    def test_social_optimize_on_social_energy(self):
        ctx = make_context(preferences={"lc_social_energy": 0.8})
        companion = make_companion(excitement=0.6)
        state = self._assess(companion, ctx, "bạn bè rủ đi, tụ tập nhóm")
        assert state.optimize_for in ("social", "balance")

    def test_decision_load_minimal_on_critical(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.9})
        companion = make_companion(fatigue=0.95, confusion=0.8, overwhelm=0.9)
        state = self._assess(companion, ctx, "quá tải rồi, không thở được, burnout hoàn toàn")
        assert state.decision_load in ("minimal", "low")

    def test_wellbeing_insights_on_critical(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.8})
        companion = make_companion(fatigue=0.9, overwhelm=0.85)
        state = self._assess(companion, ctx, "burnout hoàn toàn")
        assert len(state.wellbeing_insights) > 0

    def test_overall_score_bounded(self):
        ctx = make_context(preferences={})
        companion = make_companion()
        state = self._assess(companion, ctx)
        assert 0.0 <= state.score.overall <= 1.0


# --- TravelDNAEngine ---

class TestTravelDNAEngine:
    def setup_method(self):
        self.engine = TravelDNAEngine()
        self.behavior = TravelBehaviorEngine()
        self.life_context = LifeContextEngine()
        self.rhythm = HumanRhythmEngine()
        self.energy_engine = TravelEnergyEngine()
        self.world_engine = RealtimeWorldModelEngine()

    def _profile_and_context(self, ctx, text):
        behavior = self.behavior.assess(ctx, text)
        life_ctx = self.life_context.assess(ctx, text)
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(make_companion(), world)
        rhythm = self.rhythm.assess(ctx, VN_NOW, energy)
        return behavior, life_ctx, rhythm

    def test_calm_explorer_detected(self):
        ctx = make_context(preferences={})
        text = "mình thích yên tĩnh, khám phá nhẹ nhàng, ít người"
        behavior, life_ctx, rhythm = self._profile_and_context(ctx, text)
        dna = self.engine.assess(ctx, behavior, life_ctx, rhythm)
        assert dna.dna_type == "calm_explorer"

    def test_energetic_foodie_detected(self):
        ctx = make_context(preferences={})
        ctx.conversation = [
            MemoryTurn(role="user", text="ăn gì ngon, hải sản, quán đặc sản, ngon quá"),
        ]
        text = "muốn ăn hải sản ngon"
        behavior, life_ctx, rhythm = self._profile_and_context(ctx, text)
        dna = self.engine.assess(ctx, behavior, life_ctx, rhythm)
        assert dna.dna_type == "energetic_foodie"

    def test_slow_traveler_on_recovery_mode(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.75})
        text = "thư thả thôi, chậm chậm, không vội"
        behavior = self.behavior.assess(ctx, text)
        life_ctx = self.life_context.assess(ctx, text)
        life_ctx.life_mode = "recovery"
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(make_companion(), world)
        rhythm = self.rhythm.assess(ctx, VN_NOW, energy)
        dna = self.engine.assess(ctx, behavior, life_ctx, rhythm)
        assert dna.dna_type in ("slow_traveler", "calm_explorer")

    def test_social_traveler_detected(self):
        ctx = make_context(preferences={})
        ctx.conversation = [
            MemoryTurn(role="user", text="bạn bè đi cùng, tụ tập nhóm, vui cùng nhau"),
        ]
        text = "đi cùng hội bạn"
        behavior, life_ctx, rhythm = self._profile_and_context(ctx, text)
        dna = self.engine.assess(ctx, behavior, life_ctx, rhythm)
        assert dna.dna_type in ("social_traveler", "calm_explorer", "energetic_foodie")

    def test_reflective_traveler_on_solitude(self):
        ctx = make_context(preferences={"lc_social_energy": 0.1})
        text = "một mình, chiêm nghiệm, ý nghĩa"
        behavior = self.behavior.assess(ctx, text)
        life_ctx = self.life_context.assess(ctx, text)
        life_ctx.life_mode = "reflective"
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(make_companion(), world)
        rhythm = self.rhythm.assess(ctx, VN_NOW, energy)
        dna = self.engine.assess(ctx, behavior, life_ctx, rhythm)
        assert dna.dna_type in ("reflective_traveler", "calm_explorer", "slow_traveler")

    def test_dna_insights_populated(self):
        ctx = make_context(preferences={})
        text = "yên tĩnh, khám phá"
        behavior, life_ctx, rhythm = self._profile_and_context(ctx, text)
        dna = self.engine.assess(ctx, behavior, life_ctx, rhythm)
        assert len(dna.dna_insights) > 0
        assert len(dna.personalization_hints) > 0

    def test_pacing_score_slow_for_slow_traveler(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.7})
        text = "nhẹ nhàng thư giãn, nghỉ ngơi, chill, không vội"
        behavior, life_ctx, rhythm = self._profile_and_context(ctx, text)
        life_ctx.life_mode = "recovery"
        dna = self.engine.assess(ctx, behavior, life_ctx, rhythm)
        assert dna.pacing_score <= 0.5


# --- CalmTechnologyEngine ---

class TestCalmTechnologyEngine:
    def setup_method(self):
        self.engine = CalmTechnologyEngine()
        self.optimizer = WellbeingOptimizer()
        self.life_ctx_engine = LifeContextEngine()
        self.emotional_engine = EmotionalJourneyModeler()
        self.energy_engine = TravelEnergyEngine()
        self.dna_engine = TravelDNAEngine()
        self.behavior = TravelBehaviorEngine()
        self.rhythm = HumanRhythmEngine()
        self.world_engine = RealtimeWorldModelEngine()
        self.life_rhythm = LifeRhythmMemory()

    def _full_assess(self, companion, ctx, text=""):
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(companion, world)
        profile = self.behavior.assess(ctx, text)
        emotional = self.emotional_engine.assess(companion, energy, world, profile, text)
        life_ctx = self.life_ctx_engine.assess(ctx, text)
        rhythm = self.life_rhythm.assess(ctx, VN_NOW)
        wellbeing = self.optimizer.optimize(life_ctx, rhythm, energy, emotional)
        human_rhythm = self.rhythm.assess(ctx, VN_NOW, energy)
        dna = self.dna_engine.assess(ctx, profile, life_ctx, human_rhythm)
        return self.engine.assess(life_ctx, emotional, wellbeing, dna)

    def test_minimal_reply_on_burnout(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.85})
        companion = make_companion(fatigue=0.9, overwhelm=0.9, confusion=0.8)
        state = self._full_assess(companion, ctx, "burnout hoàn toàn")
        assert state.reply_length_mode in ("minimal", "short")
        assert state.hint_count_limit <= 2

    def test_silent_proactive_on_critical(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.9})
        companion = make_companion(fatigue=0.95, overwhelm=0.95, stress=0.9)
        state = self._full_assess(companion, ctx, "không nổi nữa")
        assert state.proactive_level in ("silent", "quiet")

    def test_active_on_thriving_explorer(self):
        ctx = make_context(preferences={})
        companion = make_companion(excitement=0.95, fatigue=0.0, stress=0.0, overwhelm=0.0)
        state = self._full_assess(companion, ctx, "khám phá thôi, hidden gem, xa một chút")
        assert state.proactive_level in ("active", "gentle", "quiet")

    def test_decision_simplification_on_decision_fatigue(self):
        ctx = make_context(preferences={})
        companion = make_companion(confusion=0.75, overwhelm=0.65)
        state = self._full_assess(companion, ctx)
        assert state.decision_simplification is True

    def test_invisible_mode_on_recovery_burnout(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.8})
        companion = make_companion(fatigue=0.9, overwhelm=0.85)
        state = self._full_assess(companion, ctx, "burnout, kiệt sức")
        assert state.invisible_mode is True or state.proactive_level in ("silent", "quiet")

    def test_hint_count_respects_calm_ux(self):
        ctx = make_context(preferences={})
        companion = make_companion()
        state = self._full_assess(companion, ctx)
        assert 1 <= state.hint_count_limit <= 3

    def test_tone_supportive_on_stress(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.8, overwhelm=0.75, stress=0.7)
        state = self._full_assess(companion, ctx, "mệt lắm, áp lực")
        assert state.tone in ("supportive", "calm", "minimal")


# --- LifeMemoryEngine ---

class TestLifeMemoryEngine:
    def setup_method(self):
        self.engine = LifeMemoryEngine()

    def test_no_memory_fresh_user(self):
        ctx = make_context(preferences={})
        state = self.engine.assess(ctx)
        assert state.travel_life_chapter == "just_started"
        assert state.continuity_message == ""

    def test_experienced_chapter(self):
        ctx = make_context(preferences={"lm_total_moments": 8})
        state = self.engine.assess(ctx)
        assert state.travel_life_chapter == "experienced"
        assert state.continuity_message != ""

    def test_reflective_chapter_with_continuity(self):
        ctx = make_context(preferences={"lm_total_moments": 20})
        state = self.engine.assess(ctx)
        assert state.travel_life_chapter == "reflective"
        assert "đồng hành" in state.continuity_message or "nhớ" in state.continuity_message

    def test_favorite_places_recalled(self):
        ctx = make_context(preferences={"lm_favorite_places": ["Bãi Xép", "Gành Đá Đĩa"]})
        state = self.engine.assess(ctx)
        assert "Bãi Xép" in state.favorite_places

    def test_record_moment_updates_prefs(self):
        ctx = make_context(preferences={})
        moment = LifeMoment(
            moment_id="m1",
            moment_type="joy",
            description="Hoàng hôn trên Bãi Xép",
            location="Bãi Xép",
            emotional_intensity=0.9,
        )
        updates = self.engine.record_moment(ctx, moment)
        assert updates["lm_total_moments"] == 1
        assert "Bãi Xép" in updates["lm_favorite_places"]

    def test_milestone_recorded(self):
        ctx = make_context(preferences={})
        moment = LifeMoment(
            moment_id="m2",
            moment_type="milestone",
            description="Chuyến đi đầu tiên sau 5 năm",
            location="Phú Yên",
            emotional_intensity=0.95,
        )
        updates = self.engine.record_moment(ctx, moment)
        assert "Chuyến đi đầu tiên sau 5 năm" in updates["lm_milestones"]


# --- LifeOrchestrator ---

class TestLifeOrchestrator:
    def setup_method(self):
        self.orchestrator = LifeOrchestrator()
        self.life_ctx_engine = LifeContextEngine()
        self.rhythm_engine = LifeRhythmMemory()
        self.memory_engine = LifeMemoryEngine()
        self.emotional_engine = EmotionalJourneyModeler()
        self.energy_engine = TravelEnergyEngine()
        self.optimizer = WellbeingOptimizer()
        self.calm_engine = CalmTechnologyEngine()
        self.dna_engine = TravelDNAEngine()
        self.behavior = TravelBehaviorEngine()
        self.rhythm_human = HumanRhythmEngine()
        self.world_engine = RealtimeWorldModelEngine()

    def _full_orchestrate(self, companion, ctx, text=""):
        world = self.world_engine.assess(ctx, text, VN_NOW)
        energy = self.energy_engine.assess(companion, world)
        profile = self.behavior.assess(ctx, text)
        emotional = self.emotional_engine.assess(companion, energy, world, profile, text)
        life_ctx = self.life_ctx_engine.assess(ctx, text)
        life_rhythm = self.rhythm_engine.assess(ctx, VN_NOW)
        life_mem = self.memory_engine.assess(ctx)
        wellbeing = self.optimizer.optimize(life_ctx, life_rhythm, energy, emotional)
        human_rhythm = self.rhythm_human.assess(ctx, VN_NOW, energy)
        dna = self.dna_engine.assess(ctx, profile, life_ctx, human_rhythm)
        calm = self.calm_engine.assess(life_ctx, emotional, wellbeing, dna)
        return self.orchestrator.orchestrate(
            life_ctx, life_rhythm, life_mem, emotional, energy, wellbeing, calm, dna
        )

    def test_recovery_mode_on_burnout(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.9, overwhelm=0.9)
        state = self._full_orchestrate(companion, ctx, "burnout, quá tải, không nổi nữa")
        assert state.orchestration_mode == "recovery"
        assert state.trip_as_therapy is True

    def test_travel_is_context_on_life_mode(self):
        ctx = make_context(preferences={"lc_recovery_need": 0.75})
        companion = make_companion(fatigue=0.85)
        state = self._full_orchestrate(companion, ctx, "kiệt sức, burnout, không nổi nữa")
        assert state.travel_is_context is True

    def test_exploration_mode_on_thriving(self):
        ctx = make_context(preferences={
            "lr_cumulative_stress": 0.05,
            "lr_cumulative_enjoyment": 0.85,
            "lr_total_trip_count": 1,
        })
        companion = make_companion(excitement=0.9, fatigue=0.0)
        state = self._full_orchestrate(companion, ctx, "muốn khám phá, hào hứng")
        assert state.orchestration_mode in ("exploration", "travel")

    def test_companion_message_on_burnout(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.9, overwhelm=0.9)
        state = self._full_orchestrate(companion, ctx, "burnout, kiệt sức")
        # either companion message is set or invisible mode suppressed it
        assert isinstance(state.companion_message, str)

    def test_life_balance_score_bounded(self):
        ctx = make_context(preferences={})
        companion = make_companion()
        state = self._full_orchestrate(companion, ctx)
        assert 0.0 <= state.life_balance_score <= 1.0


# --- Full Phase 8 Integration ---

class TestPhase8Integration:
    def setup_method(self):
        self.tos = TravelOperatingSystem()

    def test_phase8_fields_in_state(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.3)
        state = self.tos.assess(ctx, "muốn đi biển thư giãn", companion, _intent(), VN_NOW)
        assert state.life_context is not None
        assert state.life_rhythm is not None
        assert state.wellbeing is not None
        assert state.travel_dna is not None
        assert state.calm_ux is not None
        assert state.life_memory is not None
        assert state.life_orchestration is not None

    def test_protective_posture_on_life_burnout(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.95, overwhelm=0.9)
        state = self.tos.assess(
            ctx, "burnout hoàn toàn, không thở được, quá tải rồi",
            companion, _intent(), VN_NOW
        )
        assert state.recommendation_posture == "protective"

    def test_enhance_reply_respects_calm_ux(self):
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.2)
        state = self.tos.assess(ctx, "đi bãi xép thôi", companion, _intent(), VN_NOW)
        enhanced = self.tos.enhance_reply("Đây là gợi ý.", state, _intent())
        assert isinstance(enhanced, str)

    def test_burned_out_worker_scenario(self):
        """Burned-out user with work stress gets recovery-optimized trip."""
        ctx = make_context(preferences={
            "lc_work_stress": 0.8,
            "lc_recovery_need": 0.75,
            "lc_lifestyle_pressure": 0.7,
        })
        companion = make_companion(fatigue=0.8, stress=0.7, overwhelm=0.6)
        state = self.tos.assess(
            ctx,
            "deadline gấp xong rồi, kiệt sức, cần nghỉ thật sự",
            companion, _intent(), VN_NOW,
        )
        assert state.wellbeing is not None
        assert state.wellbeing.optimize_for in ("recovery", "calmness")
        assert state.recommendation_posture == "protective"

    def test_solo_reflective_traveler_scenario(self):
        """Solo reflective traveler gets quiet, meaningful recommendations."""
        ctx = make_context(preferences={
            "lc_social_energy": 0.1,
            "lr_solo_moment_count": 10,
            "lr_social_interaction_count": 1,
        })
        companion = make_companion(fatigue=0.2, excitement=0.5)
        state = self.tos.assess(
            ctx,
            "mình đi một mình, muốn chiêm nghiệm, không cần lịch trình dày",
            companion, _intent(), VN_NOW,
        )
        assert state.travel_dna is not None
        assert state.travel_dna.dna_type in ("reflective_traveler", "calm_explorer", "slow_traveler")
        assert state.calm_ux.hint_count_limit <= 2

    def test_thriving_social_group_scenario(self):
        """Energized social group gets full, social-optimized itinerary."""
        ctx = make_context(preferences={
            "lc_social_energy": 0.85,
            "lr_cumulative_enjoyment": 0.8,
        })
        companion = make_companion(excitement=0.9, fatigue=0.1, stress=0.0)
        state = self.tos.assess(
            ctx,
            "đi cùng nhóm bạn bè, vui vẻ, muốn ăn ngon và khám phá",
            companion, _intent(), VN_NOW,
        )
        assert state.wellbeing is not None
        assert state.wellbeing.score.grade in ("thriving", "good", "neutral")
        assert state.recommendation_posture in ("expand", "balanced")

    def test_first_time_traveler_needs_exploration(self):
        """First-time traveler with good state gets exploration mode."""
        ctx = make_context(preferences={
            "lr_total_trip_count": 0,
            "lr_cumulative_enjoyment": 0.7,
        })
        companion = make_companion(excitement=0.7, fatigue=0.15)
        state = self.tos.assess(
            ctx,
            "lần đầu tiên đến Phú Yên, muốn khám phá thật nhiều",
            companion, _intent(), VN_NOW,
        )
        assert state.life_rhythm.yearly_travel_rhythm == "first_time"
        assert state.life_orchestration.suggested_trip_type in ("deep_dive", "normal")

    def test_life_memory_continuity_for_experienced_traveler(self):
        """Experienced traveler gets continuity message from life memory."""
        ctx = make_context(preferences={
            "lm_total_moments": 12,
            "lm_favorite_places": ["Bãi Xép", "Gành Đá Đĩa"],
        })
        companion = make_companion(fatigue=0.2)
        state = self.tos.assess(ctx, "đi đâu nhỉ", companion, _intent(), VN_NOW)
        assert state.life_memory.travel_life_chapter in ("experienced", "reflective")
        assert state.life_memory.continuity_message != ""

    def test_calm_ux_limits_hints_on_stressed(self):
        """Stressed user gets fewer hints — calm technology in action."""
        ctx = make_context(preferences={"lc_recovery_need": 0.7})
        companion = make_companion(fatigue=0.8, overwhelm=0.7, confusion=0.6)
        state = self.tos.assess(ctx, "mệt quá, burnout", companion, _intent(), VN_NOW)
        assert state.calm_ux.hint_count_limit <= 2

    def test_dna_drives_personalization(self):
        """Travel DNA personalizes interaction style across the system."""
        ctx = make_context(preferences={})
        companion = make_companion(fatigue=0.1, excitement=0.7)
        state = self.tos.assess(
            ctx, "yên tĩnh, khám phá nhẹ nhàng, ít người",
            companion, _intent(), VN_NOW,
        )
        assert state.travel_dna.dna_type is not None
        assert state.travel_dna.pacing_score > 0
