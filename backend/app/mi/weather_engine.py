"""
Mi Weather Intelligence — Phú Yên tháng 5 weather patterns.

Mi understands weather as human experience:
- not "rain detected" → "kế hoạch biển hủy, vào trong đi"
- not "UV high" → "nắng gắt rồi, tránh ra ngoài buổi trưa"
- not "sea warning" → "biển hôm nay có sóng, bé không xuống được"
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class WeatherRisk(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WeatherState:
    rain: WeatherRisk = WeatherRisk.NONE
    heat: WeatherRisk = WeatherRisk.NONE
    sea_danger: WeatherRisk = WeatherRisk.NONE
    humidity: WeatherRisk = WeatherRisk.NONE
    wind: WeatherRisk = WeatherRisk.NONE
    uv: WeatherRisk = WeatherRisk.NONE

    # Derived
    outdoor_safe: bool = True
    beach_safe_for_child: bool = True
    indoor_recommended: bool = False
    recovery_boost_needed: bool = False

    # Mi's weather read
    mi_weather_note: str = ""
    redirect_suggestion: str = ""


# ── Text-based weather signal detection ───────────────────────────────────────

_RAIN_HEAVY = ["mưa như trút", "mưa to quá", "mưa bão", "bão rồi", "ngập rồi"]
_RAIN_MEDIUM = ["mưa rồi", "trời mưa", "mưa", "mưa nhẹ", "mưa phùn"]
_HEAT_CRITICAL = ["nóng muốn chết", "nóng vãi", "chảy mỡ rồi", "nóng chảy người"]
_HEAT_HIGH = ["nóng quá", "nắng gắt", "oi bức", "nóng", "nắng", "oi quá"]
_SEA_DANGER = ["sóng to", "biển động", "sóng lớn", "biển dữ", "không an toàn"]
_JELLYFISH = ["sứa", "có sứa", "sứa nhiều"]
_WIND = ["gió to", "gió mạnh", "gió lớn"]


def detect_weather_from_text(text: str) -> WeatherState:
    """Detect weather conditions from user message."""
    t = text.lower()
    state = WeatherState()

    if any(w in t for w in _RAIN_HEAVY):
        state.rain = WeatherRisk.HIGH
        state.outdoor_safe = False
        state.indoor_recommended = True
        state.mi_weather_note = "Mưa to rồi — hủy kế hoạch ngoài trời đi."
        state.redirect_suggestion = (
            "Mưa thì vào trong thôi — ghé Vincom Tuy Hòa cho bé chơi, "
            "hoặc tìm quán phở/cafe có mái ngồi chờ. Mưa Phú Yên thường tạnh sau 1-2h."
        )
    elif any(w in t for w in _RAIN_MEDIUM):
        state.rain = WeatherRisk.MEDIUM
        state.outdoor_safe = False
        state.indoor_recommended = True
        state.beach_safe_for_child = False
        state.mi_weather_note = "Đang mưa — biển tạm hoãn."
        state.redirect_suggestion = (
            "Mưa rồi thì tạm nghỉ biển, không vội. "
            "Ghé cafe trong thành phố ngồi chờ, hoặc dạo chợ Tuy Hòa cho mát. "
            "Mưa Phú Yên thường tạnh nhanh thôi."
        )

    if any(w in t for w in _HEAT_CRITICAL):
        state.heat = WeatherRisk.CRITICAL
        state.outdoor_safe = False
        state.indoor_recommended = True
        state.recovery_boost_needed = True
        state.mi_weather_note = "Nắng cực gắt — không ra ngoài giờ này."
        state.redirect_suggestion = (
            "Nóng quá rồi, đừng ra ngoài. "
            "Vào cafe máy lạnh, hồ bơi khách sạn, hoặc nằm nghỉ — "
            "chiều mát từ 15h sẽ ra tiếp thôi."
        )
    elif any(w in t for w in _HEAT_HIGH):
        state.heat = WeatherRisk.HIGH
        state.uv = WeatherRisk.HIGH
        state.recovery_boost_needed = True
        state.mi_weather_note = "Nắng gắt, UV cao."
        state.redirect_suggestion = (
            "Nắng gắt thì tránh ra ngoài buổi trưa. "
            "Kem chống nắng SPF50+, áo dài tay cho cả bé. "
            "Chiều sau 15h mát hơn nhiều."
        )

    if any(w in t for w in _SEA_DANGER):
        state.sea_danger = WeatherRisk.HIGH
        state.beach_safe_for_child = False
        state.mi_weather_note = "Biển có sóng lớn — bé không xuống được."
        state.redirect_suggestion = (
            "Biển hôm nay sóng to — không cho bé xuống nước nhé. "
            "Bãi Xép thường an toàn hơn các bãi hở, nhưng vẫn cần kiểm tra tại chỗ. "
            "Ngắm từ bờ hoặc đổi sang hoạt động trong."
        )

    if any(w in t for w in _JELLYFISH):
        state.sea_danger = WeatherRisk.MEDIUM
        state.beach_safe_for_child = False
        state.mi_weather_note = "Có sứa — kiểm tra trước khi bé xuống."
        state.redirect_suggestion = (
            "Tháng 5 thỉnh thoảng có sứa. "
            "Kiểm tra mặt nước 5 phút trước khi bé xuống — "
            "tránh khu có sứa nhỏ trong suốt. Bãi Xép ít sứa hơn các bãi khác."
        )

    if any(w in t for w in _WIND):
        state.wind = WeatherRisk.MEDIUM

    return state


def get_time_based_weather_warning(hour: int) -> str | None:
    """
    Return a proactive weather note based on time of day.
    Phú Yên May patterns: hot midday, possible afternoon showers, calm evenings.
    """
    if 10 <= hour <= 14:
        return "Giờ này nắng gắt nhất — UV rất cao, nên ở trong hoặc có mái che."
    if 14 <= hour <= 16:
        return "Chiều tháng 5 Phú Yên hay có mưa bất chợt — mang theo áo mưa nhỏ nếu đi xa."
    if hour >= 18:
        return None  # Evening usually fine
    return None


@dataclass
class WeatherRoutingResult:
    """What Mi recommends based on weather."""
    should_redirect: bool
    redirect_message: str
    indoor_alternatives: list[str]
    safe_outdoor: list[str]


def route_around_weather(state: WeatherState, has_child: bool = True) -> WeatherRoutingResult:
    """Build Mi's routing recommendation around weather conditions."""
    indoor_alternatives = [
        "Cafe có mái/máy lạnh trong trung tâm Tuy Hòa",
        "Vincom Tuy Hòa (có điều hòa, cho bé chơi)" if has_child else "Quán ăn trong trung tâm",
        "Nghỉ tại khách sạn, hồ bơi",
    ]
    safe_outdoor = [
        "Bãi Xép buổi sáng sớm (trước 9h) hoặc chiều mát (sau 15h)",
        "Đầm Ô Loan kayak sáng sớm",
        "Chợ Tuy Hòa có mái che",
    ]

    should_redirect = state.indoor_recommended or state.rain in (WeatherRisk.MEDIUM, WeatherRisk.HIGH)

    return WeatherRoutingResult(
        should_redirect=should_redirect,
        redirect_message=state.redirect_suggestion or "",
        indoor_alternatives=indoor_alternatives,
        safe_outdoor=safe_outdoor,
    )
