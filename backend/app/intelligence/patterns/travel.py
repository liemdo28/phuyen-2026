"""
Vietnamese Travel Behavior Intelligence Database

Covers:
- Travel intent classification
- Activity preferences (beach, attraction, food tour, relaxation)
- Time-aware travel patterns
- Weather-affected travel decisions
- Nightlife routing
- Recovery/healing trip patterns
- Photo/content creation intent
- Budget travel patterns
"""
from __future__ import annotations

# ── Travel Intent Classification ──────────────────────────────────────────────
BEACH_INTENT: list[str] = [
    "ra biển", "đi biển", "tắm biển", "biển",
    "bãi biển", "ngắm biển", "nhìn ra biển",
    "bơi", "bơi lội", "lặn", "snorkeling",
    "chơi cát", "cát biển", "sóng biển",
    "bình minh biển", "hoàng hôn biển",
    "đi biển sáng", "đi biển chiều",
    "biển vắng", "biển đẹp",
    "bãi xép", "hòn yến", "mũi điện", "bãi tuy hòa",
]

ATTRACTION_INTENT: list[str] = [
    "tham quan", "khám phá", "du lịch",
    "di tích", "lịch sử", "văn hóa",
    "gành đá đĩa", "tháp nhạn", "mũi điện",
    "đầm ô loan", "hòn yến", "đảo",
    "ngắm cảnh", "xem phong cảnh", "view",
    "check-in", "chụp ảnh", "sống ảo",
    "cảnh đẹp", "địa điểm đẹp",
    "địa điểm nổi tiếng", "must visit",
]

RELAXATION_INTENT: list[str] = [
    "thư giãn", "nghỉ ngơi", "nằm nghỉ",
    "chill", "relax", "thả lỏng",
    "không làm gì", "ngồi ngắm",
    "thoải mái", "không vội",
    "healing", "me time", "tự do",
    "không có kế hoạch", "tùy hứng",
    "đi đâu cũng được", "không quan trọng",
    "ngồi cafe", "ngồi nhìn biển",
]

FOOD_TOUR_INTENT: list[str] = [
    "tour ẩm thực", "food tour", "ăn gì ngon",
    "thử đồ ăn", "ăn thử", "đặc sản",
    "ẩm thực địa phương", "ăn gì ở phú yên",
    "phải thử cái gì", "must eat", "must try",
    "đặc sản phú yên", "món ngon", "quán ngon",
    "ăn tất cả", "ăn nhiều thứ", "thực đơn",
    "food crawl", "ăn khám phá",
]

NIGHTLIFE_INTENT: list[str] = [
    "đêm nay đi đâu", "tối nay làm gì",
    "đi bar", "đi pub", "đi club", "nightlife",
    "đêm tuy hòa", "đi nhậu", "quán nhậu",
    "nhậu đêm", "bia đêm", "rượu đêm",
    "quán mở khuya", "quán về đêm",
    "karaoke", "hát hò", "đêm vui",
    "âm nhạc live", "live music",
    "cocktail bar", "rooftop bar",
]

SHOPPING_INTENT: list[str] = [
    "mua sắm", "shopping", "chợ", "đặc sản mua",
    "mua đặc sản", "quà", "quà về", "đặc sản về",
    "mua cho", "mua tặng",
    "chợ tuy hòa", "siêu thị",
    "cá khô", "mực khô", "khô bò", "tôm khô",
    "đặc sản mang về", "mua về làm quà",
]

PHOTOGRAPHY_INTENT: list[str] = [
    "chụp ảnh", "chụp hình", "chụp",
    "sống ảo", "check-in", "instagram",
    "view đẹp", "cảnh đẹp", "chụp cảnh",
    "golden hour", "giờ vàng", "ánh sáng đẹp",
    "bình minh", "hoàng hôn", "sunrise", "sunset",
    "phong cảnh", "landscape",
    "chụp biển", "chụp núi", "chụp đồng quê",
    "filter", "lightroom", "edit ảnh",
]

# ── Time-Aware Travel Patterns ─────────────────────────────────────────────────
MORNING_TRAVEL: list[str] = [
    "sáng sớm", "buổi sáng", "đi sáng",
    "trước 9 giờ", "trước 10 giờ",
    "bình minh", "sunrise",
    "sáng mát", "trời mát sáng",
    "tránh nắng", "chưa nóng",
]

MIDDAY_AVOIDANCE: list[str] = [
    "nắng quá", "nóng quá trưa", "tránh trưa",
    "không ra ngoài giờ trưa", "nghỉ trưa",
    "trời nóng gắt", "nắng gắt",
    "vào trong lúc trưa", "tránh nắng trưa",
]

GOLDEN_HOUR_TRAVEL: list[str] = [
    "hoàng hôn", "sunset", "chiều tà",
    "3-5 giờ chiều", "4 giờ chiều", "5 giờ chiều",
    "ánh sáng đẹp buổi chiều", "golden hour",
    "ngắm hoàng hôn", "xem mặt trời lặn",
    "chiều đẹp", "buổi chiều mát",
]

NIGHT_TRAVEL: list[str] = [
    "buổi tối", "đêm", "tối nay",
    "sau 7 giờ", "sau 8 giờ", "sau 9 giờ",
    "đêm tối", "về đêm",
    "ánh đèn đêm", "đêm thành phố",
]

# ── Weather-Travel Decision Matrix ────────────────────────────────────────────
HOT_WEATHER_ALTERNATIVES: dict[str, list[str]] = {
    "avoid": ["bãi biển buổi trưa", "di chuyển xa"],
    "suggest": ["quán cafe máy lạnh", "bảo tàng", "trung tâm thương mại",
                "nghỉ khách sạn", "hồ bơi", "ăn kem", "sinh tố"],
}

RAIN_ALTERNATIVES: dict[str, list[str]] = {
    "avoid": ["biển", "gành đá đĩa", "mũi điện", "leo núi"],
    "suggest": ["quán cafe", "nhà hàng", "bảo tàng", "chợ có mái che",
                "xem phim", "mua sắm trong nhà"],
}

WIND_WAVE_ALTERNATIVES: dict[str, list[str]] = {
    "avoid": ["tắm biển", "kayak", "lặn biển", "đảo"],
    "suggest": ["biển ngắm cảnh", "đầm ô loan", "thị trấn", "cafe biển"],
}

# ── Movement Cost Estimation ──────────────────────────────────────────────────
# How far is "too far" for each energy level
DISTANCE_TOLERANCE: dict[str, int] = {
    "high_energy": 50,    # km - willing to drive 50km
    "medium_energy": 20,  # km
    "low_energy": 5,      # km
    "fatigue": 2,         # km - only very nearby
}

# ── Phú Yên Specific Local Knowledge ─────────────────────────────────────────
PHU_YEN_TIMING_RULES: list[dict] = [
    {
        "place": "Gành Đá Đĩa",
        "best_time": "06:00-09:00",
        "avoid_time": "10:00-15:00",
        "reason": "Đông khách du lịch, nắng gắt buổi trưa",
        "tip": "Đi sáng sớm trước 9h, ít người, ánh sáng đẹp",
    },
    {
        "place": "Mũi Điện",
        "best_time": "04:30-07:00",
        "avoid_time": "10:00-16:00",
        "reason": "Bình minh cực Đông, cần dậy sớm",
        "tip": "Xuất phát 4h30, mang đèn pin, đặt báo thức",
    },
    {
        "place": "Đầm Ô Loan",
        "best_time": "06:00-10:00",
        "avoid_time": "12:00-15:00",
        "reason": "Sáng mát, ánh sáng đẹp, nước yên",
        "tip": "Kayak buổi sáng tốt nhất, chiều gió có thể to",
    },
    {
        "place": "Hòn Yến",
        "best_time": "06:00-10:00",
        "avoid_time": "Mùa gió",
        "reason": "San hô đẹp nhất tháng 3-8, nước trong",
        "tip": "Mang áo phao, không tắm khi sóng to",
    },
    {
        "place": "Bãi Xép",
        "best_time": "06:00-08:00, 16:00-18:00",
        "avoid_time": "11:00-15:00",
        "reason": "Sóng nhỏ, an toàn cho bé",
        "tip": "Bãi nhỏ đẹp, ít đông hơn bãi chính",
    },
    {
        "place": "Chợ Tuy Hòa",
        "best_time": "05:00-08:00",
        "avoid_time": "14:00-17:00",
        "reason": "Sáng sớm tươi nhất, đặc sản đầy đủ",
        "tip": "Mua cá khô, mực khô, nước mắm Phú Yên",
    },
]


def detect_travel_intent(text: str) -> list[str]:
    """Returns list of travel intent types detected."""
    intents = []
    if any(m in text for m in BEACH_INTENT):
        intents.append("beach")
    if any(m in text for m in ATTRACTION_INTENT):
        intents.append("attraction")
    if any(m in text for m in RELAXATION_INTENT):
        intents.append("relaxation")
    if any(m in text for m in FOOD_TOUR_INTENT):
        intents.append("food_tour")
    if any(m in text for m in NIGHTLIFE_INTENT):
        intents.append("nightlife")
    if any(m in text for m in SHOPPING_INTENT):
        intents.append("shopping")
    if any(m in text for m in PHOTOGRAPHY_INTENT):
        intents.append("photography")
    return intents


def detect_time_preference(text: str) -> str:
    """Returns time preference for travel: morning | midday_avoid | golden_hour | night | any"""
    if any(m in text for m in GOLDEN_HOUR_TRAVEL):
        return "golden_hour"
    if any(m in text for m in MORNING_TRAVEL):
        return "morning"
    if any(m in text for m in MIDDAY_AVOIDANCE):
        return "midday_avoid"
    if any(m in text for m in NIGHT_TRAVEL):
        return "night"
    return "any"


def get_max_distance_km(fatigue: float, movement_tolerance: str) -> int:
    """Get maximum acceptable distance based on energy state."""
    if fatigue >= 0.7 or movement_tolerance == "low":
        return DISTANCE_TOLERANCE["fatigue"]
    if fatigue >= 0.4:
        return DISTANCE_TOLERANCE["low_energy"]
    if movement_tolerance == "high":
        return DISTANCE_TOLERANCE["high_energy"]
    return DISTANCE_TOLERANCE["medium_energy"]
