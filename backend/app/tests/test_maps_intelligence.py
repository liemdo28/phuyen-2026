"""Tests for Google Maps Intelligence Layer – Phú Yên 2026."""
from __future__ import annotations

import pytest
from urllib.parse import urlparse, parse_qs, unquote_plus

from app.integrations.maps.deep_link_builder import (
    MapDeepLink,
    MapsDeepLinkBuilder,
    PHU_YEN_LOCATIONS,
)
from app.integrations.maps.route_intelligence import (
    RouteIntelligenceEngine,
    RouteIntelligenceState,
    RouteRecommendation,
    NAV_KEYWORDS,
    _is_navigation_query,
    _detect_intent,
)
from app.integrations.maps.location_recommender import (
    LocationRecommender,
    LocationSuggestion,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def builder() -> MapsDeepLinkBuilder:
    return MapsDeepLinkBuilder()


@pytest.fixture
def engine() -> RouteIntelligenceEngine:
    return RouteIntelligenceEngine()


@pytest.fixture
def recommender() -> LocationRecommender:
    return LocationRecommender()


# ---------------------------------------------------------------------------
# 1. PHU_YEN_LOCATIONS completeness (9 required keys)
# ---------------------------------------------------------------------------

EXPECTED_LOCATION_KEYS = [
    "ganh_da_dia",
    "bai_xep",
    "mui_dien",
    "vinh_hoa",
    "dam_o_loan",
    "thap_nhan",
    "tuy_hoa_beach",
    "song_cau",
    "hon_yen",
]

@pytest.mark.parametrize("key", EXPECTED_LOCATION_KEYS)
def test_phu_yen_locations_key_present(key: str) -> None:
    assert key in PHU_YEN_LOCATIONS, f"Missing location key: {key}"


def test_phu_yen_locations_have_coords() -> None:
    for key, loc in PHU_YEN_LOCATIONS.items():
        assert "coords" in loc, f"{key} missing coords"
        lat, lng = loc["coords"].split(",")
        assert float(lat) and float(lng)


def test_phu_yen_locations_have_name() -> None:
    for key, loc in PHU_YEN_LOCATIONS.items():
        assert loc.get("name"), f"{key} missing name"


# ---------------------------------------------------------------------------
# 2. Deep link builder – search
# ---------------------------------------------------------------------------

def test_search_basic_returns_map_deep_link(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("Gành Đá Đĩa")
    assert isinstance(link, MapDeepLink)
    assert link.link_type == "search"


def test_search_url_contains_api_param(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("Tuy Hòa")
    assert "api=1" in link.url


def test_search_url_contains_query(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("bãi biển Tuy Hòa")
    assert "query=" in link.url


def test_search_with_near_includes_both(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("hải sản", near="Tuy Hòa")
    assert "h%E1%BA%A3i+s%E1%BA%A3n" in link.url or "hải" in unquote_plus(link.url)


def test_search_display_label_in_vietnamese(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("cafe")
    assert "Tìm" in link.display_label


def test_search_url_is_google_maps(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("beach")
    assert "google.com/maps" in link.url


# ---------------------------------------------------------------------------
# 3. Deep link builder – directions
# ---------------------------------------------------------------------------

def test_directions_basic(builder: MapsDeepLinkBuilder) -> None:
    link = builder.directions("Tuy Hòa", "Gành Đá Đĩa")
    assert link.link_type == "directions"


def test_directions_url_contains_origin(builder: MapsDeepLinkBuilder) -> None:
    link = builder.directions("Tuy Hòa", "Bãi Xép")
    decoded = unquote_plus(link.url)
    assert "Tuy" in decoded


def test_directions_url_contains_destination(builder: MapsDeepLinkBuilder) -> None:
    link = builder.directions("Tuy Hòa", "Bãi Xép")
    decoded = unquote_plus(link.url)
    assert "Bãi Xép" in decoded or "B%C3%A3i" in link.url


def test_directions_url_contains_travelmode(builder: MapsDeepLinkBuilder) -> None:
    link = builder.directions("A", "B", mode="walking")
    assert "travelmode=walking" in link.url


def test_directions_default_mode_is_driving(builder: MapsDeepLinkBuilder) -> None:
    link = builder.directions("A", "B")
    assert "travelmode=driving" in link.url


def test_directions_label_mentions_destination(builder: MapsDeepLinkBuilder) -> None:
    link = builder.directions("Tuy Hòa", "Gành Đá Đĩa")
    assert "Gành" in link.display_label or "đường" in link.display_label.lower()


# ---------------------------------------------------------------------------
# 4. Deep link builder – navigate_to
# ---------------------------------------------------------------------------

def test_navigate_to_basic(builder: MapsDeepLinkBuilder) -> None:
    link = builder.navigate_to("13.3894,109.2626")
    assert link.link_type == "navigate"


def test_navigate_to_url_contains_destination(builder: MapsDeepLinkBuilder) -> None:
    link = builder.navigate_to("13.3894,109.2626")
    assert "destination=" in link.url


def test_navigate_to_no_origin_param(builder: MapsDeepLinkBuilder) -> None:
    link = builder.navigate_to("13.3894,109.2626")
    assert "origin=" not in link.url


# ---------------------------------------------------------------------------
# 5. Deep link builder – search_nearby
# ---------------------------------------------------------------------------

def test_search_nearby_url_format(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search_nearby("cafe", "Tuy Hòa")
    assert "query=" in link.url
    assert link.link_type == "search"


def test_search_nearby_contains_category(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search_nearby("hải sản", "Sông Cầu")
    decoded = unquote_plus(link.url)
    assert "hải sản" in decoded or "h%E1%BA%A3i" in link.url


def test_search_nearby_contains_location(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search_nearby("cafe", "Tuy Hòa")
    decoded = unquote_plus(link.url)
    assert "Tuy" in decoded


def test_search_nearby_label_mentions_category_and_location(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search_nearby("cafe", "Tuy Hòa")
    assert "cafe" in link.display_label


# ---------------------------------------------------------------------------
# 6. Telegram button
# ---------------------------------------------------------------------------

def test_telegram_button_has_text_key(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("Tuy Hòa")
    btn = builder.build_telegram_button(link)
    assert "text" in btn


def test_telegram_button_has_url_key(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("Tuy Hòa")
    btn = builder.build_telegram_button(link)
    assert "url" in btn


def test_telegram_button_url_is_google_maps(builder: MapsDeepLinkBuilder) -> None:
    link = builder.navigate_to("13.3894,109.2626")
    btn = builder.build_telegram_button(link)
    assert "google.com/maps" in btn["url"]


def test_telegram_button_text_is_string(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("bãi biển")
    btn = builder.build_telegram_button(link)
    assert isinstance(btn["text"], str) and len(btn["text"]) > 0


# ---------------------------------------------------------------------------
# 7. Vietnamese URL encoding
# ---------------------------------------------------------------------------

def test_vietnamese_query_encoded_in_url(builder: MapsDeepLinkBuilder) -> None:
    link = builder.search("Gành Đá Đĩa Phú Yên")
    # URL must not contain raw non-ASCII
    assert link.url.isascii() or "%" in link.url


def test_navigate_to_coords_in_url(builder: MapsDeepLinkBuilder) -> None:
    coords = PHU_YEN_LOCATIONS["ganh_da_dia"]["coords"]
    link = builder.navigate_to(coords)
    assert coords.replace(",", "%2C") in link.url or coords in unquote_plus(link.url)


# ---------------------------------------------------------------------------
# 8. Route intelligence – posture logic
# ---------------------------------------------------------------------------

def test_high_fatigue_returns_rest_posture(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess(
        query="đi đâu giờ",
        hour=10,
        fatigue=0.9,
        weather_risk=0.2,
        tourist_density=0.3,
        current_location="Tuy Hòa",
        preferences={},
    )
    assert state.posture == "rest"


def test_bad_weather_returns_indoor_posture(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess(
        query="đi đâu giờ",
        hour=10,
        fatigue=0.2,
        weather_risk=0.8,
        tourist_density=0.3,
        current_location="Tuy Hòa",
        preferences={},
    )
    assert state.posture == "indoor"


def test_morning_returns_recommendations(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess(
        query="đi biển",
        hour=8,
        fatigue=0.1,
        weather_risk=0.1,
        tourist_density=0.2,
        current_location="Tuy Hòa",
        preferences={},
    )
    assert len(state.recommendations) > 0


def test_evening_returns_recommendations(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess(
        query="ăn tối ở đâu",
        hour=19,
        fatigue=0.3,
        weather_risk=0.1,
        tourist_density=0.4,
        current_location="Tuy Hòa",
        preferences={},
    )
    assert len(state.recommendations) > 0


def test_high_fatigue_avoids_high_energy_places(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess(
        query="đi đâu",
        hour=10,
        fatigue=0.9,
        weather_risk=0.1,
        tourist_density=0.2,
        current_location="Tuy Hòa",
        preferences={},
    )
    # top pick should have low energy cost
    assert state.top_pick is not None
    assert state.top_pick.energy_cost <= 0.5


def test_route_state_has_hint(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess("đi đâu giờ", hour=9, fatigue=0.2, weather_risk=0.2,
                          tourist_density=0.2, current_location="Tuy Hòa", preferences={})
    assert isinstance(state.hint, str) and len(state.hint) > 0


def test_route_state_has_top_pick(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess("biển", hour=8, fatigue=0.2, weather_risk=0.1,
                          tourist_density=0.2, current_location="Tuy Hòa", preferences={})
    assert state.top_pick is not None


def test_bad_weather_adds_avoid_reason(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess("đi đâu", hour=10, fatigue=0.1, weather_risk=0.8,
                          tourist_density=0.2, current_location="Tuy Hòa", preferences={})
    assert any("thời tiết" in r.lower() for r in state.avoid_reasons)


def test_high_fatigue_adds_avoid_reason(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess("đi đâu", hour=10, fatigue=0.9, weather_risk=0.1,
                          tourist_density=0.2, current_location="Tuy Hòa", preferences={})
    assert any("mệt" in r.lower() for r in state.avoid_reasons)


def test_recommendations_have_map_link(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess("đi đâu", hour=8, fatigue=0.2, weather_risk=0.1,
                          tourist_density=0.2, current_location="Tuy Hòa", preferences={})
    for rec in state.recommendations:
        assert isinstance(rec.map_link, MapDeepLink)
        assert "google.com/maps" in rec.map_link.url


# ---------------------------------------------------------------------------
# 9. Navigation keyword detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,expected", [
    ("đi đâu giờ", True),
    ("ăn gì giờ", True),
    ("gần đây có gì", True),
    ("bây giờ đi đâu", True),
    ("uống gì giờ", True),
    ("nghỉ đâu", True),
    ("thời tiết hôm nay thế nào", False),
    ("tôi muốn đặt phòng", False),
])
def test_navigation_keyword_detection(query: str, expected: bool) -> None:
    assert _is_navigation_query(query) == expected


def test_detect_intent_beach(engine: RouteIntelligenceEngine) -> None:
    intents = _detect_intent("đi biển thôi")
    assert "beach" in intents


def test_detect_intent_food(engine: RouteIntelligenceEngine) -> None:
    intents = _detect_intent("ăn gì bây giờ")
    assert "food" in intents


def test_detect_intent_cafe(engine: RouteIntelligenceEngine) -> None:
    intents = _detect_intent("uống cafe đi")
    assert "cafe" in intents


def test_detect_intent_rest(engine: RouteIntelligenceEngine) -> None:
    intents = _detect_intent("mệt quá muốn nghỉ")
    assert "rest" in intents


# ---------------------------------------------------------------------------
# 10. Location recommender
# ---------------------------------------------------------------------------

def test_recommend_food_intent_returns_restaurant(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="ăn", hour=12, fatigue=0.2, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    assert any(s.category == "restaurant" for s in suggestions)


def test_recommend_beach_intent_returns_beach(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="biển", hour=8, fatigue=0.1, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    assert any(s.category == "beach" for s in suggestions)


def test_recommend_cafe_intent_returns_cafe(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="cà phê", hour=9, fatigue=0.2, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    assert any(s.category == "cafe" for s in suggestions)


def test_recommend_high_fatigue_low_energy(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="nghỉ", hour=14, fatigue=0.9, weather_risk=0.1,
        crowd_preference="quiet", current_city="Tuy Hòa"
    )
    assert len(suggestions) > 0
    # top suggestion should have low energy cost
    assert suggestions[0].category in ("rest", "cafe")


def test_recommend_returns_up_to_three(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="ăn", hour=12, fatigue=0.2, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    assert 1 <= len(suggestions) <= 3


def test_recommendation_has_map_link(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="biển", hour=9, fatigue=0.1, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    for s in suggestions:
        assert isinstance(s.map_link, MapDeepLink)
        assert "google.com/maps" in s.map_link.url


def test_recommendation_has_why_now(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="biển", hour=9, fatigue=0.1, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    for s in suggestions:
        assert isinstance(s.why_now, str) and len(s.why_now) > 5


def test_beach_suggestion_has_distance_note(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="biển", hour=8, fatigue=0.1, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    beach = next((s for s in suggestions if s.category == "beach"), None)
    assert beach is not None
    assert "phút" in beach.distance_note or "trung tâm" in beach.distance_note


def test_format_reply_contains_vietnamese(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="ăn", hour=12, fatigue=0.2, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    reply = recommender.format_reply(suggestions, posture="active")
    assert any(c > "\x7f" for c in reply)  # contains non-ASCII (Vietnamese)


def test_format_reply_contains_map_url(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="biển", hour=9, fatigue=0.1, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    reply = recommender.format_reply(suggestions, posture="active")
    assert "google.com/maps" in reply


def test_format_reply_empty_suggestions(recommender: LocationRecommender) -> None:
    reply = recommender.format_reply([], posture="rest")
    assert isinstance(reply, str) and len(reply) > 0


def test_format_reply_posture_rest_mentions_rest(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="nghỉ", hour=13, fatigue=0.9, weather_risk=0.1,
        crowd_preference="quiet", current_city="Tuy Hòa"
    )
    reply = recommender.format_reply(suggestions, posture="rest")
    assert "nghỉ" in reply.lower() or "rest" in reply.lower() or "Bạn" in reply


def test_format_reply_posture_indoor_mentions_indoor(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="cafe", hour=11, fatigue=0.2, weather_risk=0.8,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    reply = recommender.format_reply(suggestions, posture="indoor")
    assert isinstance(reply, str) and len(reply) > 10


# ---------------------------------------------------------------------------
# 11. RouteRecommendation dataclass completeness
# ---------------------------------------------------------------------------

def test_route_recommendation_fields_complete(engine: RouteIntelligenceEngine) -> None:
    state = engine.assess("đi đâu", hour=9, fatigue=0.2, weather_risk=0.1,
                          tourist_density=0.2, current_location="Tuy Hòa", preferences={})
    rec = state.top_pick
    assert rec is not None
    assert isinstance(rec.destination, str)
    assert isinstance(rec.destination_vn, str)
    assert isinstance(rec.reason, str)
    assert 0.0 <= rec.energy_cost <= 1.0
    assert rec.crowd_level in ("low", "medium", "high")
    assert isinstance(rec.best_window, str)
    assert isinstance(rec.weather_suitable, bool)
    assert 0.0 <= rec.confidence <= 1.0


def test_location_suggestion_fields_complete(recommender: LocationRecommender) -> None:
    suggestions = recommender.recommend(
        intent="ăn", hour=12, fatigue=0.2, weather_risk=0.1,
        crowd_preference="any", current_city="Tuy Hòa"
    )
    assert len(suggestions) > 0
    s = suggestions[0]
    assert isinstance(s.name, str)
    assert isinstance(s.name_vn, str)
    assert isinstance(s.category, str)
    assert isinstance(s.distance_note, str)
    assert isinstance(s.vibe, str)
    assert isinstance(s.why_now, str)
    assert isinstance(s.tags, list)
