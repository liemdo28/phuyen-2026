from __future__ import annotations

from app.adapters.google_sheets import GoogleSheetsAdapter, SheetsActionResult
from app.schemas.assistant import AssistantIntent, AssistantResponse
from app.services.travel_companion import TravelCompanionState


class WorkflowEngine:
    def __init__(self, sheets_adapter: GoogleSheetsAdapter) -> None:
        self.sheets = sheets_adapter

    async def execute(self, intent: AssistantIntent, companion_state: TravelCompanionState | None = None) -> AssistantResponse:
        if intent.intent_type == "create":
            return await self._handle_create(intent)
        if intent.intent_type == "update":
            return await self._handle_update(intent)
        if intent.intent_type == "query":
            return await self._handle_query(intent, companion_state)
        if intent.intent_type == "delete":
            return AssistantResponse(text="Mình hiểu ý xoá rồi, nhưng backend xoá cứng chưa được bật ở môi trường này.")
        return AssistantResponse(text=self._chat_reply(intent, companion_state))

    async def _handle_create(self, intent: AssistantIntent) -> AssistantResponse:
        domain = normalize_domain(intent.domain)
        result = await self.sheets.create_record(domain, intent.extracted_fields)
        return build_sheet_response(result, success_text="Mình đã lưu thông tin rồi.")

    async def _handle_update(self, intent: AssistantIntent) -> AssistantResponse:
        domain = normalize_domain(intent.domain)
        result = await self.sheets.update_latest_record(domain, intent.extracted_fields)
        if not result.success:
            return AssistantResponse(text="Mình chưa thấy bản ghi phù hợp để cập nhật. Nếu bạn muốn, mình có thể tạo mới luôn.")
        return build_sheet_response(result, success_text="Mình đã cập nhật lại giúp bạn.")

    async def _handle_query(self, intent: AssistantIntent, companion_state: TravelCompanionState | None = None) -> AssistantResponse:
        domain = normalize_domain(intent.domain)
        result = await self.sheets.query_records(domain, {})
        if domain == "travel":
            return AssistantResponse(text=self._travel_reply(intent, companion_state))
        if not result.rows:
            return AssistantResponse(text="Hiện mình chưa thấy dữ liệu phù hợp trong ngữ cảnh này.")
        return AssistantResponse(text=f"Mình tìm thấy {len(result.rows)} mục gần nhất trong nhóm {domain}.", action_summary=result.message)

    def _chat_reply(self, intent: AssistantIntent, companion_state: TravelCompanionState | None = None) -> str:
        if intent.domain == "travel":
            return self._travel_reply(intent, companion_state)
        return "Mình hiểu ý bạn. Backend AI đã nhận được ngữ cảnh này và có thể chuyển nó thành workflow phù hợp."

    def _travel_reply(self, intent: AssistantIntent, companion_state: TravelCompanionState | None = None) -> str:
        if companion_state and companion_state.response_mode == "comfort":
            return (
                "Mình sẽ ưu tiên phương án nhẹ nhàng và ít đổi chỗ cho bạn. "
                "Nếu bạn gửi khu vực hiện tại hoặc nói rõ đang cần ăn, nghỉ hay tránh mưa, mình sẽ chốt gọn 1-2 lựa chọn dễ đi nhất."
            )
        if companion_state and companion_state.response_mode == "energize":
            return (
                "Mood này hợp đi khám phá hơn đó. "
                "Nếu bạn muốn, mình sẽ gợi ý thêm quán chill, góc chụp đẹp, điểm ngắm hoàng hôn hoặc hidden spot gần khu bạn đang đứng."
            )
        return (
            "Mình hiểu câu hỏi theo hướng travel assistant. "
            "Bạn cứ nói tự nhiên như đang hỏi một người local: cần ăn gì, đi đâu, tránh mưa, ngắm hoàng hôn hay muốn lịch trình nhẹ hơn."
        )


def normalize_domain(domain: str) -> str:
    mapping = {
        "note": "notes",
        "expense": "expenses",
        "task": "tasks",
        "inventory": "inventory",
        "revenue": "revenue",
        "travel": "travel",
        "crm": "crm",
        "general": "notes",
    }
    return mapping.get(domain, "notes")


def build_sheet_response(result: SheetsActionResult, success_text: str) -> AssistantResponse:
    if not result.success:
        return AssistantResponse(text=result.message)
    row = result.rows[0] if result.rows else {}
    natural_text = build_human_confirmation(row, fallback=success_text)
    return AssistantResponse(
        text=natural_text,
        action_summary=result.message,
        memory_updates=row,
    )


def build_human_confirmation(row: dict[str, object], fallback: str) -> str:
    amount = row.get("amount")
    note = row.get("note") or row.get("entity_name") or row.get("category")
    domain_sheet = row.get("sheet_name")
    if amount and note:
        return f"Đã cập nhật {note} với số tiền {format_vnd(int(amount))}."
    if domain_sheet and note:
        return f"Đã cập nhật {note} trong sheet {domain_sheet}."
    return fallback


def format_vnd(amount: int) -> str:
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f} tỷ".replace(".0", "")
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f} triệu".replace(".0", "")
    if amount >= 1_000:
        return f"{amount / 1_000:.0f}k"
    return f"{amount:,}đ".replace(",", ".")
