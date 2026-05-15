from __future__ import annotations

from dataclasses import dataclass, field

from app.dna.travel_dna import TravelDNAProfile
from app.emotional.journey_modeler import EmotionalJourneyState
from app.life.context_engine import LifeContextState
from app.wellbeing.optimizer import WellbeingOptimizationState


@dataclass
class CalmUXState:
    hint_count_limit: int = 2           # max hints to surface to user
    reply_length_mode: str = "normal"   # minimal | short | normal | detailed
    proactive_level: str = "quiet"      # silent | quiet | gentle | active
    notification_suppressed: bool = False
    decision_simplification: bool = False
    invisible_mode: bool = False        # true when AI should just quietly help
    tone: str = "warm"                  # warm | energetic | calm | supportive | minimal
    sentence_count_limit: int = 4
    calm_signals: list[str] = field(default_factory=list)
    ux_rationale: str = ""


class CalmTechnologyEngine:
    """
    Calm Technology UX: ensures the AI helps quietly, avoids overwhelming
    the user, minimizes notifications, and reduces digital noise.
    The best AI behavior feels almost invisible — present when needed,
    absent when not. Never intrusive, addictive, or overwhelming.
    """

    def assess(
        self,
        life_context: LifeContextState,
        emotional: EmotionalJourneyState,
        wellbeing: WellbeingOptimizationState,
        dna: TravelDNAProfile,
    ) -> CalmUXState:
        state = CalmUXState()

        grade = wellbeing.score.grade
        optimize_for = wellbeing.optimize_for
        life_mode = life_context.life_mode
        dna_interaction = dna.interaction_style

        # --- Hint count ---
        if grade in ("critical", "stressed") or emotional.decision_fatigue:
            state.hint_count_limit = 1
        elif grade == "thriving" and optimize_for == "exploration":
            state.hint_count_limit = 3
        else:
            state.hint_count_limit = 2

        # --- Reply length ---
        if emotional.decision_fatigue or grade == "critical":
            state.reply_length_mode = "minimal"
            state.sentence_count_limit = 2
        elif grade == "stressed" or life_mode in ("recovery", "escape"):
            state.reply_length_mode = "short"
            state.sentence_count_limit = 3
        elif dna_interaction == "minimal_push":
            state.reply_length_mode = "short"
            state.sentence_count_limit = 3
        elif dna_interaction in ("enthusiastic", "proactive_suggestions"):
            state.reply_length_mode = "detailed"
            state.sentence_count_limit = 6
        else:
            state.reply_length_mode = "normal"
            state.sentence_count_limit = 4

        # --- Proactive level ---
        if grade in ("critical", "stressed") or emotional.burnout_risk > 0.6:
            state.proactive_level = "silent"
            state.notification_suppressed = True
        elif life_mode in ("recovery", "reflective") or dna_interaction == "minimal_push":
            state.proactive_level = "quiet"
        elif dna_interaction in ("enthusiastic", "proactive_suggestions"):
            state.proactive_level = "active"
        elif grade == "thriving":
            state.proactive_level = "gentle"
        else:
            state.proactive_level = "quiet"

        # --- Decision simplification ---
        state.decision_simplification = (
            emotional.decision_fatigue or
            grade in ("critical", "stressed") or
            dna.decision_tolerance in ("very_low", "low")
        )

        # --- Invisible mode ---
        state.invisible_mode = (
            grade == "critical" or
            (life_mode == "recovery" and emotional.burnout_risk > 0.5) or
            dna_interaction == "minimal_push"
        )

        # --- Tone ---
        if grade in ("critical", "stressed") or emotional.burnout_risk > 0.5:
            state.tone = "supportive"
        elif life_mode == "reflective":
            state.tone = "calm"
        elif dna_interaction in ("enthusiastic", "proactive_suggestions"):
            state.tone = "energetic"
        elif grade == "thriving" and optimize_for == "joy":
            state.tone = "warm"
        elif state.invisible_mode:
            state.tone = "minimal"
        else:
            state.tone = "warm"

        # --- Calm signals for the reply composer ---
        if state.invisible_mode:
            state.calm_signals.append("invisible_assist")
        if state.decision_simplification:
            state.calm_signals.append("simplify_choices")
        if state.proactive_level == "silent":
            state.calm_signals.append("no_unsolicited_hints")
        if state.notification_suppressed:
            state.calm_signals.append("suppress_notifications")
        if state.reply_length_mode == "minimal":
            state.calm_signals.append("ultra_brief_reply")

        state.ux_rationale = self._build_rationale(state, grade, life_mode)
        return state

    def _build_rationale(self, state: CalmUXState, grade: str, life_mode: str) -> str:
        if state.invisible_mode:
            return "AI hoạt động trong chế độ im lặng — chỉ xuất hiện khi thật sự cần thiết."
        if state.proactive_level == "quiet":
            return "AI giúp nhẹ nhàng, không dồn thêm thông tin vào không gian tinh thần của bạn."
        if state.proactive_level == "active" and grade == "thriving":
            return "Trạng thái tốt — AI có thể chủ động hơn với những gợi ý phù hợp."
        return "AI điều chỉnh để hỗ trợ vừa đủ, không gây thêm nhận thức tải."
