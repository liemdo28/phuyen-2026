from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.domain import UserContext
from app.schemas.assistant import AssistantIntent

STRESS_MARKERS = [
    "mệt", "roi", "rối", "không biết", "ko biết",
    "nhiều quá", "khó chọn", "khó quá", "kẹt xe", "mưa quá",
    # Intelligence graph expansion
    "stress", "stress quá", "nổ đầu", "loạn não", "rối tung", "rối cả lên",
    "không biết phải làm sao", "điên rồi", "bực quá", "ức chế",
    "căng thẳng", "áp lực", "choáng ngợp", "ngộp",
    "đau đầu quá", "nhức đầu",
]
CONFUSION_MARKERS = [
    "đi đâu", "ăn gì", "nên đi", "nên ăn", "sao giờ", "không biết", "làm sao",
    # Intelligence graph expansion
    "không biết phải đi đâu", "không biết ăn gì", "không biết chọn",
    "khó quá không chọn được", "rối quá", "nhiều lựa chọn quá",
    "sao bây giờ", "bây giờ sao đây", "phải làm sao", "làm sao bây giờ",
    "đi đâu bây giờ", "ăn gì bây giờ", "nên làm gì", "nên đi đâu",
]
EXCITEMENT_MARKERS = [
    "wow", "đẹp", "chill", "sunset", "hoàng hôn", "check-in",
    "sống ảo", "hào hứng", "thích quá",
    # Intelligence graph expansion
    "hype", "phấn khích", "thích phết", "mê quá", "đỉnh quá",
    "ngầu quá", "xịn quá", "tuyệt quá", "trời ơi đẹp",
    "muốn sống ở đây luôn", "chill quá", "vui quá", "sướng quá",
    "tan chảy", "mlem mlem", "ngon quá",
]
FATIGUE_MARKERS = [
    "buồn ngủ", "đuối", "mệt", "kiệt sức", "ngủ thôi",
    # Intelligence graph expansion — sarcasm-scaled fatigue
    "mệt xỉu", "mệt muốn chết", "hết pin", "hết năng lượng",
    "không còn sức", "đuối quá", "rã rời", "bã người", "bở người",
    "die rồi", "chết rồi", "sắp ngất", "mệt lắm", "buồn ngủ quá",
    "ngủ gật", "không muốn làm gì", "lười quá", "ngại quá",
    "cần nghỉ", "muốn nghỉ", "nghỉ tí", "nằm xỉu", "đi healing",
    "muốn reset", "recharge", "hết xăng", "não lag", "lag não",
    "đơ người", "đơ hết rồi",
]
RELAXED_MARKERS = [
    "cafe", "cà phê", "chụp ảnh", "chụp hình", "ngắm", "thảnh thơi",
    # Intelligence graph expansion
    "thư giãn", "nghỉ ngơi", "relax", "thả lỏng", "không vội",
    "healing", "me time", "tự do", "thoải mái",
    "ngồi cafe", "ngồi ngắm biển", "chill nhẹ", "nhẹ nhàng thôi",
]
WEATHER_MARKERS = [
    "mưa", "nắng", "thời tiết", "gió", "giông",
    # Intelligence graph expansion
    "nóng quá", "nóng muốn chết", "nóng vãi", "oi bức", "nắng gắt",
    "mưa to", "mưa như trút", "biển động", "sóng to", "bão",
    "trời đẹp", "mát mẻ", "trời trong",
]
TRANSPORT_MARKERS = [
    "grab", "taxi", "kẹt xe", "đường", "di chuyển",
    # Intelligence graph expansion
    "không muốn đi xa", "ngại đi xa", "lười di chuyển",
    "gần thôi", "gần đây thôi", "đi bộ thôi",
]
PHOTO_MARKERS = [
    "cafe", "cà phê", "ảnh", "hình", "sunset", "hoàng hôn", "view",
    # Intelligence graph expansion
    "chụp ảnh", "chụp hình", "sống ảo", "check-in", "instagram",
    "golden hour", "bình minh", "ánh sáng đẹp", "cảnh đẹp",
]
LOCATION_CHANGE_MARKERS = [
    "gần đây", "đổi chỗ", "chỗ khác", "quán khác", "đi đâu", "qua đâu",
    # Intelligence graph expansion
    "chỗ vắng", "tránh đông", "chỗ ít người", "chỗ yên tĩnh",
    "không muốn ở đây", "đi chỗ khác thôi",
]
FOOD_MARKERS = [
    "ăn", "quán", "cafe", "cà phê", "nhà hàng", "bún", "phở", "hải sản",
    # Intelligence graph expansion
    "đói", "thèm ăn", "kiếm gì ăn", "ăn gì", "quán ngon",
    "đặc sản", "ẩm thực", "food tour", "nhậu", "bia",
    "bún cá", "bánh căn", "tôm hùm", "cá ngừ", "sò huyết",
]


@dataclass
class TravelCompanionState:
    mood: str = "neutral"
    stress: float = 0.0
    excitement: float = 0.0
    fatigue: float = 0.0
    confusion: float = 0.0
    overwhelm: float = 0.0
    signals: list[str] = field(default_factory=list)
    response_mode: str = "balanced"
    proactive_hints: list[str] = field(default_factory=list)


class TravelCompanionEngine:
    def assess(
        self,
        context: UserContext,
        incoming_text: str,
        intent: AssistantIntent | None = None,
        now: datetime | None = None,
    ) -> TravelCompanionState:
        local_now = self._to_local_now(context, now)
        normalized = incoming_text.lower().strip()
        state = TravelCompanionState()

        recent_user_turns = [turn for turn in context.conversation[-8:] if turn.role == "user"]
        rapid_turns = self._count_recent_turns(recent_user_turns, local_now, context)
        repeated_phrases = self._count_repeated_phrases(recent_user_turns, normalized)

        state.stress += self._score_markers(normalized, STRESS_MARKERS, 0.22, state, "stress_signal")
        state.confusion += self._score_markers(normalized, CONFUSION_MARKERS, 0.18, state, "confusion_signal")
        state.excitement += self._score_markers(normalized, EXCITEMENT_MARKERS, 0.18, state, "excitement_signal")
        state.fatigue += self._score_markers(normalized, FATIGUE_MARKERS, 0.22, state, "fatigue_signal")

        if rapid_turns >= 3:
            state.overwhelm += 0.22
            state.stress += 0.1
            state.signals.append("rapid_search_pattern")
        if repeated_phrases >= 2:
            state.confusion += 0.16
            state.overwhelm += 0.16
            state.signals.append("repeated_question_pattern")
        if any(marker in normalized for marker in LOCATION_CHANGE_MARKERS) and rapid_turns >= 2:
            state.stress += 0.14
            state.signals.append("repeated_location_changes")
        if any(marker in normalized for marker in WEATHER_MARKERS):
            state.signals.append("weather_context")
        if any(marker in normalized for marker in TRANSPORT_MARKERS):
            state.signals.append("transport_context")
        if any(marker in normalized for marker in RELAXED_MARKERS):
            state.excitement += 0.08
            state.signals.append("slow_exploration_interest")

        if local_now.hour >= 22 or local_now.hour <= 5:
            state.fatigue += 0.18
            if rapid_turns >= 2:
                state.stress += 0.12
                state.signals.append("late_night_rapid_searches")

        state.stress = min(state.stress, 1.0)
        state.excitement = min(state.excitement, 1.0)
        state.fatigue = min(state.fatigue, 1.0)
        state.confusion = min(state.confusion, 1.0)
        state.overwhelm = min(state.overwhelm, 1.0)

        state.mood = self._infer_mood(state)
        state.response_mode = self._infer_response_mode(state)
        state.proactive_hints = self._build_proactive_hints(normalized, local_now, state, intent)
        return state

    def adapt_reply(
        self,
        reply_text: str,
        state: TravelCompanionState,
        intent: AssistantIntent | None = None,
    ) -> str:
        if not reply_text:
            return reply_text

        lines = [line for line in reply_text.splitlines() if line.strip()]
        text = reply_text

        if state.response_mode == "comfort":
            body = self._compress_lines(lines, limit=4)
            prefix = "Mình chốt gọn cho đỡ rối nhé."
            text = "\n".join([prefix, body]).strip()
        elif state.response_mode == "energize":
            body = self._compress_lines(lines, limit=6)
            prefix = "Mood này hợp đi thêm một chút đó."
            text = "\n".join([prefix, body]).strip()
        elif state.response_mode == "clarify":
            body = self._compress_lines(lines, limit=5)
            prefix = "Mình gom lại ngắn gọn để bạn dễ chọn."
            text = "\n".join([prefix, body]).strip()

        if state.proactive_hints:
            hints = "\n".join(f"• {hint}" for hint in state.proactive_hints[:2])
            text = f"{text}\n\nGợi ý nhanh:\n{hints}"
        return text

    def _to_local_now(self, context: UserContext, now: datetime | None) -> datetime:
        ref = now or datetime.now(ZoneInfo(context.timezone))
        if ref.tzinfo is None:
            return ref.replace(tzinfo=ZoneInfo(context.timezone))
        return ref.astimezone(ZoneInfo(context.timezone))

    def _count_recent_turns(self, turns, local_now: datetime, context: UserContext) -> int:
        count = 0
        for turn in turns[-6:]:
            turn_local = turn.timestamp.astimezone(ZoneInfo(context.timezone))
            if (local_now - turn_local).total_seconds() <= 20 * 60:
                count += 1
        return count

    def _count_repeated_phrases(self, turns, normalized: str) -> int:
        if not normalized:
            return 0
        phrases = [turn.text.lower().strip() for turn in turns[-6:]]
        return sum(1 for phrase in phrases if phrase and phrase == normalized)

    def _score_markers(
        self,
        normalized: str,
        markers: list[str],
        step: float,
        state: TravelCompanionState,
        signal_name: str,
    ) -> float:
        hits = sum(1 for marker in markers if marker in normalized)
        if hits:
            state.signals.append(signal_name)
        return min(hits * step, 0.44)

    def _infer_mood(self, state: TravelCompanionState) -> str:
        if state.stress >= 0.35 or state.overwhelm >= 0.3:
            return "stressed"
        if state.fatigue >= 0.35:
            return "fatigued"
        if state.excitement >= 0.32:
            return "excited"
        return "neutral"

    def _infer_response_mode(self, state: TravelCompanionState) -> str:
        if state.stress >= 0.35 or state.overwhelm >= 0.3 or state.fatigue >= 0.35:
            return "comfort"
        if state.confusion >= 0.3:
            return "clarify"
        if state.excitement >= 0.32:
            return "energize"
        return "balanced"

    def _build_proactive_hints(
        self,
        normalized: str,
        local_now: datetime,
        state: TravelCompanionState,
        intent: AssistantIntent | None,
    ) -> list[str]:
        hints: list[str] = []
        domain = intent.domain if intent else "general"

        if any(marker in normalized for marker in FOOD_MARKERS):
            if 10 <= local_now.hour <= 12:
                hints.append("Khoảng 45 phút nữa dễ đông quán trưa, nếu chốt nhanh mình sẽ ưu tiên chỗ gần và dễ ngồi.")
            elif 17 <= local_now.hour <= 19:
                hints.append("Khung giờ này dễ đói và đông, mình có thể chốt 1-2 quán gần nhất thay vì dàn quá nhiều lựa chọn.")

        if domain == "travel" or any(marker in normalized for marker in WEATHER_MARKERS):
            if 15 <= local_now.hour <= 17:
                hints.append("Nếu muốn ngắm hoàng hôn hoặc chụp ảnh, mình sẽ ưu tiên điểm đến trước 17:30 để không bị gấp.")
            hints.append("Nếu trời đổi nhanh hoặc có mưa, mình sẽ tự nghiêng về phương án ít di chuyển và dễ trú hơn.")

        if any(marker in normalized for marker in PHOTO_MARKERS) and 15 <= local_now.hour <= 18:
            hints.append("Khung giờ này ánh sáng đẹp, mình có thể ưu tiên quán view hoặc điểm chụp ảnh trước khi mặt trời xuống.")

        if state.response_mode == "comfort":
            hints.append("Nếu bạn đang mệt, mình sẽ mặc định rút còn 1-2 lựa chọn dễ đi và ít đổi chỗ.")

        deduped: list[str] = []
        for hint in hints:
            if hint not in deduped:
                deduped.append(hint)
        return deduped[:2]

    def _compress_lines(self, lines: list[str], limit: int) -> str:
        if not lines:
            return ""
        return "\n".join(lines[:limit])
