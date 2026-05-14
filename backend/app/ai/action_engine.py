from __future__ import annotations

from app.schemas.assistant import AssistantIntent


def infer_action_name(intent: AssistantIntent) -> str:
    action_map = {
        ("create", "expense"): "add_expense",
        ("update", "expense"): "update_expense",
        ("query", "expense"): "summarize_expense",
        ("create", "task"): "create_task",
        ("update", "task"): "update_task",
        ("query", "task"): "query_task",
        ("create", "inventory"): "update_inventory",
        ("query", "travel"): "travel_recommendation",
        ("query", "revenue"): "summarize_revenue",
    }
    return action_map.get((intent.intent_type, intent.domain), "chat_response")

