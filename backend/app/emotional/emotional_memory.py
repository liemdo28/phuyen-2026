from __future__ import annotations

from dataclasses import dataclass, field

from app.models.domain import UserContext
from app.services.travel_companion import TravelCompanionState


@dataclass
class EmotionalMemorySnapshot:
    dominant_mood: str = "neutral"
    stress_baseline: float = 0.0
    fatigue_baseline: float = 0.0
    excitement_baseline: float = 0.0
    confusion_baseline: float = 0.0
    burnout_risk: float = 0.0
    notes: list[str] = field(default_factory=list)


class EmotionalMemoryEngine:
    def build_snapshot(self, context: UserContext, current: TravelCompanionState) -> EmotionalMemorySnapshot:
        prefs = context.preferences
        stress_baseline = float(prefs.get("stress_baseline", current.stress))
        fatigue_baseline = float(prefs.get("fatigue_baseline", current.fatigue))
        excitement_baseline = float(prefs.get("excitement_baseline", current.excitement))
        confusion_baseline = float(prefs.get("confusion_baseline", current.confusion))

        burnout_risk = min(
            1.0,
            current.stress * 0.35
            + current.fatigue * 0.35
            + current.overwhelm * 0.2
            + confusion_baseline * 0.1,
        )

        notes: list[str] = []
        if burnout_risk >= 0.45:
            notes.append("User đang có dấu hiệu mệt cảm xúc, nên ưu tiên guidance ngắn và ít quyết định.")
        if excitement_baseline >= 0.35:
            notes.append("User thường phản ứng tốt với trải nghiệm có cảm giác khám phá hoặc khoảnh khắc đẹp.")

        return EmotionalMemorySnapshot(
            dominant_mood=current.mood,
            stress_baseline=stress_baseline,
            fatigue_baseline=fatigue_baseline,
            excitement_baseline=excitement_baseline,
            confusion_baseline=confusion_baseline,
            burnout_risk=burnout_risk,
            notes=notes,
        )

    def preference_updates(self, current: TravelCompanionState) -> dict[str, float]:
        return {
            "stress_baseline": round(current.stress, 2),
            "fatigue_baseline": round(current.fatigue, 2),
            "excitement_baseline": round(current.excitement, 2),
            "confusion_baseline": round(current.confusion, 2),
        }
