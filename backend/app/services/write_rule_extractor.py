from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta


EXPENSE_CATEGORIES = {
    "🏨 Lưu trú": ["khách sạn", "ks", "hotel", "resort", "homestay", "phòng", "lưu trú", "nhà nghỉ", "villa", "airbnb", "agoda", "booking"],
    "🍜 Ăn uống": ["ăn", "uống", "cafe", "cà phê", "quán", "nhà hàng", "bữa", "trưa", "tối", "sáng", "nhậu", "hải sản", "buffet", "lẩu"],
    "🚗 Di chuyển": ["taxi", "grab", "xe", "vé", "máy bay", "tàu", "thuê xe", "gửi xe", "đỗ xe", "cầu đường", "phà"],
    "⛽ Xăng dầu": ["xăng", "dầu", "đổ xăng", "nhiên liệu", "petrol"],
    "🎡 Vui chơi": ["vé tham quan", "vui chơi", "tham quan", "lặn", "tour", "công viên", "khu du lịch", "trò chơi", "giải trí"],
    "🛒 Mua sắm": ["mua", "shopping", "siêu thị", "quà", "đặc sản", "souvenir"],
    "💊 Y tế": ["thuốc", "y tế", "bệnh viện", "khám", "bác sĩ", "nhà thuốc"],
    "📦 Khác": [],
}

GROUP_ALIASES = {
    "Nhóm LV": ["nhóm lv", "lv", "liem", "liêm", "liemdo", "liem do"],
    "Nhóm LH": ["nhóm lh", "lh"],
    "Nhóm CM": ["nhóm cm", "cm"],
}

WRITE_INTENT_MARKERS = {
    "expense": ["chi", "tiền", "trả", "thanh toán", "mua", "đồng", "vnđ", "khách sạn", "ăn", "xăng", "vé"],
    "packing": ["đã đem", "đã mang", "đem rồi", "mang rồi", "đã lấy", "packed", "đã chuẩn bị", "bỏ vào vali", "đã bỏ"],
    "contribution": ["đã góp", "đã chuyển", "góp tiền", "chuyển khoản", "đóng tiền", "đã đóng", "transfer"],
    "restaurant": ["thêm quán", "quán mới", "thêm nhà hàng", "lưu quán", "quán này ngon", "ghi lại quán"],
}

# Desire/intent markers — nếu xuất hiện mà KHÔNG có số tiền → KHÔNG phải ghi chép,
# chỉ là user đang bày tỏ mong muốn / hỏi gợi ý.
# Ví dụ: "muốn ăn chè" ≠ "đã ăn chè 30k"
DESIRE_MARKERS = [
    "muốn", "thèm", "định", "dự định", "sắp", "muốn thử",
    "muốn ăn", "muốn uống", "muốn đi", "muốn ghé", "muốn mua",
    "có thể", "nên ăn gì", "ăn gì", "uống gì", "đi đâu",
    "gợi ý", "recommend", "tư vấn",
]


@dataclass
class RuleExtractResult:
    raw_text: str
    write_intent: str = "unknown"
    amount: int | None = None
    urls: list[str] = field(default_factory=list)
    iso_date: str | None = None
    category: str | None = None
    group: str | None = None
    lines: list[str] = field(default_factory=list)
    confidence: float = 0.0


def extract_amount(text: str) -> int | None:
    t = text.lower()
    compact = re.sub(r"\s+", "", t)

    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:tr|triệu)\b", t)
    if m:
        return int(float(m.group(1).replace(",", ".")) * 1_000_000)

    m = re.search(r"(\d+)tr(\d)\b", compact)
    if m:
        return int(m.group(1)) * 1_000_000 + int(m.group(2)) * 100_000

    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:k|nghìn|ngàn|ng)\b", t)
    if m:
        return int(float(m.group(1).replace(",", ".")) * 1_000)

    m = re.search(r"\b(\d{1,3}(?:[.,]\d{3}){1,3})\b", text)
    if m:
        return int(m.group(1).replace(",", "").replace(".", ""))

    m = re.search(r"\b(\d{4,9})\b", text)
    if m:
        val = int(m.group(1))
        if val >= 1000:
            return val
    return None


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", text)


def extract_date(text: str) -> str | None:
    t = text.lower()
    today = datetime.now()
    if "hôm nay" in t or "hnay" in t:
        return today.strftime("%Y-%m-%d")
    if "hôm qua" in t or "qua " in t:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    if "mai" in t or "ngày mai" in t:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except ValueError:
            return None

    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})\b", t)
    if m:
        d, mo = int(m.group(1)), int(m.group(2))
        if 1 <= d <= 31 and 1 <= mo <= 12:
            try:
                return datetime(2026, mo, d).strftime("%Y-%m-%d")
            except ValueError:
                return None
    return None


def extract_category(text: str) -> str | None:
    t = text.lower()
    for category, keywords in EXPENSE_CATEGORIES.items():
        if any(kw in t for kw in keywords):
            return category
    return None


def extract_group(text: str) -> str | None:
    t = text.lower()
    for group, aliases in GROUP_ALIASES.items():
        if any(alias in t for alias in aliases):
            return group
    return None


def is_desire_expression(text: str, has_amount: bool) -> bool:
    """
    Trả về True nếu tin nhắn là biểu đạt mong muốn/ý định chứ không phải ghi chép.
    Ví dụ: "muốn ăn chè" → True (desire)
           "ăn chè 30k"  → False (có số tiền = đã chi thật)
    """
    if has_amount:
        return False  # có số tiền → khả năng cao là đang ghi chi tiêu thật
    t = text.lower().strip()
    return any(marker in t for marker in DESIRE_MARKERS)


def detect_write_intent(text: str, has_amount: bool) -> str:
    t = text.lower()
    for intent in ("contribution", "packing", "restaurant"):
        if any(marker in t for marker in WRITE_INTENT_MARKERS[intent]):
            return intent
    # Lọc desire trước khi classify expense — "muốn ăn X" ≠ khoản chi
    if is_desire_expression(text, has_amount):
        return "unknown"
    if has_amount:
        return "expense"
    if any(marker in t for marker in WRITE_INTENT_MARKERS["expense"]):
        return "expense"
    return "unknown"


def rule_extract(text: str) -> RuleExtractResult:
    text = (text or "").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    amount = extract_amount(text)
    urls = extract_urls(text)
    iso_date = extract_date(text)
    category = extract_category(text)
    group = extract_group(text)
    write_intent = detect_write_intent(text, has_amount=amount is not None)

    confidence = 0.0
    if write_intent != "unknown":
        confidence += 0.3
    if amount is not None:
        confidence += 0.3
    if category is not None:
        confidence += 0.2
    if group is not None:
        confidence += 0.1
    if iso_date is not None:
        confidence += 0.1

    return RuleExtractResult(
        raw_text=text,
        write_intent=write_intent,
        amount=amount,
        urls=urls,
        iso_date=iso_date,
        category=category,
        group=group,
        lines=lines,
        confidence=round(confidence, 2),
    )
