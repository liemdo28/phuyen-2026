from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.adapters.sheets_api_client import SheetsApiClient, SheetsApiError
from app.services.write_llm_parser import ParsedWrite, parse_write_message


YES_WORDS = {"y", "yes", "co", "có", "ok", "oke", "okay", "đúng", "dung", "ừ", "u", "uh", "ghi", "lưu", "luu", "xác nhận", "xac nhan", "👍", "✅"}
NO_WORDS = {"n", "no", "không", "khong", "huỷ", "huy", "hủy", "thôi", "thoi", "sai", "bỏ", "bo", "cancel", "❌"}
PENDING_TTL_SECONDS = 600


@dataclass
class PendingWrite:
    parsed: ParsedWrite
    created_at: float = field(default_factory=time.time)
    mode: str = "confirm"
    original_text: str = ""

    @property
    def expired(self) -> bool:
        return (time.time() - self.created_at) > PENDING_TTL_SECONDS


def _fmt_vnd(amount) -> str:
    amount = int(amount or 0)
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}tr".replace(".0tr", "tr")
    if amount >= 1_000:
        return f"{amount / 1_000:.0f}k"
    return f"{amount:,}đ".replace(",", ".")


class WriteFlowHandler:
    def __init__(self, sheets: SheetsApiClient | None = None) -> None:
        self.sheets = sheets or SheetsApiClient()
        self._pending: dict[tuple[int, int], PendingWrite] = {}

    async def handle(self, text: str, chat_id: int, user_id: int) -> str | None:
        text = (text or "").strip()
        if not text:
            return None

        key = (chat_id, user_id)
        pending = self._pending.get(key)

        if pending and pending.expired:
            self._pending.pop(key, None)
            pending = None

        if pending and pending.mode == "confirm":
            decision = self._interpret_yes_no(text)
            if decision == "yes":
                self._pending.pop(key, None)
                return await self._commit(pending.parsed)
            if decision == "no":
                self._pending.pop(key, None)
                return "Đã huỷ, không ghi gì cả. Bạn gửi lại khi cần nhé."
            self._pending.pop(key, None)

        if pending and pending.mode == "clarify":
            self._pending.pop(key, None)
            merged_text = f"[CÂU GỐC]: {pending.original_text}\n[BỔ SUNG]: {text}"
            parsed = await parse_write_message(merged_text)
            if parsed.needs_clarification or not parsed.items:
                return (
                    "Mình vẫn chưa parse được. Bạn gõ lại đầy đủ giúp mình nhé, vd:\n"
                    "• \"500k ăn tối\"\n"
                    "• \"24/5 - 300k xăng nhóm LV trả\""
                )
            self._pending[key] = PendingWrite(parsed=parsed, mode="confirm")
            return self._build_preview(parsed)

        parsed = await parse_write_message(text)
        if parsed.write_intent == "unknown":
            return None
        if parsed.needs_clarification:
            self._pending[key] = PendingWrite(
                parsed=parsed,
                mode="clarify",
                original_text=text,
            )
            question = parsed.clarification_question or "Bạn ghi rõ hơn giúp mình nhé."
            return f"🤔 {question}"
        if not parsed.items:
            return None

        self._pending[key] = PendingWrite(parsed=parsed, mode="confirm")
        return self._build_preview(parsed)

    def _interpret_yes_no(self, text: str) -> str:
        t = text.strip().lower()
        if t in YES_WORDS or any(t.startswith(w) for w in YES_WORDS if len(w) > 1):
            return "yes"
        if t in NO_WORDS or any(t.startswith(w) for w in NO_WORDS if len(w) > 1):
            return "no"
        return "other"

    def _build_preview(self, parsed: ParsedWrite) -> str:
        intent = parsed.write_intent
        lines = []
        if intent == "expense":
            lines += ["📝 Mình hiểu đây là khoản chi tiêu:", ""]
            for idx, it in enumerate(parsed.items, 1):
                prefix = f"{idx}. " if len(parsed.items) > 1 else ""
                lines.append(f"{prefix}💰 {it.get('khoan_chi', '?')}")
                lines.append(f"   • Số tiền: {_fmt_vnd(it.get('so_tien'))}")
                lines.append(f"   • Danh mục: {it.get('danh_muc', '📦 Khác')}")
                if it.get("ngay"):
                    lines.append(f"   • Ngày: {it['ngay']}")
                if it.get("nhom"):
                    lines.append(f"   • Nhóm trả: {it['nhom']}")
                if it.get("ghi_chu"):
                    gc = it["ghi_chu"]
                    lines.append(f"   • Ghi chú: {gc if len(gc) <= 80 else gc[:80] + '...'}")
        elif intent == "packing":
            lines += ["📦 Mình sẽ đánh dấu ĐÃ ĐEM các món:", ""]
            for it in parsed.items:
                lines.append(f"   ✓ {it.get('ten_do', '?')}")
        elif intent == "contribution":
            lines += ["💵 Mình sẽ cập nhật góp tiền:", ""]
            for it in parsed.items:
                line = f"   • {it.get('nhom', '?')}"
                if it.get("so_tien"):
                    line += f": {_fmt_vnd(it['so_tien'])}"
                line += f" — {it.get('trang_thai', 'Đã chuyển')}"
                lines.append(line)
        elif intent == "restaurant":
            lines += ["🍜 Mình sẽ thêm quán ăn mới:", ""]
            for it in parsed.items:
                lines.append(f"   • {it.get('ten_quan', '?')}")
                detail = []
                if it.get("khu_vuc"):
                    detail.append(it["khu_vuc"])
                if it.get("loai"):
                    detail.append(it["loai"])
                if it.get("gia_k"):
                    detail.append(f"~{it['gia_k']}k/người")
                if detail:
                    lines.append(f"     {' · '.join(detail)}")
                if it.get("ghi_chu"):
                    lines.append(f"     💬 {it['ghi_chu']}")
        lines += ["", "👉 Ghi vào Sheet chứ? Trả lời: có / không"]
        return "\n".join(lines)

    async def _commit(self, parsed: ParsedWrite) -> str:
        try:
            if parsed.write_intent == "expense":
                return await self._commit_expense(parsed.items)
            if parsed.write_intent == "packing":
                return await self._commit_packing(parsed.items)
            if parsed.write_intent == "contribution":
                return await self._commit_contribution(parsed.items)
            if parsed.write_intent == "restaurant":
                return await self._commit_restaurant(parsed.items)
            return "Có gì đó không đúng — mình không ghi được loại này."
        except SheetsApiError as exc:
            return f"❌ Ghi vào Sheet thất bại 😔\n({exc})\nBạn thử lại sau một chút nhé. Dữ liệu CHƯA được lưu."

    async def _commit_expense(self, items: list[dict]) -> str:
        ok_count, total = 0, 0
        for it in items:
            res = await self.sheets.write_expense(it)
            if res.get("ok"):
                ok_count += 1
                total += int(it.get("so_tien") or 0)
        if ok_count == len(items):
            if ok_count == 1:
                return f"✅ Đã ghi: {items[0].get('khoan_chi')} — {_fmt_vnd(total)}"
            return f"✅ Đã ghi {ok_count} khoản, tổng {_fmt_vnd(total)}"
        return f"⚠️ Ghi được {ok_count}/{len(items)} khoản. Phần còn lại bị lỗi, bạn thử lại."

    async def _commit_packing(self, items: list[dict]) -> str:
        done, not_found = [], []
        for it in items:
            res = await self.sheets.write_packing(it)
            if res.get("ok"):
                done.append(res.get("written", {}).get("item", it.get("ten_do")))
            else:
                not_found.append(it.get("ten_do"))
        msg = []
        if done:
            msg.append(f"✅ Đã đánh dấu đã đem: {', '.join(done)}")
        if not_found:
            msg.append(f"⚠️ Không tìm thấy trong danh sách: {', '.join(not_found)}")
            msg.append("(Tên phải gần khớp với món trong sheet Phải Đem)")
        return "\n".join(msg) if msg else "Không có món nào được cập nhật."

    async def _commit_contribution(self, items: list[dict]) -> str:
        ok = []
        for it in items:
            res = await self.sheets.write_contribution(it)
            if res.get("ok"):
                w = res.get("written", {})
                ok.append(f"{w.get('group')} — {w.get('trang_thai')}")
        if ok:
            return "✅ Đã cập nhật góp tiền:\n" + "\n".join(f"   • {x}" for x in ok)
        return "⚠️ Không cập nhật được. Kiểm tra lại tên nhóm (Nhóm LV/LH/CM)."

    async def _commit_restaurant(self, items: list[dict]) -> str:
        ok = []
        for it in items:
            res = await self.sheets.write_restaurant(it)
            if res.get("ok"):
                ok.append(it.get("ten_quan"))
        if ok:
            return f"✅ Đã thêm quán: {', '.join(ok)}"
        return "⚠️ Không thêm được quán. Bạn thử lại nhé."
