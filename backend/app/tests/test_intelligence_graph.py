"""
Tests for the Vietnamese Human Communication & Travel Intelligence Graph.

Covers:
- No-accent normalization
- Emotion detection (fatigue, hunger, stress, excitement)
- Sarcasm / exaggeration handling
- Social context (group type, movement tolerance, crowd tolerance)
- Travel intent detection
- Weather intelligence
- Prompt context generation
"""
from __future__ import annotations

import pytest

from app.intelligence.analyzer import analyze_message, build_prompt_context, _normalize


# ── Normalization ─────────────────────────────────────────────────────────────

class TestNormalization:
    def test_no_accent_fatigue(self):
        result = _normalize("met xiu roi")
        assert "mệt xỉu" in result

    def test_no_accent_hunger(self):
        result = _normalize("doi qua, an gi bay gio")
        assert "đói quá" in result
        assert "ăn gì" in result or "đi đâu" in result or "bây giờ" in result

    def test_no_accent_movement(self):
        result = _normalize("khong muon di xa, gan thoi")
        assert "không muốn" in result
        assert "gần thôi" in result

    def test_no_accent_food(self):
        result = _normalize("an sang o dau")
        assert "ăn sáng" in result

    def test_no_cascading_replacement(self):
        """Ensure 'không' doesn't get double-replaced after accent reconstruction."""
        result = _normalize("khong biet phai di dau")
        assert "kkhông" not in result
        assert "khôngkhông" not in result
        assert "không" in result

    def test_abbreviation_ny_expansion(self):
        """'ny' should expand to 'người yêu' for couple detection."""
        result = _normalize("đi với ny thôi")
        assert "người yêu" in result


# ── Emotion Detection ─────────────────────────────────────────────────────────

class TestEmotionDetection:
    def test_fatigue_direct(self):
        a = analyze_message("mệt xỉu rồi, không còn sức nữa")
        assert a.fatigue >= 0.8
        assert a.dominant_emotion == "tired"

    def test_fatigue_no_accent(self):
        a = analyze_message("met roi, met qua")
        assert a.fatigue >= 0.5
        assert a.dominant_emotion == "tired"

    def test_hunger_sarcasm(self):
        """'đói xỉu' is sarcastic exaggeration = very hungry."""
        a = analyze_message("đói xỉu rồi ăn gì đây")
        assert a.hunger >= 0.85
        assert a.dominant_emotion == "hungry"

    def test_hunger_indirect(self):
        a = analyze_message("kiếm gì ăn đi, chưa ăn gì cả")
        assert a.hunger >= 0.4
        assert a.dominant_emotion in ("hungry", "neutral")

    def test_stress_high(self):
        a = analyze_message("stress quá trời, rối hết cả lên, không biết làm gì")
        assert a.stress >= 0.6
        assert a.dominant_emotion == "stressed"

    def test_excitement(self):
        a = analyze_message("hào hứng quá, thích quá, đỉnh lắm")
        assert a.excitement >= 0.6
        assert a.dominant_emotion == "excited"

    def test_recovery_intent(self):
        a = analyze_message("đi healing chill nhẹ thôi, muốn yên tĩnh")
        assert a.recovery_need >= 0.5
        assert a.dominant_emotion == "need_rest"

    def test_confusion(self):
        a = analyze_message("không biết phải đi đâu, rối quá, nhiều lựa chọn quá")
        assert a.confusion >= 0.6


# ── Social Context ─────────────────────────────────────────────────────────────

class TestSocialContext:
    def test_family_detection(self):
        a = analyze_message("đi cả gia đình, có bé con theo")
        assert a.group_type == "family"
        assert a.needs_child_friendly is True

    def test_couple_detection(self):
        a = analyze_message("đi với ny, muốn chỗ lãng mạn")
        assert a.group_type == "couple"

    def test_couple_via_abbreviation(self):
        a = analyze_message("muốn ngắm hoàng hôn với ny")
        assert a.group_type == "couple"
        assert a.is_romantic is True

    def test_solo_detection(self):
        a = analyze_message("đi một mình thôi, solo trip")
        assert a.group_type == "solo"

    def test_group_detection(self):
        a = analyze_message("cả hội bạn bè 6 đứa đi")
        assert a.group_type == "group"

    def test_low_movement(self):
        a = analyze_message("mệt rồi, gần thôi, không muốn đi xa")
        assert a.movement_tolerance == "low"
        assert a.max_distance_km <= 5

    def test_low_movement_no_accent(self):
        a = analyze_message("met xiu roi, khong muon di dau ca")
        assert a.movement_tolerance == "low"

    def test_crowd_averse(self):
        a = analyze_message("đông quá nhức đầu, kiếm chỗ vắng ít người")
        assert a.crowd_tolerance == "low"

    def test_local_preference(self):
        a = analyze_message("local local thôi, người địa phương ăn đâu")
        assert a.prefers_local_food is True

    def test_romantic_context(self):
        a = analyze_message("ngắm hoàng hôn riêng tư, cafe view đẹp")
        assert a.is_romantic is True


# ── Travel Intent ─────────────────────────────────────────────────────────────

class TestTravelIntent:
    def test_beach_intent(self):
        a = analyze_message("muốn ra biển tắm, bãi nào đẹp")
        assert "beach" in a.travel_intents

    def test_food_tour_intent(self):
        a = analyze_message("muốn thử đặc sản phú yên, food tour đi")
        assert "food_tour" in a.travel_intents

    def test_nightlife_intent(self):
        a = analyze_message("tối nay đi bar uống bia không")
        assert "nightlife" in a.travel_intents

    def test_photography_intent(self):
        a = analyze_message("muốn chụp ảnh hoàng hôn, golden hour đẹp")
        assert "photography" in a.travel_intents

    def test_relaxation_intent(self):
        a = analyze_message("cần thư giãn, không làm gì cả")
        assert "relaxation" in a.travel_intents

    def test_attraction_intent(self):
        a = analyze_message("muốn tham quan gành đá đĩa")
        assert "attraction" in a.travel_intents

    def test_seafood_food_type(self):
        a = analyze_message("ăn hải sản tôm hùm sông cầu")
        assert "seafood" in a.food_types

    def test_cafe_food_type(self):
        a = analyze_message("uống cà phê buổi sáng ngắm biển")
        assert "cafe" in a.food_types

    def test_drinking_context(self):
        a = analyze_message("nhậu vài lon bia với mồi")
        assert a.is_drinking is True

    def test_golden_hour_preference(self):
        a = analyze_message("muốn xem hoàng hôn, golden hour đẹp nhất")
        assert a.time_preference == "golden_hour"

    def test_late_night_meal(self):
        a = analyze_message("ăn khuya quán nào mở khuya")
        assert a.meal_time == "late_night"

    def test_budget_preference(self):
        a = analyze_message("quán bình dân thôi, giá rẻ")
        assert a.price_preference == "budget"


# ── Weather Intelligence ───────────────────────────────────────────────────────

class TestWeatherIntelligence:
    def test_rain_redirect(self):
        a = analyze_message("mưa to quá không ra ngoài được")
        assert a.rain_level >= 0.7
        assert a.weather_action == "redirect_indoor"

    def test_heat_warn(self):
        a = analyze_message("nóng vãi, nóng quá trời")
        assert a.heat_level >= 0.8
        assert a.weather_action in ("suggest_cool_indoor", "warn_heat_midday")

    def test_sea_danger(self):
        a = analyze_message("biển động không tắm được, sóng to")
        assert a.sea_danger >= 0.7
        assert a.weather_action == "avoid_beach"

    def test_good_weather_positive(self):
        a = analyze_message("trời đẹp quá, nắng nhẹ mát mẻ")
        assert a.good_weather >= 0.6

    def test_sarcastic_heat(self):
        """'nóng muốn chết' = extremely hot, not literal death."""
        a = analyze_message("nóng muốn chết, oi bức khó chịu")
        assert a.heat_level >= 0.9


# ── Prompt Context Generation ──────────────────────────────────────────────────

class TestPromptContext:
    def test_fatigue_context_generated(self):
        a = analyze_message("mệt xỉu rồi, không muốn đi xa")
        ctx = build_prompt_context(a)
        assert "MỆT MỎI" in ctx or "mệt" in ctx.lower()
        assert len(ctx) > 0

    def test_family_context_generated(self):
        a = analyze_message("cả nhà đi, có bé con theo")
        ctx = build_prompt_context(a)
        assert "GIA ĐÌNH" in ctx or "trẻ em" in ctx.lower()

    def test_rain_context_generated(self):
        a = analyze_message("mưa to rồi không ra biển được")
        ctx = build_prompt_context(a)
        assert "MƯA" in ctx or "indoor" in ctx.lower() or "trong" in ctx.lower()

    def test_neutral_no_noise(self):
        """Neutral messages shouldn't generate noisy context."""
        a = analyze_message("xin chào, hôm nay thế nào")
        ctx = build_prompt_context(a)
        # Should be empty or very short for truly neutral message
        assert len(ctx) < 200

    def test_context_has_routing_signals(self):
        a = analyze_message("mệt quá, gần thôi, ít người, chỗ yên tĩnh")
        assert len(a.routing_hints) >= 2
        assert any("SIMPLIFY" in h or "FILTER" in h for h in a.routing_hints)
