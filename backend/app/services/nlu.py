from __future__ import annotations

import re
import unicodedata

from app.ai.action_engine import infer_action_name
from app.nlp.intent_preprocessor import preprocess_intent_text
from app.nlp.money_parser import parse_money_amount, strip_money_phrases
from app.nlp.relative_date_parser import parse_relative_date
from app.schemas.assistant import AssistantIntent

DOMAIN_KEYWORDS = {
    "expense": ["bill", "chi phí", "chi tiêu", "tiền", "điện", "nước", "sơn", "receipt", "hóa đơn", "hoá đơn"],
    "task": ["task", "deadline", "overdue", "việc", "công việc", "kitchen", "todo", "chưa xong"],
    "inventory": ["inventory", "tồn kho", "kho", "stock"],
    "revenue": ["doanh thu", "revenue", "sales", "bán hàng"],
    "travel": [
        # Original
        "trời", "ăn ngon", "đi đâu", "cafe", "quán", "lịch trình", "đà lạt", "nearby", "gần đây", "mở khuya", "chill",
        # Intelligence graph expansion — rich travel signals
        "biển", "bãi biển", "gành đá đĩa", "mũi điện", "đầm ô loan", "hòn yến", "bãi xép",
        "tham quan", "khám phá", "du lịch", "view", "cảnh đẹp", "check-in",
        "ăn gì", "ăn ở đâu", "kiếm gì ăn", "quán ngon", "đặc sản",
        "hải sản", "bún cá", "bánh căn", "tôm hùm", "cá ngừ",
        "nhậu", "bia", "quán nhậu", "pub", "bar",
        "healing", "relax", "thư giãn", "nghỉ ngơi",
        "mệt", "đói", "đói rồi", "đói quá",
        "mưa", "nắng", "nóng", "thời tiết",
        "sunset", "hoàng hôn", "bình minh", "sống ảo",
        "đi với ny", "đi gia đình", "cả nhà", "có bé",
        "food tour", "tour ẩm thực",
        "chụp ảnh", "chụp hình", "golden hour",
    ],
    "crm": ["khách", "lead", "crm", "follow up"],
    "note": ["ghi chú", "note", "lưu thông tin"],
}

CREATE_MARKERS = ["thêm", "bổ sung", "tao", "tạo", "add", "create", "lưu"]
UPDATE_MARKERS = ["update", "cập nhật", "sửa", "đổi", "dời", "chỉnh"]
DELETE_MARKERS = ["xóa", "xoá", "remove", "delete"]
QUERY_MARKERS = ["bao nhiêu", "có", "tìm", "sao", "nào", "không", "hôm nay", "hôm qua"]
REFERENCE_PATTERNS = ["cái trên", "cái hôm qua", "task kia", "task này", "bill này", "khoản đó"]
INTENT_KEYWORDS = {
    "itinerary": [
        "lich trinh", "lich di", "lich hom nay", "lich ngay mai",
        "lich ngay", "ngay mai lam gi", "hom nay lam gi",
        "schedule", "itinerary", "ke hoach ngay",
    ],
    "food": [
        "an gi", "an dau", "quan an", "quan nao", "nha hang",
        "food", "restaurant", "dac san", "do an",
    ],
    "suggestion": [
        "goi y", "diem den", "co gi choi", "tham quan", "noi nao dep",
    ],
    "weather": [
        "thoi tiet", "troi", "mua khong", "nang khong",
        "forecast", "weather",
    ],
    "packing": [
        "phai dem", "can mang", "do can", "checklist", "danh sach do",
        "quen gi", "thieu gi",
    ],
    "contribution": [
        "ai gop", "gop tien", "dong bao nhieu", "share tien",
        "ung truoc", "phi ca nhan",
    ],
    "budget": [
        "ngan sach", "chi phi", "tong chi", "het bao nhieu",
        "tien con lai", "budget", "tong cong",
    ],
    "expense_query": [
        "chi tieu", "xem chi", "xem bill", "bill nao", "da chi",
    ],
    "summary": [
        "tong hop", "bao cao tong", "summary",
    ],
}


def heuristic_intent_parse(message_text: str, memory_summary: str = "") -> AssistantIntent:
    preprocessed = preprocess_intent_text(message_text)
    normalized = preprocessed.normalized_text
    intent_type = detect_intent_type(normalized)
    domain = detect_domain(normalized)
    extracted_fields = extract_common_fields(normalized, preprocessed)
    reply_style = build_reply_style(intent_type, domain, extracted_fields)
    confidence = 0.55
    if extracted_fields:
        confidence += 0.15
    if domain != "general":
        confidence += 0.1
    if memory_summary and any(phrase in normalized for phrase in REFERENCE_PATTERNS):
        confidence += 0.1

    intent = AssistantIntent(
        intent_type=intent_type,
        domain=domain,
        confidence=min(confidence, 0.95),
        normalized_text=normalized,
        extracted_fields=extracted_fields,
        missing_fields=missing_fields_for_intent(intent_type, domain, extracted_fields),
        reply_style=reply_style,
        action_name="",
    )
    intent.action_name = infer_action_name(intent)
    return intent


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def normalize_loose_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.strip().lower())
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c)).replace("đ", "d")
    return re.sub(r"\s+", " ", ascii_text)


def classify_travel_intent(text: str) -> str | None:
    normalized = normalize_loose_text(text)
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return intent
    return None


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


def extract_common_fields(text: str, preprocessed=None) -> dict[str, object]:
    fields: dict[str, object] = {}
    amount = preprocessed.money_amount if preprocessed else extract_amount(text)
    if amount is not None:
        fields["amount"] = amount

    date_ref = preprocessed.iso_date if preprocessed else extract_relative_date(text)
    if date_ref:
        fields["date"] = date_ref

    note = preprocessed.stripped_text if preprocessed else strip_amount_phrases(text)
    if note and note != text:
        fields["note"] = note

    category = infer_expense_category(text)
    if category:
        fields["category"] = category

    reference = extract_reference(text)
    if reference:
        fields["entity_reference"] = reference

    deadline = extract_deadline_reference(text)
    if deadline:
        fields["deadline"] = deadline

    if "entity_name" not in fields:
        for keyword in ["task", "cong viec"]:
            if keyword in text:
                entity_name = extract_named_entity_after_keyword(text, keyword)
                if entity_name:
                    fields["entity_name"] = entity_name
                    break

    if "inventory" in text or "tồn kho" in text:
        fields["sheet_hint"] = "inventory"
    if preprocessed and preprocessed.hints.get("continue_previous_flow"):
        fields["continue_previous_flow"] = True
    if preprocessed and preprocessed.hints.get("entity_reference"):
        fields["entity_reference"] = preprocessed.hints["entity_reference"]

    return fields


def extract_amount(text: str) -> int | None:
    return parse_money_amount(text)


def extract_relative_date(text: str) -> str | None:
    return parse_relative_date(text)


def strip_amount_phrases(text: str) -> str:
    return strip_money_phrases(text)


def infer_expense_category(text: str) -> str | None:
    if any(word in text for word in ["điện", "diện", "electricity"]):
        return "utilities_electricity"
    if any(word in text for word in ["sơn", "paint"]):
        return "materials_paint"
    if any(word in text for word in ["ăn", "uống", "cafe", "quán"]):
        return "food_and_beverage"
    if any(word in text for word in ["xăng", "grab", "taxi", "vé"]):
        return "transport"
    return None


def extract_reference(text: str) -> str | None:
    for pattern in REFERENCE_PATTERNS:
        if pattern in text:
            return pattern
    return None


def extract_deadline_reference(text: str) -> str | None:
    if not any(marker in text for marker in ["deadline", "dời", "sang", "đổi"]):
        return ""
    return extract_relative_date(text) or ""


def extract_named_entity_after_keyword(text: str, keyword: str) -> str | None:
    match = re.search(rf"{keyword}\s+([a-zA-Z0-9_\-\s]+?)(?:\s+(?:sang|thứ|hôm|mai|mốt|deadline|overdue|chưa|đã)|$)", text)
    if not match:
        return None
    candidate = match.group(1).strip(" -,:")
    return candidate or None


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
