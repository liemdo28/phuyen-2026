from __future__ import annotations

from app.ai.context_resolver import build_context_snapshot
from app.ai.entity_resolver import resolve_entity_reference
from app.ai.workflow_reasoner import build_workflow_reasoning
from app.adapters.google_sheets import GoogleSheetsAdapter
from app.adapters.llm import LLMAdapter
from app.adapters.media import MediaAdapter
from app.adapters.telegram import TelegramAdapter
from app.orchestration.travel_operating_system import TravelOperatingSystem
from app.schemas.assistant import AssistantIntent, AssistantResponse
from app.schemas.telegram import TelegramUpdate
from app.services.action_logger import ActionLogger
from app.services.command_handlers import CommandHandlers
from app.services.loop_guard import LoopGuard
from app.services.memory import MemoryService
from app.services.travel_companion import TravelCompanionEngine
from app.services.trip_context import TripContextService
from app.services.write_flow_handler import WriteFlowHandler
from app.services.workflow_engine import WorkflowEngine

# Domains routed to sheets workflow (not companion AI)
_STRUCTURED_DOMAINS = {"expense", "task", "inventory", "revenue", "crm"}
_STRUCTURED_ACTIONS = {"create", "update", "delete"}


class TelegramOrchestrator:
    def __init__(self) -> None:
        self.memory = MemoryService()
        self.llm = LLMAdapter()
        self.media = MediaAdapter()
        self.telegram = TelegramAdapter()
        self.workflow = WorkflowEngine(GoogleSheetsAdapter())
        self.action_logger = ActionLogger()
        self.loop_guard = LoopGuard()
        self.commands = CommandHandlers()
        self.write_flow = WriteFlowHandler()
        self.companion = TravelCompanionEngine()
        self.trip_context = TripContextService()
        self.travel_os = TravelOperatingSystem()

    async def handle_update(self, update: TelegramUpdate) -> None:
        message = update.message
        if message is None:
            return

        user = message.from_user
        chat = message.chat
        incoming_text = ""
        decision = None
        try:
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

            command_reply = await self.commands.handle(incoming_text.strip(), message)
            if command_reply is not None:
                await self.action_logger.log("command_response", chat.id, user.id, {"text": incoming_text, "reply": command_reply})
                if decision.allow_reply:
                    await self.telegram.send_message(chat.id, command_reply)
                return

            write_reply = await self.write_flow.handle(incoming_text, chat.id, user.id)
            if write_reply is not None:
                await self.action_logger.log("write_flow_response", chat.id, user.id, {"text": incoming_text, "reply": write_reply})
                if decision.allow_reply:
                    await self.telegram.send_message(chat.id, write_reply)
                return

            await self.action_logger.log("incoming_message", chat.id, user.id, {"text": incoming_text, "update_id": update.update_id})
            await self.memory.append_user_turn(context, incoming_text)

            # Emotional state assessment (TravelCompanionEngine)
            pre_intent_state = self.companion.assess(context, incoming_text)
            await self.memory.update_preferences(context, self._build_preference_updates(pre_intent_state))
            await self.action_logger.log(
                "travel_companion_state",
                chat.id,
                user.id,
                {
                    "stage": "pre_intent",
                    "mood": pre_intent_state.mood,
                    "stress": pre_intent_state.stress,
                    "excitement": pre_intent_state.excitement,
                    "fatigue": pre_intent_state.fatigue,
                    "confusion": pre_intent_state.confusion,
                    "overwhelm": pre_intent_state.overwhelm,
                    "response_mode": pre_intent_state.response_mode,
                    "signals": pre_intent_state.signals,
                    "proactive_hints": pre_intent_state.proactive_hints,
                },
            )

            memory_summary = self.memory.summarize(context)
            intent_result = await self.llm.detect_intent(incoming_text, memory_summary)
            intent_result.intent.extracted_fields = resolve_entity_reference(context, intent_result.intent.extracted_fields)
            companion_state = self.companion.assess(context, incoming_text, intent=intent_result.intent)
            await self.memory.update_preferences(context, self._build_preference_updates(companion_state))
            workflow_reasoning = build_workflow_reasoning(intent_result.intent)
            await self.action_logger.log("intent_detected", chat.id, user.id, intent_result.intent.model_dump())
            await self.action_logger.log(
                "workflow_reasoning",
                chat.id,
                user.id,
                workflow_reasoning
                | {
                    "context": build_context_snapshot(context),
                    "travel_companion": {
                        "mood": companion_state.mood,
                        "response_mode": companion_state.response_mode,
                        "signals": companion_state.signals,
                        "proactive_hints": companion_state.proactive_hints,
                    },
                },
            )

            # Phase 6-8: Full Travel Intelligence assessment for all message types
            tos_state = self.travel_os.assess(
                context,
                incoming_text,
                companion_state,
                intent_result.intent,
            )
            await self.memory.update_preferences(context, tos_state.preference_updates)

            if _is_companion_mode(intent_result.intent):
                # Travel/chat/general → OpenAI with trip context + emotional state
                response = await self._companion_reply(incoming_text, context, companion_state)
                # Enrich reply with Phase 6-8 intelligence (emotional journey, life context, etc.)
                response.text = self.travel_os.enhance_reply(response.text, tos_state, intent_result.intent)
            else:
                # Structured action (expense/task/etc.) → sheets workflow
                response = await self.workflow.execute(intent_result.intent, companion_state=companion_state)
                response.text = self.companion.adapt_reply(response.text, companion_state, intent=intent_result.intent)

            if response.memory_updates:
                entity_type = intent_result.intent.domain or "general"
                entity_id = str(response.memory_updates.get("id", "latest"))
                await self.memory.store_entity(context, entity_type, entity_id, response.memory_updates)
                await self.action_logger.log("memory_entity_stored", chat.id, user.id, response.memory_updates)

            await self.memory.append_assistant_turn(context, response.text)
            await self.action_logger.log("assistant_response", chat.id, user.id, {"text": response.text})
            if decision.allow_reply:
                await self.telegram.send_message(chat.id, response.text)
        except Exception as exc:
            await self.action_logger.log(
                "orchestrator_exception",
                chat.id,
                user.id if user else 0,
                {
                    "update_id": update.update_id,
                    "message_id": message.message_id,
                    "text": incoming_text,
                    "error": str(exc),
                },
            )
            if decision is None or decision.allow_reply:
                try:
                    await self.telegram.send_message(
                        chat.id,
                        "Mình vừa gặp lỗi khi xử lý tin nhắn này. Bạn thử gửi lại ngắn gọn hơn hoặc đợi mình một chút nhé.",
                    )
                except Exception:
                    pass

    async def _companion_reply(self, message_text: str, context, companion_state) -> AssistantResponse:
        trip_state = self.trip_context.get_state()
        trip_context_str = self.trip_context.format_for_prompt(trip_state, companion_state=companion_state)
        conversation_history = _context_to_messages(context)
        reply = await self.llm.generate_companion_reply(
            message_text,
            conversation_history,
            trip_context_str,
        )
        return AssistantResponse(text=reply)

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

    def _build_preference_updates(self, state) -> dict[str, object]:
        updates: dict[str, object] = {
            "last_detected_mood": state.mood,
            "last_response_mode": state.response_mode,
        }
        if "slow_exploration_interest" in state.signals:
            updates["prefers_slow_exploration"] = True
        if "weather_context" in state.signals:
            updates["weather_sensitive"] = True
        if "transport_context" in state.signals:
            updates["transport_sensitive"] = True
        return updates


def _is_companion_mode(intent: AssistantIntent) -> bool:
    """True if message should go to AI companion rather than sheets workflow."""
    if intent.intent_type in _STRUCTURED_ACTIONS and intent.domain in _STRUCTURED_DOMAINS:
        return False
    return True


def _context_to_messages(context) -> list[dict[str, str]]:
    """Convert UserContext conversation to OpenAI message format, excluding current turn."""
    messages = []
    for turn in context.conversation[:-1]:
        role = "user" if turn.role == "user" else "assistant"
        messages.append({"role": role, "content": turn.text})
    return messages
