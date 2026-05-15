from __future__ import annotations

import re
from dataclasses import dataclass

from app.conversation.temporal_memory import ExpenseSession

# ---------------------------------------------------------------------------
# Amount parsing
# ---------------------------------------------------------------------------

_AMOUNT_PATTERN = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*(k|nghìn|ngàn|tr|triệu|đồng|đ|vnd|vnđ)?",
    re.IGNORECASE,
)

_MULTIPLIERS = {
    "k": 1_000,
    "nghìn": 1_000,
    "ngàn": 1_000,
    "tr": 1_000_000,
    "triệu": 1_000_000,
    "đồng": 1,
    "đ": 1,
    "vnd": 1,
    "vnđ": 1,
}

# ---------------------------------------------------------------------------
# Category / subcategory signals
# ---------------------------------------------------------------------------

CATEGORY_MAP: dict[str, tuple[str, str]] = {
    # food
    "ăn": ("food", "meal"),
    "uống": ("food", "drink"),
    "cà phê": ("food", "coffee"),
    "cafe": ("food", "coffee"),
    "cơm": ("food", "meal"),
    "phở": ("food", "meal"),
    "bún": ("food", "meal"),
    "bánh": ("food", "snack"),
    "trà": ("food", "drink"),
    "hải sản": ("food", "seafood"),
    "tôm": ("food", "seafood"),
    "cua": ("food", "seafood"),
    "mực": ("food", "seafood"),
    "cá": ("food", "seafood"),
    "thịt": ("food", "meal"),
    "lẩu": ("food", "meal"),
    "buffet": ("food", "buffet"),
    "nhà hàng": ("food", "restaurant"),
    "quán": ("food", "restaurant"),
    # transport
    "xăng": ("transport", "fuel"),
    "grab": ("transport", "rideshare"),
    "taxi": ("transport", "taxi"),
    "xe": ("transport", "vehicle"),
    "uber": ("transport", "rideshare"),
    "vé": ("transport", "ticket"),
    "tàu": ("transport", "boat"),
    "thuyền": ("transport", "boat"),
    # accommodation
    "khách sạn": ("accommodation", "hotel"),
    "resort": ("accommodation", "resort"),
    "phòng": ("accommodation", "room"),
    "thuê": ("accommodation", "rental"),
    "homestay": ("accommodation", "homestay"),
    # shopping
    "mua": ("shopping", "purchase"),
    "siêu thị": ("shopping", "supermarket"),
    "shop": ("shopping", "retail"),
    "mua sắm": ("shopping", "retail"),
    "chợ": ("shopping", "market"),
    "đồ": ("shopping", "goods"),
    # activities
    "vé vào": ("activity", "entry"),
    "tham quan": ("activity", "sightseeing"),
    "tour": ("activity", "tour"),
    "snorkeling": ("activity", "water_sport"),
    "lặn": ("activity", "water_sport"),
    # health
    "thuốc": ("health", "medicine"),
    "bệnh viện": ("health", "hospital"),
    "spa": ("health", "wellness"),
    "massage": ("health", "wellness"),
}

MEAL_TYPE_MAP: dict[str, str] = {
    "sáng": "breakfast",
    "bữa sáng": "breakfast",
    "ăn sáng": "breakfast",
    "trưa": "lunch",
    "bữa trưa": "lunch",
    "ăn trưa": "lunch",
    "tối": "dinner",
    "bữa tối": "dinner",
    "ăn tối": "dinner",
    "chiều": "afternoon_snack",
    "xế": "afternoon_snack",
    "đêm": "late_night",
    "khuya": "late_night",
}

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class MergeResult:
    amount: float | None
    category: str | None
    subcategory: str | None
    meal_type: str | None
    location: str | None
    description: str
    confidence: float      # 0.0–1.0
    ambiguity: float       # 0.0–1.0 (lower = clearer)
    confirmation_message: str


# ---------------------------------------------------------------------------
# Merger
# ---------------------------------------------------------------------------


class ExpenseMerger:
    """
    Merges accumulated text fragments (and optional image OCR fragments)
    into a structured expense inference with confidence/ambiguity scores.
    """

    def merge(self, session: ExpenseSession) -> MergeResult:
        combined = " ".join(session.fragments).lower().strip()
        # Also fold in any image OCR text
        for img in session.image_fragments:
            raw = img.get("raw_text", "") or ""
            combined = (combined + " " + raw.lower()).strip()

        amount = self._parse_amount(combined)
        category, subcategory = self._detect_category(combined)
        meal_type = self._detect_meal_type(combined)
        location = self._detect_location(combined)

        confidence = self._compute_confidence(amount, category, meal_type)
        ambiguity = round(1.0 - confidence, 3)

        description = self._build_description(session.fragments, session.image_fragments)
        confirmation_message = self._build_confirmation(amount, category, subcategory, meal_type, location, confidence)

        return MergeResult(
            amount=amount,
            category=category,
            subcategory=subcategory,
            meal_type=meal_type,
            location=location,
            description=description,
            confidence=confidence,
            ambiguity=ambiguity,
            confirmation_message=confirmation_message,
        )

    # ------------------------------------------------------------------
    # Amount parsing
    # ------------------------------------------------------------------

    _THOUSANDS_DOT = re.compile(r"\.\d{3}")

    def _parse_amount(self, text: str) -> float | None:
        best: float | None = None
        for m in _AMOUNT_PATTERN.finditer(text):
            raw_num = m.group(1)
            unit = (m.group(2) or "").lower()
            try:
                if self._THOUSANDS_DOT.search(raw_num):
                    # "350.000" — dot is thousands separator
                    value = float(raw_num.replace(".", "").replace(",", ""))
                else:
                    # "1.5" — dot is decimal separator
                    value = float(raw_num.replace(",", ""))
            except ValueError:
                continue
            multiplier = _MULTIPLIERS.get(unit, 1)
            # Bare numbers: if no unit and value is small (1-999), assume it's "k"
            if not unit and 1 <= value <= 999:
                value *= 1_000
            elif not unit and value >= 1_000:
                pass  # already in đồng
            else:
                value *= multiplier
            if best is None or value > best:
                best = value
        return best

    # ------------------------------------------------------------------
    # Category detection
    # ------------------------------------------------------------------

    def _detect_category(self, text: str) -> tuple[str | None, str | None]:
        # Match longest keyword first to prefer specific over generic
        for kw in sorted(CATEGORY_MAP, key=len, reverse=True):
            if kw in text:
                return CATEGORY_MAP[kw]
        return None, None

    def _detect_meal_type(self, text: str) -> str | None:
        for kw in sorted(MEAL_TYPE_MAP, key=len, reverse=True):
            if kw in text:
                return MEAL_TYPE_MAP[kw]
        return None

    def _detect_location(self, text: str) -> str | None:
        # Heuristic: look for Vietnamese place markers
        patterns = [
            r"ở\s+([^\s,\.]{2,30})",
            r"tại\s+([^\s,\.]{2,30})",
            r"@\s*([^\s,\.]{2,30})",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        return None

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _compute_confidence(
        self,
        amount: float | None,
        category: str | None,
        meal_type: str | None,
    ) -> float:
        score = 0.0
        if amount is not None:
            score += 0.55
        if category is not None:
            score += 0.30
        if meal_type is not None:
            score += 0.15
        return round(min(score, 1.0), 3)

    # ------------------------------------------------------------------
    # Natural language output
    # ------------------------------------------------------------------

    def _build_description(self, fragments: list[str], image_fragments: list[dict]) -> str:
        parts = [f for f in fragments if f.strip()]
        if image_fragments:
            parts.append("[ảnh/receipt]")
        return " | ".join(parts)

    def _build_confirmation(
        self,
        amount: float | None,
        category: str | None,
        subcategory: str | None,
        meal_type: str | None,
        location: str | None,
        confidence: float,
    ) -> str:
        parts: list[str] = []

        if meal_type:
            meal_labels = {
                "breakfast": "bữa sáng",
                "lunch": "bữa trưa",
                "dinner": "bữa tối",
                "afternoon_snack": "xế chiều",
                "late_night": "đêm khuya",
            }
            parts.append(meal_labels.get(meal_type, meal_type))

        if subcategory and subcategory not in ("meal", "purchase"):
            sub_labels = {
                "coffee": "cà phê",
                "drink": "nước uống",
                "seafood": "hải sản",
                "snack": "ăn vặt",
                "restaurant": "nhà hàng",
                "buffet": "buffet",
                "fuel": "xăng",
                "rideshare": "xe công nghệ",
                "taxi": "taxi",
                "vehicle": "xe",
                "boat": "tàu thuyền",
                "ticket": "vé",
                "hotel": "khách sạn",
                "resort": "resort",
                "room": "phòng",
                "rental": "thuê",
                "homestay": "homestay",
                "supermarket": "siêu thị",
                "retail": "mua sắm",
                "market": "chợ",
                "goods": "đồ dùng",
                "entry": "vé vào cửa",
                "sightseeing": "tham quan",
                "tour": "tour",
                "water_sport": "thể thao nước",
                "medicine": "thuốc",
                "hospital": "bệnh viện",
                "wellness": "spa/massage",
            }
            parts.append(sub_labels.get(subcategory, subcategory))
        elif category and not subcategory:
            cat_labels = {
                "food": "ăn uống",
                "transport": "đi lại",
                "accommodation": "chỗ ở",
                "shopping": "mua sắm",
                "activity": "hoạt động",
                "health": "sức khỏe",
            }
            parts.append(cat_labels.get(category, category))

        if location:
            parts.append(f"tại {location}")

        expense_desc = " ".join(parts) if parts else "chi tiêu này"

        if amount is not None:
            amount_str = _format_amount(amount)
            msg = f"Mình hiểu đây là khoản {expense_desc} khoảng {amount_str} đúng không?"
        else:
            msg = f"Mình đang ghi nhận khoản {expense_desc}. Bạn cho mình biết số tiền là bao nhiêu nhé?"

        if confidence < 0.5:
            msg += " (mình chưa chắc lắm, xác nhận giúp mình nhé)"

        return msg


def _format_amount(amount: float) -> str:
    if amount >= 1_000_000:
        val = amount / 1_000_000
        return f"{val:g} triệu"
    if amount >= 1_000:
        val = amount / 1_000
        return f"{val:g}k"
    return f"{int(amount):,}đ"
