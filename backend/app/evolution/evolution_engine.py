from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.emotional.journey_modeler import EmotionalJourneyState
from app.learning.feedback_engine import FeedbackState
from app.memory.long_term_memory import LongTermMemoryState
from app.models.domain import UserContext


@dataclass
class EvolutionSignal:
    dimension: str
    direction: str   # improve | degrade | stable
    magnitude: float = 0.0
    confidence: float = 0.0
    source: str = ""


@dataclass
class EvolutionState:
    recommendation_quality_score: float = 0.5
    adaptation_velocity: float = 0.0    # how fast the AI is adapting
    learning_signals: list[EvolutionSignal] = field(default_factory=list)
    evolved_preferences: dict[str, Any] = field(default_factory=dict)
    evolution_insights: list[str] = field(default_factory=list)
    intelligence_level: str = "learning"  # learning | adapting | evolved | instinctive
    quality_trend: str = "stable"         # improving | stable | declining
    instinct_signals: list[str] = field(default_factory=list)


class EvolutionEngine:
    """
    Self-evolution engine: continuously improves recommendation quality,
    detects intelligence growth across dimensions, and evolves the AI from
    rule-based toward instinctive travel intelligence.

    Progression: learning → adapting → evolved → instinctive
    """

    _QUALITY_DECAY = 0.9
    _VELOCITY_DECAY = 0.85

    def evolve(
        self,
        context: UserContext,
        feedback: FeedbackState,
        emotional: EmotionalJourneyState,
        memory: LongTermMemoryState,
    ) -> EvolutionState:
        prefs = context.preferences
        state = EvolutionState()

        # Retrieve evolution baseline
        prev_quality = float(prefs.get("evo_quality_score", 0.5))
        prev_velocity = float(prefs.get("evo_adaptation_velocity", 0.0))
        total_interactions = int(prefs.get("evo_total_interactions", 0)) + 1
        correct_calls = int(prefs.get("evo_correct_calls", 0))
        avoided_burnout_count = int(prefs.get("evo_avoided_burnout", 0))

        # --- Recommendation quality scoring ---
        quality_delta = 0.0
        if feedback.acceptance_rate > 0.6:
            quality_delta += 0.06
        if feedback.skip_rate > 0.45:
            quality_delta -= 0.04
        if emotional.burnout_risk < 0.3 and emotional.journey_phase == "active":
            quality_delta += 0.04
            correct_calls += 1
        if emotional.emotional_safety_needed:
            quality_delta -= 0.03
        if memory.has_history and memory.repeat_destination_count > 1:
            quality_delta += 0.03  # cross-trip learning is working

        new_quality = min(1.0, max(0.0, prev_quality * self._QUALITY_DECAY + quality_delta))
        quality_trend = "improving" if new_quality > prev_quality + 0.01 else (
            "declining" if new_quality < prev_quality - 0.01 else "stable"
        )

        # --- Adaptation velocity ---
        velocity_delta = 0.0
        if feedback.patterns:
            velocity_delta += len(feedback.patterns) * 0.025
        if memory.has_history:
            velocity_delta += 0.03
        if len(feedback.avoid_types) + len(feedback.amplify_types) > 2:
            velocity_delta += 0.04

        new_velocity = min(1.0, max(0.0, prev_velocity * self._VELOCITY_DECAY + velocity_delta))

        # --- Intelligence level progression ---
        level = "learning"
        if total_interactions >= 5 and new_quality > 0.55:
            level = "adapting"
        if total_interactions >= 15 and new_quality > 0.68 and new_velocity > 0.3:
            level = "evolved"
        if total_interactions >= 30 and new_quality > 0.80 and memory.has_history and new_velocity > 0.5:
            level = "instinctive"

        # --- Evolution signals ---
        signals: list[EvolutionSignal] = []
        if quality_trend == "improving":
            signals.append(EvolutionSignal(
                dimension="recommendation_quality",
                direction="improve",
                magnitude=quality_delta,
                confidence=min(1.0, total_interactions / 20),
                source="acceptance_feedback",
            ))
        if new_velocity > 0.3:
            signals.append(EvolutionSignal(
                dimension="adaptation_speed",
                direction="improve",
                magnitude=new_velocity,
                confidence=min(1.0, total_interactions / 15),
                source="behavioral_patterns",
            ))
        if memory.has_history:
            signals.append(EvolutionSignal(
                dimension="cross_trip_memory",
                direction="improve",
                magnitude=0.5,
                confidence=min(1.0, memory.repeat_destination_count / 3),
                source="long_term_memory",
            ))

        # --- Instinct signals (what the AI now "knows" without being told) ---
        instinct: list[str] = []
        if level in ("evolved", "instinctive"):
            if feedback.quiet_preference > 0.6:
                instinct.append("quiet_spaces_preferred")
            if feedback.pacing_preference < 0.4:
                instinct.append("slow_pacing_natural")
            if memory.cross_trip_patterns.get("dominant_style") == "relax_traveler":
                instinct.append("rest_first_traveler")
            if avoided_burnout_count > 2:
                instinct.append("burnout_prevention_learned")

        # --- Evolved preferences to propagate ---
        evolved_prefs: dict[str, Any] = {
            "evo_quality_score": round(new_quality, 3),
            "evo_adaptation_velocity": round(new_velocity, 3),
            "evo_total_interactions": total_interactions,
            "evo_correct_calls": correct_calls,
            "evo_avoided_burnout": avoided_burnout_count,
            "evo_intelligence_level": level,
        }
        if feedback.evolution_signals:
            evolved_prefs.update(feedback.evolution_signals)

        # --- Insights ---
        evolution_insights: list[str] = []
        if level == "adapting":
            evolution_insights.append("AI đang học từ các chuyến đi của bạn và cải thiện gợi ý theo thời gian.")
        elif level == "evolved":
            evolution_insights.append("AI đã hiểu phong cách du lịch của bạn và có thể dự đoán nhu cầu trước.")
        elif level == "instinctive":
            evolution_insights.append(
                "AI đã phát triển 'bản năng du lịch' — hiểu khi nào bạn cần nghỉ, khi nào nên khám phá, "
                "và khi nào nên tạo ra khoảnh khắc đáng nhớ mà không cần bạn yêu cầu."
            )

        state.recommendation_quality_score = round(new_quality, 3)
        state.adaptation_velocity = round(new_velocity, 3)
        state.learning_signals = signals
        state.evolved_preferences = evolved_prefs
        state.evolution_insights = evolution_insights
        state.intelligence_level = level
        state.quality_trend = quality_trend
        state.instinct_signals = instinct
        return state
