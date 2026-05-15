from __future__ import annotations

import asyncio
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

═══ QUAN TRỌNG — TRƯỜNG TỐI THIỂU ═══
Mỗi loại chỉ cần các trường TỐI THIỂU sau là ĐỦ để ghi, KHÔNG được đòi thêm:
  - expense:      khoan_chi + so_tien   (ngày/nhóm/danh mục TÙY CHỌN, đoán được thì điền, không thì để trống/mặc định)
  - packing:      ten_do
  - contribution: nhom
  - restaurant:   ten_quan

CHỈ đặt needs_clarification=true khi THỰC SỰ THIẾU trường tối thiểu.
VÍ DỤ:
  ✅ "600k ăn tối"          → đủ (khoan_chi="Ăn tối", so_tien=600000). KHÔNG hỏi lại ngày/nhóm.
  ✅ "500k"                 → THIẾU khoan_chi → hỏi lại
  ✅ "ăn tối"               → THIẾU so_tien → hỏi lại
  ✅ "đã đem ô"             → đủ (ten_do="Ô"). KHÔNG hỏi gì thêm.
  ✅ "Nhóm CM đã chuyển"    → đủ (nhom="Nhóm CM"). KHÔNG đòi số tiền.

═══ CHI TIẾT TỪNG LOẠI ═══

[expense] mỗi item gồm:
  - khoan_chi: tên khoản chi NGẮN GỌN (vd "Sun Village Resort", "Ăn tối", "Đổ xăng")
  - so_tien: số nguyên VNĐ
  - danh_muc: chọn ĐÚNG 1 trong: "🏨 Lưu trú", "🍜 Ăn uống", "🚗 Di chuyển", "⛽ Xăng dầu", "🎡 Vui chơi", "🛒 Mua sắm", "💊 Y tế", "📦 Khác". Nếu không chắc → "📦 Khác".
  - ngay: ISO yyyy-MM-dd nếu tin có nhắc ngày, KHÔNG có thì để "" (KHÔNG hỏi user).
  - nhom: "Nhóm LV" / "Nhóm LH" / "Nhóm CM" nếu tin có nhắc, KHÔNG có thì để "" (KHÔNG hỏi).
  - ghi_chu: MỌI chi tiết phụ — URL, mô tả phòng, số lượng, điều kiện... gộp hết vào đây
  Nếu tin có nhiều khoản chi (vd "1.5tr phòng, 200k cafe"), tách thành nhiều item.

[packing] mỗi item gồm:
  - ten_do: tên món đồ (vd "Kem chống nắng", "Thuốc hạ sốt", "Ô")
  Tách mỗi món thành 1 item. Khớp gần đúng với tên trong danh sách là được.

[contribution] mỗi item gồm:
  - nhom: "Nhóm LV" / "Nhóm LH" / "Nhóm CM"
  - so_tien: số nguyên VNĐ (TÙY CHỌN — nếu không có để 0)
  - trang_thai: "Đã chuyển" hoặc "Chưa góp" (mặc định "Đã chuyển" nếu tin có chữ "chuyển/góp")

[restaurant] mỗi item gồm:
  - ten_quan: tên quán
  - khu_vuc: TÙY CHỌN
  - loai: TÙY CHỌN
  - gia_k: TÙY CHỌN, mặc định 0
  - ghi_chu: chi tiết khác

═══ NHÓM (cho expense) ═══
"Liêm/Liem/liemdo" = Nhóm LV. Các tên khác suy theo ngữ cảnh, không chắc thì để "".

═══ GHÉP CÂU TRẢ LỜI CLARIFICATION ═══
Nếu USER PROMPT chứa "[CÂU GỐC]: ... [BỔ SUNG]: ...", bạn phải GHÉP cả 2 phần,
hiểu BỔ SUNG là user trả lời câu hỏi bạn đã hỏi về CÂU GỐC. Trích xuất từ
tổng hợp 2 phần. KHÔNG hỏi lại lần nữa.

═══ NẾU KHÔNG PHẢI HÀNH ĐỘNG GHI ═══
Tin là câu hỏi, chào hỏi, hoặc không liên quan ghi chép → write_intent="unknown".

═══ FORMAT OUTPUT ═══
CHỈ trả JSON, không markdown, không giải thích:
{"write_intent": "...", "needs_clarification": false, "clarification_question": "", "items": [...]}
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
    async with asyncio.timeout(8):
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


def _should_short_circuit_to_rule(rule: RuleExtractResult) -> bool:
    if rule.write_intent != "expense" or rule.amount is None:
        return False
    # Expense cases with amount + a strong hint are cheap and reliable enough
    # to parse locally, especially when the message contains long URLs.
    if rule.urls:
        return True
    if rule.category or rule.group or rule.iso_date:
        return True
    return rule.confidence >= 0.6


async def parse_write_message(text: str) -> ParsedWrite:
    text = (text or "").strip()
    if not text:
        return ParsedWrite(write_intent="unknown")

    rule = rule_extract(text)
    if _should_short_circuit_to_rule(rule):
        return _rule_only_parse(text, rule)

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
