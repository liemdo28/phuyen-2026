from __future__ import annotations

from app.adapters.google_sheets import GoogleSheetsAdapter, SheetsActionResult
from app.schemas.assistant import AssistantIntent, AssistantResponse


class WorkflowEngine:
    def __init__(self, sheets_adapter: GoogleSheetsAdapter) -> None:
        self.sheets = sheets_adapter

    async def execute(self, intent: AssistantIntent) -> AssistantResponse:
        if intent.intent_type == "create":
            return await self._handle_create(intent)
        if intent.intent_type == "update":
            return await self._handle_update(intent)
        if intent.intent_type == "query":
            return await self._handle_query(intent)
        if intent.intent_type == "delete":
            return AssistantResponse(text="Mình hiểu ý xoá rồi, nhưng backend xoá cứng chưa được bật ở môi trường này.")
        return AssistantResponse(text=self._chat_reply(intent))

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

    async def _handle_query(self, intent: AssistantIntent) -> AssistantResponse:
        domain = normalize_domain(intent.domain)
        result = await self.sheets.query_records(domain, {})
        if domain == "travel":
            return AssistantResponse(text="Mình có thể trả lời thời tiết, lịch trình, quán ăn và địa điểm gần bạn khi đã nối API thật.")
        if not result.rows:
            return AssistantResponse(text="Hiện mình chưa thấy dữ liệu phù hợp trong ngữ cảnh này.")
        return AssistantResponse(text=f"Mình tìm thấy {len(result.rows)} mục gần nhất trong nhóm {domain}.", action_summary=result.message)

    def _chat_reply(self, intent: AssistantIntent) -> str:
        if intent.domain == "travel":
            return "Mình hiểu câu hỏi theo hướng travel assistant. Khi nối API thật, mình sẽ trả lời thời tiết, quán ăn và lịch trình theo vị trí hiện tại."
        return "Mình hiểu ý bạn. Backend AI đã nhận được ngữ cảnh này và có thể chuyển nó thành workflow phù hợp."


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
    return AssistantResponse(
        text=success_text,
        action_summary=result.message,
        memory_updates=result.rows[0] if result.rows else {},
    )

