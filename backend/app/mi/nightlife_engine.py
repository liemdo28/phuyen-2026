"""
Mi Nightlife & Social Engine — Sunset-to-night orchestration.

Mi doesn't just list bars. She understands:
- when the group has energy for nightlife
- how to pair seafood + social drinking naturally
- sunset → golden hour → dinner → night flow
- emotional decompression after a long day
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.mi.location_db import PlaceProfile, PHU_YEN_PLACES, find_places


class NightPhase(str, Enum):
    GOLDEN_HOUR = "golden_hour"     # 16:30-18:30
    DINNER_TIME = "dinner_time"     # 18:30-20:30
    NIGHTLIFE = "nightlife"         # 20:30-23:00
    WIND_DOWN = "wind_down"         # 23:00+


class DrinkingIntent(str, Enum):
    NONE = "none"
    LIGHT = "light"         # 1-2 drinks, casual
    MODERATE = "moderate"   # social drinking
    FULL = "full"           # full nhậu session


@dataclass
class NightflowPlan:
    phase: NightPhase
    drinking_intent: DrinkingIntent
    has_social_energy: bool
    suggested_flow: list[str]       # sequence of places/activities
    places: list[PlaceProfile] = field(default_factory=list)
    mi_suggestion: str = ""
    buttons_hint: list[str] = field(default_factory=list)  # what buttons Mi should show


# ── Signal detection ──────────────────────────────────────────────────────────

_NIGHTLIFE_SIGNALS = [
    "nhậu", "bia", "làm vài lon", "quất vài",
    "quán nhậu", "đi bar", "đêm nay", "đi chơi tối",
    "party", "mồi ngon", "lai rai",
]

_SUNSET_SIGNALS = [
    "hoàng hôn", "sunset", "ngắm biển tối", "chiều tà",
    "ánh nắng chiều", "ráng đỏ",
]

_DINNER_SIGNALS = [
    "ăn tối", "tối ăn gì", "ăn gì tối nay",
    "đi ăn tối", "bữa tối", "nhà hàng tối",
]

_DECOMPRESSION_SIGNALS = [
    "xả hơi", "xả stress", "giải tỏa", "thở",
    "đi lang thang", "không biết làm gì", "buổi tối làm gì",
]

_DRINKING_LIGHT = ["bia", "1-2 lon", "lon bia", "uống chút"]
_DRINKING_FULL = ["nhậu", "quất", "làm vài lon", "làm đến sáng", "đêm dài"]


def detect_nightlife_intent(text: str) -> tuple[bool, DrinkingIntent]:
    """Returns (is_nightlife_intent, drinking_level)."""
    t = text.lower()
    if any(w in t for w in _NIGHTLIFE_SIGNALS):
        if any(w in t for w in _DRINKING_FULL):
            return True, DrinkingIntent.FULL
        if any(w in t for w in _DRINKING_LIGHT):
            return True, DrinkingIntent.LIGHT
        return True, DrinkingIntent.MODERATE
    return False, DrinkingIntent.NONE


def plan_night_flow(
    text: str,
    hour: int,
    social_energy_high: bool = True,
    has_child: bool = True,
) -> NightflowPlan | None:
    """
    Build Mi's sunset-to-night flow plan.
    Returns None if no nightlife intent detected.
    """
    t = text.lower()
    is_nightlife, drinking = detect_nightlife_intent(text)
    is_sunset = any(w in t for w in _SUNSET_SIGNALS)
    is_dinner = any(w in t for w in _DINNER_SIGNALS)
    is_decompression = any(w in t for w in _DECOMPRESSION_SIGNALS)

    if not (is_nightlife or is_sunset or is_dinner or is_decompression):
        return None

    # Determine phase
    if hour < 17:
        phase = NightPhase.GOLDEN_HOUR
    elif hour < 19:
        phase = NightPhase.DINNER_TIME
    elif hour < 23:
        phase = NightPhase.NIGHTLIFE
    else:
        phase = NightPhase.WIND_DOWN

    # Build flow
    if drinking == DrinkingIntent.FULL and social_energy_high:
        if has_child:
            # Can't do full nightlife with 4yo — redirect warmly
            flow = [
                "Ăn hải sản tươi tại Sông Cầu (family-friendly, có chỗ ngồi thoải mái)",
                "Sau khi bé ngủ: lai rai vài lon bia tại quán gần khách sạn",
            ]
            places = find_places(type="food", child_safe=True, max_results=2)
            mi_suggestion = (
                "Nhậu kiểu gia đình thì ghé Sông Cầu ăn hải sản tươi trước — "
                "bé ăn được, mồi ngon. Sau khi bé nghỉ tụi mình lai rai thêm nhé 😄"
            )
        else:
            flow = [
                "Sunset tại Bãi Xép hoặc Đầm Ô Loan",
                "Hải sản tươi Sông Cầu hoặc khu cảng cá",
                "Quán nhậu biển — bia hơi + mồi tươi",
            ]
            places = find_places(type="nightlife", max_results=2)
            mi_suggestion = (
                "Nhậu thì đi bài này: sunset Bãi Xép → hải sản Sông Cầu → "
                "quán nhậu biển lai rai. Tôm hùm + bia hơi = đêm Phú Yên đỉnh nhất 😄"
            )
    elif is_sunset:
        flow = [
            "Bãi Xép hoặc Đầm Ô Loan ngắm hoàng hôn (best 16:30-18:00)",
            "Cafe ven biển — ngồi nhìn ráng đỏ",
            "Ăn tối hải sản sau sunset",
        ]
        places = [p for p in PHU_YEN_PLACES if p.sunset_score >= 0.7][:2]
        mi_suggestion = (
            "Hoàng hôn đẹp nhất là Đầm Ô Loan — "
            "ánh nắng chiều phản chiếu trên mặt đầm rất đẹp. "
            "Ra khoảng 16h30, ngồi cafe ven bờ rồi ngắm 😊"
        )
    elif is_decompression:
        flow = [
            "Dạo phố đêm Tuy Hòa — không cần mục tiêu",
            "Bia hơi vỉa hè + hải sản nướng",
            "Về nghỉ sớm nếu mệt",
        ]
        places = find_places(type="food", max_results=2)
        mi_suggestion = (
            "Tối nay không cần plan nhiều đâu — dạo phố đêm Tuy Hòa, "
            "ngồi bia hơi vỉa hè, gió biển thổi là đủ xả hơi rồi. "
            "Không cần đi xa."
        )
    else:
        # Generic dinner
        flow = ["Hải sản tươi khu Sông Cầu hoặc cảng cá Tuy Hòa"]
        places = find_places(type="food", child_safe=has_child, max_results=2)
        mi_suggestion = (
            "Tối ăn hải sản đi — khu cảng cá Tuy Hòa tươi ngon, "
            "giá vừa phải. Hoặc lên Sông Cầu nếu muốn xịn hơn."
        )

    buttons = []
    if places:
        buttons.append("📍 Mở Maps")
    if drinking != DrinkingIntent.NONE:
        buttons.append("🍺 Quán nhậu gần đây")
    if is_sunset:
        buttons.append("🌅 Điểm sunset")
    buttons.append("🍜 Hải sản tươi")

    return NightflowPlan(
        phase=phase,
        drinking_intent=drinking,
        has_social_energy=social_energy_high,
        suggested_flow=flow,
        places=places,
        mi_suggestion=mi_suggestion,
        buttons_hint=buttons,
    )


def build_night_context(plan: NightflowPlan) -> str:
    """Build guidance string to inject into Mi's system prompt."""
    lines = [
        "## Night/Social Routing",
        f"Phase: {plan.phase.value} | Drinking: {plan.drinking_intent.value}",
        f"Flow: {' → '.join(plan.suggested_flow)}",
    ]
    if plan.places:
        lines.append("Suggested places: " + ", ".join(p.name_vi for p in plan.places))
    return "\n".join(lines)
