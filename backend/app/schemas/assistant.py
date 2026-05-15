from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantIntent(BaseModel):
    intent_type: str = "chat"
    domain: str = "general"
    confidence: float = 0.0
    normalized_text: str = ""
    extracted_fields: dict[str, object] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    reply_style: str = ""
    action_name: str = ""


class AssistantResponse(BaseModel):
    text: str
    action_summary: str | None = None
    memory_updates: dict[str, object] = Field(default_factory=dict)
    reply_markup: dict | None = None  # Telegram InlineKeyboardMarkup
    suggested_place_name: str | None = None  # place name extracted from AI response
