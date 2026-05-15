"""
Context Fusion Engine for the Vietnamese AI travel companion.

Fuses multiple input types — raw text, OCR image results, expense sessions,
trip context, world model signals, and conversation threads — into a single
unified FusedContext that downstream engines can act on.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# FusedContext dataclass
# ---------------------------------------------------------------------------

@dataclass
class FusedContext:
    text_fragments: list[str] = field(default_factory=list)
    image_contexts: list[dict] = field(default_factory=list)  # OCR results, image classifications
    expense_session: Any = None   # ExpenseSession | None
    conversation_thread: Any = None  # ConversationThread | None
    trip_context: dict = field(default_factory=dict)
    emotional_signals: list[str] = field(default_factory=list)
    world_signals: list[str] = field(default_factory=list)
    fused_amount: float | None = None
    fused_category: str | None = None
    fused_sentiment: str = "neutral"  # positive | negative | neutral | mixed
    fused_crowdedness: bool | None = None
    fused_location_hint: str | None = None
    confidence: float = 0.0
    needs_confirmation: bool = False
    confirmation_hint: str = ""  # Vietnamese natural language confirmation


# ---------------------------------------------------------------------------
# Amount extraction helpers
# ---------------------------------------------------------------------------

_AMOUNT_PATTERNS = [
    # "500k", "500 k", "500K"
    re.compile(r"(\d[\d,\.]*)\s*k\b", re.IGNORECASE),
    # "500,000 đ", "500.000đ", "500000đ", "500000 vnd"
    re.compile(r"(\d[\d,\.]+)\s*(?:đ|vnd|vnđ)\b", re.IGNORECASE),
    # "500 nghìn", "500 ngàn"
    re.compile(r"(\d[\d,\.]*)\s*(?:nghìn|ngàn)\b", re.IGNORECASE),
    # "1.5 triệu", "1,5 triệu"
    re.compile(r"(\d[\d,\.]*)\s*triệu\b", re.IGNORECASE),
    # "500 trăm"
    re.compile(r"(\d[\d,\.]*)\s*trăm\b", re.IGNORECASE),
    # bare large number "500000"
    re.compile(r"\b(\d{4,})\b"),
]


def _parse_amount(raw: str) -> float | None:
    """Extract a Vietnamese currency amount from raw text, return as float VND."""
    text = raw.lower().strip()
    # triệu
    m = re.search(r"(\d[\d,\.]*)\s*triệu", text)
    if m:
        val = _clean_number(m.group(1))
        if val is not None:
            return val * 1_000_000

    # nghìn / ngàn
    m = re.search(r"(\d[\d,\.]*)\s*(?:nghìn|ngàn)", text)
    if m:
        val = _clean_number(m.group(1))
        if val is not None:
            return val * 1_000

    # k suffix
    m = re.search(r"(\d[\d,\.]*)\s*k\b", text, re.IGNORECASE)
    if m:
        val = _clean_number(m.group(1))
        if val is not None:
            return val * 1_000

    # trăm
    m = re.search(r"(\d[\d,\.]*)\s*trăm", text)
    if m:
        val = _clean_number(m.group(1))
        if val is not None:
            return val * 100

    # explicit currency suffix
    m = re.search(r"(\d[\d,\.]+)\s*(?:đ|vnd|vnđ)\b", text, re.IGNORECASE)
    if m:
        val = _clean_number(m.group(1))
        if val is not None:
            return val

    # bare large number (>=4 digits)
    m = re.search(r"\b(\d{4,})\b", text)
    if m:
        val = _clean_number(m.group(1))
        return val

    return None


def _clean_number(s: str) -> float | None:
    """Normalise a number string that may contain dots or commas as separators."""
    s = s.replace(" ", "")
    # Remove thousand separators that precede a three-digit group at end
    if re.match(r"^\d{1,3}(?:[,\.]\d{3})+$", s):
        s = re.sub(r"[,\.]", "", s)
    else:
        # Replace comma as decimal separator or remove
        s = s.replace(",", ".")
        # If multiple dots, treat all as thousand separators
        if s.count(".") > 1:
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------

_CATEGORY_SIGNALS: list[tuple[str, list[str]]] = [
    ("food", [
        "ăn", "uống", "cafe", "cà phê", "hải sản", "cơm", "bún", "phở",
        "bánh", "trà", "nhà hàng", "quán", "buffet", "lẩu", "sushi",
        "bữa sáng", "bữa trưa", "bữa tối", "ăn trưa", "ăn sáng", "ăn tối",
        "food", "restaurant",
    ]),
    ("transport", [
        "xăng", "grab", "taxi", "xe", "uber", "bus", "xe ôm", "vé xe",
        "tàu", "máy bay", "vé", "transport",
    ]),
    ("accommodation", [
        "khách sạn", "resort", "phòng", "thuê phòng", "hostel", "homestay",
        "hotel", "accommodation",
    ]),
    ("shopping", [
        "mua", "siêu thị", "shop", "mua sắm", "chợ", "mall", "shopping",
        "quần áo", "giày", "túi",
    ]),
    ("entertainment", [
        "vui chơi", "giải trí", "phim", "cinema", "bar", "club",
        "karaoke", "trò chơi", "spa", "massage",
    ]),
]


def _detect_category(texts: list[str]) -> str | None:
    combined = " ".join(texts).lower()
    for category, tokens in _CATEGORY_SIGNALS:
        if any(tok in combined for tok in tokens):
            return category
    return None


# ---------------------------------------------------------------------------
# Meal type detection
# ---------------------------------------------------------------------------

_MEAL_SIGNALS = {
    "breakfast": ["bữa sáng", "ăn sáng", "breakfast"],
    "lunch": ["bữa trưa", "ăn trưa", "lunch"],
    "dinner": ["bữa tối", "ăn tối", "dinner"],
    "snack": ["ăn vặt", "snack", "bánh", "trà sữa"],
}


def _detect_meal_type(texts: list[str]) -> str | None:
    combined = " ".join(texts).lower()
    for meal, tokens in _MEAL_SIGNALS.items():
        if any(tok in combined for tok in tokens):
            return meal
    return None


# ---------------------------------------------------------------------------
# Sentiment helpers
# ---------------------------------------------------------------------------

_POS_SIGNALS = [
    "ngon quá", "ngon lắm", "mà ngon", "rất ngon", "quán ngon",
    "tuyệt vời", "tuyệt", "hay quá", "hay lắm", "đẹp quá",
    "thích lắm", "thích quá", "ổn lắm", "quán ổn", "tốt lắm",
    "chill", "thoải mái", "yên tĩnh", "positive", "good", "great",
]
# Standalone positive words (but NOT when preceded by negation)
_POS_WORDS_RE = re.compile(
    r"(?<!không\s)(?<!chẳng\s)(?<!chả\s)\b(ngon|tuyệt|thích|ổn|tốt|đẹp|hay)\b"
)
_NEG_SIGNALS = [
    "không ngon", "dở quá", "dở lắm", "dở", "tệ quá", "tệ lắm", "tệ",
    "không thích", "chán", "mắc quá", "đắt quá", "đắt", "chặt chém",
    "ồn quá", "negative", "bad",
]


def _fuse_sentiment(
    text_signals: list[str],
    meta_from_thread: dict,
) -> str:
    combined = " ".join(text_signals).lower()

    has_neg = any(s in combined for s in _NEG_SIGNALS)
    # Check multi-word positive phrases first
    has_pos = any(s in combined for s in _POS_SIGNALS)
    # Then check standalone words that aren't preceded by negation
    if not has_pos and _POS_WORDS_RE.search(combined):
        has_pos = True

    # Also read from thread metadata
    if meta_from_thread.get("positive_sentiment"):
        has_pos = True
    if meta_from_thread.get("negative_sentiment"):
        has_neg = True

    if has_pos and has_neg:
        return "mixed"
    if has_pos:
        return "positive"
    if has_neg:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# OCR helpers
# ---------------------------------------------------------------------------

_OCR_UNCERTAIN_MARKERS = ["ocr pending", "unknown", "unclear", "n/a", "???"]


def _is_ocr_uncertain(raw_text: str) -> bool:
    t = raw_text.lower()
    return any(marker in t for marker in _OCR_UNCERTAIN_MARKERS)


def _extract_from_images(image_contexts: list[dict]) -> tuple[float | None, str | None, str | None, bool]:
    """
    Returns (amount, category, location, uncertain) extracted from image contexts.
    """
    img_amount: float | None = None
    img_category: str | None = None
    img_location: str | None = None
    uncertain = False

    for img in image_contexts:
        raw = img.get("raw_text", img.get("ocr_text", ""))
        if not raw:
            continue
        if _is_ocr_uncertain(raw):
            uncertain = True
            continue

        # Try amount
        amt = _parse_amount(raw)
        if amt is not None:
            # Prefer higher amount (assume higher confidence for larger receipts)
            if img_amount is None or amt > img_amount:
                img_amount = amt

        # Category
        cat = _detect_category([raw])
        if cat and img_category is None:
            img_category = cat

        # Location hint from image
        loc = img.get("location") or img.get("place")
        if loc and img_location is None:
            img_location = loc

    return img_amount, img_category, img_location, uncertain


# ---------------------------------------------------------------------------
# Confidence calculator
# ---------------------------------------------------------------------------

def _calc_confidence(
    amount: float | None,
    category: str | None,
    needs_confirmation: bool,
) -> float:
    if amount is not None and category is not None:
        base = 0.85
    elif amount is not None or category is not None:
        base = 0.65
    else:
        base = 0.40

    if needs_confirmation:
        base = min(base, 0.55)

    return round(base, 2)


# ---------------------------------------------------------------------------
# Vietnamese confirmation message builder
# ---------------------------------------------------------------------------

def _build_confirmation_hint(
    category: str | None,
    meal_type: str | None,
    amount: float | None,
    location: str | None,
) -> str:
    cat_map = {
        "food": "ăn uống",
        "transport": "di chuyển",
        "accommodation": "lưu trú",
        "shopping": "mua sắm",
        "entertainment": "vui chơi giải trí",
    }
    meal_map = {
        "breakfast": "bữa sáng",
        "lunch": "bữa trưa",
        "dinner": "bữa tối",
        "snack": "ăn vặt",
    }

    cat_str = cat_map.get(category or "", category or "chi tiêu")
    meal_str = meal_map.get(meal_type or "", "")

    if amount is not None:
        if amount >= 1_000_000:
            amt_str = f"{amount / 1_000_000:.1f} triệu".rstrip("0").rstrip(".")
            amt_str = f"{amount / 1_000_000:g} triệu"
        elif amount >= 1_000:
            amt_str = f"{int(amount // 1_000)}k"
        else:
            amt_str = f"{int(amount)} đồng"
    else:
        amt_str = "?"

    parts = [cat_str]
    if meal_str:
        parts.append(meal_str)

    desc = " ".join(parts)
    loc_part = f" tại {location}" if location else ""
    return f"Mình hiểu đây là {desc} khoảng {amt_str}{loc_part} đúng không?"


# ---------------------------------------------------------------------------
# ContextFusion
# ---------------------------------------------------------------------------

class ContextFusion:
    """
    Fuses text, images, expense session, trip context, world model, and
    conversation thread into a single FusedContext.
    """

    def fuse(
        self,
        text: str | list[str],
        images: list[dict] | None = None,
        expense_session: Any = None,
        trip_context: dict | None = None,
        world_model: dict | None = None,
        conversation_thread: Any = None,
    ) -> FusedContext:
        images = images or []
        trip_context = trip_context or {}
        world_model = world_model or {}

        # Normalise text to list of fragments
        if isinstance(text, str):
            text_fragments = [text] if text else []
        else:
            text_fragments = list(text)

        # Gather all text sources
        all_texts = list(text_fragments)

        # Pull from expense session fragments
        session_fragments: list[str] = []
        if expense_session is not None:
            session_fragments = list(getattr(expense_session, "fragments", []))
            all_texts.extend(session_fragments)

        # Pull from conversation thread fragments / sentiment signals
        thread_meta: dict = {}
        thread_sentiment_signals: list[str] = []
        if conversation_thread is not None:
            thread_frags = list(getattr(conversation_thread, "fragments", []))
            thread_sigs = list(getattr(conversation_thread, "sentiment_signals", []))
            thread_meta = dict(getattr(conversation_thread, "metadata", {}))
            thread_sentiment_signals = thread_sigs
            all_texts.extend(thread_frags)
            all_texts.extend(thread_sigs)

        # World / emotional signals from world model
        emotional_signals: list[str] = list(world_model.get("emotional_signals", []))
        world_signals: list[str] = list(world_model.get("world_signals", []))

        # --- Extract from images ---
        img_amount, img_category, img_location, ocr_uncertain = _extract_from_images(images)

        # --- Extract from text ---
        text_amount = _parse_amount(" ".join(text_fragments))
        text_category = _detect_category(all_texts)
        text_meal_type = _detect_meal_type(all_texts)
        text_location: str | None = trip_context.get("location") or trip_context.get("current_location")

        # --- Prefer session values if present ---
        session_amount: float | None = getattr(expense_session, "amount", None) if expense_session else None
        session_category: str | None = getattr(expense_session, "category", None) if expense_session else None
        session_meal_type: str | None = getattr(expense_session, "meal_type", None) if expense_session else None
        session_location: str | None = getattr(expense_session, "location", None) if expense_session else None

        # --- Fuse amount: image wins if both present and image is more specific ---
        fused_amount: float | None = None
        if session_amount is not None and img_amount is not None:
            # Prefer image amount if confidence is high (no OCR uncertain)
            if not ocr_uncertain:
                fused_amount = img_amount
            else:
                fused_amount = session_amount
        elif img_amount is not None and not ocr_uncertain:
            fused_amount = img_amount
        elif text_amount is not None:
            fused_amount = text_amount
        elif session_amount is not None:
            fused_amount = session_amount

        # --- Fuse category ---
        fused_category = session_category or img_category or text_category

        # --- Fuse location ---
        fused_location = session_location or img_location or text_location

        # --- Fuse meal type ---
        fused_meal_type = session_meal_type or text_meal_type

        # --- Crowdedness ---
        fused_crowdedness: bool | None = thread_meta.get("crowded", None)
        if fused_crowdedness is None:
            # Check all texts for crowded signals
            combined = " ".join(all_texts).lower()
            crowded_keywords = ["đông ghê", "đông thật", "đông vãi", "đông quá", "nhiều người", "đông lắm", "chật"]
            if any(kw in combined for kw in crowded_keywords):
                fused_crowdedness = True

        # --- Sentiment ---
        fused_sentiment = _fuse_sentiment(all_texts + thread_sentiment_signals, thread_meta)

        # --- needs_confirmation ---
        needs_confirmation = ocr_uncertain

        # --- Confidence ---
        confidence = _calc_confidence(fused_amount, fused_category, needs_confirmation)

        # --- Confirmation hint ---
        confirmation_hint = _build_confirmation_hint(
            fused_category, fused_meal_type, fused_amount, fused_location
        )

        return FusedContext(
            text_fragments=text_fragments,
            image_contexts=images,
            expense_session=expense_session,
            conversation_thread=conversation_thread,
            trip_context=trip_context,
            emotional_signals=emotional_signals,
            world_signals=world_signals,
            fused_amount=fused_amount,
            fused_category=fused_category,
            fused_sentiment=fused_sentiment,
            fused_crowdedness=fused_crowdedness,
            fused_location_hint=fused_location,
            confidence=confidence,
            needs_confirmation=needs_confirmation,
            confirmation_hint=confirmation_hint,
        )
