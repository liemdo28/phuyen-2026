from __future__ import annotations

from app.ai.action_engine import infer_action_name
from app.schemas.assistant import AssistantIntent


def build_workflow_reasoning(intent: AssistantIntent) -> dict[str, object]:
    return {
        "action_name": infer_action_name(intent),
        "intent_type": intent.intent_type,
        "domain": intent.domain,
        "confidence": intent.confidence,
        "requires_follow_up": bool(intent.missing_fields),
        "missing_fields": intent.missing_fields,
    }
