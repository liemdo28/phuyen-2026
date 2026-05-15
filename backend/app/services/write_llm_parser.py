from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.core.config import settings
from app.services.write_rule_extractor import RuleExtractResult, rule_extract


@dataclass
class ParsedWrite:
    write_intent: str
    items: list[dict] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str = ""
    parse_source: str = "rule"
    error: str = ""


SYSTEM_PROMPT = """Bạn là parser cho bot ghi chép chuyến đi Phú Yên 2026 của một nhóm bạn.
Nhiệm vụ: đọc tin nhắn tiếng Việt (có thể không dấu, nhiều dòng, có URL) và trích xuất thông tin có cấu trúc để ghi vào Google Sheet.

Có 4 loại hành động ghi (write_intent):
1. "expense" — ghi một khoản chi tiêu
2. "packing" — đánh dấu đồ đã đem (đã chuẩn bị)
3. "contribution" — cập nhật một nhóm đã góp/chuyển tiền
4. "restaurant" — thêm một quán ăn mới vào danh sách

Với expense mỗi item gồm: khoan_chi, so_tien, danh_muc, ngay, nhom, ghi_chu.
Với packing mỗi item gồm: ten_do.
Với contribution mỗi item gồm: nhom, so_tien, trang_thai.
Với restaurant mỗi item gồm: ten_quan, khu_vuc, loai, gia_k, ghi_chu.

Nếu không đủ thông tin tối thiểu, đặt needs_clarification=true và viết clarification_question.
Nếu không phải hành động ghi, trả write_intent="unknown".
Chỉ trả JSON.
"""


def _build_user_prompt(text: str, rule: RuleExtractResult) -> str:
    hints = []
    if rule.write_intent != "unknown":
        hints.append(f"- rule đoán loại: {rule.write_intent}")
    if rule.amount is not None:
        hints.append(f"- rule bóc được số tiền: {rule.amount}")
    if rule.category:
        hints.append(f"- rule đoán danh mục: {rule.category}")
    if rule.group:
        hints.append(f"- rule đoán nhóm: {rule.group}")
    if rule.iso_date:
        hints.append(f"- rule bóc được ngày: {rule.iso_date}")
    if rule.urls:
        hints.append(f"- có {len(rule.urls)} URL (đưa vào ghi chú)")
    hint_block = "\n".join(hints) if hints else "(rule không bóc được gì rõ ràng)"
    return f"TIN NHẮN:\n{text}\n\nGỢI Ý TỪ RULE:\n{hint_block}"


async def _call_openai(text: str, rule: RuleExtractResult) -> dict:
    from openai import AsyncOpenAI

    if not settings.openai_api_key:
        raise RuntimeError("Chưa cấu hình OPENAI_API_KEY.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(text, rule)},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def _rule_only_parse(text: str, rule: RuleExtractResult) -> ParsedWrite:
    if rule.write_intent == "expense" and rule.amount is not None:
        khoan_chi = ""
        ghi_chu_parts = []
        for ln in rule.lines:
            if ln.startswith("http"):
                ghi_chu_parts.append(ln)
            elif rule.amount and str(rule.amount) in ln.replace(",", "").replace(".", ""):
                continue
            elif not khoan_chi:
                khoan_chi = ln
            else:
                ghi_chu_parts.append(ln)
        return ParsedWrite(
            write_intent="expense",
            items=[{
                "khoan_chi": khoan_chi or "Khoản chi",
                "so_tien": rule.amount,
                "danh_muc": rule.category or "📦 Khác",
                "ngay": rule.iso_date or "",
                "nhom": rule.group or "",
                "ghi_chu": " | ".join(ghi_chu_parts),
            }],
            parse_source="rule",
        )
    return ParsedWrite(
        write_intent=rule.write_intent,
        needs_clarification=True,
        clarification_question="Mình chưa chắc hiểu đúng tin nhắn này. Bạn ghi rõ hơn giúp mình nhé (vd: '500k ăn tối', 'đã đem ô và thuốc', 'nhóm CM đã chuyển 15tr').",
        parse_source="rule",
    )


async def parse_write_message(text: str) -> ParsedWrite:
    text = (text or "").strip()
    if not text:
        return ParsedWrite(write_intent="unknown")

    rule = rule_extract(text)
    try:
        llm_out = await _call_openai(text, rule)
    except Exception as exc:
        result = _rule_only_parse(text, rule)
        if not result.error:
            result.error = f"LLM fallback: {exc}"
        return result

    write_intent = llm_out.get("write_intent", "unknown")
    items = llm_out.get("items", []) or []
    needs_clarification = bool(llm_out.get("needs_clarification", False))
    clarification = llm_out.get("clarification_question", "")

    if write_intent == "unknown" and rule.amount is not None:
        return _rule_only_parse(text, rule)

    return ParsedWrite(
        write_intent=write_intent,
        items=items,
        needs_clarification=needs_clarification or (not items and write_intent != "unknown"),
        clarification_question=clarification,
        parse_source="hybrid",
    )
