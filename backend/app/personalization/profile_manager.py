from __future__ import annotations

from dataclasses import dataclass, field

from app.behavior.profile_engine import TravelBehaviorProfile
from app.emotional.emotional_memory import EmotionalMemorySnapshot
from app.models.domain import UserContext
from app.orchestration.travel_operating_system import TravelOperatingState


@dataclass
class PersonalizationSnapshot:
    travel_style: str = "balanced"
    comfort_priority: float = 0.5
    crowd_tolerance: float = 0.5
    prefers_hidden_spots: bool = False
    prefers_photo_spots: bool = False
    prefers_food_experiences: bool = False
    low_friction_mode: bool = False
    notes: list[str] = field(default_factory=list)


class PersonalizationManager:
    def build_snapshot(
        self,
        context: UserContext,
        profile: TravelBehaviorProfile,
        emotional: EmotionalMemorySnapshot,
        operating: TravelOperatingState,
    ) -> PersonalizationSnapshot:
        prefs = context.preferences
        snapshot = PersonalizationSnapshot(
            travel_style=str(prefs.get("travel_primary_style", profile.primary_style)),
            comfort_priority=float(prefs.get("comfort_bias", profile.comfort_bias)),
            crowd_tolerance=float(prefs.get("crowd_tolerance", profile.crowd_tolerance)),
            prefers_hidden_spots=bool(profile.primary_style == "explorer" or prefs.get("prefers_slow_exploration")),
            prefers_photo_spots=bool(prefs.get("prefers_photo_spots") or profile.photo_bias >= 0.35),
            prefers_food_experiences=bool(prefs.get("prefers_food_experiences") or profile.food_bias >= 0.35),
            low_friction_mode=bool(
                operating.recommendation_posture == "protective"
                or emotional.burnout_risk >= 0.45
                or prefs.get("transport_sensitive")
            ),
        )
        if snapshot.low_friction_mode:
            snapshot.notes.append("Ưu tiên ít lựa chọn, ít di chuyển, ít context switching.")
        if snapshot.prefers_hidden_spots:
            snapshot.notes.append("Ưu tiên local/hidden spots hơn tourist traps nếu không làm tăng friction.")
        return snapshot
