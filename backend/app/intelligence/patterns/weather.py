"""
Vietnamese Weather & Environment Intelligence Database

Covers:
- Hot weather expressions (with sarcasm scaling)
- Rain patterns
- Wind / sea conditions
- Beautiful weather (positive triggers)
- Seasonal context for Phú Yên
"""
from __future__ import annotations

# ── Hot Weather Detection ──────────────────────────────────────────────────────
HOT_MARKERS: list[tuple[str, float]] = [
    # Extreme / sarcastic
    ("nóng muốn chết", 1.0),
    ("nóng chảy mỡ", 1.0),
    ("nóng vãi", 0.9),
    ("nóng cực kỳ", 0.9),
    ("nóng kinh khủng", 0.9),
    ("oi bức", 0.85),
    ("oi bức khó chịu", 0.9),
    # High signal
    ("nóng gắt", 0.8),
    ("nắng gắt", 0.8),
    ("nóng quá", 0.75),
    ("nắng quá", 0.75),
    ("nóng lắm", 0.7),
    ("oi quá", 0.7),
    ("ngột ngạt", 0.7),
    ("bức bối", 0.65),
    # Medium signal
    ("nóng", 0.5),
    ("nắng", 0.45),
    ("oi", 0.4),
    ("trời nóng", 0.55),
    ("trời nắng", 0.5),
    ("nắng chói", 0.6),
    ("nắng to", 0.6),
    ("38 độ", 0.8),
    ("39 độ", 0.85),
    ("40 độ", 0.9),
]

# ── Rain Detection ─────────────────────────────────────────────────────────────
RAIN_MARKERS: list[tuple[str, float]] = [
    # Extreme
    ("mưa như trút nước", 1.0),
    ("mưa to kinh khủng", 0.9),
    ("mưa vãi", 0.9),
    ("lũ rồi", 0.95),
    ("ngập rồi", 0.85),
    # High signal
    ("mưa to", 0.8),
    ("mưa lớn", 0.8),
    ("mưa dữ", 0.8),
    ("đang mưa", 0.7),
    ("mưa rồi", 0.7),
    ("mưa liên tục", 0.75),
    ("mưa cả ngày", 0.75),
    # Medium signal
    ("mưa", 0.5),
    ("trời mưa", 0.55),
    ("có mưa", 0.55),
    ("mưa nhẹ", 0.45),
    ("lắc rắc", 0.35),
    ("âm u", 0.4),
    ("trời xám", 0.4),
    ("mây đen", 0.5),
    ("sắp mưa", 0.55),
    ("có thể mưa", 0.45),
]

# ── Wind / Sea Conditions ─────────────────────────────────────────────────────
WIND_MARKERS: list[tuple[str, float]] = [
    ("gió to", 0.75),
    ("gió mạnh", 0.75),
    ("gió dữ", 0.8),
    ("bão", 0.95),
    ("bão đổ bộ", 1.0),
    ("áp thấp nhiệt đới", 0.9),
    ("gió", 0.35),
    ("có gió", 0.4),
    ("gió nhẹ", 0.25),
]

SEA_CONDITION_MARKERS: list[tuple[str, float]] = [
    ("sóng to", 0.8),
    ("sóng lớn", 0.8),
    ("biển động", 0.85),
    ("biển động dữ", 0.9),
    ("không tắm được", 0.75),
    ("cấm tắm biển", 0.95),
    ("biển xấu", 0.75),
    ("sóng mạnh", 0.75),
    ("nguy hiểm", 0.8),
    ("cảnh báo sóng", 0.9),
]

# ── Beautiful Weather (positive triggers) ─────────────────────────────────────
GOOD_WEATHER_MARKERS: list[tuple[str, float]] = [
    ("trời đẹp quá", 0.9),
    ("trời đẹp lắm", 0.85),
    ("đẹp thời tiết", 0.8),
    ("trời trong", 0.75),
    ("nắng nhẹ", 0.7),
    ("nắng đẹp", 0.8),
    ("mát mẻ", 0.75),
    ("trời mát", 0.7),
    ("thời tiết đẹp", 0.8),
    ("bầu trời đẹp", 0.75),
    ("không khí trong lành", 0.7),
    ("trời trong xanh", 0.8),
    ("nắng vừa đủ", 0.7),
    ("trời đẹp", 0.65),
    ("đẹp", 0.2),  # weak signal alone
]

# ── Seasonal Context for Phú Yên ─────────────────────────────────────────────
# May is typically hot and sunny in Phú Yên (dry season)
PHU_YEN_MAY_CONTEXT = {
    "season": "khô",
    "avg_temp_c": 30,
    "rain_risk": "thấp",
    "sea_condition": "tốt",
    "notes": [
        "Tháng 5 Phú Yên ít mưa, trời nắng đẹp",
        "Nhiệt độ trung bình 30-35°C, có thể nóng gắt buổi trưa",
        "Biển yên, phù hợp tắm biển và lặn",
        "Tránh ra ngoài 11h-14h vì nắng gắt",
        "Buổi sáng sớm và chiều mát là thời điểm đẹp nhất",
    ],
    "best_times": ["06:00-09:00", "16:00-18:30"],
    "avoid_times": ["11:00-14:00"],
}


def score_heat(text: str) -> float:
    """Score heat level 0.0–1.0."""
    score = 0.0
    for pattern, weight in HOT_MARKERS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_rain(text: str) -> float:
    """Score rain severity 0.0–1.0."""
    score = 0.0
    for pattern, weight in RAIN_MARKERS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_wind(text: str) -> float:
    """Score wind severity 0.0–1.0."""
    score = 0.0
    for pattern, weight in WIND_MARKERS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_sea_danger(text: str) -> float:
    """Score sea danger level 0.0–1.0."""
    score = 0.0
    for pattern, weight in SEA_CONDITION_MARKERS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_good_weather(text: str) -> float:
    """Score beautiful/nice weather 0.0–1.0."""
    score = 0.0
    for pattern, weight in GOOD_WEATHER_MARKERS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def get_weather_action(heat: float, rain: float, sea_danger: float) -> str:
    """
    Returns recommended AI action based on weather signals.
    """
    if rain >= 0.7:
        return "redirect_indoor"
    if sea_danger >= 0.7:
        return "avoid_beach"
    if heat >= 0.8:
        return "suggest_cool_indoor"
    if heat >= 0.5:
        return "warn_heat_midday"
    return "proceed_normal"
