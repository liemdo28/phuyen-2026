from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.schemas.assistant import AssistantIntent


AMOUNT_PATTERNS = [
    (re.compile(r"(\d+(?:[\.,]\d+)?)\s*(tr|triệu|trieu)\b", re.IGNORECASE), 1_000_000),
    (re.compile(r"(\d+(?:[\.,]\d+)?)\s*(k|nghìn|nghin)\b", re.IGNORECASE), 1_000),
]

DOMAIN_KEYWORDS = {
    "expense": ["bill", "chi phí", "chi tiêu", "tiền", "điện", "nước", "sơn", "receipt", "hóa đơn", "hoá đơn"],
    "task": ["task", "deadline", "overdue", "việc", "công việc", "kitchen", "todo"],
    "inventory": ["inventory", "tồn kho", "kho", "stock"],
    "revenue": ["doanh thu", "revenue", "sales", "bán hàng"],
    "travel": ["trời", "ăn ngon", "đi đâu", "cafe", "quán", "lịch trình", "đà lạt", "nearby", "gần đây"],
    "crm": ["khách", "lead", "crm", "follow up"],
    "note": ["ghi chú", "note", "lưu thông tin"],
}

CREATE_MARKERS = ["thêm", "tạo", "add", "create", "lưu"]
UPDATE_MARKERS = ["update", "cập nhật", "sửa", "đổi", "dời", "chỉnh"]
DELETE_MARKERS = ["xóa", "xoá", "remove", "delete"]
QUERY_MARKERS = ["bao nhiêu", "có", "tìm", "sao", "nào", "không", "hôm nay", "hôm qua"]


def heuristic_intent_parse(message_text: str, memory_summary: str = "") -> AssistantIntent:
    normalized = normalize_text(message_text)
    intent_type = detect_intent_type(normalized)
    domain = detect_domain(normalized)
    extracted_fields = extract_common_fields(normalized)
    reply_style = build_reply_style(intent_type, domain, extracted_fields)
    confidence = 0.55
    if extracted_fields:
        confidence += 0.15
    if domain != "general":
        confidence += 0.1
    if memory_summary and any(phrase in normalized for phrase in ["cái trên", "task này", "bill này"]):
        confidence += 0.1

    return AssistantIntent(
        intent_type=intent_type,
        domain=domain,
        confidence=min(confidence, 0.95),
        extracted_fields=extracted_fields,
        missing_fields=missing_fields_for_intent(intent_type, domain, extracted_fields),
        reply_style=reply_style,
    )


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def detect_intent_type(text: str) -> str:
    if any(marker in text for marker in DELETE_MARKERS):
        return "delete"
    if any(marker in text for marker in UPDATE_MARKERS):
        return "update"
    if any(marker in text for marker in CREATE_MARKERS):
        return "create"
    if any(marker in text for marker in QUERY_MARKERS):
        return "query"
    return "chat"


def detect_domain(text: str) -> str:
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return domain
    if extract_amount(text) is not None:
        return "expense"
    return "general"


def extract_common_fields(text: str) -> dict[str, object]:
    fields: dict[str, object] = {}
    amount = extract_amount(text)
    if amount is not None:
        fields["amount"] = amount

    date_ref = extract_relative_date(text)
    if date_ref:
        fields["date"] = date_ref

    note = strip_amount_phrases(text)
    if note and note != text:
        fields["note"] = note

    category = infer_expense_category(text)
    if category:
        fields["category"] = category

    return fields


def extract_amount(text: str) -> int | None:
    compact_text = text.replace(" ", "")
    match = re.search(r"(\d+)\s*(?:tr|triệu|trieu)\s*(\d{1,3})(?!\d)", text, re.IGNORECASE)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2).ljust(3, "0")[:3])
        return major * 1_000_000 + minor * 1_000

    match = re.search(r"(\d+)tr(\d{1,3})(?!\d)", compact_text, re.IGNORECASE)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2).ljust(3, "0")[:3])
        return major * 1_000_000 + minor * 1_000

    for pattern, multiplier in AMOUNT_PATTERNS:
        found = pattern.search(text)
        if found:
            value = float(found.group(1).replace(",", "."))
            return int(round(value * multiplier))

    raw_digits = re.search(r"\b(\d{4,10})\b", text)
    if raw_digits:
        return int(raw_digits.group(1))
    return None


def extract_relative_date(text: str) -> str | None:
    now = datetime.now()
    mapping = {
        "hôm nay": now,
        "hôm qua": now - timedelta(days=1),
        "mai": now + timedelta(days=1),
        "ngày mai": now + timedelta(days=1),
    }
    for phrase, dt in mapping.items():
        if phrase in text:
            return dt.strftime("%Y-%m-%d")
    weekday_match = re.search(r"thứ\s*(\d)", text)
    if weekday_match:
        target = int(weekday_match.group(1))
        today = now.isoweekday()
        offset = (target - today) % 7
        offset = 7 if offset == 0 else offset
        return (now + timedelta(days=offset)).strftime("%Y-%m-%d")
    return None


def strip_amount_phrases(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"\d+\s*(?:tr|triệu|trieu)\s*\d{1,3}(?!\d)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\d+tr\d{1,3}(?!\d)", "", cleaned, flags=re.IGNORECASE)
    for pattern, _ in AMOUNT_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = re.sub(r"\b\d{4,10}\b", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip(" -,:")


def infer_expense_category(text: str) -> str | None:
    if any(word in text for word in ["điện", "electricity"]):
        return "utilities_electricity"
    if any(word in text for word in ["sơn", "paint"]):
        return "materials_paint"
    if any(word in text for word in ["ăn", "uống", "cafe", "quán"]):
        return "food_and_beverage"
    if any(word in text for word in ["xăng", "grab", "taxi", "vé"]):
        return "transport"
    return None


def missing_fields_for_intent(intent_type: str, domain: str, extracted_fields: dict[str, object]) -> list[str]:
    if domain == "expense" and intent_type in {"create", "update"}:
        missing = []
        if "amount" not in extracted_fields:
            missing.append("amount")
        return missing
    return []


def build_reply_style(intent_type: str, domain: str, extracted_fields: dict[str, object]) -> str:
    if intent_type == "query" and domain == "travel":
        return "Friendly travel concierge tone in Vietnamese."
    if intent_type in {"create", "update"}:
        return "Warm confirmation in Vietnamese with action summary."
    return "Helpful conversational Vietnamese answer."
