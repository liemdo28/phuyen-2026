"""
ChillContextResolver — context-aware disambiguation of "chill".

"Chill" and "kiếm chỗ chill" are among the most common travel requests
but mean completely different things depending on:
  - Time of day
  - Current emotional state
  - Social energy
  - Fatigue level
  - What was done before

Examples:
  9am + family tired       → AC indoor cafe, quiet corner, bé có chỗ ngồi
  3pm + couple excited     → beach cafe, sunset view, romantic
  5pm + group social mood  → rooftop bar or chill quán nhậu
  9pm + everyone exhausted → hotel lobby, room delivery
  Anytime + crowd averse   → hidden spot, < 10 people, no loud music

Design: returns a ChillRecommendation with enough context to inject
into the LLM prompt OR to produce a direct heuristic reply.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChillRecommendation:
    """Resolved chill type + rich context for the companion reply."""
    chill_type: str          # "cafe_quiet"|"cafe_view"|"beach_chill"|"nightlife"|"rest_indoor"|"recovery"
    label_vi: str            # Human-readable label
    reasoning: str           # Why this was chosen (for logging/debug)
    example_places: list[str]
    max_distance_km: float
    prompt_hint: str         # What to inject into LLM to guide response


# ── Known Phú Yên chill places by type ───────────────────────────────────────

_CHILL_PLACES: dict[str, list[str]] = {
    "cafe_quiet": [
        "Cafe trong Tuy Hòa (góc yên tĩnh, ít người)",
        "Quán cà phê nhỏ đường Trần Phú",
        "Cafe có khoảng sân sau, ít tiếng ồn",
    ],
    "cafe_view": [
        "Cafe Biển Bãi Xép — view biển, gió mát",
        "Phố cà phê Tuy Hòa — nhiều quán view biển",
        "Quán ven biển khu Bãi Bàng",
    ],
    "beach_chill": [
        "Bãi Xép — sóng nhỏ, nước trong, ít khách",
        "Bãi Bàng — yên tĩnh hơn Bãi Xép, ít người hơn",
        "Khu bãi phía bắc Tuy Hòa — ít đông",
    ],
    "nightlife": [
        "Khu quán nhậu hải sản gần cảng cá",
        "Phố đêm Tuy Hòa — đường Trần Hưng Đạo",
        "Quán bia hải sản Sông Cầu nếu còn sức chạy lên",
    ],
    "rest_indoor": [
        "Phòng khách sạn / nghỉ tại Sun Village",
        "Sảnh khách sạn — có điều hòa, yên tĩnh",
    ],
    "recovery": [
        "Quán cafe điều hòa gần khách sạn",
        "Sun Village hồ bơi — không di chuyển",
        "Phòng khách sạn — nghỉ ngơi hoàn toàn",
    ],
}

_PROMPT_HINTS: dict[str, str] = {
    "cafe_quiet": (
        "User muốn chill theo nghĩa yên tĩnh, ít người, low-noise. "
        "Gợi ý quán cafe ít đông, có chỗ ngồi thoải mái. Không gợi ý biển hay bar."
    ),
    "cafe_view": (
        "User muốn chill với view đẹp, không khí. "
        "Gợi ý quán cafe view biển, buổi chiều đẹp. "
        "Nhắc thêm ánh sáng buổi chiều / golden hour nếu phù hợp."
    ),
    "beach_chill": (
        "User muốn chill theo nghĩa ra biển ngồi, không nhất thiết tắm. "
        "Gợi ý bãi ít đông, buổi chiều mát, mang theo đồ uống là đủ."
    ),
    "nightlife": (
        "User muốn chill theo nghĩa socializing / nhậu nhẹ. "
        "Gợi ý quán hải sản hoặc khu phố đêm. "
        "Không gợi ý yên tĩnh."
    ),
    "rest_indoor": (
        "User không muốn đi đâu — chill là nghỉ ngơi. "
        "Gợi ý ở lại nơi hiện tại hoặc về khách sạn. "
        "Giữ reply rất ngắn, không cần nhiều options."
    ),
    "recovery": (
        "User cần recovery, không phải chill thư giãn. "
        "Gợi ý nghỉ ngơi hoàn toàn — hồ bơi khách sạn, phòng nghỉ, hoặc quán cafe gần nhất. "
        "Reply phải ngắn, không hỏi thêm, không liệt kê nhiều chỗ."
    ),
}


class ChillContextResolver:
    """
    Resolves what "chill" actually means given current context.

    Usage:
        resolver = ChillContextResolver()
        rec = resolver.resolve(
            hour=17, fatigue=0.3, social_mode="couple",
            crowd_tolerance="low", is_drinking=False,
        )
        # → ChillRecommendation(chill_type="cafe_view", ...)
    """

    def resolve(
        self,
        hour: int,
        fatigue: float,
        social_mode: str,            # "solo"|"couple"|"family"|"group"
        crowd_tolerance: str,        # "low"|"medium"|"high"
        is_drinking: bool = False,
        movement_tolerance: str = "medium",  # "high"|"medium"|"low"|"resistance"
        excitement: float = 0.0,
        text_hint: str = "",         # raw user text for keyword disambiguation
    ) -> ChillRecommendation:

        t = text_hint.lower()

        # Explicit nightlife signals override everything
        if is_drinking or any(w in t for w in ["nhậu", "bia", "bar", "quán nhậu", "đêm nay"]):
            return self._make("nightlife", "Chill kiểu nhậu nhẹ + hải sản", "nightlife_explicit", 15.0)

        # Extreme fatigue → recovery, not chill
        if fatigue >= 0.75 or movement_tolerance == "resistance":
            return self._make("recovery", "Nghỉ ngơi hoàn toàn", "fatigue_high", 0.5)

        # Late night → rest
        if hour >= 22 or hour <= 5:
            return self._make("rest_indoor", "Giờ này nghỉ là hợp nhất", "late_night", 0.5)

        # High excitement + social → beach or view
        if excitement >= 0.5 and social_mode in ("couple", "group") and 14 <= hour <= 19:
            if crowd_tolerance == "low":
                return self._make("beach_chill", "Chill biển, chỗ yên tĩnh", "excited_social_low_crowd", 10.0)
            return self._make("cafe_view", "Cafe view biển, buổi chiều", "excited_social_view", 8.0)

        # Golden hour (16:30–18:30) → cafe view or beach
        if 16 <= hour <= 18:
            if crowd_tolerance == "low":
                return self._make("beach_chill", "Chill biển trước hoàng hôn", "golden_hour_quiet", 8.0)
            return self._make("cafe_view", "Cafe view hoàng hôn", "golden_hour_view", 8.0)

        # Midday peak heat → indoor quiet cafe
        if 10 <= hour <= 14:
            return self._make("cafe_quiet", "Tránh nắng, cafe điều hòa", "midday_heat", 3.0)

        # Morning → quiet cafe with energy
        if 6 <= hour <= 10 and fatigue < 0.4:
            return self._make("cafe_view", "Cafe sáng, không khí biển", "morning_fresh", 5.0)

        # Low crowd tolerance → always quiet
        if crowd_tolerance == "low":
            return self._make("cafe_quiet", "Chỗ yên tĩnh, ít người", "crowd_averse", 3.0)

        # Family with child + moderate fatigue → indoor cafe with space for child
        if social_mode == "family" and fatigue >= 0.3:
            return self._make("cafe_quiet", "Cafe rộng, bé có chỗ ngồi thoải mái", "family_moderate_fatigue", 3.0)

        # Default: cafe view in afternoon, quiet in evening
        if hour >= 18:
            return self._make("cafe_quiet", "Cafe yên tĩnh buổi tối", "evening_default", 3.0)
        return self._make("cafe_view", "Cafe view dễ chịu", "default", 5.0)

    def _make(self, chill_type: str, label: str, reasoning: str, max_km: float) -> ChillRecommendation:
        return ChillRecommendation(
            chill_type=chill_type,
            label_vi=label,
            reasoning=reasoning,
            example_places=_CHILL_PLACES.get(chill_type, []),
            max_distance_km=max_km,
            prompt_hint=_PROMPT_HINTS.get(chill_type, ""),
        )

    def resolve_from_analysis(self, analysis, now: datetime | None = None) -> ChillRecommendation:
        """Convenience wrapper that takes a VietnameseMessageAnalysis object."""
        hour = (now or datetime.now()).hour
        return self.resolve(
            hour=hour,
            fatigue=analysis.fatigue,
            social_mode=analysis.group_type or "family",
            crowd_tolerance=analysis.crowd_tolerance or "medium",
            is_drinking=analysis.is_drinking,
            movement_tolerance=analysis.movement_tolerance or "medium",
            excitement=analysis.excitement,
            text_hint=analysis.raw_text if hasattr(analysis, "raw_text") else "",
        )
