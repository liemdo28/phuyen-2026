"""Fatigue/weather/crowd-aware route intelligence for Phú Yên."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.maps.deep_link_builder import (
    MapDeepLink,
    MapsDeepLinkBuilder,
    PHU_YEN_LOCATIONS,
)

# ---------------------------------------------------------------------------
# Vietnamese navigation keyword detection
# ---------------------------------------------------------------------------

NAV_KEYWORDS: list[str] = [
    "bây giờ đi đâu",
    "đi đâu giờ",
    "đâu giờ",
    "đi đâu",
    "gần đây có gì",
    "gần đây",
    "chỗ nào",
    "ăn gì giờ",
    "uống gì giờ",
    "nghỉ đâu",
]

INTENT_KEYWORDS: dict[str, list[str]] = {
    "beach": ["biển", "tắm biển", "bờ biển", "bãi biển"],
    "food": ["ăn", "ăn gì", "ăn ở đâu", "quán ăn", "nhà hàng", "hải sản", "cơm", "bún", "phở"],
    "cafe": ["cafe", "cà phê", "cà-phê", "uống", "trà", "coffee"],
    "rest": ["nghỉ", "mệt", "ngủ", "nghỉ ngơi", "nghỉ trưa"],
    "view": ["view", "ngắm", "hoàng hôn", "bình minh", "sunset", "sunrise"],
}


def _detect_intent(query: str) -> set[str]:
    """Return a set of detected intent keys from the query string."""
    q = query.lower()
    found: set[str] = set()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            found.add(intent)
    return found


def _is_navigation_query(query: str) -> bool:
    """Return True if the query contains a known Vietnamese navigation keyword."""
    q = query.lower()
    return any(kw in q for kw in NAV_KEYWORDS)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class RouteRecommendation:
    destination: str
    destination_vn: str
    reason: str            # Vietnamese explanation
    map_link: MapDeepLink
    energy_cost: float     # 0.0–1.0
    crowd_level: str       # low | medium | high
    best_window: str       # e.g. "6h-9h"
    weather_suitable: bool
    confidence: float      # 0.0–1.0


@dataclass
class RouteIntelligenceState:
    recommendations: list[RouteRecommendation]
    top_pick: RouteRecommendation | None
    avoid_reasons: list[str]
    posture: str   # active | rest | gentle | indoor
    hint: str      # Vietnamese summary hint


# ---------------------------------------------------------------------------
# Curated place catalogue used by the engine
# ---------------------------------------------------------------------------

_PLACE_CATALOGUE: list[dict] = [
    # Beaches
    {
        "key": "bai_xep",
        "destination": "Bãi Xép",
        "destination_vn": "Bãi Xép",
        "category": "beach",
        "energy_cost": 0.4,
        "crowd_level": "low",
        "best_window": "7h-11h",
        "best_hours": (6, 11),
        "afternoon_ok": True,
        "weather_sensitive": True,
        "coords": PHU_YEN_LOCATIONS["bai_xep"]["coords"],
        "tags": ["biển", "yên tĩnh", "an toàn"],
    },
    {
        "key": "tuy_hoa_beach",
        "destination": "Bãi biển Tuy Hòa",
        "destination_vn": "Bãi biển Tuy Hòa",
        "category": "beach",
        "energy_cost": 0.3,
        "crowd_level": "medium",
        "best_window": "7h-11h",
        "best_hours": (6, 11),
        "afternoon_ok": True,
        "weather_sensitive": True,
        "coords": PHU_YEN_LOCATIONS["tuy_hoa_beach"]["coords"],
        "tags": ["biển", "trung tâm", "tiện lợi"],
    },
    {
        "key": "vinh_hoa",
        "destination": "Vịnh Hòa",
        "destination_vn": "Vịnh Hòa",
        "category": "beach",
        "energy_cost": 0.5,
        "crowd_level": "low",
        "best_window": "7h-11h",
        "best_hours": (6, 12),
        "afternoon_ok": True,
        "weather_sensitive": True,
        "coords": PHU_YEN_LOCATIONS["vinh_hoa"]["coords"],
        "tags": ["biển", "xa xôi", "hoang sơ"],
    },
    {
        "key": "hon_yen",
        "destination": "Hòn Yến",
        "destination_vn": "Hòn Yến",
        "category": "beach",
        "energy_cost": 0.6,
        "crowd_level": "low",
        "best_window": "7h-11h",
        "best_hours": (6, 11),
        "afternoon_ok": False,
        "weather_sensitive": True,
        "coords": PHU_YEN_LOCATIONS["hon_yen"]["coords"],
        "tags": ["biển", "lặn ngắm san hô", "đảo"],
    },
    # Attractions
    {
        "key": "ganh_da_dia",
        "destination": "Gành Đá Đĩa",
        "destination_vn": "Gành Đá Đĩa",
        "category": "attraction",
        "energy_cost": 0.5,
        "crowd_level": "medium",
        "best_window": "6h-9h",
        "best_hours": (6, 9),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "coords": PHU_YEN_LOCATIONS["ganh_da_dia"]["coords"],
        "tags": ["thiên nhiên", "đá basalt", "sáng sớm"],
    },
    {
        "key": "mui_dien",
        "destination": "Mũi Điện",
        "destination_vn": "Mũi Điện",
        "category": "attraction",
        "energy_cost": 0.7,
        "crowd_level": "low",
        "best_window": "4:30h-7h",
        "best_hours": (4, 7),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "coords": PHU_YEN_LOCATIONS["mui_dien"]["coords"],
        "tags": ["bình minh", "cực đông", "leo núi"],
    },
    {
        "key": "thap_nhan",
        "destination": "Tháp Nhạn",
        "destination_vn": "Tháp Nhạn",
        "category": "heritage",
        "energy_cost": 0.25,
        "crowd_level": "low",
        "best_window": "7h-17h",
        "best_hours": (7, 17),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "coords": PHU_YEN_LOCATIONS["thap_nhan"]["coords"],
        "tags": ["văn hóa", "Chăm Pa", "lịch sử"],
    },
    {
        "key": "dam_o_loan",
        "destination": "Đầm Ô Loan",
        "destination_vn": "Đầm Ô Loan",
        "category": "nature",
        "energy_cost": 0.3,
        "crowd_level": "low",
        "best_window": "7h-17h",
        "best_hours": (7, 17),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "coords": PHU_YEN_LOCATIONS["dam_o_loan"]["coords"],
        "tags": ["thiên nhiên", "đầm phá", "hải sản"],
    },
    # Cafes
    {
        "key": "cafe_tuy_hoa_1",
        "destination": "Cà phê Tuy Hòa",
        "destination_vn": "Cà phê Tuy Hòa",
        "category": "cafe",
        "energy_cost": 0.1,
        "crowd_level": "medium",
        "best_window": "7h-21h",
        "best_hours": (7, 22),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "coords": "13.0878,109.3027",
        "tags": ["cafe", "nghỉ", "view biển"],
        "query": "cafe Tuy Hòa view biển",
    },
    {
        "key": "cafe_local_1",
        "destination": "Cà phê sáng Tuy Hòa",
        "destination_vn": "Cà phê sáng Tuy Hòa",
        "category": "cafe",
        "energy_cost": 0.1,
        "crowd_level": "low",
        "best_window": "6h-10h",
        "best_hours": (6, 10),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "coords": "13.0878,109.3027",
        "tags": ["cafe", "sáng sớm", "local"],
        "query": "cafe sáng Tuy Hòa",
    },
    # Restaurants
    {
        "key": "hai_san_tuy_hoa",
        "destination": "Hải sản Tuy Hòa",
        "destination_vn": "Nhà hàng hải sản Tuy Hòa",
        "category": "restaurant",
        "energy_cost": 0.1,
        "crowd_level": "medium",
        "best_window": "11h-13h, 17h-20h",
        "best_hours": (11, 20),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "coords": "13.0878,109.3027",
        "tags": ["ăn", "hải sản", "ngon"],
        "query": "hải sản Tuy Hòa",
    },
    {
        "key": "bun_ca_tuy_hoa",
        "destination": "Bún cá Tuy Hòa",
        "destination_vn": "Bún cá Tuy Hòa",
        "category": "restaurant",
        "energy_cost": 0.1,
        "crowd_level": "medium",
        "best_window": "6h-10h",
        "best_hours": (6, 10),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "coords": "13.0878,109.3027",
        "tags": ["ăn", "sáng", "đặc sản", "local"],
        "query": "bún cá Tuy Hòa",
    },
    {
        "key": "tran_phu_street",
        "destination": "Đường Trần Phú",
        "destination_vn": "Phố đêm Trần Phú",
        "category": "market",
        "energy_cost": 0.2,
        "crowd_level": "high",
        "best_window": "18h-22h",
        "best_hours": (18, 22),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "coords": "13.0910,109.3050",
        "tags": ["phố đêm", "ăn uống", "chợ đêm"],
        "query": "phố đêm Trần Phú Tuy Hòa",
    },
    # Rest spots
    {
        "key": "rest_hotel_pool",
        "destination": "Hồ bơi khách sạn",
        "destination_vn": "Hồ bơi khách sạn Tuy Hòa",
        "category": "rest",
        "energy_cost": 0.05,
        "crowd_level": "low",
        "best_window": "12h-15h",
        "best_hours": (11, 16),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "coords": "13.0878,109.3027",
        "tags": ["nghỉ", "thư giãn", "khách sạn"],
        "query": "khách sạn hồ bơi Tuy Hòa",
    },
    {
        "key": "rest_park",
        "destination": "Công viên trung tâm",
        "destination_vn": "Công viên trung tâm Tuy Hòa",
        "category": "rest",
        "energy_cost": 0.1,
        "crowd_level": "low",
        "best_window": "6h-11h, 16h-19h",
        "best_hours": (6, 19),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "coords": "13.0939,109.3095",
        "tags": ["nghỉ", "bóng mát", "công viên"],
        "query": "công viên Tuy Hòa",
    },
]


def _build_reason(place: dict, posture: str, hour: int) -> str:
    """Generate a Vietnamese reason sentence for a recommendation."""
    cat = place["category"]
    name = place["destination_vn"]
    if posture == "rest":
        return f"{name} là lựa chọn nhẹ nhàng để bạn nghỉ ngơi lấy lại sức."
    if posture == "indoor":
        return f"{name} phù hợp khi thời tiết không thuận lợi, thoải mái trong nhà."
    if cat == "beach" and hour < 11:
        return f"Buổi sáng là thời điểm đẹp nhất để tắm biển tại {name}."
    if cat == "beach":
        return f"{name} mát mẻ buổi chiều, lý tưởng để thư giãn."
    if cat == "restaurant" and hour < 10:
        return f"Thưởng thức bữa sáng đặc sản địa phương tại {name}."
    if cat == "restaurant":
        return f"{name} nổi tiếng ngon miệng, hợp túi tiền du khách."
    if cat == "cafe":
        return f"{name} – góc cà phê yên tĩnh để nhấm nháp và thư giãn."
    if cat == "market":
        return f"{name} sôi động buổi tối, nhiều lựa chọn ăn uống hấp dẫn."
    if cat == "attraction":
        return f"{name} là điểm check-in ấn tượng không thể bỏ qua ở Phú Yên."
    if cat == "heritage":
        return f"{name} mang đậm dấu ấn văn hóa Chăm Pa, thích hợp tham quan."
    if cat == "nature":
        return f"{name} phong cảnh thiên nhiên yên bình, dễ chịu."
    return f"{name} là gợi ý phù hợp với bạn lúc này."


def _score_place(
    place: dict,
    hour: int,
    fatigue: float,
    weather_risk: float,
    tourist_density: float,
    intents: set[str],
    posture: str,
) -> float:
    """Return a relevance score 0.0–1.0 for this place given current context."""
    score = 0.5

    cat = place["category"]
    low_h, high_h = place["best_hours"]

    # Time-of-day fit
    if low_h <= hour < high_h:
        score += 0.2
    elif cat == "beach" and 15 <= hour < 18 and place.get("afternoon_ok"):
        score += 0.15

    # Intent matching
    intent_map = {
        "beach": {"beach"},
        "food": {"restaurant", "market"},
        "cafe": {"cafe"},
        "rest": {"rest", "cafe"},
        "view": {"attraction", "beach"},
    }
    for intent in intents:
        if cat in intent_map.get(intent, set()):
            score += 0.25

    # Fatigue – prefer low energy cost places
    if fatigue > 0.7:
        score -= place["energy_cost"] * 0.4
        if place["energy_cost"] < 0.2:
            score += 0.15

    # Weather – downgrade weather-sensitive places in bad weather
    if weather_risk > 0.6 and place.get("weather_sensitive"):
        score -= 0.35
    if weather_risk > 0.6 and cat in ("cafe", "restaurant", "rest"):
        score += 0.15

    # Crowd preference
    if tourist_density > 0.5 and place["crowd_level"] == "low":
        score += 0.1
    if tourist_density > 0.5 and place["crowd_level"] == "high":
        score -= 0.1

    # Posture alignment
    if posture == "rest" and place["energy_cost"] < 0.2:
        score += 0.2
    if posture == "indoor" and cat in ("cafe", "restaurant", "rest"):
        score += 0.2
    if posture == "active" and place["energy_cost"] > 0.4:
        score += 0.1

    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class RouteIntelligenceEngine:
    """Assess context and return ordered route recommendations."""

    def __init__(self) -> None:
        self._builder = MapsDeepLinkBuilder()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess(
        self,
        query: str,
        hour: int,
        fatigue: float,
        weather_risk: float,
        tourist_density: float,
        current_location: str,
        preferences: dict,
    ) -> RouteIntelligenceState:
        posture = self._determine_posture(fatigue, weather_risk, hour)
        intents = _detect_intent(query)
        avoid_reasons: list[str] = []

        if fatigue > 0.7:
            avoid_reasons.append("Bạn đang mệt – tránh những điểm cần đi bộ nhiều.")
        if weather_risk > 0.6:
            avoid_reasons.append("Thời tiết xấu – hạn chế hoạt động ngoài trời.")
        if tourist_density > 0.7:
            avoid_reasons.append("Đông khách du lịch – nên chọn điểm ít người hơn.")

        # Score all places
        scored: list[tuple[float, dict]] = []
        for place in _PLACE_CATALOGUE:
            s = _score_place(
                place, hour, fatigue, weather_risk, tourist_density, intents, posture
            )
            scored.append((s, place))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_places = scored[:5]

        recommendations: list[RouteRecommendation] = []
        for score_val, place in top_places:
            link = self._make_link(place, current_location)
            reason = _build_reason(place, posture, hour)
            is_weather_ok = not (
                weather_risk > 0.6 and place.get("weather_sensitive", False)
            )
            rec = RouteRecommendation(
                destination=place["destination"],
                destination_vn=place["destination_vn"],
                reason=reason,
                map_link=link,
                energy_cost=place["energy_cost"],
                crowd_level=place["crowd_level"],
                best_window=place["best_window"],
                weather_suitable=is_weather_ok,
                confidence=round(score_val, 2),
            )
            recommendations.append(rec)

        top_pick = recommendations[0] if recommendations else None
        hint = self._generate_hint(posture, top_pick, hour, fatigue, weather_risk)

        return RouteIntelligenceState(
            recommendations=recommendations,
            top_pick=top_pick,
            avoid_reasons=avoid_reasons,
            posture=posture,
            hint=hint,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _determine_posture(
        self, fatigue: float, weather_risk: float, hour: int
    ) -> str:
        if fatigue > 0.7:
            return "rest"
        if weather_risk > 0.6:
            return "indoor"
        if 11 <= hour < 15:
            return "gentle"
        return "active"

    def _make_link(self, place: dict, current_location: str) -> MapDeepLink:
        coords = place.get("coords")
        query = place.get("query")
        if coords:
            return self._builder.navigate_to(coords)
        if query:
            return self._builder.search(query, near=current_location)
        return self._builder.search(place["destination"], near=current_location)

    def _generate_hint(
        self,
        posture: str,
        top_pick: RouteRecommendation | None,
        hour: int,
        fatigue: float,
        weather_risk: float,
    ) -> str:
        if top_pick is None:
            return "Không có gợi ý phù hợp lúc này."
        name = top_pick.destination_vn
        if posture == "rest":
            return f"Bạn nên nghỉ ngơi một chút. Gợi ý: {name}."
        if posture == "indoor":
            return f"Thời tiết không đẹp lắm – ghé {name} cho thoải mái nhé."
        if posture == "gentle":
            return f"Buổi trưa nắng, đi nhẹ nhàng thôi. {name} là lựa chọn ổn."
        if 6 <= hour < 10:
            return f"Buổi sáng đẹp! {name} đang chờ bạn khám phá."
        if 15 <= hour < 18:
            return f"Chiều mát rồi – {name} là điểm lý tưởng buổi chiều."
        if 18 <= hour < 22:
            return f"Buổi tối ở Phú Yên: {name} sẽ không làm bạn thất vọng."
        return f"Gợi ý hiện tại: {name}. Chúc bạn có trải nghiệm vui!"
