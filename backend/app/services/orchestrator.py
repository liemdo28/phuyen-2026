from __future__ import annotations

from app.adapters.google_sheets import GoogleSheetsAdapter
from app.adapters.llm import LLMAdapter
from app.adapters.media import MediaAdapter
from app.adapters.telegram import TelegramAdapter
from app.schemas.telegram import TelegramUpdate
from app.services.action_logger import ActionLogger
from app.services.memory import MemoryService
from app.services.workflow_engine import WorkflowEngine


class TelegramOrchestrator:
    def __init__(self) -> None:
        self.memory = MemoryService()
        self.llm = LLMAdapter()
        self.media = MediaAdapter()
        self.telegram = TelegramAdapter()
        self.workflow = WorkflowEngine(GoogleSheetsAdapter())
        self.action_logger = ActionLogger()
        self._last_update_id: int | None = None

    async def handle_update(self, update: TelegramUpdate) -> None:
        if self._is_duplicate(update.update_id):
            return

        message = update.message
        if message is None:
            return

        user = message.from_user
        chat = message.chat
        context = await self.memory.get_context(chat_id=chat.id, user_id=user.id)

        incoming_text = await self._extract_message_text(message)
        if not incoming_text:
            await self.telegram.send_message(chat.id, "Mình đã nhận nội dung này, nhưng hiện chỉ mới xử lý tốt text/voice/ảnh theo pipeline AI mới.")
            return

        await self.action_logger.log("incoming_message", chat.id, user.id, {"text": incoming_text, "update_id": update.update_id})
        await self.memory.append_user_turn(context, incoming_text)
        memory_summary = self.memory.summarize(context)
        intent_result = await self.llm.detect_intent(incoming_text, memory_summary)
        await self.action_logger.log("intent_detected", chat.id, user.id, intent_result.intent.model_dump())
        response = await self.workflow.execute(intent_result.intent)

        if response.memory_updates:
            entity_type = intent_result.intent.domain or "general"
            entity_id = str(response.memory_updates.get("id", "latest"))
            await self.memory.store_entity(context, entity_type, entity_id, response.memory_updates)
            await self.action_logger.log("memory_entity_stored", chat.id, user.id, response.memory_updates)

        await self.memory.append_assistant_turn(context, response.text)
        await self.action_logger.log("assistant_response", chat.id, user.id, {"text": response.text})
        await self.telegram.send_message(chat.id, response.text)

    async def _extract_message_text(self, message) -> str:
        if message.text:
            return message.text
        if message.caption:
            return message.caption
        if message.voice:
            return await self.media.transcribe_voice(message.voice.file_id)
        if message.photo:
            ocr = await self.media.extract_receipt(message.photo[-1].file_id)
            return ocr.get("raw_text", "")
        if message.location:
            return f"User shared location {message.location.latitude},{message.location.longitude}"
        return ""

    def _is_duplicate(self, update_id: int) -> bool:
        if self._last_update_id is not None and update_id <= self._last_update_id:
            return True
        self._last_update_id = update_id
        return False
