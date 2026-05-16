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

CRITICAL reply rules — violating ANY of these is a failure:
- Maximum 2-3 sentences. NEVER write paragraphs or lists.
- Do NOT use any markdown: no ###, no **bold**, no *italic*, no bullet lists.
- Do NOT start with "Chào bạn!", "Dạ", "Vâng", or any greeting/affirmation.
- Do NOT end with "Mình rất vui được hỗ trợ!", "Hãy cho mình biết nhé!", or similar.
- Do NOT explain what you're about to say — just say it directly.
- Do NOT write in English — Vietnamese only, always.
- Sound like a friend texting, not a customer service agent or tourist guide.
- Your name is Mi. If asked, say "Mình là Mi".
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
        # Lazy import to avoid circular deps
        self._mi_engine = None
        self._mien_tay_engine = None

    def _get_mi_engine(self):
        if self._mi_engine is None:
            try:
                from app.mi import MiEngine
                self._mi_engine = MiEngine()
            except Exception as e:
                logger.warning("MiEngine unavailable: %s", e)
        return self._mi_engine

    def _get_mien_tay_engine(self):
        if self._mien_tay_engine is None:
            try:
                from app.mi.mien_tay import MienTayEngine
                self._mien_tay_engine = MienTayEngine()
            except Exception as e:
                logger.warning("MienTayEngine unavailable: %s", e)
        return self._mien_tay_engine

    async def detect_intent(self, message_text: str, memory_summary: str) -> LLMResult:
        intent = heuristic_intent_parse(message_text, memory_summary=memory_summary)
        return LLMResult(intent=intent, raw={"provider": "heuristic-fallback"})

    async def generate_companion_reply(
        self,
        message_text: str,
        conversation_history: list[dict[str, str]],
        trip_context_str: str = "",
        interaction_guidance: str = "",
        chat_id: int = 0,
    ) -> CompanionReply:
        if not settings.openai_api_key:
            logger.warning("No OPENAI_API_KEY — using heuristic companion reply")
            return CompanionReply(text=_heuristic_companion_reply(message_text))

        try:
            from openai import AsyncOpenAI
        except ImportError:
            return CompanionReply(text=_heuristic_companion_reply(message_text))

        # Enrich interaction_guidance with Mi's live emotion + pronoun analysis
        mi = self._get_mi_engine()
        mi_guidance = ""
        if mi:
            try:
                mi_ctx = mi.analyze(message_text)
                mi_guidance = mi_ctx.full_interaction_guidance()
                logger.debug("Mi analysis: %s | mode=%s",
                             mi_ctx.emotion.summary(), mi_ctx.emotion.response_mode.value)
            except Exception as e:
                logger.warning("MiEngine.analyze failed: %s", e)

        # Enrich with Miền Tây cultural intelligence if Southern dialect detected
        mien_tay_guidance = ""
        mt_engine = self._get_mien_tay_engine()
        if mt_engine:
            try:
                mt_ctx = mt_engine.analyze(message_text)
                if mt_ctx.is_mien_tay:
                    mien_tay_guidance = mt_engine.build_llm_guidance(mt_ctx)
                    logger.debug(
                        "MienTay: score=%.0f%% signals=%s exaggeration=%s",
                        mt_ctx.dialect_score * 100,
                        [s.value for s in mt_ctx.signals],
                        mt_ctx.is_exaggeration,
                    )
            except Exception as e:
                logger.warning("MienTayEngine.analyze failed: %s", e)

        # Human Presence Engine — emotional pacing, comfort orchestration, mental load reduction
        presence_guidance = ""
        try:
            from app.mi.presence import build_presence_context
            p_ctx = build_presence_context(message_text, chat_id=chat_id)
            if (p_ctx.current.fatigue > 0.15 or p_ctx.current.stress > 0.15
                    or p_ctx.current.wants_quiet or p_ctx.recent_was_tired):
                presence_guidance = p_ctx.build_guidance()
                logger.debug(
                    "Presence: fatigue=%.0f%% stress=%.0f%% mode=%s pace=%s",
                    p_ctx.current.fatigue * 100, p_ctx.current.stress * 100,
                    p_ctx.social_mode.value, p_ctx.response_pace.value,
                )
        except Exception as e:
            logger.warning("Presence engine failed: %s", e)

        combined_guidance = "\n\n".join(
            p for p in [interaction_guidance, mi_guidance, mien_tay_guidance, presence_guidance] if p
        )
        system = _build_system_prompt(trip_context_str, combined_guidance) + _STRUCTURED_SUFFIX
        messages = _build_messages(system, conversation_history, message_text)

        try:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            async with asyncio.timeout(15):
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    temperature=0.5,
                    max_tokens=200,
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


def _sanitize_reply(text: str) -> str:
    """
    MANDATORY post-processing — runs on every LLM reply regardless of prompt instructions.
    Strips markdown, removes banned phrases, truncates to 3 sentences max.
    This is a hard enforcement layer — not dependent on LLM compliance.
    """
    import re

    # 1. Strip markdown bold/italic (**text** → text, *text* → text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)

    # 2. Strip ATX headers (### Header → Header)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # 3. Convert numbered/bulleted lists to inline sentences
    # "1. Tuy Hòa: ..." → "Tuy Hòa: ..."
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-•*]\s+', '', text, flags=re.MULTILINE)

    # 4. Collapse multiple blank lines to single newline
    text = re.sub(r'\n{2,}', ' ', text).strip()
    text = re.sub(r'\n', ' ', text).strip()

    # 5. Remove banned opener phrases
    _BANNED_OPENERS = [
        "Chào bạn! 😊 Rất vui được hỗ trợ bạn",
        "Rất vui được hỗ trợ bạn",
        "Chào bạn! Mình rất vui",
        "Mình rất vui được hỗ trợ",
        "Hãy cho mình biết nhé!",
        "Hy vọng thông tin này hữu ích",
        "Chúc bạn có một chuyến đi vui vẻ",
        "Dạ bạn",
    ]
    for phrase in _BANNED_OPENERS:
        if text.startswith(phrase):
            # Remove up to first sentence end after the phrase
            idx = text.find('!', len(phrase))
            if idx == -1:
                idx = text.find('.', len(phrase))
            if idx != -1:
                text = text[idx + 1:].strip()
            break

    # 6. Truncate to 3 sentences (split on . ! ?)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) > 3:
        text = ' '.join(sentences[:3])

    return text.strip()


def _parse_companion_response(raw: str) -> CompanionReply:
    try:
        data = json.loads(raw)
        reply_text = data.get("reply") or data.get("message") or raw
        # data.get("place_name") returns Python None for JSON null — the `or None`
        # handles that. The "null" string check was dead code after json.loads.
        place_name = data.get("place_name") or None
        if isinstance(place_name, str) and not place_name.strip():
            place_name = None
        return CompanionReply(text=_sanitize_reply(reply_text), place_name=place_name)
    except Exception:
        logger.debug("Failed to parse LLM JSON response, using raw text: %.120s", raw)
        return CompanionReply(text=_sanitize_reply(raw) if isinstance(raw, str) else raw)


def _heuristic_companion_reply(text: str) -> str:
    """
    Mi's built-in response when LLM is unavailable.
    Uses Mi's full engine stack: weather → nightlife → location → keyword handlers.
    """
    # ── Mi engine fast-path (weather + nightlife + location) ──────────────────
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from app.mi.weather_engine import detect_weather_from_text
        from app.mi.nightlife_engine import plan_night_flow

        weather = detect_weather_from_text(text)
        if weather.redirect_suggestion:
            return weather.redirect_suggestion

        now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        night_plan = plan_night_flow(text, hour=now.hour, has_child=True)
        if night_plan and night_plan.mi_suggestion:
            return night_plan.mi_suggestion
    except Exception:
        pass  # engines unavailable — fall through to keyword handlers

    t = text.lower().strip()

    # English greeting → respond in Vietnamese only
    if t in ("hello", "hi", "hey", "hello!", "hi!", "hey!") or t.startswith(("hello ", "hi ", "hey ")):
        return "Chào bạn 😊 Mình là Mi — bạn đồng hành Phú Yên. Hỏi gì cũng được nhé!"

    # Pure greeting — respond warmly in Vietnamese, never in English
    _greeting_norm = t.strip().rstrip("!.,~")
    if _greeting_norm in {
        "hello", "hi", "hey", "helo", "hii",
        "chao", "chào", "chao em", "chào em",
        "chao anh", "chào anh", "chao chi", "chào chị", "chao ban", "chào bạn",
        "xin chao", "xin chào",
    }:
        return "Chào anh/chị! Em là Mi — bạn đồng hành Phú Yên 2026 😊 Cần gì cứ hỏi em nhé."

    # Miền Tây / Southern dialect detection
    _mien_tay = any(w in t for w in [
        "hen", "nhen", "dzậy", "dzô", "vậy nhen", "thôi nha", "ổng", "bả", "cái này nè",
    ])

    # Gen Z detection
    _gen_z = any(w in t for w in [
        "quẩy", "phê", "chill", "hype", "oke bạn ei", "oke nha", "siuuu", "đỉnh", "xịn sò",
    ])

    # Child water safety — CRITICAL, must check before anything else
    child_water = any(w in t for w in [
        "bé bơi", "bé tắm", "cho bé ra biển", "bé có tắm", "bé xuống nước",
        "có sứa", "bé ra biển", "an toàn không", "nuoc co sau",
    ])
    if child_water:
        return (
            "Bãi Xép an toàn nhất cho bé — sóng nhỏ, nước trong. "
            "Bé 4 tuổi cần người lớn cầm tay trực tiếp, nước tới đầu gối là giới hạn. "
            "Kiểm tra sứa 5 phút trước khi xuống nhé — tháng 5 thỉnh thoảng có."
        )

    # Sarcasm detection — address underlying complaint
    if any(w in t for w in ["🙄", "ừ đúng rồi", "tuyệt vời lắm", "giỏi thật", "hay thật"]):
        return "Nghe có vẻ không như kỳ vọng — xin lỗi nhé. Muốn mình gợi ý chỗ khác không? Nói khu vực đang ở, mình tìm ngay."

    # Extreme fatigue — ULTRA SHORT, max 1 sentence
    if any(w in t for w in [
        "mệt xỉu", "kiệt sức rồi", "không còn sức", "sắp ngất",
        "lần này cuối cùng", "mệt muốn chết", "die rồi", "hết pin",
    ]):
        return "Mệt rồi thì về nghỉ thôi, mình tính tiếp sau."

    # Regular fatigue
    if any(w in t for w in [
        "mệt lắm", "mệt quá", "mệt rồi", "mệt",
        "buồn ngủ", "buồn ngủ quá", "ngủ gật", "đuối quá",
    ]):
        return "Mệt rồi thì nghỉ đi, đừng ép. Tìm cái quán cafe gần đây ngồi nhâm nhi, hoặc về khách sạn nằm một lúc. Không cần phải đi thêm đâu hết."

    # Seafood request (with/without accent)
    if any(w in t for w in [
        "hải sản", "hai san", "tôm", "mực", "cá tươi", "seafood",
        "muon an hai san", "muốn ăn hải sản",
    ]):
        return "Hải sản tươi thì ghé khu cảng cá Tuy Hòa hoặc lên Sông Cầu — tôm hùm, cá ngừ, mực ống đều tươi sống. Bạn muốn trong thành phố hay chạy lên Sông Cầu?"

    # Hunger — (with no-accent variants: doi qua, doi roi)
    if any(w in t for w in [
        "đói xỉu", "đói muốn chết", "đói bẹp", "đói cồn cào", "bụng kêu",
        "đói lắm", "đói rồi", "đói quá", "đói", "chưa ăn gì",
        "ăn gì", "ăn ở đâu", "kiếm gì ăn",
        "doi qua", "doi roi", "doi lam", "an gi",
    ]):
        return "Đói thì ghé quán bún cá ngừ hoặc bánh căn gần trung tâm — địa phương nhất, giá tốt, bé cũng ăn được. Bạn đang ở khu nào?"

    # Drinking / nightlife
    if any(w in t for w in [
        "nhậu", "bia", "làm vài lon", "quất vài", "quán nhậu", "đi bar",
    ]):
        return "Nhậu thì kiếm hải sản sông biển hoặc tôm hùm Sông Cầu — tươi, ngon, mồi tốt. Muốn mình chỉ quán cụ thể không?"

    # Rain redirect — especially with kid
    if any(w in t for w in [
        "mưa như trút", "mưa to", "mưa rồi", "mưa", "trời xấu", "bão",
        "kế hoạch hủy",
    ]):
        has_kid = any(k in t for k in ["bé", "con", "trẻ em"])
        if has_kid:
            return "Mưa thì vào trong thôi — ghé Trung tâm thương mại Vincom Tuy Hòa cho bé chơi, hoặc ăn phở bò trong quán có mái. Mưa Phú Yên thường tạnh sau 1-2h."
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
    # Recovery / rest / quiet seeking
    if any(w in t for w in [
        "muốn nghỉ", "cần nghỉ", "đi healing", "muốn reset", "kiếm chỗ chill",
        "muốn yên tĩnh", "không muốn đi xa",
        "thư giãn", "thu gian", "không ồn", "khong on",
        "cần chỗ ngồi", "can cho ngoi", "chỗ ngồi yên", "chỗ yên tĩnh",
    ]):
        return "Nghe có vẻ cần xả hơi. Cafe Biển Bãi Xép view đẹp, gió mát, không đông — ngồi ngắm biển thư giãn là hợp nhất lúc này."

    # Movement resistance / nearby-only request
    if any(w in t for w in [
        "gần thôi", "gan thoi", "gần đây thôi", "gan day thoi",
        "lười đi xa", "luoi di xa", "ngại đi xa", "ngai di xa",
        "không muốn đi xa", "khong muon di xa",
        "đi bộ thôi", "di bo thoi",
    ]):
        return "Hiểu rồi, gần thôi nhé. Cho mình biết đang ở khu nào (trung tâm, cảng, Sông Cầu?) mình tìm điểm gần nhất — ăn, cafe hay hoạt động gì?"

    # Expense / spending queries
    if any(w in t for w in [
        "ăn hết", "an het", "tiêu hôm nay", "tieu hom nay",
        "tiêu bao nhiêu", "tieu bao nhieu", "hôm nay tiêu", "hom nay tieu",
        "đổ xăng", "do xang", "chi tiêu", "chi tieu",
        "ghi lại", "ghi nợ", "ghi chi", "tổng chi",
    ]):
        return "Ghi lại nhé. Khoản gì vậy — ăn uống, đi lại, hay mua sắm? Nói số tiền luôn mình lưu cho."

    # Itinerary / schedule query
    if any(w in t for w in [
        "lịch trình", "lich trinh", "kế hoạch hôm nay", "ke hoach hom nay",
        "hôm nay làm gì", "hom nay lam gi", "đi đâu hôm nay", "di dau hom nay",
        "buổi chiều đi đâu", "buổi sáng đi đâu",
    ]):
        return "Hôm nay mình gợi ý: sáng đi biển sớm, trưa nghỉ + ăn hải sản, chiều cafe hoặc chụp ảnh, tối đi dạo phố. Đang ở khu nào để mình chỉ cụ thể hơn?"

    # Gen Z — quẩy/hype/phê
    if _gen_z or any(w in t for w in ["quẩy", "phê", "hype", "đỉnh kout", "siuuu"]):
        return "Phú Yên quẩy kiểu gì bây giờ 😄 Biển chiều? Hải sản tối? Hay tìm chỗ chill ngắm hoàng hôn? Bạn chọn đi mình chỉ ngay!"

    # Excitement / exploration
    if any(w in t for w in [
        "hào hứng", "hype", "thích quá", "muốn khám phá", "đi đâu vui",
    ]):
        return "Mood tốt đấy! Ghé Gành Đá Đĩa hoặc Đầm Ô Loan — 2 địa điểm đỉnh nhất Phú Yên. Mình chỉ cụ thể hơn nếu bạn cho biết đang ở đâu nhé."

    # Older user / formal tone (cô/chú/bác)
    if any(w in t for w in ["cô cần", "chú cần", "bác cần", "cô muốn", "chú muốn", "bác muốn"]):
        if any(w in t for w in ["quán ăn", "ăn", "nhà hàng"]):
            return "Dạ mình gợi ý vài chỗ gia đình ăn được nhé — Nhà hàng Hải Sản Sông Cầu tươi ngon, hoặc các quán Bún Cá Ngừ trong trung tâm Tuy Hòa, yên tĩnh và phù hợp cả nhà. Cô/chú đang ở khu nào để mình tính đường cho tiện ạ?"
        return "Dạ cô/chú/bác cần gì mình hỗ trợ ngay nhé. Cho mình biết đang ở đâu để gợi ý phù hợp ạ."

    # Miền Tây warmth
    if _mien_tay:
        return "Oke nhen! Bạn cần gì mình lo liền — hỏi thêm đi, mình ở đây nè 😊"

    # Name query
    if any(w in t for w in ["mi là ai", "tên gì", "bạn là ai", "mi tên gì", "ai vậy"]):
        return "Mình là Mi — bạn đồng hành chuyến Phú Yên của bạn 😊 Cần gì cứ hỏi mình nhé!"

    # Location self-query (fallback if orchestrator intercept missed)
    if any(w in t for w in ["đang ở đâu", "toi dang o dau", "o dau vay"]):
        return "Bạn chưa share vị trí cho mình. Nhấn 📎 → Location để share GPS nhé!"

    # Miền Tây social warmth / soft negotiation fallback
    if any(w in t for w in ["hông ấy", "hong ay", "hay vầy", "hay vay di", "thôi kệ heng", "tính sau hen"]):
        return "Ừ, tính sau cũng được nhen 😊 Cần gì cứ nói mình lo."

    if any(w in t for w in ["nhậu hông", "nhau hong", "làm vài lon", "lai rai", "quán ruột"]):
        return "Nhậu thì kiếm hải sản hoặc mực nướng Sông Cầu — mồi tươi, lai rai được lắm nhen."

    if any(w in t for w in ["cafe võng", "cafe vong", "cafe sân vườn"]):
        return "Cafe võng thì Bãi Xép có vài chỗ chill dữ lắm — view biển, ngồi đung đưa ngắm sóng nhen."

    return "Mình đây — cần gì cứ nói nhé! 😊"
