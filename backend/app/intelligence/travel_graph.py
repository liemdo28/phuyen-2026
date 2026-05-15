from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.behavior.profile_engine import TravelBehaviorProfile
from app.realtime.world_model import RealtimeWorldModel

# Phú Yên location intelligence graph — seeded with known patterns
_LOCATION_GRAPH: dict[str, dict] = {
    "bai_xep": {
        "name": "Bãi Xép",
        "comfort_score": 0.85,
        "stress_score": 0.10,
        "crowd_peak_hours": [10, 11, 14, 15],
        "best_hours": [6, 7, 17, 18],
        "traveler_fit": ["relax_traveler", "photographer", "explorer"],
        "emotional_tag": "relaxing",
        "keywords": ["bãi xép", "xep"],
    },
    "ganh_da_dia": {
        "name": "Gành Đá Đĩa",
        "comfort_score": 0.65,
        "stress_score": 0.35,
        "crowd_peak_hours": [9, 10, 11, 14],
        "best_hours": [6, 7, 16, 17],
        "traveler_fit": ["explorer", "photographer"],
        "emotional_tag": "energizing",
        "keywords": ["gành đá đĩa", "đá đĩa", "ganh"],
    },
    "mui_dien": {
        "name": "Mũi Điện",
        "comfort_score": 0.70,
        "stress_score": 0.22,
        "crowd_peak_hours": [10, 11],
        "best_hours": [5, 6, 7, 17, 18],
        "traveler_fit": ["explorer", "photographer", "relax_traveler"],
        "emotional_tag": "inspiring",
        "keywords": ["mũi điện", "mũi", "điện"],
    },
    "vung_ro": {
        "name": "Vũng Rô",
        "comfort_score": 0.78,
        "stress_score": 0.14,
        "crowd_peak_hours": [11, 12, 13],
        "best_hours": [7, 8, 16, 17],
        "traveler_fit": ["relax_traveler", "foodie", "explorer"],
        "emotional_tag": "relaxing",
        "keywords": ["vũng rô", "vũng"],
    },
    "tuy_hoa_center": {
        "name": "Trung tâm Tuy Hòa",
        "comfort_score": 0.55,
        "stress_score": 0.42,
        "crowd_peak_hours": [8, 9, 17, 18, 19],
        "best_hours": [6, 7, 21, 22],
        "traveler_fit": ["foodie", "spontaneous_traveler"],
        "emotional_tag": "stimulating",
        "keywords": ["tuy hòa", "tuy hoà", "thành phố", "trung tâm"],
    },
    "da_rang_river": {
        "name": "Sông Đà Rằng",
        "comfort_score": 0.72,
        "stress_score": 0.15,
        "crowd_peak_hours": [],
        "best_hours": [5, 6, 17, 18, 19],
        "traveler_fit": ["relax_traveler", "photographer"],
        "emotional_tag": "calming",
        "keywords": ["đà rằng", "sông", "hoàng hôn sông"],
    },
}


@dataclass
class LocationIntelligence:
    location_id: str
    name: str
    comfort_score: float = 0.5
    stress_score: float = 0.3
    timing_fit: float = 0.5  # how well current time matches best hours
    traveler_fit: float = 0.5
    emotional_tag: str = "neutral"
    is_peak_crowded: bool = False
    best_visit_hint: str = ""


@dataclass
class TravelGraphState:
    detected_location: str = ""
    location_intelligence: LocationIntelligence | None = None
    timing_score: float = 0.5
    emotional_context: str = "neutral"
    crowd_warning: bool = False
    avoid_now: bool = False
    graph_insights: list[str] = field(default_factory=list)
    timing_advice: str = ""


class TravelGraphEngine:
    """
    Global Travel Intelligence Graph — understands location behavior,
    crowd patterns, timing intelligence, and emotional location mapping.
    Learns which places feel relaxing vs. stressful at specific times.
    """

    def assess(
        self,
        incoming_text: str,
        now: datetime,
        world: RealtimeWorldModel,
        profile: TravelBehaviorProfile,
    ) -> TravelGraphState:
        text = incoming_text.lower()
        hour = now.hour
        state = TravelGraphState()

        # Detect which location is being referenced
        matched_key: str | None = None
        for loc_key, loc_data in _LOCATION_GRAPH.items():
            if any(kw in text for kw in loc_data["keywords"]):
                matched_key = loc_key
                break

        if not matched_key:
            return state

        loc = _LOCATION_GRAPH[matched_key]
        state.detected_location = matched_key

        is_peak = hour in loc["crowd_peak_hours"]
        is_best = hour in loc["best_hours"]
        traveler_fit = 1.0 if profile.primary_style in loc["traveler_fit"] else 0.4

        timing_fit = 0.85 if is_best else (0.2 if is_peak else 0.55)

        # World-adjusted stress/comfort
        comfort = loc["comfort_score"]
        stress = loc["stress_score"]
        if world.tourist_density > 0.4:
            stress += 0.15
            comfort -= 0.12
        if world.weather_risk > 0.3:
            stress += 0.1
            comfort -= 0.08
        if world.heat_pressure > 0.6:
            stress += 0.12

        state.location_intelligence = LocationIntelligence(
            location_id=matched_key,
            name=loc["name"],
            comfort_score=min(1.0, max(0.0, comfort)),
            stress_score=min(1.0, max(0.0, stress)),
            timing_fit=timing_fit,
            traveler_fit=traveler_fit,
            emotional_tag=loc["emotional_tag"],
            is_peak_crowded=is_peak,
            best_visit_hint=self._format_best_hours(loc["best_hours"]),
        )

        state.timing_score = timing_fit
        state.emotional_context = loc["emotional_tag"]
        state.crowd_warning = is_peak and world.tourist_density > 0.3
        state.avoid_now = is_peak and stress > 0.5

        # Generate insights
        insights: list[str] = []
        if is_peak and is_peak:
            insights.append(f"{loc['name']} hiện đang vào giờ cao điểm — có thể khá đông và ồn ào hơn thường.")
        if is_best:
            insights.append(f"Đây là khung giờ lý tưởng để ghé {loc['name']} — ít người và ánh sáng đẹp hơn.")
        if loc["emotional_tag"] == "relaxing" and profile.primary_style == "relax_traveler":
            insights.append(f"{loc['name']} rất phù hợp với phong cách du lịch của bạn — yên tĩnh và thoải mái.")
        if traveler_fit < 0.5:
            insights.append(f"{loc['name']} thường hợp hơn với khách thích khám phá hoặc chụp ảnh.")
        if state.avoid_now:
            best = self._format_best_hours(loc["best_hours"])
            insights.append(f"Nên ghé {loc['name']} vào {best} để có trải nghiệm tốt hơn.")

        state.graph_insights = insights[:2]
        if insights:
            state.timing_advice = insights[0]

        return state

    def _format_best_hours(self, hours: list[int]) -> str:
        if not hours:
            return "giờ linh hoạt"
        formatted = []
        for h in sorted(hours):
            if h < 12:
                formatted.append(f"{h}h sáng")
            elif h == 12:
                formatted.append("12h trưa")
            else:
                formatted.append(f"{h}h chiều/tối" if h >= 17 else f"{h}h chiều")
        return " hoặc ".join(formatted[:2])
