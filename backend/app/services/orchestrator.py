from __future__ import annotations

from datetime import datetime

from app.ai.context_resolver import build_context_snapshot
from app.ai.entity_resolver import resolve_entity_reference
from app.ai.workflow_reasoner import build_workflow_reasoning
from app.adapters.google_sheets import GoogleSheetsAdapter
from app.adapters.llm import LLMAdapter
from app.adapters.media import MediaAdapter
from app.adapters.telegram import TelegramAdapter
from app.ethics.calm_technology import CalmTechnologyPolicy
from app.orchestration.travel_brain import TravelBrain
from app.orchestration.travel_operating_system import TravelOperatingSystem
from app.recovery.recovery_engine import RecoveryEngine
from app.schemas.assistant import AssistantIntent, AssistantResponse
from app.schemas.telegram import TelegramUpdate
from app.services.action_logger import ActionLogger
from app.services.command_handlers import CommandHandlers
from app.services.loop_guard import LoopGuard
from app.services.memory import MemoryService
from app.services.maps_service import build_telegram_keyboard, find_place
from app.services.travel_companion import TravelCompanionEngine
from app.services.trip_context import TripContextService
from app.services.write_flow_handler import WriteFlowHandler
from app.nlp.conversation_merger import ConversationMerger, MergedIntent
from app.services.workflow_engine import WorkflowEngine
from app.society.agent_society import TravelAgentSociety

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
        # Phase 5: Autonomous Travel Operating System
        self.travel_os = TravelOperatingSystem()
        self.travel_brain = TravelBrain()
        self.calm_policy = CalmTechnologyPolicy()
        self.recovery = RecoveryEngine()
        self.agent_society = TravelAgentSociety()
        # Phase: Human Chaos NLP — multi-message conversation merger
        self.merger = ConversationMerger()

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

            # Human Chaos NLP: merge fragmented multi-message conversations
            merged_intent: MergedIntent = self.merger.merge(
                chat.id, incoming_text, datetime.now()
            )

            command_reply = await self.commands.handle(incoming_text.strip(), message)
            if command_reply is not None:
                await self.action_logger.log("command_response", chat.id, user.id, {"text": incoming_text, "reply": command_reply})
                if decision.allow_reply:
                    await self.telegram.send_message(chat.id, command_reply)
                return

            write_reply = await self.write_flow.handle(incoming_text, chat.id, user.id)
            if write_reply is not None:
                await self.action_logger.log("write_flow_response", chat.id, user.id, {"text": incoming_text, "reply": write_reply})
                soft_confirm = merged_intent.soft_confirmation_text()
                if soft_confirm and decision.allow_reply:
                    await self.telegram.send_message(chat.id, f"{soft_confirm} — đã lưu rồi nhé!")
                elif decision.allow_reply:
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

            # Phase 5: Autonomous Travel Operating System
            travel_os_state = self.travel_os.assess(context, incoming_text, companion_state, intent_result.intent)
            travel_brain_state = await self.travel_brain.assess(context, incoming_text, intent_result.intent)
            calm_decision = self.calm_policy.evaluate(
                future_stress=travel_os_state.prediction.future_stress,
                safety_risk=travel_os_state.safety.risk_level,
                burnout_risk=travel_brain_state.emotional.burnout_risk,
                option_count=travel_brain_state.option_count,
                user_initiated=True,
                attention_noise_risk=travel_brain_state.attention_protection.noise_risk,
                city_overload_risk=travel_brain_state.city_flow.stress_propagation_risk,
            )
            recovery_plan = self.recovery.build_plan(
                travel_brain_state.emotional,
                travel_os_state,
                travel_brain_state.city_flow,
                travel_brain_state.emotional_zone,
                travel_brain_state.collective_rhythm,
            )
            society_decision = self.agent_society.coordinate(travel_brain_state, calm_decision, recovery_plan)
            await self.memory.update_preferences(context, travel_os_state.preference_updates)
            await self.memory.update_preferences(context, travel_brain_state.preference_updates)

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
                    "travel_os": {
                        "posture": travel_os_state.recommendation_posture,
                        "profile": travel_os_state.profile.primary_style,
                        "rest_pressure": travel_os_state.energy.rest_pressure,
                        "simplify_pressure": travel_os_state.energy.simplify_pressure,
                        "future_stress": travel_os_state.prediction.future_stress,
                        "traffic_risk": travel_os_state.prediction.traffic_issue_risk,
                        "weather_risk": travel_os_state.prediction.weather_interruption_risk,
                        "overcrowding_risk": travel_os_state.prediction.overcrowding_risk,
                        "local_insights": travel_os_state.local.insights,
                        "rhythm": travel_os_state.rhythm.pacing_mode,
                    },
                    "travel_brain": {
                        "option_count": travel_brain_state.option_count,
                        "city_stress": travel_brain_state.city_flow.stress_propagation_risk,
                        "attention_noise": travel_brain_state.attention_protection.noise_risk,
                        "emotional_zone": travel_brain_state.emotional_zone.name,
                        "planetary_calmness": travel_brain_state.planetary.calmness_score,
                    },
                    "calm_policy": {
                        "max_option_count": calm_decision.max_option_count,
                        "allowed_surface": calm_decision.allowed_surface,
                        "notification_budget": calm_decision.notification_budget,
                        "should_batch": calm_decision.should_batch,
                    },
                },
            )

            if _is_companion_mode(intent_result.intent):
                # Travel/chat/general → OpenAI with trip context + emotional state
                response = await self._companion_reply(
                    incoming_text,
                    context,
                    companion_state,
                    travel_brain_state,
                    calm_decision,
                    recovery_plan,
                )
                # Phase 5: enhance with Travel OS
                response.text = self.companion.adapt_reply(response.text, companion_state, intent=intent_result.intent)
                response.text = self.travel_os.enhance_reply(response.text, travel_os_state, intent=intent_result.intent)
            else:
                # Structured action (expense/task/etc.) → sheets workflow
                response = await self.workflow.execute(intent_result.intent, companion_state=companion_state)
                response.text = self.companion.adapt_reply(response.text, companion_state, intent=intent_result.intent)
                # Phase 5: Travel OS also enhances structured responses for travel-related queries
                response.text = self.travel_os.enhance_reply(response.text, travel_os_state, intent=intent_result.intent)

            response.text = self._compose_live_reply(
                response.text,
                intent_result.intent,
                travel_brain_state,
                calm_decision,
                recovery_plan,
                society_decision,
            )

            if response.memory_updates:
                entity_type = intent_result.intent.domain or "general"
                entity_id = str(response.memory_updates.get("id", "latest"))
                await self.memory.store_entity(context, entity_type, entity_id, response.memory_updates)
                await self.action_logger.log("memory_entity_stored", chat.id, user.id, response.memory_updates)

            await self.memory.append_assistant_turn(context, response.text)
            await self.action_logger.log("assistant_response", chat.id, user.id, {"text": response.text, "has_map_button": response.reply_markup is not None})
            if decision.allow_reply:
                await self.telegram.send_message(chat.id, response.text, reply_markup=response.reply_markup)
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

    async def _companion_reply(self, message_text: str, context, companion_state, travel_brain_state, calm_decision, recovery_plan) -> AssistantResponse:
        trip_state = self.trip_context.get_state()
        trip_context_str = self.trip_context.format_for_prompt(trip_state, companion_state=companion_state)
        interaction_guidance = self._build_companion_interaction_guidance(
            travel_brain_state,
            calm_decision,
            recovery_plan,
        )
        conversation_history = _context_to_messages(context)
        companion = await self.llm.generate_companion_reply(
            message_text,
            conversation_history,
            trip_context_str,
            interaction_guidance,
        )
        # Auto-attach Maps buttons if AI recommended a specific place
        reply_markup = None
        if companion.place_name:
            place = find_place(companion.place_name)
            if place:
                reply_markup = build_telegram_keyboard(place)
        return AssistantResponse(
            text=companion.text,
            reply_markup=reply_markup,
            suggested_place_name=companion.place_name,
        )

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

    def _build_companion_interaction_guidance(self, brain, calm, recovery) -> str:
        lines: list[str] = []
        if calm.max_option_count <= 2:
            lines.append("Keep the reply tightly scoped: prefer 1-2 options maximum.")
        if calm.should_batch:
            lines.append("Collapse multiple ideas into one calm, low-friction answer.")
        if brain.city_flow.stress_propagation_risk >= 0.55:
            lines.append("The surrounding movement context is stressful; reduce movement and avoid multi-stop suggestions.")
        if brain.attention_protection.noise_risk >= 0.45:
            lines.append("Protect the user's attention: speak less, remove extra detail, and avoid noisy option lists.")
        if recovery.protect_energy:
            lines.append("Prioritize recovery, comfort, and shorter movement over exploration.")
        if brain.emotional_zone.name == "overstimulating_zone":
            lines.append("Avoid recommending overstimulating environments unless the user explicitly asks for them.")
        elif brain.emotional_zone.name in {"calming_zone", "recovery_zone"}:
            lines.append("If helpful, lean toward calming or restorative environments.")
        if brain.operating.recommendation_posture == "expand":
            lines.append("The user still has energy to explore, but only add one meaningful extra idea if it stays low-friction.")
        lines.append(f"Current response budget: at most {calm.max_option_count} surfaced options.")
        return "\n".join(lines)

    def _compose_live_reply(
        self,
        text: str,
        intent: AssistantIntent,
        brain,
        calm,
        recovery,
        society,
    ) -> str:
        limited = self._truncate_option_lines(text, calm.max_option_count)
        prefix = self._calm_prefix(brain, calm, recovery)
        guidance = self._select_live_guidance(intent, brain, calm, recovery, society)

        parts: list[str] = []
        if prefix:
            parts.append(prefix)
        parts.append(limited.strip())
        if guidance:
            parts.append("Giữ nhịp nhẹ:\n" + "\n".join(f"• {line}" for line in guidance))
        return "\n\n".join(part for part in parts if part).strip()

    def _calm_prefix(self, brain, calm, recovery) -> str:
        if brain.city_flow.stress_propagation_risk >= 0.55 or brain.attention_protection.noise_risk >= 0.6:
            return "Mình chốt gọn để đỡ quá tải nhé."
        if recovery.protect_energy:
            return "Mình ưu tiên nhịp nhẹ và dễ theo trước nhé."
        if calm.max_option_count <= 2:
            return "Mình gom lại ngắn gọn để bạn dễ chốt hơn nhé."
        if calm.should_batch:
            return "Mình gom lại ngắn gọn để bạn đỡ phải xử lý nhiều cùng lúc."
        return ""

    def _select_live_guidance(self, intent, brain, calm, recovery, society) -> list[str]:
        if intent.domain not in {"travel", "general"} and not recovery.protect_energy:
            return []

        limit = 1 if calm.max_option_count <= 2 else 2
        guidance: list[str] = []
        if recovery.actions:
            guidance.append(recovery.actions[0])
        if brain.city_flow.stress_propagation_risk >= 0.55:
            guidance.append("Nhịp di chuyển quanh bạn đang khá áp lực, nên mình ưu tiên chặng ngắn và ít đổi chỗ.")
        guidance.extend(society.top_messages(limit=limit))

        deduped: list[str] = []
        for item in guidance:
            cleaned = item.strip()
            if cleaned and cleaned not in deduped:
                deduped.append(cleaned)
        return deduped[:limit]

    def _truncate_option_lines(self, text: str, max_option_count: int) -> str:
        if max_option_count >= 4:
            return text
        lines = text.splitlines()
        kept: list[str] = []
        option_count = 0
        truncated = False
        for line in lines:
            stripped = line.strip()
            if self._is_option_line(stripped):
                if option_count < max_option_count:
                    kept.append(line)
                else:
                    truncated = True
                option_count += 1
                continue
            kept.append(line)
        if truncated and max_option_count <= 2:
            kept.append("• Nếu cần mình mở thêm lựa chọn sau.")
        return "\n".join(kept).strip()

    def _is_option_line(self, line: str) -> bool:
        if not line:
            return False
        if line.startswith(("•", "-", "*")):
            return True
        if len(line) > 2 and line[0].isdigit() and line[1] in {".", ")"}:
            return True
        return False


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
