from __future__ import annotations

from app.adapters.google_sheets import GoogleSheetsAdapter
from app.adapters.llm import LLMAdapter
from app.adapters.media import MediaAdapter
from app.adapters.telegram import TelegramAdapter
from app.schemas.telegram import TelegramUpdate
from app.services.action_logger import ActionLogger
from app.services.loop_guard import LoopGuard
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
        self.loop_guard = LoopGuard()

    async def handle_update(self, update: TelegramUpdate) -> None:
        message = update.message
        if message is None:
            return

        user = message.from_user
        if self._should_ignore_message(message):
            await self.action_logger.log(
                "ignored_message",
                message.chat.id,
                user.id if user else 0,
                {
                    "update_id": update.update_id,
                    "message_id": message.message_id,
                    "is_bot": getattr(user, "is_bot", False),
                    "text": message.text or message.caption or "",
                },
            )
            return

        chat = message.chat
        incoming_text = await self._extract_message_text(message)
        decision = self.loop_guard.evaluate(
            update_id=update.update_id,
            message_id=message.message_id,
            chat_id=chat.id,
            user_id=user.id,
            text=incoming_text,
        )
        await self.action_logger.log(
            "update_received",
            chat.id,
            user.id,
            {
                "update_id": update.update_id,
                "message_id": message.message_id,
                "text": incoming_text,
                "from_user_id": user.id,
                "from_user_is_bot": user.is_bot,
                "decision": decision.reason,
            },
        )
        if not decision.allow_processing:
            return

        context = await self.memory.get_context(chat_id=chat.id, user_id=user.id)
        if not incoming_text:
            if decision.allow_reply:
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
        if decision.allow_reply:
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

    def _should_ignore_message(self, message) -> bool:
        user = message.from_user
        if user is None or user.is_bot:
            return True
        if message.via_bot is not None:
            return True
        if message.new_chat_members or message.left_chat_member:
            return True
        if message.group_chat_created or message.supergroup_chat_created or message.channel_chat_created:
            return True
        return False
