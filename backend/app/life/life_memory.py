from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.models.domain import UserContext

_LM_PREFIX = "lm_"


@dataclass
class LifeMoment:
    moment_id: str
    moment_type: str        # joy | calm | discovery | connection | challenge | milestone
    description: str
    location: str = ""
    emotional_intensity: float = 0.5
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LifeMemoryState:
    meaningful_moments: list[dict] = field(default_factory=list)
    favorite_places: list[str] = field(default_factory=list)
    emotional_milestones: list[str] = field(default_factory=list)
    life_stage: str = "active"          # young_explorer | career_focused | family | retirement | active
    travel_life_chapter: str = "ongoing" # just_started | growing | experienced | reflective
    meaningful_count: int = 0
    top_emotions: list[str] = field(default_factory=list)
    life_memory_insights: list[str] = field(default_factory=list)
    continuity_message: str = ""        # AI continuity statement across years


class LifeMemoryEngine:
    """
    Life Memory Engine: remembers meaningful travel moments, favorite places,
    emotional milestones, and life-stage travel patterns across years.
    Enables emotional continuity — the AI feels present and aware across time.
    """

    def assess(self, context: UserContext) -> LifeMemoryState:
        prefs = context.preferences
        state = LifeMemoryState()

        moments: list[dict] = list(prefs.get(f"{_LM_PREFIX}moments", []))[-10:]
        favorite_places: list[str] = list(prefs.get(f"{_LM_PREFIX}favorite_places", []))
        milestones: list[str] = list(prefs.get(f"{_LM_PREFIX}milestones", []))
        life_stage: str = str(prefs.get(f"{_LM_PREFIX}life_stage", "active"))
        total_moments = int(prefs.get(f"{_LM_PREFIX}total_moments", 0))
        top_emotions: list[str] = list(prefs.get(f"{_LM_PREFIX}top_emotions", []))

        # Infer travel chapter
        if total_moments == 0:
            chapter = "just_started"
        elif total_moments < 5:
            chapter = "growing"
        elif total_moments < 15:
            chapter = "experienced"
        else:
            chapter = "reflective"

        # Life memory insights
        insights: list[str] = []
        continuity_message = ""

        if favorite_places:
            place_list = "、".join(favorite_places[:3])
            insights.append(f"Những nơi bạn thật sự yêu thích: {place_list}.")

        if milestones:
            insights.append(f"Kỷ niệm đáng nhớ nhất: {milestones[0]}")

        if chapter == "reflective" and total_moments >= 15:
            continuity_message = (
                "Mình đã đồng hành với bạn qua nhiều chuyến đi. "
                "Mỗi lần bạn quay lại, mình nhớ bạn thích gì và cần gì — "
                "để hành trình lần này thật sự là của bạn."
            )
        elif chapter == "experienced":
            continuity_message = (
                "Qua các chuyến đi trước, mình đã hiểu dần phong cách và cảm xúc của bạn. "
                "Lần này sẽ gợi ý sát hơn với những gì bạn thật sự tìm kiếm."
            )
        elif chapter == "growing":
            continuity_message = (
                "Mình nhớ những lần trước và đang học dần để hiểu bạn hơn."
            )

        if "joy" in top_emotions:
            insights.append("Những khoảnh khắc vui vẻ nhất của bạn thường gắn với sự bất ngờ và tự do.")
        if "calm" in top_emotions:
            insights.append("Bạn tìm thấy sự bình yên thật sự trong những không gian yên tĩnh và ít người.")

        state.meaningful_moments = moments
        state.favorite_places = favorite_places[:6]
        state.emotional_milestones = milestones[:4]
        state.life_stage = life_stage
        state.travel_life_chapter = chapter
        state.meaningful_count = total_moments
        state.top_emotions = top_emotions[:4]
        state.life_memory_insights = insights[:2]
        state.continuity_message = continuity_message
        return state

    def record_moment(self, context: UserContext, moment: LifeMoment) -> dict[str, Any]:
        """Returns preference updates after recording a meaningful life moment."""
        prefs = context.preferences
        moments: list[dict] = list(prefs.get(f"{_LM_PREFIX}moments", []))
        favorites: list[str] = list(prefs.get(f"{_LM_PREFIX}favorite_places", []))
        milestones: list[str] = list(prefs.get(f"{_LM_PREFIX}milestones", []))
        top_emotions: list[str] = list(prefs.get(f"{_LM_PREFIX}top_emotions", []))
        total = int(prefs.get(f"{_LM_PREFIX}total_moments", 0)) + 1

        moments.append({
            "id": moment.moment_id,
            "type": moment.moment_type,
            "desc": moment.description,
            "loc": moment.location,
            "intensity": moment.emotional_intensity,
        })
        if moment.location and moment.location not in favorites and moment.emotional_intensity > 0.6:
            favorites.append(moment.location)
        if moment.moment_type == "milestone" and moment.description not in milestones:
            milestones.append(moment.description)
        if moment.moment_type not in top_emotions and moment.emotional_intensity > 0.65:
            top_emotions.append(moment.moment_type)

        return {
            f"{_LM_PREFIX}moments": moments[-12:],
            f"{_LM_PREFIX}favorite_places": favorites[-8:],
            f"{_LM_PREFIX}milestones": milestones[-6:],
            f"{_LM_PREFIX}top_emotions": top_emotions[-6:],
            f"{_LM_PREFIX}total_moments": total,
        }
