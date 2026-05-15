from __future__ import annotations


# ─── Slang & shorthand patterns ───────────────────────────────────────────────
SLANG_PATTERNS: list[tuple[str, str]] = [
    # Money shorthand
    ("2 củ", "2 triệu"),
    ("2 cu", "2 triệu"),
    ("củ", "triệu"),
    ("cu", "triệu"),
    ("3 củ", "3 triệu"),
    ("5 củ", "5 triệu"),
    ("10 củ", "10 triệu"),
    ("2tr6", "2.6 triệu"),
    ("3tr5", "3.5 triệu"),
    ("1tr5", "1.5 triệu"),
    ("1tr2", "1.2 triệu"),
    ("8tr", "8 triệu"),
    ("k", "nghìn"),
    ("củ", "triệu"),
    ("tr", "triệu"),

    # Travel & food
    ("hải sản", "seafood"),
    ("hai san", "seafood"),
    ("ảnh", "chụp ảnh"),
    ("đông ghê", "đông nhiều"),
    ("bãi", "bãi biển"),
    ("tắm biển", "bơi biển"),
    ("ngắm biển", "biển"),
    ("vịnh", "vịnh hòa"),
    ("cực đông", "mũi điện"),
    ("bình minh", "mũi điện"),
    ("hoàng hôn", "sunset"),

    # Tone & emotion
    ("ngon quá", "tích cực"),
    ("đẹp quá", "tích cực"),
    ("tuyệt vời", "tích cực"),
    ("wow", "tích cực"),
    ("vui quá", "tích cực"),
    ("mệt ghê", "mệt"),
    ("nóng ghê", "nóng"),
    ("đắt mà ngon", "đắt nhưng đáng"),
    ("đắt quá", "đắt"),
    ("chờ lâu", "đông"),
    ("kẹt", "đông"),
    ("bực", "tiêu cực"),
    ("chán", "tiêu cực"),
    ("hơi mệt", "mệt nhẹ"),
    ("mệt rồi", "mệt"),

    # Places & activities
    ("quán local", "quán địa phương"),
    ("local local", "địa phương"),
    ("quán chill", "quán yên tĩnh"),
    ("chill chill", "rất yên tĩnh"),
    ("quán đông", "đông"),
    ("quán vắng", "vắng"),
    ("ngồi uống", "cafe"),
    ("uống cafe", "cafe"),
    ("cà phê", "cafe"),
    ("cốc cà phê", "cafe"),
    ("ăn vặt", "snack"),
    ("ăn xíu", "ăn ít"),
    ("bữa xíu", "bữa nhỏ"),
    ("bữa níu", "bữa nhỏ"),

    # Corrections & continuation
    ("à nhầm", "hiệu chỉnh"),
    ("nhầm", "hiệu chỉnh"),
    ("sửa lại", "hiệu chỉnh"),
    ("thêm", "bổ sung"),
    ("cái trên", "bản ghi trước đó"),
    ("cái hôm qua", "bản ghi hôm qua"),
    ("task kia", "công việc trước đó"),
    ("bill này", "chi tiêu hiện tại"),
    ("khoản đó", "chi tiêu trước đó"),
    ("lúc nãy", "trước đó"),
    ("hôm qua", "ngày trước"),

    # Intent signals
    ("gửi ảnh", "hình ảnh"),
    ("chụp lại", "hình ảnh"),
    ("đã đem", "đã mang"),
    ("đem theo", "mang"),
    ("quên đem", "chưa mang"),
]

# ─── Category keywords ────────────────────────────────────────────────────────
CANONICAL_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "utilities_electricity": ["điện", "bill điện", "tiền điện", "hoá đơn điện"],
    "utilities_water": ["nước", "bill nước", "tiền nước", "hoá đơn nước"],
    "materials_paint": ["sơn", "tiền sơn", "chi phí sơn"],
    "food_and_beverage": [
        "ăn", "uống", "cafe", "cà phê", "quán an", "quán mo", "hải sản",
        "bún", "bánh", "bữa", "trưa", "tối", "sáng", "xế",
        "đặc sản", "seafood", "local",
    ],
    "transport": [
        "xăng", "grab", "taxi", "vé", "di chuyển", "đi xe",
        "xực dụ", "dịch vụ",
    ],
    "accommodation": [
        "phòng", "khách sạn", "homestay", "resort", "住宿",
        "checkin", "check-in", "check out",
    ],
    "shopping": [
        "mua", "quần áo", "đồ", "shop", "market", "chợ",
        "đặc sản", "mang về", "quà",
    ],
    "entertainment": [
        " vé", "show", "tour", "boat", "cano", "ca nô",
        "kayak", "câu", "lướt",
    ],
    "health": [
        "thuốc", "bệnh viện", "phòng khám", "y tế",
        "kem chống nắng", "dầu gội", "sữa tắm",
    ],
}


# ─── Fuzzy Vietnamese normalizer ────────────────────────────────────────────
def normalize_slang(text: str) -> str:
    """Apply slang patterns to normalize text before parsing."""
    result = text.lower().strip()
    for slang, canonical in SLANG_PATTERNS:
        result = result.replace(slang.lower(), canonical.lower())
    return result


def expand_category_keywords(text: str) -> list[str]:
    """Return matched canonical category names from text."""
    text_lower = text.lower()
    matched = []
    for category, keywords in CANONICAL_CATEGORY_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            matched.append(category)
    return matched