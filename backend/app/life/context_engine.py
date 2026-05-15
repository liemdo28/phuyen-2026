from __future__ import annotations

from dataclasses import dataclass, field

from app.models.domain import UserContext

# Life-context signal tokens — inferred from conversation, not explicit inputs
WORK_STRESS_TOKENS = [
    "công việc", "deadline", "họp", "sếp", "áp lực", "dự án", "overtime",
    "làm thêm", "căng thẳng", "mệt vì làm",
]
RECOVERY_TOKENS = [
    "nghỉ ngơi", "cần nghỉ", "kiệt sức", "muốn nghỉ", "burn out", "burnout",
    "không nổi nữa", "cần nạp năng lượng", "nạp pin", "recharge",
]
SOCIAL_ENERGY_HIGH = [
    "bạn bè", "hội bạn", "nhóm", "party", "tiệc", "cùng nhau", "đi chơi cùng",
    "gặp gỡ", "tụ tập",
]
SOCIAL_ENERGY_LOW = [
    "một mình", "solo", "yên tĩnh", "không muốn gặp ai", "cần không gian riêng",
    "tránh xa", "ẩn", "im lặng",
]
EMOTIONAL_LOW_TOKENS = [
    "buồn", "chán", "trống rỗng", "cô đơn", "không vui", "thất vọng",
    "không có hứng", "flat", "meh",
]
EMOTIONAL_HIGH_TOKENS = [
    "vui", "hào hứng", "năng lượng", "sẵn sàng", "tuyệt vời", "thích quá",
    "excited", "hạnh phúc", "phấn khởi",
]
BURNOUT_SIGNALS = [
    "quá tải", "overwhelm", "quá nhiều thứ", "không thở được", "bão não",
    "muốn biến mất", "cần thoát", "đủ rồi", "không muốn nghĩ",
]
LIFESTYLE_BUSY = [
    "bận", "không có thời gian", "lịch kín", "không rảnh", "tight schedule",
    "ít thời gian", "tranh thủ",
]
LIFESTYLE_FREE = [
    "rảnh", "thoải mái", "không vội", "có thời gian", "thư thả",
    "không có gì đặc biệt", "tự do",
]


@dataclass
class LifeContextState:
    work_stress_level: float = 0.0      # 0=none, 1=extreme
    recovery_need: float = 0.0          # 0=not needed, 1=critical
    social_energy: float = 0.5          # 0=needs solitude, 1=needs people
    emotional_baseline: float = 0.5     # 0=low, 1=high
    lifestyle_pressure: float = 0.5     # 0=free, 1=packed schedule
    burnout_detected: bool = False
    life_mode: str = "normal"           # normal | recovery | escape | exploration | social | reflective
    life_insights: list[str] = field(default_factory=list)
    travel_recommendation_bias: str = "balanced"  # slow | recovery | social | solo | active


class LifeContextEngine:
    """
    Understands the traveler's life context beyond travel: work stress,
    recovery needs, social energy, emotional state, lifestyle pressure,
    and burnout signals. Travel recommendations adapt to life condition.
    """

    _DECAY = 0.82

    def assess(self, context: UserContext, incoming_text: str) -> LifeContextState:
        text = incoming_text.lower()
        history = " ".join(t.text.lower() for t in context.conversation[-20:] if t.role == "user")
        combined = f"{history} {text}".strip()
        prefs = context.preferences
        state = LifeContextState()

        # Score raw signals
        work_stress = min(1.0, sum(1 for t in WORK_STRESS_TOKENS if t in combined) * 0.22)
        recovery = min(1.0, sum(1 for t in RECOVERY_TOKENS if t in combined) * 0.28)
        social_high = min(1.0, sum(1 for t in SOCIAL_ENERGY_HIGH if t in combined) * 0.2)
        social_low = min(1.0, sum(1 for t in SOCIAL_ENERGY_LOW if t in combined) * 0.25)
        emo_high = min(1.0, sum(1 for t in EMOTIONAL_HIGH_TOKENS if t in combined) * 0.2)
        emo_low = min(1.0, sum(1 for t in EMOTIONAL_LOW_TOKENS if t in combined) * 0.22)
        burnout_raw = min(1.0, sum(1 for t in BURNOUT_SIGNALS if t in combined) * 0.35)
        busy = min(1.0, sum(1 for t in LIFESTYLE_BUSY if t in combined) * 0.2)
        free = min(1.0, sum(1 for t in LIFESTYLE_FREE if t in combined) * 0.18)

        # Retrieve persisted life context
        prev_work_stress = float(prefs.get("life_work_stress", 0.0))
        prev_recovery = float(prefs.get("life_recovery_need", 0.0))
        prev_social = float(prefs.get("life_social_energy", 0.5))
        prev_emo = float(prefs.get("life_emotional_baseline", 0.5))
        prev_lifestyle = float(prefs.get("life_lifestyle_pressure", 0.5))

        # EMA updates
        d = 1 - self._DECAY
        if work_stress > 0:
            prev_work_stress = min(1.0, prev_work_stress * self._DECAY + work_stress * d)
        if recovery > 0:
            prev_recovery = min(1.0, prev_recovery * self._DECAY + recovery * d)
        if social_high > 0:
            prev_social = min(1.0, prev_social * self._DECAY + social_high * d)
        if social_low > 0:
            prev_social = max(0.0, prev_social * self._DECAY - social_low * d)
        if emo_high > 0:
            prev_emo = min(1.0, prev_emo * self._DECAY + emo_high * d)
        if emo_low > 0:
            prev_emo = max(0.0, prev_emo * self._DECAY - emo_low * d)
        if busy > 0:
            prev_lifestyle = min(1.0, prev_lifestyle * self._DECAY + busy * d)
        if free > 0:
            prev_lifestyle = max(0.0, prev_lifestyle * self._DECAY - free * d)

        state.work_stress_level = round(prev_work_stress, 3)
        state.recovery_need = round(max(prev_recovery, burnout_raw * 0.8), 3)
        state.social_energy = round(prev_social, 3)
        state.emotional_baseline = round(prev_emo, 3)
        state.lifestyle_pressure = round(prev_lifestyle, 3)
        state.burnout_detected = burnout_raw > 0.25 or prev_recovery > 0.6

        # Determine life mode
        if state.burnout_detected or state.recovery_need > 0.55:
            state.life_mode = "recovery"
            state.travel_recommendation_bias = "recovery"
        elif state.work_stress_level > 0.5 and state.lifestyle_pressure > 0.55:
            state.life_mode = "escape"
            state.travel_recommendation_bias = "slow"
        elif state.social_energy > 0.65:
            state.life_mode = "social"
            state.travel_recommendation_bias = "social"
        elif state.social_energy < 0.35:
            state.life_mode = "reflective"
            state.travel_recommendation_bias = "solo"
        elif state.emotional_baseline > 0.65 and state.lifestyle_pressure < 0.4:
            state.life_mode = "exploration"
            state.travel_recommendation_bias = "active"
        else:
            state.life_mode = "normal"
            state.travel_recommendation_bias = "balanced"

        # Life insights
        insights: list[str] = []
        if state.life_mode == "recovery":
            insights.append(
                "Bạn đang cần nghỉ ngơi thật sự — không phải chuyến đi bận rộn, "
                "mà là không gian để thoát khỏi áp lực và nạp lại năng lượng."
            )
        elif state.life_mode == "escape":
            insights.append(
                "Với áp lực công việc hiện tại, chuyến đi lý tưởng là nơi yên tĩnh, "
                "ít quyết định, và không cần lịch trình dày đặc."
            )
        elif state.life_mode == "social":
            insights.append("Bạn đang có năng lượng xã hội cao — lý tưởng để khám phá cùng nhóm hoặc gặp gỡ thêm người.")
        elif state.life_mode == "reflective":
            insights.append("Bạn cần không gian riêng để suy nghĩ và tái kết nối với bản thân.")
        elif state.life_mode == "exploration":
            insights.append("Trạng thái sống tốt và thời gian thoải mái — đây là lúc khám phá sâu hơn.")

        state.life_insights = insights
        return state
