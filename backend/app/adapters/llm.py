from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.schemas.assistant import AssistantIntent
from app.services.nlu import heuristic_intent_parse


@dataclass
class LLMResult:
    intent: AssistantIntent
    raw: dict[str, Any]


class LLMAdapter:
    def __init__(self) -> None:
        self.system_prompt = Path(__file__).resolve().parents[1] / "prompts" / "system_prompt.txt"

    async def detect_intent(self, message_text: str, memory_summary: str) -> LLMResult:
        # Production note:
        # Replace this heuristic-first implementation with real OpenAI/Anthropic structured output.
        intent = heuristic_intent_parse(message_text, memory_summary=memory_summary)
        return LLMResult(intent=intent, raw={"provider": "heuristic-fallback"})

