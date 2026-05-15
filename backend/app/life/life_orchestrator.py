from __future__ import annotations

from dataclasses import dataclass, field

from app.dna.travel_dna import TravelDNAProfile
from app.emotional.journey_modeler import EmotionalJourneyState
from app.fatigue.energy_engine import TravelEnergyState
from app.life.context_engine import LifeContextState
from app.life.life_memory import LifeMemoryState
from app.life.rhythm_memory import LifeRhythmState
from app.wellbeing.calm_ux import CalmUXState
from app.wellbeing.optimizer import WellbeingOptimizationState


@dataclass
class LifeOrchestrationState:
    orchestration_mode: str = "travel"      # travel | recovery | exploration | social | reflective | life_balance
    travel_is_context: bool = False         # True when travel is just one part of a life session
    primary_life_goal: str = "enjoy_trip"
    wellbeing_first: bool = False
    trip_as_therapy: bool = False
    suggested_trip_type: str = "normal"     # normal | recovery | micro_escape | deep_dive | social | solo
    daily_rhythm_aligned: bool = True
    life_balance_score: float = 0.5
    orchestration_insights: list[str] = field(default_factory=list)
    companion_message: str = ""             # The AI's "voice" as life companion


class LifeOrchestrator:
    """
    AI Life Orchestration: quietly helps orchestrate travel, recovery,
    exploration, social balance, wellbeing, and life rhythm — without
    becoming intrusive, addictive, or overwhelming.
    Travel is one context inside a larger lifestyle intelligence layer.
    The AI eventually feels less like software, more like a calm
    intelligent companion throughout life.
    """

    def orchestrate(
        self,
        life_context: LifeContextState,
        life_rhythm: LifeRhythmState,
        life_memory: LifeMemoryState,
        emotional: EmotionalJourneyState,
        energy: TravelEnergyState,
        wellbeing: WellbeingOptimizationState,
        calm_ux: CalmUXState,
        dna: TravelDNAProfile,
    ) -> LifeOrchestrationState:
        state = LifeOrchestrationState()

        # Is travel just one context in a broader life moment?
        state.travel_is_context = life_context.life_mode in (
            "recovery", "escape", "reflective", "social"
        )

        # Determine orchestration mode
        if life_context.burnout_detected:
            state.orchestration_mode = "recovery"
            state.primary_life_goal = "restore_energy"
            state.wellbeing_first = True
            state.trip_as_therapy = True
            state.suggested_trip_type = "recovery"
        elif life_context.life_mode == "escape":
            state.orchestration_mode = "recovery"
            state.primary_life_goal = "decompress"
            state.wellbeing_first = True
            state.suggested_trip_type = "micro_escape"
        elif life_context.life_mode == "social":
            state.orchestration_mode = "social"
            state.primary_life_goal = "connect"
            state.suggested_trip_type = "social"
        elif life_context.life_mode == "reflective":
            state.orchestration_mode = "reflective"
            state.primary_life_goal = "self_discovery"
            state.suggested_trip_type = "solo"
        elif life_rhythm.needs_exploration and wellbeing.score.grade in ("good", "thriving"):
            state.orchestration_mode = "exploration"
            state.primary_life_goal = "discover"
            state.suggested_trip_type = "deep_dive"
        else:
            state.orchestration_mode = "travel"
            state.primary_life_goal = "enjoy_trip"
            state.suggested_trip_type = "normal"

        # Daily rhythm alignment
        state.daily_rhythm_aligned = not (
            life_rhythm.energy_cycle_phase == "recovery" and
            wellbeing.itinerary_density in ("full", "dense")
        )

        # Life balance score
        state.life_balance_score = round(
            wellbeing.score.overall * 0.5 +
            (1.0 - life_context.work_stress_level) * 0.25 +
            (1.0 - emotional.burnout_risk) * 0.25,
            3,
        )

        # Orchestration insights
        insights: list[str] = []
        if state.trip_as_therapy:
            insights.append(
                "Chuyến đi này quan trọng hơn một kỳ nghỉ thông thường — "
                "đây là không gian để bạn phục hồi và tái kết nối với bản thân."
            )
        elif state.suggested_trip_type == "deep_dive":
            insights.append(
                "Bạn đang ở trạng thái lý tưởng để khám phá sâu — "
                "không chỉ là checklist địa điểm mà là trải nghiệm thật sự."
            )
        elif state.orchestration_mode == "social":
            insights.append("Năng lượng xã hội đang cao — lịch trình sẽ ưu tiên những không gian vui, kết nối.")
        elif state.orchestration_mode == "reflective":
            insights.append("Chuyến đi sẽ nhẹ nhàng và có ý nghĩa — không gian để suy nghĩ và chiêm nghiệm.")

        if life_memory.continuity_message:
            insights.append(life_memory.continuity_message)

        if not state.daily_rhythm_aligned:
            insights.append("Lịch trình đang không khớp với chu kỳ năng lượng của bạn — mình sẽ điều chỉnh cho phù hợp hơn.")

        # Build companion voice
        state.companion_message = self._build_companion_voice(state, dna, life_context, calm_ux)
        state.orchestration_insights = insights[:2]
        return state

    def _build_companion_voice(
        self,
        state: LifeOrchestrationState,
        dna: TravelDNAProfile,
        life_context: LifeContextState,
        calm_ux: CalmUXState,
    ) -> str:
        if calm_ux.invisible_mode:
            return ""  # invisible mode: AI stays silent unless asked

        if state.trip_as_therapy:
            return (
                "Mình ở đây — không ép bạn làm gì cả. "
                "Khi bạn muốn gợi ý, chỉ cần hỏi. Khi bạn chỉ muốn yên tĩnh, mình cũng biết lúc nào nên im."
            )
        if state.orchestration_mode == "exploration" and dna.dna_type == "adventure_traveler":
            return "Hành trình của bạn, nhịp độ của bạn — mình chỉ là người dẫn đường khi cần."
        if state.orchestration_mode == "reflective":
            return "Một số chuyến đi thay đổi cách nhìn — mình sẽ giúp bạn tìm những khoảnh khắc đó."
        if dna.dna_type == "calm_explorer":
            return "Không vội, không ồn — mình hiểu bạn thích như thế nào."
        if life_context.life_mode == "escape":
            return "Đây là thời gian của bạn. Tắt hết đi, mình lo phần còn lại."
        return ""
