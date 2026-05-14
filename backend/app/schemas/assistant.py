from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantIntent(BaseModel):
    intent_type: str = "chat"
    domain: str = "general"
    confidence: float = 0.0
    extracted_fields: dict[str, object] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    reply_style: str = ""


class AssistantResponse(BaseModel):
    text: str
    action_summary: str | None = None
    memory_updates: dict[str, object] = Field(default_factory=dict)

