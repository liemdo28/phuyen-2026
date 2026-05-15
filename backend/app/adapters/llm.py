from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.assistant import AssistantIntent
from app.services.nlu import heuristic_intent_parse

logger = logging.getLogger(__name__)

_COMPANION_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "companion_system_prompt.txt"


@dataclass
class LLMResult:
    intent: AssistantIntent
    raw: dict[str, Any]


class LLMAdapter:
    def __init__(self) -> None:
        self.system_prompt = Path(__file__).resolve().parents[1] / "prompts" / "system_prompt.txt"

    async def detect_intent(self, message_text: str, memory_summary: str) -> LLMResult:
        intent = heuristic_intent_parse(message_text, memory_summary=memory_summary)
        return LLMResult(intent=intent, raw={"provider": "heuristic-fallback"})

    async def generate_companion_reply(
        self,
        message_text: str,
        conversation_history: list[dict[str, str]],
        trip_context_str: str = "",
    ) -> str:
        if not settings.openai_api_key:
            logger.warning("No OPENAI_API_KEY — using heuristic companion reply")
            return _heuristic_companion_reply(message_text)

        try:
            from openai import AsyncOpenAI
        except ImportError:
            return _heuristic_companion_reply(message_text)

        system = _build_system_prompt(trip_context_str)
        messages = _build_messages(system, conversation_history, message_text)

        try:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            async with asyncio.timeout(15):
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=512,
                )
            return response.choices[0].message.content or _heuristic_companion_reply(message_text)
        except Exception as exc:
            logger.error("OpenAI companion reply error: %s", exc)
            return _heuristic_companion_reply(message_text)


def _build_system_prompt(trip_context_str: str) -> str:
    base = _COMPANION_PROMPT_PATH.read_text(encoding="utf-8")
    if trip_context_str:
        return base + f"\n\n## Current Trip State\n{trip_context_str}"
    return base


def _build_messages(
    system: str,
    history: list[dict[str, str]],
    current_message: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for turn in history[-10:]:
        role = turn.get("role", "")
        content = (turn.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": current_message})
    return messages


def _heuristic_companion_reply(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["mệt", "buồn ngủ", "kiệt sức", "đuối"]):
        return "Mệt rồi thì nghỉ đi, đừng ép. Tìm cái quán cafe gần đây ngồi nhâm nhi, hoặc về khách sạn nằm một lúc. Không cần phải đi thêm đâu hết."
    if any(w in t for w in ["đói", "ăn gì", "ăn ở đâu"]):
        return "Đói thì ghé quán bún cá ngừ hoặc bánh căn gần trung tâm — địa phương nhất, giá tốt, bé cũng ăn được. Bạn đang ở khu nào?"
    if any(w in t for w in ["mưa", "trời xấu", "bão"]):
        return "Mưa rồi thì tạm hoãn biển, không vội. Ghé cafe trong thành phố ngồi chờ, hoặc dạo chợ Tuy Hòa cho mát. Mưa Phú Yên thường tạnh nhanh thôi."
    if any(w in t for w in ["rối", "không biết", "đi đâu", "làm gì", "bây giờ"]):
        return "Bình tĩnh nào. Cho mình biết đang ở đâu và mấy giờ, mình tính cho ngay."
    if any(w in t for w in ["nóng", "nắng gắt"]):
        return "Nắng gắt thì tránh ra ngoài buổi trưa. Vào cafe, hồ bơi khách sạn, hoặc nghỉ ngơi — chiều mát sẽ ra tiếp thôi."
    return "Mình đây, cần gì cứ nói nhé!"
