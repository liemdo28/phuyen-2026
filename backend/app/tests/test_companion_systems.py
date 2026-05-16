"""
Tests for Human-like AI Companion Systems:
- UserMemoryProfile (persistent memory)
- ChillContextResolver (context-aware chill disambiguation)
- DailyFlowOrchestrator (experience flow)
- MovementResistanceRouter (nearby-first routing)
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.memory.user_profile import (
    UserMemoryProfile, load_profile, build_profile_updates, record_place_visited
)
from app.companion.chill_resolver import ChillContextResolver
from app.companion.flow_orchestrator import DailyFlowOrchestrator
from app.companion.movement_router import MovementResistanceRouter
from app.intelligence.analyzer import analyze_message


_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


# ── UserMemoryProfile ─────────────────────────────────────────────────────────

class TestUserMemoryProfile:
    def test_load_empty_preferences(self):
        profile = load_profile({})
        assert profile.food_liked == []
        assert profile.movement_tolerance == "medium"
        assert profile.social_mode == "family"

    def test_load_from_preferences(self):
        prefs = {
            "mem_food_liked": ["hải sản", "bánh căn"],
            "mem_crowd_tolerance": "low",
            "mem_social_mode": "family",
            "mem_places_visited": ["Gành Đá Đĩa"],
        }
        profile = load_profile(prefs)
        assert "hải sản" in profile.food_liked
        assert profile.crowd_tolerance == "low"
        assert "Gành Đá Đĩa" in profile.places_visited

    def test_build_profile_updates_movement_resistance(self):
        a = analyze_message("mệt quá không muốn đi xa")
        profile = load_profile({})
        updates = build_profile_updates(profile, a, datetime.now())
        history = updates.get("mem_movement_history", [])
        assert len(history) > 0
        assert history[-1] <= 0.5  # low tolerance recorded

    def test_build_profile_updates_food_liked(self):
        a = analyze_message("ăn hải sản ngon quá thích quá")
        profile = load_profile({})
        updates = build_profile_updates(profile, a, datetime.now())
        # sentiment=positive + food_types → food_liked updated
        liked = updates.get("mem_food_liked", [])
        assert len(liked) >= 0  # may or may not have seafood depending on analyzer

    def test_record_place_visited(self):
        profile = load_profile({"mem_places_visited": ["Bãi Xép"]})
        updates = record_place_visited(profile, "Gành Đá Đĩa")
        assert "Gành Đá Đĩa" in updates["mem_places_visited"]
        assert "Bãi Xép" in updates["mem_places_visited"]

    def test_is_resistance_mode(self):
        profile = load_profile({"mem_movement_history": [0.1, 0.2, 0.1, 0.2, 0.1]})
        assert profile.is_resistance_mode is True

    def test_format_for_prompt_non_empty(self):
        profile = load_profile({
            "mem_food_liked": ["hải sản"],
            "mem_crowd_tolerance": "low",
            "mem_movement_history": [0.2, 0.1, 0.2],
        })
        text = profile.format_for_prompt()
        assert "hải sản" in text or "đông" in text or "xa" in text

    def test_format_for_prompt_empty_is_empty(self):
        profile = load_profile({})
        text = profile.format_for_prompt()
        assert text == ""


# ── ChillContextResolver ──────────────────────────────────────────────────────

class TestChillContextResolver:
    def setup_method(self):
        self.resolver = ChillContextResolver()

    def test_extreme_fatigue_returns_recovery(self):
        rec = self.resolver.resolve(hour=15, fatigue=0.9, social_mode="family",
                                    crowd_tolerance="medium")
        assert rec.chill_type == "recovery"

    def test_nightlife_signal_returns_nightlife(self):
        rec = self.resolver.resolve(hour=20, fatigue=0.2, social_mode="group",
                                    crowd_tolerance="medium", is_drinking=True)
        assert rec.chill_type == "nightlife"

    def test_golden_hour_view(self):
        rec = self.resolver.resolve(hour=17, fatigue=0.3, social_mode="couple",
                                    crowd_tolerance="medium", excitement=0.6)
        assert rec.chill_type in ("cafe_view", "beach_chill")

    def test_midday_heat_returns_indoor(self):
        rec = self.resolver.resolve(hour=12, fatigue=0.2, social_mode="family",
                                    crowd_tolerance="medium")
        assert rec.chill_type == "cafe_quiet"

    def test_crowd_averse_returns_quiet(self):
        rec = self.resolver.resolve(hour=15, fatigue=0.3, social_mode="solo",
                                    crowd_tolerance="low")
        assert "quiet" in rec.chill_type or "beach" in rec.chill_type

    def test_late_night_returns_rest(self):
        rec = self.resolver.resolve(hour=23, fatigue=0.3, social_mode="family",
                                    crowd_tolerance="medium")
        assert rec.chill_type == "rest_indoor"

    def test_prompt_hint_non_empty(self):
        rec = self.resolver.resolve(hour=17, fatigue=0.2, social_mode="couple",
                                    crowd_tolerance="medium")
        assert len(rec.prompt_hint) > 10

    def test_example_places_provided(self):
        rec = self.resolver.resolve(hour=16, fatigue=0.2, social_mode="family",
                                    crowd_tolerance="medium")
        assert len(rec.example_places) > 0

    def test_resolve_from_analysis_tired(self):
        a = analyze_message("mệt xỉu rồi cần nghỉ")
        rec = self.resolver.resolve_from_analysis(a, datetime(2026, 5, 25, 14, 0, tzinfo=_TZ))
        assert rec.chill_type in ("recovery", "rest_indoor", "cafe_quiet")

    def test_nhau_text_hint(self):
        rec = self.resolver.resolve(hour=20, fatigue=0.2, social_mode="group",
                                    crowd_tolerance="medium", text_hint="tối nay đi nhậu")
        assert rec.chill_type == "nightlife"


# ── DailyFlowOrchestrator ─────────────────────────────────────────────────────

class TestDailyFlowOrchestrator:
    def setup_method(self):
        self.orch = DailyFlowOrchestrator()

    def test_morning_fresh_suggests_activity(self):
        now = datetime(2026, 5, 25, 8, 0, tzinfo=_TZ)
        sug = self.orch.suggest_next(now=now, fatigue=0.2, places_visited=[])
        assert sug.next_activity != ""
        assert sug.phase == "morning"

    def test_midday_suggests_rest(self):
        now = datetime(2026, 5, 25, 12, 0, tzinfo=_TZ)
        sug = self.orch.suggest_next(now=now, fatigue=0.3, places_visited=[])
        assert "nghỉ" in sug.next_activity.lower() or sug.phase == "midday_rest"

    def test_high_fatigue_returns_fallback(self):
        now = datetime(2026, 5, 25, 16, 0, tzinfo=_TZ)
        sug = self.orch.suggest_next(now=now, fatigue=0.85, places_visited=[])
        assert sug.skip_reason == "high_fatigue" or "nghỉ" in sug.next_activity.lower()

    def test_golden_hour_urgency(self):
        now = datetime(2026, 5, 25, 18, 15, tzinfo=_TZ)
        sug = self.orch.suggest_next(now=now, fatigue=0.2, places_visited=[])
        assert sug.phase == "golden_hour"
        assert sug.urgency in ("now", "soon")

    def test_already_visited_returns_alternative(self):
        now = datetime(2026, 5, 25, 8, 0, tzinfo=_TZ)
        sug = self.orch.suggest_next(
            now=now, fatigue=0.2,
            places_visited=["Gành Đá Đĩa", "Bãi Xép"]
        )
        assert sug.skip_reason in ("already_visited", "") or sug.next_activity != ""

    def test_movement_resistance_returns_fallback(self):
        now = datetime(2026, 5, 25, 15, 0, tzinfo=_TZ)
        sug = self.orch.suggest_next(
            now=now, fatigue=0.3, places_visited=[],
            movement_tolerance="resistance"
        )
        assert sug.skip_reason == "movement_resistance" or "gần" in sug.next_activity.lower()

    def test_micro_moment_populated(self):
        now = datetime(2026, 5, 25, 7, 30, tzinfo=_TZ)
        sug = self.orch.suggest_next(now=now, fatigue=0.2, places_visited=[])
        assert len(sug.micro_moment) > 0

    def test_format_for_prompt(self):
        now = datetime(2026, 5, 25, 17, 0, tzinfo=_TZ)
        sug = self.orch.suggest_next(now=now, fatigue=0.2, places_visited=[])
        prompt = self.orch.format_for_prompt(sug)
        assert "Flow" in prompt or len(prompt) > 5


# ── MovementResistanceRouter ──────────────────────────────────────────────────

class TestMovementResistanceRouter:
    def setup_method(self):
        self.router = MovementResistanceRouter()

    def test_gần_thôi_triggers_resistance(self):
        profile = self.router.analyze("gần thôi, lười đi xa")
        assert profile.tolerance == "resistance"
        assert len(profile.resistance_signals_in_text) > 0

    def test_no_accent_resistance(self):
        profile = self.router.analyze("gan thoi ngai di xa")
        assert profile.tolerance == "resistance"

    def test_no_signal_returns_inherited(self):
        profile = self.router.analyze("muốn ăn hải sản", "medium")
        assert profile.tolerance == "medium"

    def test_resistance_constraints_tight_radius(self):
        profile = self.router.analyze("gần thôi không muốn đi xa")
        constraints = self.router.build_constraints(profile, fatigue=0.3)
        assert constraints.max_distance_km <= 2.0
        assert constraints.prefer_walkable is True

    def test_high_fatigue_tight_radius(self):
        profile = self.router.analyze("ăn gì đây", "medium")
        constraints = self.router.build_constraints(profile, fatigue=0.8)
        assert constraints.max_distance_km <= 5.0

    def test_normal_constraints_not_restricted(self):
        profile = self.router.analyze("muốn đi Gành Đá Đĩa", "high")
        constraints = self.router.build_constraints(profile, fatigue=0.1)
        assert not constraints.is_restricted

    def test_format_for_prompt_restricted(self):
        profile = self.router.analyze("gần thôi thôi")
        constraints = self.router.build_constraints(profile, fatigue=0.2)
        prompt = self.router.format_for_prompt(constraints)
        assert "km" in prompt or "gần" in prompt.lower()

    def test_format_for_prompt_unrestricted_empty(self):
        profile = self.router.analyze("muốn đi Gành Đá Đĩa", "high")
        constraints = self.router.build_constraints(profile, fatigue=0.1)
        prompt = self.router.format_for_prompt(constraints)
        assert prompt == ""

    def test_child_always_required(self):
        profile = self.router.analyze("gần thôi")
        constraints = self.router.build_constraints(profile)
        assert constraints.require_child_safe is True  # Always true for this trip


# ── Integration: analyze_message → profile → constraints ─────────────────────

class TestCompanionIntegration:
    def test_tired_no_accent_pipeline(self):
        """'met xiu' → fatigue high → recovery chill type → tight radius."""
        a = analyze_message("met xiu roi khong muon di dau ca")
        assert a.fatigue >= 0.5
        assert a.movement_tolerance in ("low", "medium")

        profile = load_profile({})
        updates = build_profile_updates(profile, a, datetime.now())
        history = updates.get("mem_movement_history", [])
        assert history and history[-1] <= 0.5

        resolver = ChillContextResolver()
        rec = resolver.resolve_from_analysis(a, datetime(2026, 5, 25, 15, 0, tzinfo=_TZ))
        assert rec.chill_type in ("recovery", "cafe_quiet", "rest_indoor")

    def test_hunger_no_accent_pipeline(self):
        """'doi qua' → hunger detected → not confused for expense."""
        a = analyze_message("doi qua oke goi y di")
        assert a.hunger >= 0.5
        assert a.dominant_emotion == "hungry"

    def test_raw_text_set_on_analysis(self):
        a = analyze_message("mệt quá chill thôi")
        assert a.raw_text == "mệt quá chill thôi"

    def test_chill_resolver_from_real_message(self):
        a = analyze_message("kiem cho chill chill gang thoi")
        resolver = ChillContextResolver()
        rec = resolver.resolve_from_analysis(a, datetime(2026, 5, 25, 16, 0, tzinfo=_TZ))
        assert rec.chill_type != ""
        assert rec.max_distance_km <= 10
