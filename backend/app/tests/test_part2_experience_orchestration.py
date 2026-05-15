"""
Tests for Part 2 — Real-World Human Experience Orchestration:
- EmotionalGeographyEngine
- TravelFlowOrchestrator
- DecisionFatigueReducer
- Integration: Part 2 engines in TravelOperatingSystem
"""
from __future__ import annotations

import pytest

from app.emotional.geography_engine import (
    EmotionalGeographyEngine,
    PlaceEmotionalProfile,
    _ema,
    _resolve_sentiment,
)
from app.orchestration.travel_flow_orchestrator import (
    TravelFlowOrchestrator,
    _hour_to_phase,
    _resolve_posture,
    _phase_progress,
)
from app.services.decision_fatigue_reducer import (
    DecisionFatigueReducer,
    simplify_reply,
)


# ===========================================================================
# EmotionalGeographyEngine
# ===========================================================================


class TestEmotionalGeographyEngine:
    def setup_method(self):
        self.engine = EmotionalGeographyEngine()

    def test_default_phu_yen_profiles_loaded(self):
        state = self.engine.get_state()
        assert "bai_xep" in state.place_profiles
        assert "ganh_da_dia" in state.place_profiles
        assert "mui_dien" in state.place_profiles
        assert "vinh_hoa" in state.place_profiles
        assert "dam_o_loan" in state.place_profiles
        assert "hon_yen" in state.place_profiles

    def test_bai_xep_is_calm(self):
        profile = self.engine.get_profile("bai_xep")
        assert profile is not None
        assert profile.calm_score >= 0.75

    def test_observe_positive_signal_increases_joy(self):
        before = self.engine.get_profile("bai_xep").joy_score
        self.engine.observe("tuyệt, đẹp quá, thích lắm", "bai_xep")
        after = self.engine.get_profile("bai_xep").joy_score
        assert after >= before

    def test_observe_calm_signal_increases_calm(self):
        before = self.engine.get_profile("vinh_hoa").calm_score
        self.engine.observe("yên tĩnh quá, thoải mái, bình yên", "vinh_hoa")
        after = self.engine.get_profile("vinh_hoa").calm_score
        assert after >= before

    def test_observe_stress_signal_decreases_calm(self):
        # First set calm high
        self.engine.observe("yên tĩnh", "song_cau", "Sông Cầu", "town")
        profile_before = self.engine.get_profile("song_cau")
        calm_before = profile_before.calm_score
        # Now stress signal
        self.engine.observe("đông ghê, ồn ào, chật chội", "song_cau")
        profile_after = self.engine.get_profile("song_cau")
        assert profile_after.calm_score <= calm_before

    def test_observe_increments_visit_count(self):
        key = "thap_nhan"
        before = self.engine.get_profile(key).visit_count
        self.engine.observe("đẹp quá", key)
        assert self.engine.get_profile(key).visit_count == before + 1

    def test_create_unknown_place_on_observe(self):
        self.engine.observe("yên tĩnh, chill", "new_cafe", "Cafe Ven Biển", "cafe")
        profile = self.engine.get_profile("new_cafe")
        assert profile is not None
        assert profile.place_name == "Cafe Ven Biển"
        assert profile.place_type == "cafe"

    def test_cafe_baseline_calm(self):
        self.engine.observe("yên tĩnh", "test_cafe", "Test Cafe", "cafe")
        profile = self.engine.get_profile("test_cafe")
        # Baseline for cafe = 0.6, after calm signal should be >= 0.6
        assert profile.calm_score >= 0.58

    def test_market_baseline_stress(self):
        self.engine.observe("ồn ào", "test_market", "Test Market", "market")
        profile = self.engine.get_profile("test_market")
        # Baseline for market = 0.30, after stress should be <= 0.38
        assert profile.calm_score <= 0.40

    def test_recovery_signal_increases_recovery_power(self):
        before = self.engine.get_profile("hon_yen").recovery_power
        self.engine.observe("nghỉ ngơi, thư giãn, lấy lại sức", "hon_yen")
        after = self.engine.get_profile("hon_yen").recovery_power
        assert after >= before

    def test_recommend_for_recovery_returns_best(self):
        best = self.engine.recommend_for_recovery()
        assert best is not None
        profile = self.engine.get_profile(best)
        assert profile.recovery_power >= 0.55

    def test_recommend_for_joy_returns_best(self):
        best = self.engine.recommend_for_joy()
        assert best is not None
        profile = self.engine.get_profile(best)
        assert profile.joy_score >= 0.55

    def test_state_has_best_recovery_place(self):
        state = self.engine.get_state()
        assert state.best_recovery_place is not None

    def test_state_has_recovery_hint(self):
        state = self.engine.get_state()
        assert state.hint != ""
        assert "nghỉ" in state.hint.lower() or "năng lượng" in state.hint.lower() or "lấy" in state.hint.lower()

    def test_to_preference_updates_structure(self):
        updates = self.engine.to_preference_updates()
        assert any(k.startswith("geo_") for k in updates)
        # Should have calm and joy keys
        geo_keys = [k for k in updates if k.startswith("geo_")]
        assert any("_calm" in k for k in geo_keys)
        assert any("_joy" in k for k in geo_keys)

    def test_load_from_preferences(self):
        prefs = {
            "geo_bai_xep_calm": 0.95,
            "geo_bai_xep_joy": 0.90,
            "geo_bai_xep_visits": 5,
        }
        self.engine.load_from_preferences(prefs)
        profile = self.engine.get_profile("bai_xep")
        assert abs(profile.calm_score - 0.95) < 0.01
        assert abs(profile.joy_score - 0.90) < 0.01
        assert profile.visit_count == 5

    def test_sentiment_resolved_positive_on_joy(self):
        assert _resolve_sentiment(0, 0, 2) == "positive"

    def test_sentiment_resolved_negative_on_stress(self):
        assert _resolve_sentiment(0, 3, 0) == "negative"

    def test_sentiment_neutral_no_signals(self):
        assert _resolve_sentiment(0, 0, 0) == "neutral"

    def test_ema_decays_toward_signal(self):
        result = _ema(0.5, 1.0)
        assert result > 0.5
        result2 = _ema(0.5, 0.0)
        assert result2 < 0.5


# ===========================================================================
# TravelFlowOrchestrator
# ===========================================================================


class TestTravelFlowOrchestrator:
    def setup_method(self):
        self.orc = TravelFlowOrchestrator()

    # Phase detection --------------------------------------------------------

    def test_hour_to_phase_midnight(self):
        assert _hour_to_phase(0) == "pre_dawn"
        assert _hour_to_phase(4) == "pre_dawn"

    def test_hour_to_phase_sunrise(self):
        assert _hour_to_phase(5) == "sunrise"
        assert _hour_to_phase(6) == "sunrise"

    def test_hour_to_phase_breakfast(self):
        assert _hour_to_phase(7) == "breakfast"
        assert _hour_to_phase(8) == "breakfast"

    def test_hour_to_phase_morning(self):
        assert _hour_to_phase(9) == "morning"
        assert _hour_to_phase(10) == "morning"

    def test_hour_to_phase_midday(self):
        assert _hour_to_phase(11) == "midday"
        assert _hour_to_phase(13) == "midday"

    def test_hour_to_phase_afternoon(self):
        assert _hour_to_phase(14) == "afternoon"
        assert _hour_to_phase(16) == "afternoon"

    def test_hour_to_phase_golden_hour(self):
        assert _hour_to_phase(17) == "golden_hour"
        assert _hour_to_phase(18) == "golden_hour"

    def test_hour_to_phase_dinner(self):
        assert _hour_to_phase(19) == "dinner"
        assert _hour_to_phase(20) == "dinner"

    def test_hour_to_phase_night(self):
        assert _hour_to_phase(21) == "night"
        assert _hour_to_phase(22) == "night"

    def test_hour_to_phase_late_night(self):
        assert _hour_to_phase(23) == "late_night"

    # Posture resolution -----------------------------------------------------

    def test_posture_recover_on_extreme_fatigue(self):
        assert _resolve_posture(0.90, 0.0) == "recover"

    def test_posture_rest_on_high_fatigue(self):
        assert _resolve_posture(0.70, 0.0) == "rest"

    def test_posture_rest_on_bad_weather(self):
        assert _resolve_posture(0.30, 0.80) == "rest"

    def test_posture_sustain_on_moderate(self):
        assert _resolve_posture(0.45, 0.0) == "sustain"

    def test_posture_energize_on_fresh(self):
        assert _resolve_posture(0.20, 0.0) == "energize"

    def test_posture_flexible_on_mid_range(self):
        assert _resolve_posture(0.35, 0.30) == "flexible"

    # Phase progress ---------------------------------------------------------

    def test_phase_progress_monotonic(self):
        phases = ["pre_dawn", "sunrise", "breakfast", "morning", "midday",
                  "afternoon", "golden_hour", "dinner", "night", "late_night"]
        progresses = [_phase_progress(p) for p in phases]
        assert progresses == sorted(progresses)

    def test_phase_progress_breakfast_middle(self):
        p = _phase_progress("breakfast")
        assert 0.1 < p < 0.5

    # Orchestrator assess ----------------------------------------------------

    def test_assess_returns_state(self):
        state = self.orc.assess(hour=8, fatigue=0.2, weather_risk=0.0, tourist_density=0.3)
        assert state.current_phase == "breakfast"
        assert state.posture == "energize"
        assert state.energy_remaining > 0.7

    def test_high_fatigue_triggers_rest_posture(self):
        state = self.orc.assess(hour=14, fatigue=0.80, weather_risk=0.0, tourist_density=0.0)
        assert state.posture in ("rest", "recover")
        assert state.simplify_decisions is True

    def test_bad_weather_indoor_suggestions(self):
        state = self.orc.assess(hour=10, fatigue=0.2, weather_risk=0.8, tourist_density=0.0)
        for activity in state.suggested_next:
            assert not activity.weather_sensitive

    def test_golden_hour_hint_mentions_sunset(self):
        state = self.orc.assess(hour=17, fatigue=0.2, weather_risk=0.0, tourist_density=0.0)
        assert "hoàng hôn" in state.hint.lower() or "vàng" in state.hint.lower() or "biển" in state.hint.lower()

    def test_max_suggestions_reduced_on_high_fatigue(self):
        state = self.orc.assess(hour=14, fatigue=0.85, weather_risk=0.0, tourist_density=0.0)
        assert state.max_suggestions == 1

    def test_max_suggestions_normal_on_fresh(self):
        state = self.orc.assess(hour=9, fatigue=0.10, weather_risk=0.0, tourist_density=0.0)
        assert state.max_suggestions == 3

    def test_wants_beach_text_suggests_beach(self):
        state = self.orc.assess(
            hour=9, fatigue=0.2, weather_risk=0.1, tourist_density=0.2,
            incoming_text="muốn ra biển tắm"
        )
        names = [a.name.lower() for a in state.suggested_next]
        assert any("bãi" in n or "vịnh" in n or "hòn" in n or "gành" in n for n in names)

    def test_wants_food_suggests_restaurant(self):
        state = self.orc.assess(
            hour=12, fatigue=0.3, weather_risk=0.0, tourist_density=0.0,
            incoming_text="ăn gì giờ nhỉ, đói rồi"
        )
        assert len(state.suggested_next) > 0

    def test_completed_activity_filtered(self):
        self.orc.mark_completed("Bún cá ngừ")
        state = self.orc.assess(hour=8, fatigue=0.1, weather_risk=0.0, tourist_density=0.0,
                                incoming_text="ăn sáng")
        names = [a.name for a in state.suggested_next]
        assert "Bún cá ngừ" not in names

    def test_reset_day_clears_state(self):
        self.orc.mark_completed("Gành Đá Đĩa")
        self.orc.reset_day()
        assert self.orc._completed_today == []
        assert self.orc._transitions_today == 0

    def test_signals_include_phase_and_posture(self):
        state = self.orc.assess(hour=10, fatigue=0.2, weather_risk=0.0, tourist_density=0.0)
        assert any("phase_" in s for s in state.signals)
        assert any("posture_" in s for s in state.signals)

    def test_day_arc_progress_is_fraction(self):
        state = self.orc.assess(hour=12, fatigue=0.3, weather_risk=0.0, tourist_density=0.0)
        assert 0.0 <= state.day_arc_progress <= 1.0

    def test_recovery_hint_on_exhausted(self):
        state = self.orc.assess(hour=15, fatigue=0.92, weather_risk=0.0, tourist_density=0.0)
        assert "mệt" in state.hint.lower() or "nghỉ" in state.hint.lower() or "sức" in state.hint.lower()


# ===========================================================================
# DecisionFatigueReducer
# ===========================================================================


class TestDecisionFatigueReducer:
    def setup_method(self):
        self.reducer = DecisionFatigueReducer()

    def test_fresh_state_normal_mode(self):
        state = self.reducer.assess("ăn gì giờ nhỉ")
        assert state.reply_mode in ("normal", "simplified")
        assert state.max_options >= 2

    def test_overload_signal_increases_fatigue(self):
        s1 = self.reducer.assess("không biết chọn cái nào, nhiều quá")
        assert s1.fatigue_score > 0.0
        assert "overload_detected" in s1.signals

    def test_multiple_overload_triggers_simplified(self):
        self.reducer.assess("không biết")
        self.reducer.assess("khó chọn, rối quá")
        state = self.reducer.assess("tùy bạn thôi, không muốn nghĩ")
        assert state.reply_mode in ("simplified", "single_choice")
        assert state.max_options <= 2

    def test_recovery_signal_reduces_score(self):
        self.reducer.assess("không biết, nhiều quá")
        before = self.reducer.current_score
        self.reducer.assess("ok rồi, biết rồi, ổn rồi")
        after = self.reducer.current_score
        assert after < before

    def test_high_physical_fatigue_blends_in(self):
        state = self.reducer.assess("đâu cũng được", context_fatigue=0.80)
        # Physical fatigue = 0.80 blended in → should elevate decision fatigue
        assert state.fatigue_score > 0.15

    def test_overload_detected_flag(self):
        self.reducer.assess("không biết chọn cái nào")
        self.reducer.assess("khó chọn, nhiều quá")
        state = self.reducer.assess("thôi kệ, bạn chọn đi")
        assert state.overload_detected is True

    def test_single_choice_mode_max_options_one(self):
        # Simulate very high fatigue
        for _ in range(5):
            self.reducer.assess("không biết, rối quá, nhiều quá")
        state = self.reducer.assess("không muốn nghĩ", context_fatigue=0.9)
        assert state.max_options == 1
        assert state.reply_mode == "single_choice"

    def test_reset_reduces_score(self):
        for _ in range(3):
            self.reducer.assess("không biết, nhiều quá")
        before = self.reducer.current_score
        self.reducer.reset()
        after = self.reducer.current_score
        assert after < before

    def test_no_overload_on_neutral_text(self):
        state = self.reducer.assess("500k ăn trưa hải sản")
        assert state.fatigue_score < 0.3

    def test_decision_request_increments_count(self):
        self.reducer.assess("nên đi đâu giờ")
        self.reducer.assess("hay là ra biển")
        state = self.reducer.assess("hay không nhỉ")
        assert self.reducer._decision_count >= 2

    def test_preference_updates_exported(self):
        self.reducer.assess("không biết")
        updates = self.reducer.to_preference_updates()
        assert "df_score" in updates
        assert "df_decision_count" in updates

    def test_load_from_preferences(self):
        self.reducer.load_from_preferences({"df_score": 0.55, "df_decision_count": 7})
        assert abs(self.reducer.current_score - 0.55) < 0.01
        assert self.reducer._decision_count == 7

    # simplify_reply ---------------------------------------------------------

    def test_simplify_reply_normal_unchanged(self):
        text = "Bạn có thể chọn:\n• Bãi Xép\n• Vịnh Hòa\n• Hòn Yến"
        result = simplify_reply(text, max_options=3, mode="normal")
        assert result == text

    def test_simplify_reply_limits_options(self):
        text = "Bạn có thể chọn:\n• Option 1\n• Option 2\n• Option 3"
        result = simplify_reply(text, max_options=2, mode="simplified")
        assert "Option 3" not in result
        assert "Option 1" in result

    def test_single_choice_gives_one_recommendation(self):
        text = "Một số gợi ý:\n• Bãi Xép — bãi yên tĩnh\n• Vịnh Hòa — xa hơn"
        result = simplify_reply(text, max_options=1, mode="single_choice")
        assert result.startswith("Mình gợi ý:")
        assert "Vịnh Hòa" not in result

    def test_simplified_keeps_non_option_text(self):
        text = "Thời tiết đẹp:\n• Bãi Xép\n• Vịnh Hòa\n• Hòn Yến"
        result = simplify_reply(text, max_options=1, mode="simplified")
        # Non-option text should be preserved
        assert "Thời tiết" in result


# ===========================================================================
# Integration: Part 2 fields present in TravelOperatingState
# ===========================================================================


class TestTravelOperatingSystemPart2Integration:
    def test_travel_flow_state_field_exists(self):
        from app.orchestration.travel_operating_system import TravelOperatingState
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(TravelOperatingState)}
        assert "travel_flow" in field_names
        assert "geography" in field_names
        assert "decision_fatigue" in field_names

    def test_travel_flow_orchestrator_instantiable(self):
        from app.orchestration.travel_flow_orchestrator import TravelFlowOrchestrator
        orc = TravelFlowOrchestrator()
        state = orc.assess(hour=10, fatigue=0.3, weather_risk=0.1, tourist_density=0.2)
        assert state is not None
        assert state.posture in ("energize", "sustain", "rest", "recover", "flexible")

    def test_geography_engine_instantiable(self):
        from app.emotional.geography_engine import EmotionalGeographyEngine
        engine = EmotionalGeographyEngine()
        assert len(engine.get_state().place_profiles) >= 9

    def test_decision_fatigue_reducer_instantiable(self):
        from app.services.decision_fatigue_reducer import DecisionFatigueReducer
        r = DecisionFatigueReducer()
        state = r.assess("không biết chọn cái nào")
        assert state.fatigue_score >= 0.0
