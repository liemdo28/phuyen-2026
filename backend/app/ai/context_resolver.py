from __future__ import annotations

from app.models.domain import UserContext


def build_context_snapshot(context: UserContext) -> dict[str, object]:
    latest_turns = [{"role": turn.role, "text": turn.text} for turn in context.conversation[-5:]]
    latest_entities = [
        {"entity_type": entity.entity_type, "entity_id": entity.entity_id, "payload": entity.payload}
        for entity in context.entities[-3:]
    ]
    return {
        "chat_id": context.chat_id,
        "user_id": context.user_id,
        "locale": context.locale,
        "timezone": context.timezone,
        "latest_turns": latest_turns,
        "latest_entities": latest_entities,
        "preferences": context.preferences,
    }

