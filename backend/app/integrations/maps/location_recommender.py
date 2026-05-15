"""Curated location recommender for Phú Yên travel companion."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.maps.deep_link_builder import MapDeepLink, MapsDeepLinkBuilder

# ---------------------------------------------------------------------------
# Curated location data
# ---------------------------------------------------------------------------

_LOCATIONS: list[dict] = [
    # --- Beaches ---
    {
        "name": "Bãi Xép",
        "name_vn": "Bãi Xép",
        "category": "beach",
        "distance_note": "~15 phút từ trung tâm Tuy Hòa",
        "vibe": "yên tĩnh",
        "energy_cost": 0.4,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (6, 12),
        "afternoon_ok": True,
        "weather_sensitive": True,
        "tags": ["biển", "yên tĩnh", "an toàn", "local"],
        "query": "Bãi Xép Phú Yên",
        "why_now_morning": "Buổi sáng nước trong, ít người – tắm biển rất thư giãn.",
        "why_now_afternoon": "Chiều mát gió, bãi biển yên tĩnh rất lý tưởng.",
        "why_now_default": "Bãi Xép luôn yên tĩnh và an toàn cho du khách.",
    },
    {
        "name": "Bãi biển Tuy Hòa",
        "name_vn": "Bãi biển Tuy Hòa",
        "category": "beach",
        "distance_note": "ngay trung tâm thành phố",
        "vibe": "local",
        "energy_cost": 0.3,
        "crowd_pref": ["lively", "any"],
        "best_hours": (6, 12),
        "afternoon_ok": True,
        "weather_sensitive": True,
        "tags": ["biển", "trung tâm", "tiện lợi", "đông vui"],
        "query": "bãi biển Tuy Hòa",
        "why_now_morning": "Biển sáng sớm rất đẹp, gần khách sạn, tiện di chuyển.",
        "why_now_afternoon": "Chiều về biển tắm mát, sau đó dạo phố tối luôn.",
        "why_now_default": "Bãi biển tiện nhất nếu bạn đang ở trung tâm Tuy Hòa.",
    },
    {
        "name": "Vịnh Hòa",
        "name_vn": "Vịnh Hòa",
        "category": "beach",
        "distance_note": "~45 phút từ Tuy Hòa",
        "vibe": "hoang sơ",
        "energy_cost": 0.5,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (7, 12),
        "afternoon_ok": True,
        "weather_sensitive": True,
        "tags": ["biển", "xa xôi", "hoang sơ", "view đẹp"],
        "query": "Vịnh Hòa Phú Yên",
        "why_now_morning": "Vịnh Hòa xa nhưng xứng đáng – cảnh đẹp hoang sơ ít người.",
        "why_now_afternoon": "Chiều tà Vịnh Hòa rất thơ, nhớ đi sớm để về kịp.",
        "why_now_default": "Vịnh Hòa lý tưởng cho ai muốn khám phá thiên nhiên nguyên sơ.",
    },
    {
        "name": "Hòn Yến",
        "name_vn": "Hòn Yến",
        "category": "beach",
        "distance_note": "~30 phút từ Tuy Hòa",
        "vibe": "view đẹp",
        "energy_cost": 0.6,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (7, 11),
        "afternoon_ok": False,
        "weather_sensitive": True,
        "tags": ["biển", "lặn ngắm san hô", "đảo", "view đẹp"],
        "query": "Hòn Yến Phú Yên",
        "why_now_morning": "Hòn Yến đẹp nhất sáng sớm, nước trong xanh và san hô rực rỡ.",
        "why_now_afternoon": "Buổi chiều Hòn Yến bắt đầu có sóng, nên về trước 14h.",
        "why_now_default": "Hòn Yến là điểm lặn biển đẹp bậc nhất Phú Yên.",
    },
    # --- Cafes ---
    {
        "name": "Cà phê view biển Tuy Hòa",
        "name_vn": "Cà phê view biển",
        "category": "cafe",
        "distance_note": "~5 phút từ trung tâm",
        "vibe": "view đẹp",
        "energy_cost": 0.1,
        "crowd_pref": ["lively", "any"],
        "best_hours": (7, 22),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "tags": ["cafe", "view biển", "thư giãn"],
        "query": "cafe view biển Tuy Hòa",
        "why_now_morning": "Cà phê sáng nhìn ra biển – khởi đầu ngày mới tuyệt vời.",
        "why_now_afternoon": "Ngồi cafe buổi chiều nhâm nhi, ngắm biển vàng hươm.",
        "why_now_default": "Góc cafe view biển tuyệt vời để thư giãn bất cứ lúc nào.",
    },
    {
        "name": "Cà phê sáng local Tuy Hòa",
        "name_vn": "Cà phê sáng local",
        "category": "cafe",
        "distance_note": "trong khu phố trung tâm",
        "vibe": "local",
        "energy_cost": 0.05,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (6, 10),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "tags": ["cafe", "sáng sớm", "local", "giá rẻ"],
        "query": "cà phê sáng Tuy Hòa",
        "why_now_morning": "Cà phê sáng kiểu local, ngồi vỉa hè – trải nghiệm thật sự Tuy Hòa.",
        "why_now_afternoon": "Quán sáng có thể đã đóng cửa, thử tìm quán khác nhé.",
        "why_now_default": "Cà phê sáng sớm theo kiểu người địa phương – rất thú vị.",
    },
    {
        "name": "Cà phê chiều Tuy Hòa",
        "name_vn": "Cà phê chiều",
        "category": "cafe",
        "distance_note": "~10 phút từ trung tâm",
        "vibe": "yên tĩnh",
        "energy_cost": 0.1,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (14, 21),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "tags": ["cafe", "buổi chiều", "yên tĩnh", "sách"],
        "query": "cà phê chiều Tuy Hòa",
        "why_now_morning": "Quán này mở muộn, buổi chiều tối mới có không khí nhất.",
        "why_now_afternoon": "Buổi chiều ngồi cafe yên tĩnh, sạc pin cho chuyến khám phá tối.",
        "why_now_default": "Quán cà phê mang không khí thư thái, phù hợp để nghỉ ngơi.",
    },
    # --- Restaurants ---
    {
        "name": "Nhà hàng hải sản Tuy Hòa",
        "name_vn": "Nhà hàng hải sản Tuy Hòa",
        "category": "restaurant",
        "distance_note": "khu hải sản gần biển",
        "vibe": "đông vui",
        "energy_cost": 0.1,
        "crowd_pref": ["lively", "any"],
        "best_hours": (11, 20),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "tags": ["ăn", "hải sản", "ngon", "đặc sản"],
        "query": "nhà hàng hải sản Tuy Hòa",
        "why_now_morning": "Buổi trưa ăn hải sản tươi ngon nhất – vừa bắt lên từ biển.",
        "why_now_afternoon": "Buổi chiều tối ăn hải sản Tuy Hòa, giá phải chăng tươi ngon.",
        "why_now_default": "Hải sản Tuy Hòa nổi tiếng tươi và rẻ, không thể bỏ qua.",
    },
    {
        "name": "Bún cá Tuy Hòa",
        "name_vn": "Bún cá sáng Tuy Hòa",
        "category": "restaurant",
        "distance_note": "khu chợ trung tâm",
        "vibe": "local",
        "energy_cost": 0.1,
        "crowd_pref": ["lively", "any"],
        "best_hours": (6, 10),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "tags": ["ăn", "sáng", "đặc sản", "local", "rẻ"],
        "query": "bún cá Tuy Hòa sáng",
        "why_now_morning": "Bún cá Tuy Hòa buổi sáng – đặc sản không thể bỏ, chỉ bán đến 10h!",
        "why_now_afternoon": "Bún cá sáng đã hết rồi, thử hải sản buổi trưa nhé.",
        "why_now_default": "Bún cá là đặc sản sáng sớm của Tuy Hòa, rất được yêu thích.",
    },
    {
        "name": "Phố đêm Trần Phú",
        "name_vn": "Phố đêm Trần Phú",
        "category": "restaurant",
        "distance_note": "trung tâm thành phố",
        "vibe": "đông vui",
        "energy_cost": 0.2,
        "crowd_pref": ["lively", "any"],
        "best_hours": (18, 23),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "tags": ["ăn", "phố đêm", "đêm", "đông vui", "bia hơi"],
        "query": "phố đêm Trần Phú Tuy Hòa",
        "why_now_morning": "Phố đêm Trần Phú chỉ sôi động sau 18h, đêm nay nhớ ghé.",
        "why_now_afternoon": "Tối nay ghé Trần Phú ăn tối – chợ đêm vừa mở là đông vui nhất.",
        "why_now_default": "Trần Phú về đêm là điểm ăn uống sầm uất nhất Tuy Hòa.",
    },
    # --- Rest spots ---
    {
        "name": "Hồ bơi khách sạn",
        "name_vn": "Hồ bơi khách sạn Tuy Hòa",
        "category": "rest",
        "distance_note": "tại khách sạn bạn đang ở",
        "vibe": "yên tĩnh",
        "energy_cost": 0.05,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (11, 16),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "tags": ["nghỉ", "thư giãn", "khách sạn", "hồ bơi"],
        "query": "khách sạn hồ bơi Tuy Hòa",
        "why_now_morning": "Buổi trưa hồ bơi mát – nghỉ ngơi lấy lại sức cho chiều.",
        "why_now_afternoon": "Ngâm mình hồ bơi buổi chiều – cách tốt nhất để thư giãn.",
        "why_now_default": "Hồ bơi khách sạn – nghỉ tại chỗ, lấy lại năng lượng.",
    },
    {
        "name": "Công viên trung tâm",
        "name_vn": "Công viên trung tâm Tuy Hòa",
        "category": "rest",
        "distance_note": "~5 phút đi bộ từ trung tâm",
        "vibe": "yên tĩnh",
        "energy_cost": 0.1,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (6, 19),
        "afternoon_ok": True,
        "weather_sensitive": False,
        "tags": ["nghỉ", "bóng mát", "công viên", "đi bộ"],
        "query": "công viên Tuy Hòa",
        "why_now_morning": "Công viên sáng sớm – không khí trong lành, đi dạo nhẹ nhàng.",
        "why_now_afternoon": "Tìm bóng mát nghỉ ngơi ở công viên, tránh nắng giữa trưa.",
        "why_now_default": "Công viên yên tĩnh, bóng mát, phù hợp nghỉ ngơi giữa ngày.",
    },
    # --- Attractions ---
    {
        "name": "Gành Đá Đĩa",
        "name_vn": "Gành Đá Đĩa",
        "category": "attraction",
        "distance_note": "~45 phút từ Tuy Hòa",
        "vibe": "view đẹp",
        "energy_cost": 0.5,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (6, 9),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "tags": ["thiên nhiên", "đá basalt", "sáng sớm", "check-in"],
        "query": "Gành Đá Đĩa Phú Yên",
        "why_now_morning": "Gành Đá Đĩa buổi sáng sớm: ánh nắng vàng chiếu vào đá – tuyệt đẹp!",
        "why_now_afternoon": "Buổi chiều tối Gành Đá Đĩa vẫn đẹp nhưng nắng chói.",
        "why_now_default": "Gành Đá Đĩa – kiệt tác thiên nhiên của Phú Yên, must-see!",
    },
    {
        "name": "Mũi Điện",
        "name_vn": "Mũi Điện – Cực Đông",
        "category": "attraction",
        "distance_note": "~1.5h từ Tuy Hòa",
        "vibe": "view đẹp",
        "energy_cost": 0.7,
        "crowd_pref": ["quiet", "any"],
        "best_hours": (4, 7),
        "afternoon_ok": False,
        "weather_sensitive": False,
        "tags": ["bình minh", "cực đông", "leo núi", "view đẹp"],
        "query": "Mũi Điện Phú Yên bình minh",
        "why_now_morning": "Mũi Điện bình minh đầu tiên của Việt Nam – trải nghiệm khó quên!",
        "why_now_afternoon": "Mũi Điện đẹp nhất lúc bình minh, chiều tối không có giá trị nhiều.",
        "why_now_default": "Mũi Điện – điểm cực đông nơi đón bình minh đầu tiên cả nước.",
    },
]

# ---------------------------------------------------------------------------
# Intent → category mapping
# ---------------------------------------------------------------------------

_INTENT_CATEGORY: dict[str, list[str]] = {
    "ăn": ["restaurant"],
    "hải sản": ["restaurant"],
    "cơm": ["restaurant"],
    "bún": ["restaurant"],
    "phở": ["restaurant"],
    "biển": ["beach"],
    "tắm biển": ["beach"],
    "bãi biển": ["beach"],
    "cafe": ["cafe"],
    "cà phê": ["cafe"],
    "uống": ["cafe"],
    "trà": ["cafe"],
    "nghỉ": ["rest"],
    "mệt": ["rest"],
    "thư giãn": ["rest"],
    "view": ["attraction", "beach"],
    "ngắm": ["attraction", "beach"],
    "hoàng hôn": ["attraction", "beach"],
    "bình minh": ["attraction"],
    "check-in": ["attraction", "beach"],
    "tham quan": ["attraction"],
    "lặn": ["beach"],
    "snorkeling": ["beach"],
}

_POSTURE_LABELS = {
    "rest": "Bạn cần nghỉ ngơi",
    "indoor": "Nên ở trong nhà",
    "gentle": "Hoạt động nhẹ nhàng",
    "active": "Sẵn sàng khám phá",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class LocationSuggestion:
    name: str
    name_vn: str
    category: str       # beach | cafe | restaurant | attraction | market | rest
    distance_note: str
    vibe: str
    why_now: str
    map_link: MapDeepLink
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Recommender
# ---------------------------------------------------------------------------


class LocationRecommender:
    """Return top-3 curated Phú Yên location suggestions based on context."""

    def __init__(self) -> None:
        self._builder = MapsDeepLinkBuilder()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(
        self,
        intent: str,
        hour: int,
        fatigue: float,
        weather_risk: float,
        crowd_preference: str,  # "quiet" | "lively" | "any"
        current_city: str,
    ) -> list[LocationSuggestion]:
        """Return up to 3 best-fit location suggestions."""
        # Determine target categories from intent
        target_cats: set[str] = set()
        intent_lower = intent.lower()
        for keyword, cats in _INTENT_CATEGORY.items():
            if keyword in intent_lower:
                target_cats.update(cats)

        scored: list[tuple[float, dict]] = []
        for loc in _LOCATIONS:
            s = self._score(loc, hour, fatigue, weather_risk, crowd_preference, target_cats)
            scored.append((s, loc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[LocationSuggestion] = []
        for _, loc in scored[:3]:
            link = self._builder.search(loc["query"], near=current_city)
            why = self._why_now(loc, hour)
            results.append(
                LocationSuggestion(
                    name=loc["name"],
                    name_vn=loc["name_vn"],
                    category=loc["category"],
                    distance_note=loc["distance_note"],
                    vibe=loc["vibe"],
                    why_now=why,
                    map_link=link,
                    tags=list(loc["tags"]),
                )
            )
        return results

    def format_reply(self, suggestions: list[LocationSuggestion], posture: str) -> str:
        """Return a Vietnamese natural language reply with suggestions and map links."""
        if not suggestions:
            return "Mình chưa tìm được gợi ý phù hợp lúc này. Bạn thử hỏi lại nhé!"

        posture_intro = _POSTURE_LABELS.get(posture, "Gợi ý cho bạn")
        lines: list[str] = [f"📍 {posture_intro} – đây là gợi ý của mình:\n"]

        for i, s in enumerate(suggestions, start=1):
            lines.append(f"{i}. *{s.name_vn}* ({s.distance_note})")
            lines.append(f"   ➡ {s.why_now}")
            lines.append(f"   🗺 {s.map_link.url}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score(
        self,
        loc: dict,
        hour: int,
        fatigue: float,
        weather_risk: float,
        crowd_preference: str,
        target_cats: set[str],
    ) -> float:
        score = 0.5
        cat = loc["category"]
        low_h, high_h = loc["best_hours"]

        # Category / intent match
        if target_cats and cat in target_cats:
            score += 0.35

        # Time fit
        if low_h <= hour < high_h:
            score += 0.2
        elif cat == "beach" and 15 <= hour < 18 and loc.get("afternoon_ok"):
            score += 0.1

        # Fatigue
        if fatigue > 0.7:
            score -= loc["energy_cost"] * 0.5
            if loc["energy_cost"] < 0.15:
                score += 0.2

        # Weather
        if weather_risk > 0.6 and loc.get("weather_sensitive"):
            score -= 0.4
        if weather_risk > 0.6 and cat in ("cafe", "restaurant", "rest"):
            score += 0.15

        # Crowd preference
        if crowd_preference == "quiet" and loc["vibe"] in ("yên tĩnh", "hoang sơ"):
            score += 0.1
        if crowd_preference == "lively" and loc["vibe"] == "đông vui":
            score += 0.1

        return max(0.0, min(1.0, score))

    def _why_now(self, loc: dict, hour: int) -> str:
        if 6 <= hour < 11:
            return loc.get("why_now_morning", loc["why_now_default"])
        if 11 <= hour < 15:
            return loc.get("why_now_afternoon", loc["why_now_default"])
        if 15 <= hour < 19:
            return loc.get("why_now_afternoon", loc["why_now_default"])
        return loc.get("why_now_default", "Lựa chọn phù hợp với thời điểm hiện tại.")
