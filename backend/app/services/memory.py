from __future__ import annotations

from app.models.domain import EntityReference, MemoryTurn, UserContext


class MemoryService:
    def __init__(self) -> None:
        self._contexts: dict[tuple[int, int], UserContext] = {}

    async def get_context(self, chat_id: int, user_id: int) -> UserContext:
        key = (chat_id, user_id)
        if key not in self._contexts:
            self._contexts[key] = UserContext(chat_id=chat_id, user_id=user_id)
        return self._contexts[key]

    async def append_user_turn(self, context: UserContext, text: str) -> None:
        context.conversation.append(MemoryTurn(role="user", text=text))
        context.conversation = context.conversation[-20:]

    async def append_assistant_turn(self, context: UserContext, text: str) -> None:
        context.conversation.append(MemoryTurn(role="assistant", text=text))
        context.conversation = context.conversation[-20:]

    async def store_entity(self, context: UserContext, entity_type: str, entity_id: str, payload: dict[str, object]) -> None:
        context.entities.append(EntityReference(entity_type=entity_type, entity_id=entity_id, payload=payload))
        context.entities = context.entities[-20:]

    def summarize(self, context: UserContext) -> str:
        recent_messages = [f"{turn.role}: {turn.text}" for turn in context.conversation[-6:]]
        recent_entities = [f"{entity.entity_type}:{entity.entity_id}" for entity in context.entities[-4:]]
        return "\n".join(recent_messages + recent_entities)

