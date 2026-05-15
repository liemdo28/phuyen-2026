from __future__ import annotations

from dataclasses import dataclass, field

from app.behavior.profile_engine import TravelBehaviorProfile
from app.fatigue.energy_engine import TravelEnergyState
from app.realtime.world_model import RealtimeWorldModel
from app.services.travel_companion import TravelCompanionState

STRESS_MARKERS = ["mệt", "chán", "ức", "stress", "bực", "lo", "sợ", "không ổn", "quá nhiều", "overwhelm"]
EXCITEMENT_MARKERS = ["vui", "thích", "tuyệt", "hay quá", "đẹp", "wow", "ổn", "ok", "thú vị"]
BURNOUT_MARKERS = ["thôi nghỉ", "về thôi", "không muốn", "đủ rồi", "mệt lắm", "nghỉ thôi", "không nổi"]
COMFORT_MARKERS = ["dễ chịu", "thoải mái", "ổn áp", "bình thường", "được", "ok bạn"]


@dataclass
class EmotionalJourneyState:
    emotional_rhythm: float = 0.6   # 0=burnout → 1=peak joy
    stress_accumulation: float = 0.0
    excitement_curve: float = 0.5
    recovery_timing: str = "not_needed"  # not_needed | soon | now | urgent
    burnout_risk: float = 0.0
    overload_detected: bool = False
    fatigue_detected: bool = False
    decision_fatigue: bool = False
    emotional_safety_needed: bool = False
    journey_phase: str = "active"  # warming_up | active | peak | declining | recovery
    insights: list[str] = field(default_factory=list)
    safety_alerts: list[str] = field(default_factory=list)


class EmotionalJourneyModeler:
    """
    Models emotional rhythm across a trip: stress curves, excitement decay,
    burnout risk, and recovery timing. Prevents emotional overload and decision fatigue
    while maximizing calmness and meaningful moments.
    """

    def assess(
        self,
        companion: TravelCompanionState,
        energy: TravelEnergyState,
        world: RealtimeWorldModel,
        profile: TravelBehaviorProfile,
        incoming_text: str = "",
    ) -> EmotionalJourneyState:
        text = incoming_text.lower()
        state = EmotionalJourneyState()

        # Detect emotional signals from incoming text
        stress_signal = sum(1 for m in STRESS_MARKERS if m in text) * 0.25
        excitement_signal = sum(1 for m in EXCITEMENT_MARKERS if m in text) * 0.18
        burnout_signal = sum(1 for m in BURNOUT_MARKERS if m in text) * 0.35
        comfort_signal = sum(1 for m in COMFORT_MARKERS if m in text) * 0.2

        # --- Stress accumulation model ---
        base_stress = companion.stress * 0.45 + companion.overwhelm * 0.3 + world.weather_risk * 0.1
        base_stress += stress_signal * 0.4
        base_stress -= comfort_signal * 0.2
        base_stress = min(1.0, max(0.0, base_stress))

        # --- Excitement curve (diminishes over time without novelty) ---
        excitement = companion.excitement * 0.5 + excitement_signal * 0.4
        excitement += world.beach_quality * 0.1
        excitement -= companion.fatigue * 0.15
        excitement = min(1.0, max(0.0, excitement))

        # --- Burnout risk model ---
        burnout = (
            companion.fatigue * 0.35
            + companion.overwhelm * 0.3
            + base_stress * 0.2
            + burnout_signal * 0.5
            + (1.0 - energy.physical_energy) * 0.15
        )
        burnout = min(1.0, max(0.0, burnout))

        # --- Emotional rhythm composite ---
        rhythm = (
            energy.emotional_energy * 0.4
            + excitement * 0.3
            + (1.0 - base_stress) * 0.2
            + (1.0 - burnout) * 0.1
        )
        rhythm = min(1.0, max(0.0, rhythm))

        # --- Journey phase detection ---
        phase = "active"
        if burnout > 0.55 or energy.rest_pressure > 0.55:
            phase = "declining"
        elif burnout > 0.75:
            phase = "recovery"
        elif excitement > 0.65 and energy.physical_energy > 0.6:
            phase = "peak"
        elif energy.physical_energy < 0.3:
            phase = "warming_up"

        # --- Recovery timing ---
        recovery_timing = "not_needed"
        if burnout > 0.75 or burnout_signal > 0.3:
            recovery_timing = "urgent"
        elif burnout > 0.55 or energy.rest_pressure > 0.5:
            recovery_timing = "now"
        elif burnout > 0.35 or energy.rest_pressure > 0.35:
            recovery_timing = "soon"

        # --- Detection flags ---
        overload = companion.overwhelm > 0.5 or (base_stress > 0.55 and companion.fatigue > 0.4)
        decision_fatigue = energy.decision_energy < 0.35 or companion.confusion > 0.4
        emotional_safety = burnout > 0.7 or (overload and base_stress > 0.6)

        # --- Vietnamese insights ---
        insights: list[str] = []
        safety_alerts: list[str] = []

        if phase == "peak":
            insights.append("Bạn đang trong trạng thái tốt nhất để khám phá — năng lượng và hứng thú đều cao.")
        elif phase == "declining":
            insights.append("Hôm nay bạn đã di chuyển khá nhiều. Tối nay nên chọn lịch trình nhẹ hơn để giữ sức cho ngày mai.")
        elif phase == "recovery":
            insights.append("Cơ thể và tâm trí cần được nghỉ ngơi. Mình gợi ý một buổi tối yên tĩnh, ít quyết định.")

        if decision_fatigue:
            insights.append("Bạn đang đối mặt với quá nhiều lựa chọn. Mình sẽ thu gọn gợi ý xuống 1–2 phương án rõ ràng.")

        if emotional_safety:
            safety_alerts.append("Phát hiện dấu hiệu kiệt sức cảm xúc — ưu tiên an toàn và nghỉ ngơi ngay bây giờ.")
        if base_stress > 0.5 and world.safety_risk > 0.3:
            safety_alerts.append("Cảm xúc + môi trường đang tạo áp lực kép. Hãy tìm không gian yên tĩnh gần nhất.")
        if burnout_signal > 0.2:
            safety_alerts.append("Mình nghe thấy bạn. Dừng lại và nghỉ ngơi là điều hoàn toàn đúng đắn lúc này.")

        state.emotional_rhythm = round(rhythm, 3)
        state.stress_accumulation = round(base_stress, 3)
        state.excitement_curve = round(excitement, 3)
        state.recovery_timing = recovery_timing
        state.burnout_risk = round(burnout, 3)
        state.overload_detected = overload
        state.fatigue_detected = companion.fatigue > 0.45
        state.decision_fatigue = decision_fatigue
        state.emotional_safety_needed = emotional_safety
        state.journey_phase = phase
        state.insights = insights
        state.safety_alerts = safety_alerts
        return state
