"""
Vietnamese Food & Drink Intelligence Database

Covers:
- Food category detection (seafood, street food, Vietnamese dishes, etc.)
- Drink preferences (coffee, tea, alcohol, fresh juice)
- Meal timing context
- Social food scenarios (nhậu, family meal, romantic dinner)
- Price range preferences
- Dietary signals
- Weather-appropriate food recommendations
"""
from __future__ import annotations

# ── Food Type Classification ──────────────────────────────────────────────────
SEAFOOD_MARKERS: list[str] = [
    "hải sản", "tôm", "cua", "mực", "bạch tuộc", "ốc",
    "cá", "cá ngừ", "cá biển", "cá hồi",
    "nghêu", "sò", "vẹm", "hàu", "trai",
    "tôm hùm", "tôm càng", "tôm sú", "tôm he",
    "lẩu hải sản", "nướng hải sản", "hải sản nướng",
    "bún sứa", "gỏi cá", "cháo hải sản",
    "cá nướng", "mực nướng", "tôm nướng", "cua hấp",
    "sò huyết", "sò điệp", "ốc xào", "ốc hút",
    "bún cá", "canh chua cá", "cá chiên",
]

VIETNAMESE_FOOD_MARKERS: list[str] = [
    # Noodles
    "bún", "phở", "mì", "bánh canh", "hủ tiếu", "bún bò",
    "bún mắm", "bún riêu", "bún ốc", "bún thịt nướng",
    "mì quảng", "cao lầu", "bánh đa",
    # Rice dishes
    "cơm", "cơm tấm", "cơm rang", "cơm gà", "cơm sườn",
    "cơm chiên", "cơm niêu", "cơm bình dân",
    # Bánh
    "bánh mì", "bánh căn", "bánh hỏi", "bánh xèo",
    "bánh cuốn", "bánh bèo", "bánh nậm", "bánh lọc",
    "bánh tráng", "bánh tráng nướng", "bánh ướt",
    "bánh khọt", "bánh cống",
    # Soups / stews
    "lẩu", "lẩu mắm", "lẩu chua", "lẩu nấm",
    "canh chua", "canh bí", "sup", "súp",
    # Grilled
    "thịt nướng", "nướng", "bbq", "bò nướng",
    "nem nướng", "chả nướng",
    # Specialty Phú Yên
    "cá ngừ đại dương", "tôm hùm Sông Cầu", "sò huyết Ô Loan",
    "bún sứa", "bánh hỏi lòng heo",
    # Other Vietnamese
    "gỏi", "gỏi cuốn", "chả giò", "nem",
    "mắm", "nước mắm", "kho",
    "lòng", "phủ tạng", "dồi",
]

STREET_FOOD_MARKERS: list[str] = [
    "ăn vặt", "street food", "đồ ăn đường phố",
    "xe đẩy", "hàng rong", "vỉa hè",
    "ăn bên đường", "ăn ngoài trời",
    "chợ đêm", "chợ ăn vặt",
    "bánh tráng nướng", "bắp rang bơ", "cà rem",
    "kem", "chè", "bánh tráng trộn", "ổi", "xoài dầm",
    "phá lấu", "trứng cút lộn", "hột vịt lộn",
    "súp cua", "bò bía", "gỏi đu đủ",
    "xiên que", "bò né", "bánh mì chảo",
]

CAFE_MARKERS: list[str] = [
    "cà phê", "cafe", "cf", "coffee",
    "cà phê sữa", "bạc xỉu", "cà phê đen", "cold brew",
    "americano", "latte", "cappuccino", "espresso",
    "cà phê vợt", "cà phê phin", "cà phê rang xay",
    "cafe cóc", "cafe vỉa hè", "cafe view biển",
    "cafe view đẹp", "ngồi cafe", "làm việc cafe",
    "quán cafe", "tiệm cafe",
]

DRINK_MARKERS: list[str] = [
    # Non-alcoholic
    "nước mía", "nước dừa", "sinh tố", "nước ép",
    "trà đá", "trà chanh", "trà sữa", "trà",
    "nước cam", "nước dưa hấu",
    "soda", "nước ngọt", "pepsi", "coke",
    "boba", "bubble tea", "trà trái cây",
    "smoothie",
    # Alcoholic
    "bia", "beer", "bia hơi", "bia tươi", "bia lạnh",
    "rượu", "rượu vang", "wine", "cocktail",
    "mojito", "margarita", "gin tonic",
    "whisky", "bourbon", "rum",
    "soju", "sake",
    "làm vài ly", "quất vài ly", "nhậu",
]

DESSERT_MARKERS: list[str] = [
    "chè", "kem", "bánh", "tráng miệng",
    "kem tươi", "kem cây", "kem ly",
    "chè đậu", "chè thái", "chè bà ba",
    "bánh ngọt", "cake", "cupcake",
    "sinh tố", "hoa quả dầm",
    "bingsu", "halo halo",
]

# ── Meal Time Context ─────────────────────────────────────────────────────────
BREAKFAST_MARKERS: list[str] = [
    "ăn sáng", "đồ ăn sáng", "bữa sáng",
    "sáng sớm", "mới dậy", "buổi sáng",
    "trước 10 giờ", "trước 9 giờ", "mấy giờ sáng",
    "bún cá buổi sáng", "phở sáng", "cháo sáng",
    "bánh mì sáng",
]

LUNCH_MARKERS: list[str] = [
    "ăn trưa", "bữa trưa", "giờ trưa", "trưa rồi",
    "11 giờ", "12 giờ", "giữa trưa",
    "cơm trưa", "quán cơm",
]

DINNER_MARKERS: list[str] = [
    "ăn tối", "bữa tối", "tối rồi", "buổi tối",
    "6 giờ tối", "7 giờ tối", "chiều tối",
    "nhà hàng tối", "dinner",
]

LATE_NIGHT_MARKERS: list[str] = [
    "ăn khuya", "ăn đêm", "khuya rồi", "đêm khuya",
    "quán khuya", "mở khuya", "quán mở khuya",
    "12 giờ đêm", "1 giờ đêm", "2 giờ đêm",
    "đêm hôm", "ăn đêm", "cháo khuya", "bún khuya",
    "xúc xích nướng", "mì gói", "cháo trắng khuya",
    "đồ ăn đêm", "night food",
]

# ── Price Range Preferences ───────────────────────────────────────────────────
BUDGET_MARKERS: list[str] = [
    "rẻ thôi", "bình dân", "giá rẻ", "không đắt",
    "tiết kiệm", "budget", "không tốn nhiều",
    "dưới 100k", "dưới 50k", "dưới 30k",
    "giá sinh viên", "giá bình dân",
    "vừa túi tiền", "không chặt chém",
    "quán xóm", "quán bình thường thôi",
]

MIDRANGE_MARKERS: list[str] = [
    "khoảng 150k", "khoảng 200k", "tầm 150",
    "không cần fancy", "thoải mái một chút",
    "nhà hàng bình thường", "quán ổn ổn",
]

UPSCALE_MARKERS: list[str] = [
    "sang", "cao cấp", "fine dining", "nhà hàng sang",
    "xịn xò", "sang chảnh", "luxury",
    "view đẹp nhà hàng", "nhà hàng view",
    "không ngại giá", "giá không thành vấn đề",
    "muốn trải nghiệm đặc biệt",
]

# ── Food Weather Matching ─────────────────────────────────────────────────────
HOT_WEATHER_FOODS: list[str] = [
    "đồ mát", "đá", "lạnh", "giải nhiệt",
    "sinh tố", "nước ép", "nước dừa", "chè đá",
    "kem", "cold drink", "đồ uống lạnh",
    "ăn gì mát", "đồ mát lạnh",
    "nước mía đá", "trà đá",
]

COLD_WEATHER_FOODS: list[str] = [
    "lẩu", "súp nóng", "cháo nóng", "đồ nóng",
    "ấm bụng", "giữ ấm", "hot pot",
    "canh nóng", "nước dùng nóng",
    "ăn gì ấm", "đồ ăn ấm",
]

RAINY_WEATHER_FOODS: list[str] = [
    "mưa rồi", "trời mưa", "mưa to",
    "ở trong này ăn gì", "không ra ngoài được",
    "đồ ăn trong nhà", "giao hàng", "ship đồ ăn",
    "order", "grab food",
]


# ── Composite Food Intelligence ───────────────────────────────────────────────
def detect_food_type(text: str) -> list[str]:
    """Returns list of food types detected in text."""
    types = []
    if any(m in text for m in SEAFOOD_MARKERS):
        types.append("seafood")
    if any(m in text for m in VIETNAMESE_FOOD_MARKERS):
        types.append("vietnamese")
    if any(m in text for m in STREET_FOOD_MARKERS):
        types.append("street_food")
    if any(m in text for m in CAFE_MARKERS):
        types.append("cafe")
    if any(m in text for m in DRINK_MARKERS):
        types.append("drinks")
    if any(m in text for m in DESSERT_MARKERS):
        types.append("dessert")
    return types


def detect_meal_time(text: str) -> str:
    """Returns: breakfast | lunch | dinner | late_night | any"""
    if any(m in text for m in LATE_NIGHT_MARKERS):
        return "late_night"
    if any(m in text for m in BREAKFAST_MARKERS):
        return "breakfast"
    if any(m in text for m in LUNCH_MARKERS):
        return "lunch"
    if any(m in text for m in DINNER_MARKERS):
        return "dinner"
    return "any"


def detect_price_preference(text: str) -> str:
    """Returns: budget | midrange | upscale | any"""
    if any(m in text for m in BUDGET_MARKERS):
        return "budget"
    if any(m in text for m in UPSCALE_MARKERS):
        return "upscale"
    if any(m in text for m in MIDRANGE_MARKERS):
        return "midrange"
    return "any"


def is_drinking_context(text: str) -> bool:
    """True if alcohol / nightlife drinking is the goal."""
    alcohol = ["bia", "rượu", "cocktail", "nhậu", "quán bar", "quán nhậu",
               "làm vài lon", "làm vài ly", "quất vài", "pub", "bar"]
    return any(m in text for m in alcohol)
