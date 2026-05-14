from __future__ import annotations

from app.models.domain import EntityReference, MemoryTurn, UserContext
from app.services.persistence import PersistenceStore


class MemoryService:
    def __init__(self) -> None:
        self._contexts: dict[tuple[int, int], UserContext] = {}
        self.store = PersistenceStore()

    async def get_context(self, chat_id: int, user_id: int) -> UserContext:
        key = (chat_id, user_id)
        if key not in self._contexts:
            context = UserContext(chat_id=chat_id, user_id=user_id)
            for turn in self.store.get_recent_turns(chat_id, user_id):
                context.conversation.append(MemoryTurn(role=turn.role, text=turn.text))
            for entity in self.store.get_recent_entities(chat_id, user_id):
                context.entities.append(
                    EntityReference(entity_type=entity.entity_type, entity_id=entity.entity_id, payload=entity.payload)
                )
            self._contexts[key] = context
        return self._contexts[key]

    async def append_user_turn(self, context: UserContext, text: str) -> None:
        context.conversation.append(MemoryTurn(role="user", text=text))
        context.conversation = context.conversation[-20:]
        self.store.append_turn(context.chat_id, context.user_id, "user", text)

    async def append_assistant_turn(self, context: UserContext, text: str) -> None:
        context.conversation.append(MemoryTurn(role="assistant", text=text))
        context.conversation = context.conversation[-20:]
        self.store.append_turn(context.chat_id, context.user_id, "assistant", text)

    async def store_entity(self, context: UserContext, entity_type: str, entity_id: str, payload: dict[str, object]) -> None:
        context.entities.append(EntityReference(entity_type=entity_type, entity_id=entity_id, payload=payload))
        context.entities = context.entities[-20:]
        self.store.append_entity(context.chat_id, context.user_id, entity_type, entity_id, payload)

    def summarize(self, context: UserContext) -> str:
        recent_messages = [f"{turn.role}: {turn.text}" for turn in context.conversation[-6:]]
        recent_entities = [f"{entity.entity_type}:{entity.entity_id}:{entity.payload}" for entity in context.entities[-4:]]
        return "\n".join(recent_messages + recent_entities)
