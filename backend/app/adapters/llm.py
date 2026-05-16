from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.assistant import AssistantIntent
from app.services.nlu import heuristic_intent_parse

logger = logging.getLogger(__name__)

_COMPANION_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "companion_system_prompt.txt"

_STRUCTURED_SUFFIX = """

## Output Format
Respond with valid JSON only, no markdown:
{
  "reply": "<your Vietnamese response here>",
  "place_name": "<exact place name from local database if you recommend one, else null>"
}

The place_name must match one of the known Phú Yên places if applicable, otherwise null.
"""


@dataclass
class LLMResult:
    intent: AssistantIntent
    raw: dict[str, Any]


@dataclass
class CompanionReply:
    text: str
    place_name: str | None = None


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
        interaction_guidance: str = "",
    ) -> CompanionReply:
        if not settings.openai_api_key:
            logger.warning("No OPENAI_API_KEY — using heuristic companion reply")
            return CompanionReply(text=_heuristic_companion_reply(message_text))

        try:
            from openai import AsyncOpenAI
        except ImportError:
            return CompanionReply(text=_heuristic_companion_reply(message_text))

        system = _build_system_prompt(trip_context_str, interaction_guidance) + _STRUCTURED_SUFFIX
        messages = _build_messages(system, conversation_history, message_text)

        try:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            async with asyncio.timeout(15):
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=512,
                    response_format={"type": "json_object"},
                )
            raw = response.choices[0].message.content or "{}"
            return _parse_companion_response(raw)
        except asyncio.TimeoutError:
            logger.warning("OpenAI companion timed out after 15s — falling back to heuristic")
            return CompanionReply(text=_heuristic_companion_reply(message_text))
        except Exception as exc:
            logger.exception("OpenAI companion reply error: %s", exc)
            return CompanionReply(text=_heuristic_companion_reply(message_text))


def _build_system_prompt(trip_context_str: str, interaction_guidance: str = "") -> str:
    """
    Build the full system prompt by layering context sections:
    1. Base companion persona
    2. Current trip state (day, time slot, agenda)
    3. Interaction guidance (TravelBrain + Intelligence Graph behavior signals)
    """
    base = _COMPANION_PROMPT_PATH.read_text(encoding="utf-8")
    parts = [base]
    if trip_context_str:
        parts.append(f"## Current Trip State\n{trip_context_str}")
    if interaction_guidance:
        parts.append(f"## Current Interaction Guidance\n{interaction_guidance}")
    return "\n\n".join(parts)


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


def _parse_companion_response(raw: str) -> CompanionReply:
    try:
        data = json.loads(raw)
        reply_text = data.get("reply") or data.get("message") or raw
        # data.get("place_name") returns Python None for JSON null — the `or None`
        # handles that. The "null" string check was dead code after json.loads.
        place_name = data.get("place_name") or None
        if isinstance(place_name, str) and not place_name.strip():
            place_name = None
        return CompanionReply(text=reply_text, place_name=place_name)
    except Exception:
        logger.debug("Failed to parse LLM JSON response, using raw text: %.120s", raw)
        return CompanionReply(text=raw)


def _heuristic_companion_reply(text: str) -> str:
    """
    Fallback when OpenAI is unavailable.
    Uses the intelligence patterns for richer matching.
    """
    t = text.lower()
    # Fatigue / exhaustion — most critical
    if any(w in t for w in [
        "mệt xỉu", "mệt muốn chết", "kiệt sức", "hết pin",
        "đuối quá", "die rồi", "mệt lắm", "mệt quá", "mệt rồi", "mệt",
        "buồn ngủ", "buồn ngủ quá", "ngủ gật",
    ]):
        return "Mệt rồi thì nghỉ đi, đừng ép. Tìm cái quán cafe gần đây ngồi nhâm nhi, hoặc về khách sạn nằm một lúc. Không cần phải đi thêm đâu hết."
    # Hunger — second most urgent
    if any(w in t for w in [
        "đói xỉu", "đói muốn chết", "đói bẹp", "đói cồn cào", "bụng kêu",
        "đói lắm", "đói rồi", "đói quá", "đói", "chưa ăn gì",
        "ăn gì", "ăn ở đâu", "kiếm gì ăn",
    ]):
        return "Đói thì ghé quán bún cá ngừ hoặc bánh căn gần trung tâm — địa phương nhất, giá tốt, bé cũng ăn được. Bạn đang ở khu nào?"
    # Drinking / nightlife
    if any(w in t for w in [
        "nhậu", "bia", "làm vài lon", "quất vài", "quán nhậu", "đi bar",
    ]):
        return "Nhậu thì kiếm hải sản sông biển hoặc tôm hùm Sông Cầu — tươi, ngon, mồi tốt. Muốn mình chỉ quán cụ thể không?"
    # Rain redirect
    if any(w in t for w in [
        "mưa như trút", "mưa to", "mưa rồi", "mưa", "trời xấu", "bão",
    ]):
        return "Mưa rồi thì tạm hoãn biển, không vội. Ghé cafe trong thành phố ngồi chờ, hoặc dạo chợ Tuy Hòa cho mát. Mưa Phú Yên thường tạnh nhanh thôi."
    # Heat
    if any(w in t for w in [
        "nóng muốn chết", "nóng vãi", "nóng quá", "nắng gắt", "oi bức",
        "nóng", "nắng", "oi quá",
    ]):
        return "Nắng gắt thì tránh ra ngoài buổi trưa. Vào cafe máy lạnh, hồ bơi khách sạn, hoặc nghỉ ngơi — chiều mát sẽ ra tiếp thôi."
    # Confusion / indecision
    if any(w in t for w in [
        "rối quá", "loạn não", "không biết phải làm sao",
        "rối", "không biết", "đi đâu", "làm gì", "bây giờ sao", "sao bây giờ",
    ]):
        return "Bình tĩnh nào. Cho mình biết đang ở đâu và mấy giờ, mình tính cho ngay."
    # Recovery / rest seeking
    if any(w in t for w in [
        "muốn nghỉ", "cần nghỉ", "đi healing", "muốn reset", "kiếm chỗ chill",
        "muốn yên tĩnh", "không muốn đi xa",
    ]):
        return "Nghe có vẻ cần xả hơi một chút. Cafe Biển Bãi Xép view đẹp, gió mát, không đông — ngồi ngắm biển thư giãn là hợp nhất lúc này."
    # Excitement / exploration
    if any(w in t for w in [
        "hào hứng", "hype", "thích quá", "muốn khám phá", "đi đâu vui",
    ]):
        return "Mood tốt đấy! Ghé Gành Đá Đĩa hoặc Đầm Ô Loan — 2 địa điểm đỉnh nhất Phú Yên. Mình chỉ cụ thể hơn nếu bạn cho biết đang ở đâu nhé."
    return "Mình đây, cần gì cứ nói nhé!"
