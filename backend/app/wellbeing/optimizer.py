from __future__ import annotations

from dataclasses import dataclass, field

from app.emotional.journey_modeler import EmotionalJourneyState
from app.fatigue.energy_engine import TravelEnergyState
from app.life.context_engine import LifeContextState
from app.life.rhythm_memory import LifeRhythmState


@dataclass
class WellbeingScore:
    overall: float = 0.5              # composite wellbeing 0–1
    emotional_quality: float = 0.5
    recovery_quality: float = 0.5
    exploration_quality: float = 0.5
    comfort_quality: float = 0.5
    social_quality: float = 0.5
    grade: str = "neutral"            # thriving | good | neutral | stressed | critical
    primary_need: str = "balance"     # rest | stimulation | social | solitude | comfort | exploration


@dataclass
class WellbeingOptimizationState:
    score: WellbeingScore = field(default_factory=WellbeingScore)
    optimize_for: str = "balance"     # rest | calmness | recovery | exploration | social | joy
    itinerary_density: str = "medium" # minimal | light | medium | full | dense
    decision_load: str = "normal"     # minimal | low | normal | high
    social_inclusion: str = "optional" # none | optional | encouraged | required
    quiet_spaces_priority: bool = False
    recovery_windows_required: bool = False
    spontaneity_allowed: bool = True
    wellbeing_insights: list[str] = field(default_factory=list)
    optimization_rationale: str = ""


class WellbeingOptimizer:
    """
    Human Wellbeing Optimizer: goal shifts from maximizing activity
    to maximizing wellbeing. Optimizes for emotional calmness, recovery,
    meaningful experiences, low stress, and balanced energy.
    The trip should feel emotionally smooth, deeply memorable, naturally balanced.
    """

    def optimize(
        self,
        life_context: LifeContextState,
        life_rhythm: LifeRhythmState,
        energy: TravelEnergyState,
        emotional: EmotionalJourneyState,
    ) -> WellbeingOptimizationState:
        state = WellbeingOptimizationState()

        # --- Compute wellbeing dimensions ---
        emotional_quality = max(0.0, min(1.0,
            emotional.emotional_rhythm * 0.5 +
            (1.0 - emotional.stress_accumulation) * 0.3 +
            life_context.emotional_baseline * 0.2
        ))
        recovery_quality = max(0.0, min(1.0,
            (1.0 - emotional.burnout_risk) * 0.5 +
            energy.physical_energy * 0.3 +
            (1.0 - life_context.recovery_need) * 0.2
        ))
        exploration_quality = max(0.0, min(1.0,
            energy.exploration_readiness * 0.5 +
            life_context.emotional_baseline * 0.3 +
            (1.0 - life_context.lifestyle_pressure) * 0.2
        ))
        comfort_quality = max(0.0, min(1.0,
            energy.emotional_energy * 0.4 +
            (1.0 - life_context.work_stress_level) * 0.35 +
            (1.0 - emotional.stress_accumulation) * 0.25
        ))
        social_quality = max(0.0, min(1.0,
            life_context.social_energy * 0.6 +
            (1.0 - emotional.stress_accumulation) * 0.4
        ))

        overall = (
            emotional_quality * 0.25 +
            recovery_quality * 0.25 +
            comfort_quality * 0.2 +
            exploration_quality * 0.15 +
            social_quality * 0.15
        )

        score = WellbeingScore(
            overall=round(overall, 3),
            emotional_quality=round(emotional_quality, 3),
            recovery_quality=round(recovery_quality, 3),
            exploration_quality=round(exploration_quality, 3),
            comfort_quality=round(comfort_quality, 3),
            social_quality=round(social_quality, 3),
        )

        # Grade
        if overall >= 0.75:
            score.grade = "thriving"
        elif overall >= 0.58:
            score.grade = "good"
        elif overall >= 0.42:
            score.grade = "neutral"
        elif overall >= 0.28:
            score.grade = "stressed"
        else:
            score.grade = "critical"

        # Primary need
        dimensions = {
            "rest": 1.0 - recovery_quality,
            "stimulation": 1.0 - exploration_quality,
            "social": abs(life_context.social_energy - 0.5) if life_context.social_energy > 0.6 else 0.0,
            "solitude": abs(life_context.social_energy - 0.5) if life_context.social_energy < 0.4 else 0.0,
            "comfort": 1.0 - comfort_quality,
        }
        score.primary_need = max(dimensions.items(), key=lambda x: x[1])[0]

        state.score = score

        # --- Optimization directives ---
        # Life-context recovery need overrides grade for protect/recovery logic
        high_recovery_need = life_context.recovery_need > 0.55 or life_context.burnout_detected

        if score.grade == "critical" or (high_recovery_need and recovery_quality < 0.35):
            state.optimize_for = "recovery"
            state.itinerary_density = "minimal"
            state.decision_load = "minimal"
            state.quiet_spaces_priority = True
            state.recovery_windows_required = True
            state.spontaneity_allowed = False
            state.social_inclusion = "none"
        elif score.grade == "stressed" or high_recovery_need:
            state.optimize_for = "calmness"
            state.itinerary_density = "light"
            state.decision_load = "low"
            state.quiet_spaces_priority = True
            state.recovery_windows_required = True
            state.social_inclusion = "optional"
        elif life_rhythm.needs_exploration and score.grade in ("good", "thriving"):
            state.optimize_for = "exploration"
            state.itinerary_density = "full"
            state.decision_load = "normal"
            state.social_inclusion = "optional"
            state.spontaneity_allowed = True
        elif life_context.social_energy > 0.65:
            state.optimize_for = "social"
            state.itinerary_density = "medium"
            state.social_inclusion = "encouraged"
        elif life_context.social_energy < 0.35:
            state.optimize_for = "solitude"
            state.itinerary_density = "light"
            state.quiet_spaces_priority = True
            state.social_inclusion = "none"
        elif score.grade == "thriving":
            state.optimize_for = "joy"
            state.itinerary_density = "full"
            state.spontaneity_allowed = True
        else:
            state.optimize_for = "balance"
            state.itinerary_density = "medium"

        # --- Wellbeing insights ---
        insights: list[str] = []
        if score.grade == "critical" or (high_recovery_need and recovery_quality < 0.35):
            insights.append(
                "Sức khỏe tinh thần và thể chất đang ở mức báo động — chuyến đi cần được thiết kế như một liệu pháp, không phải một lịch trình."
            )
        elif score.grade == "stressed" or high_recovery_need:
            insights.append(
                "Mục tiêu chuyến đi lúc này không phải 'thật nhiều điểm' mà là 'thật sâu và thật thư thái'."
            )
        elif score.grade == "thriving":
            insights.append("Bạn đang ở trạng thái tốt nhất — đây là lúc để tạo ra những kỷ niệm thật sự đáng nhớ.")
        elif state.optimize_for == "exploration":
            insights.append("Năng lượng và cảm xúc đang tốt — thời điểm lý tưởng để khám phá sâu hơn, không chỉ lướt qua.")

        state.wellbeing_insights = insights
        state.optimization_rationale = self._build_rationale(state, score, life_context)
        return state

    def _build_rationale(
        self,
        state: WellbeingOptimizationState,
        score: WellbeingScore,
        life_context: LifeContextState,
    ) -> str:
        if state.optimize_for == "recovery":
            return "Tối ưu hóa cho phục hồi: ít di chuyển, ít quyết định, nhiều không gian yên tĩnh."
        if state.optimize_for == "calmness":
            return "Tối ưu hóa cho sự bình yên: lịch trình nhẹ, không gian yên tĩnh, nhịp chậm."
        if state.optimize_for == "exploration":
            return "Tối ưu hóa cho khám phá: lịch trình đầy đủ, tự do quyết định, trải nghiệm sâu."
        if state.optimize_for == "social":
            return "Tối ưu hóa cho kết nối xã hội: điểm đến phù hợp nhóm, không khí vui vẻ."
        if state.optimize_for == "solitude":
            return "Tối ưu hóa cho không gian riêng: yên tĩnh, ít người, tự do khám phá cá nhân."
        if state.optimize_for == "joy":
            return "Tối ưu hóa cho niềm vui: tự do khám phá, không ràng buộc lịch trình chặt."
        return "Cân bằng tất cả các chiều: tốc độ vừa phải, linh hoạt, phù hợp trạng thái hiện tại."
