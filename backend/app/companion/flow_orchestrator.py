"""
DailyFlowOrchestrator — one emotionally smooth experience flow.

Instead of answering "where to go?" in isolation, this module understands
the shape of the ENTIRE DAY and suggests what comes NEXT naturally.

A good travel day has emotional rhythm:
  energized morning → active midday → rest → sunset → dinner → wind-down

The orchestrator knows:
  - What phase of the day it is
  - What the group has already done
  - Their current energy level
  - What's still optimal (timing windows closing soon)

Output: a FlowSuggestion that the companion uses to proactively guide,
not just reactively answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


# ── Flow phases ───────────────────────────────────────────────────────────────

FLOW_PHASES = {
    "early_morning":    (4, 7),    # Mũi Điện sunrise window
    "morning":          (7, 10),   # Gành Đá Đĩa, breakfast, markets
    "midday_rest":      (10, 14),  # Avoid heat, indoor, rest
    "afternoon_active": (14, 17),  # Beach, Bãi Xép, gentle activities
    "golden_hour":      (17, 19),  # Sunset spots, cafe view, photography
    "dinner":           (19, 21),  # Seafood, local food
    "night_wind_down":  (21, 24),  # Light stroll, bar, early rest
}

# What's IDEAL for each phase
PHASE_IDEALS: dict[str, dict] = {
    "early_morning": {
        "activity": "Mũi Điện bình minh",
        "note": "Cửa sổ 4h30–6h30. Nếu không đi được thì skip, không đáng mất ngủ.",
        "energy_required": 0.6,
    },
    "morning": {
        "activity": "Gành Đá Đĩa hoặc ăn sáng địa phương",
        "note": "Trước 9h ít người nhất. Sau 9h bắt đầu nắng và đông.",
        "energy_required": 0.4,
    },
    "midday_rest": {
        "activity": "Nghỉ ngơi + cafe điều hòa",
        "note": "Nắng gắt 10h–14h — không nên hoạt động ngoài trời. Đây là thời gian nạp năng lượng.",
        "energy_required": 0.0,
    },
    "afternoon_active": {
        "activity": "Bãi Xép hoặc Bãi Bàng",
        "note": "Sóng nhỏ, nước mát. An toàn cho bé. Tắm biển trước khi trời tối.",
        "energy_required": 0.3,
    },
    "golden_hour": {
        "activity": "Cafe view hoàng hôn",
        "note": "17h–18h30 là khung đẹp nhất. Bãi Xép hoặc phố cà phê Tuy Hòa.",
        "energy_required": 0.2,
    },
    "dinner": {
        "activity": "Hải sản tươi hoặc đặc sản địa phương",
        "note": "Cá ngừ đại dương câu tay hoặc hải sản khu cảng cá — đặt trước nếu cả nhóm 8 người.",
        "energy_required": 0.1,
    },
    "night_wind_down": {
        "activity": "Dạo biển hoặc về nghỉ sớm",
        "note": "Nếu mai còn lịch sáng sớm (Gành Đá Đĩa / Mũi Điện) thì về nghỉ trước 22h.",
        "energy_required": 0.0,
    },
}

# Places already visited → skip them next time
_SKIP_IF_VISITED = {
    "Gành Đá Đĩa", "Mũi Điện", "Bãi Xép", "Đầm Ô Loan",
    "Hòn Yến", "Bãi Môn", "Vịnh Hòa",
}


@dataclass
class FlowSuggestion:
    """What the AI recommends as the NEXT move in the day's flow."""
    phase: str
    next_activity: str
    timing_note: str           # urgency / window closing
    energy_note: str           # tailored to current fatigue
    micro_moment: str          # "Giờ này quán còn yên — hợp nghỉ nhẹ"
    skip_reason: str = ""      # why we skipped the ideal activity
    urgency: str = "normal"    # "now"|"soon"|"flexible"|"skip"
    prompt_context: str = ""   # what to inject into LLM


class DailyFlowOrchestrator:
    """
    Knows the shape of the ideal day and guides the user through it
    one emotionally appropriate step at a time.
    """

    def suggest_next(
        self,
        now: datetime,
        fatigue: float,
        places_visited: list[str],
        crowd_tolerance: str = "medium",
        movement_tolerance: str = "medium",
    ) -> FlowSuggestion:
        phase = self._get_phase(now.hour)
        ideal = PHASE_IDEALS.get(phase, PHASE_IDEALS["midday_rest"])

        # Check if user has energy for the ideal activity
        energy_ok = fatigue <= (1.0 - ideal["energy_required"])

        # Check if ideal place already visited
        already_done = any(p in ideal["activity"] for p in places_visited)

        # Check movement resistance
        resists_movement = movement_tolerance in ("low", "resistance")

        # Build suggestion
        if not energy_ok or already_done or resists_movement:
            return self._fallback_suggestion(
                phase, fatigue, already_done, resists_movement, now
            )

        micro = self._micro_moment(phase, now)
        prompt = self._build_prompt_context(phase, ideal, fatigue, crowd_tolerance)

        return FlowSuggestion(
            phase=phase,
            next_activity=ideal["activity"],
            timing_note=ideal["note"],
            energy_note=self._energy_note(fatigue),
            micro_moment=micro,
            urgency=self._urgency(phase, now),
            prompt_context=prompt,
        )

    def _get_phase(self, hour: int) -> str:
        for phase, (start, end) in FLOW_PHASES.items():
            if start <= hour < end:
                return phase
        return "night_wind_down"

    def _micro_moment(self, phase: str, now: datetime) -> str:
        h = now.hour
        if phase == "golden_hour":
            mins_left = max(0, (18 * 60 + 30) - (h * 60 + now.minute))
            if mins_left < 45:
                return f"Còn khoảng {mins_left} phút ánh sáng đẹp — đi nhanh là kịp."
            return "Giờ này ánh sáng đang vào đỉnh, hợp nhất để ra bãi hay cafe view."
        if phase == "morning":
            if h < 8:
                return "Giờ này Gành Đá Đĩa đang ít người nhất trong ngày."
            return "Sau 9h sẽ bắt đầu đông và nắng — chốt nhanh nếu muốn đi."
        if phase == "midday_rest":
            return "Giờ này quán cafe còn yên, nắng ngoài trời đang gắt nhất — hợp ngồi trong."
        if phase == "afternoon_active":
            return "Biển giờ này mát, sóng nhỏ — thời điểm tốt nhất cho bé tắm biển."
        if phase == "dinner":
            return "Giờ này quán hải sản chưa đông đỉnh — vào sớm chọn được chỗ ngồi tốt."
        return ""

    def _urgency(self, phase: str, now: datetime) -> str:
        if phase == "golden_hour":
            mins_left = max(0, (18 * 60 + 30) - (now.hour * 60 + now.minute))
            return "now" if mins_left < 30 else "soon"
        if phase == "morning" and now.hour >= 9:
            return "soon"
        if phase == "early_morning" and now.hour >= 6:
            return "skip"
        return "flexible"

    def _energy_note(self, fatigue: float) -> str:
        if fatigue >= 0.8:
            return "Mệt rồi — bỏ qua bước này, nghỉ ngơi quan trọng hơn."
        if fatigue >= 0.6:
            return "Năng lượng hơi thấp — chọn hoạt động ngắn, gần."
        if fatigue >= 0.4:
            return "Năng lượng ổn — không vội, đi từ từ."
        return "Năng lượng tốt — có thể đi theo kế hoạch đầy đủ."

    def _fallback_suggestion(
        self,
        phase: str,
        fatigue: float,
        already_done: bool,
        resists: bool,
        now: datetime,
    ) -> FlowSuggestion:
        if fatigue >= 0.7:
            activity = "Nghỉ ngơi — cafe gần nhất hoặc về phòng"
            note = "Năng lượng thấp. Không cần đi thêm."
            skip = "high_fatigue"
        elif already_done:
            activity = "Đã ghé điểm đó rồi — khám phá điểm khác gần đây"
            note = "Chọn điểm chưa đến để tránh lặp lại."
            skip = "already_visited"
        elif resists:
            activity = "Chỗ gần nhất phù hợp với giờ này"
            note = "Không cần đi xa — mình tìm chỗ gần."
            skip = "movement_resistance"
        else:
            activity = PHASE_IDEALS.get(phase, {}).get("activity", "Nghỉ ngơi")
            note = ""
            skip = ""

        return FlowSuggestion(
            phase=phase,
            next_activity=activity,
            timing_note=note,
            energy_note=self._energy_note(fatigue),
            micro_moment=self._micro_moment(phase, now),
            skip_reason=skip,
            urgency="flexible",
            prompt_context=(
                f"Phase: {phase}. Gợi ý: {activity}. "
                f"Lý do điều chỉnh: {skip or 'adjusted for context'}."
            ),
        )

    def _build_prompt_context(
        self,
        phase: str,
        ideal: dict,
        fatigue: float,
        crowd_tolerance: str,
    ) -> str:
        parts = [
            f"Giai đoạn trong ngày: {phase}.",
            f"Hoạt động lý tưởng tiếp theo: {ideal['activity']}.",
            ideal["note"],
        ]
        if fatigue >= 0.5:
            parts.append("Lưu ý: người dùng đang có dấu hiệu mệt — rút ngắn kế hoạch nếu cần.")
        if crowd_tolerance == "low":
            parts.append("Người dùng không thích đông — ưu tiên địa điểm ít người.")
        return " ".join(parts)

    def format_for_prompt(self, suggestion: FlowSuggestion) -> str:
        """Compact prompt injection."""
        if not suggestion.next_activity:
            return ""
        lines = [f"## Flow tiếp theo: {suggestion.next_activity}"]
        if suggestion.micro_moment:
            lines.append(f"Micro-moment: {suggestion.micro_moment}")
        if suggestion.urgency in ("now", "soon"):
            lines.append(f"Urgency: {suggestion.urgency} — cần nhắc user.")
        if suggestion.energy_note:
            lines.append(f"Energy: {suggestion.energy_note}")
        return "\n".join(lines)
