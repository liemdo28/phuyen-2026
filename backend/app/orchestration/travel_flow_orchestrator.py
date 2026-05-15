from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

# ---------------------------------------------------------------------------
# Day arc: the natural rhythm of a travel day
# ---------------------------------------------------------------------------

DayPhase = Literal[
    "pre_dawn",    # 0–5h  — sleeping / very early start
    "sunrise",     # 5–7h  — sunrise activities, Mũi Điện
    "breakfast",   # 7–9h  — local breakfast window
    "morning",     # 9–11h — active exploration
    "midday",      # 11–14h — heat peak, rest, lunch
    "afternoon",   # 14–17h — second wind, lighter activities
    "golden_hour", # 17–19h — sunset, beach, photography
    "dinner",      # 19–21h — seafood, local restaurants
    "night",       # 21–23h — nightlife, market, wind-down
    "late_night",  # 23–0h  — very late, return to hotel
]

FlowPosture = Literal[
    "energize",    # user has energy, push to explore
    "sustain",     # moderate energy, keep comfortable pace
    "rest",        # fatigue high, reduce movement
    "recover",     # burnout, minimal activity
    "flexible",    # no strong signal
]

# Each phase's characteristics
_PHASE_ENERGY_COST: dict[str, float] = {
    "pre_dawn": 0.0,
    "sunrise": 0.8,      # high energy cost — early wake
    "breakfast": 0.2,
    "morning": 0.6,
    "midday": 0.3,       # rest window, low cost
    "afternoon": 0.5,
    "golden_hour": 0.4,
    "dinner": 0.2,
    "night": 0.3,
    "late_night": 0.4,
}

# Recommended activity types per phase
_PHASE_ACTIVITIES: dict[str, list[str]] = {
    "pre_dawn": [],
    "sunrise": ["Mũi Điện", "Gành Đá Đĩa", "sunrise_beach"],
    "breakfast": ["Bún cá ngừ", "Bánh mì", "local_cafe", "street_food"],
    "morning": ["Gành Đá Đĩa", "Hòn Yến", "Bãi Xép", "Đầm Ô Loan", "snorkeling"],
    "midday": ["hotel_pool", "local_restaurant", "indoor_cafe", "rest"],
    "afternoon": ["Vịnh Hòa", "Bãi biển Tuy Hòa", "Tháp Nhạn", "Đầm Ô Loan"],
    "golden_hour": ["Bãi Xép sunset", "Bãi biển Tuy Hòa", "Mũi Điện view", "photography"],
    "dinner": ["Hải sản Sông Cầu", "Cá ngừ đại dương", "Tôm hùm bông", "Phố Trần Phú"],
    "night": ["Chợ đêm", "Phố Trần Phú", "local_bar", "wind_down"],
    "late_night": ["hotel_return"],
}

PHU_YEN_DAY_ARCS: list[list[str]] = [
    ["Gành Đá Đĩa", "Hòn Yến breakfast", "Vịnh Hòa", "Hải sản Sông Cầu"],
    ["Mũi Điện sunrise", "Bãi Xép morning", "local_lunch", "sunset beach", "Phố Trần Phú dinner"],
    ["Đầm Ô Loan kayak", "Tháp Nhạn", "hotel_pool", "Cá ngừ đại dương dinner"],
    ["Tuy Hòa beach morning", "local_cafe", "Chợ Tuy Hòa", "rest", "Sông Cầu seafood"],
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FlowActivity:
    name: str
    name_vn: str
    phase: DayPhase
    energy_cost: float        # 0.0–1.0
    duration_minutes: int
    location: str
    tags: list[str] = field(default_factory=list)
    weather_sensitive: bool = False
    crowd_sensitive: bool = False


@dataclass
class TravelFlowState:
    current_phase: DayPhase
    posture: FlowPosture
    suggested_next: list[FlowActivity]
    completed_today: list[str]       # activity names completed
    energy_remaining: float          # 0.0–1.0
    day_arc_progress: float          # 0.0–1.0
    transitions_today: int           # how many phase transitions happened
    hint: str                        # Vietnamese natural language guidance
    signals: list[str] = field(default_factory=list)
    simplify_decisions: bool = False  # true when decision fatigue high
    max_suggestions: int = 3


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class TravelFlowOrchestrator:
    """
    Orchestrates the travel experience as ONE connected daily arc.
    Tracks: breakfast → beaches → cafes → sunset → dinner → rest

    Takes current time, fatigue, weather and returns:
    - what phase the traveler is in
    - recommended next activities (fatigue/weather/crowd aware)
    - Vietnamese hint about the natural flow
    """

    def __init__(self) -> None:
        self._completed_today: list[str] = []
        self._transitions_today: int = 0
        self._last_phase: DayPhase | None = None

    def assess(
        self,
        hour: int,
        fatigue: float,
        weather_risk: float,
        tourist_density: float,
        incoming_text: str = "",
        preferences: dict | None = None,
    ) -> TravelFlowState:
        preferences = preferences or {}
        phase = _hour_to_phase(hour)

        # Track transitions
        if self._last_phase and self._last_phase != phase:
            self._transitions_today += 1
        self._last_phase = phase

        posture = _resolve_posture(fatigue, weather_risk)
        energy_remaining = max(0.0, 1.0 - fatigue)
        day_arc_progress = _phase_progress(phase)

        suggested = self._build_suggestions(
            phase, posture, weather_risk, tourist_density,
            fatigue, preferences, incoming_text,
        )

        simplify = fatigue > 0.65 or self._transitions_today >= 4
        max_suggestions = 1 if fatigue > 0.8 else (2 if fatigue > 0.5 else 3)

        hint = _build_hint(phase, posture, fatigue, weather_risk, suggested)

        return TravelFlowState(
            current_phase=phase,
            posture=posture,
            suggested_next=suggested[:max_suggestions],
            completed_today=list(self._completed_today),
            energy_remaining=round(energy_remaining, 2),
            day_arc_progress=round(day_arc_progress, 2),
            transitions_today=self._transitions_today,
            hint=hint,
            signals=_build_signals(phase, posture, fatigue, weather_risk),
            simplify_decisions=simplify,
            max_suggestions=max_suggestions,
        )

    def mark_completed(self, activity: str) -> None:
        if activity not in self._completed_today:
            self._completed_today.append(activity)

    def reset_day(self) -> None:
        self._completed_today = []
        self._transitions_today = 0
        self._last_phase = None

    # ------------------------------------------------------------------

    def _build_suggestions(
        self,
        phase: DayPhase,
        posture: FlowPosture,
        weather_risk: float,
        tourist_density: float,
        fatigue: float,
        preferences: dict,
        text: str,
    ) -> list[FlowActivity]:
        t = text.lower()
        activities: list[FlowActivity] = []

        # User expressed specific intent — prioritize that type
        wants_beach = any(w in t for w in ["biển", "tắm", "bãi", "sóng"])
        wants_food = any(w in t for w in ["ăn", "quán", "hải sản", "cơm", "phở"])
        wants_cafe = any(w in t for w in ["cafe", "cà phê", "chill"])
        wants_rest = any(w in t for w in ["nghỉ", "mệt", "về", "nằm"])

        if posture in ("rest", "recover"):
            activities = _rest_activities(phase)
        elif wants_beach and weather_risk < 0.6:
            activities = _beach_activities(phase, tourist_density)
        elif wants_food:
            activities = _food_activities(phase)
        elif wants_cafe:
            activities = _cafe_activities(phase)
        elif wants_rest:
            activities = _rest_activities(phase)
        else:
            activities = _default_activities(phase, weather_risk, tourist_density)

        # Filter out weather-sensitive if rain
        if weather_risk > 0.6:
            activities = [a for a in activities if not a.weather_sensitive]

        # Filter out crowd-sensitive if dense
        if tourist_density > 0.7:
            activities = [a for a in activities if not a.crowd_sensitive]

        # Filter already completed
        activities = [a for a in activities if a.name not in self._completed_today]

        return activities


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _hour_to_phase(hour: int) -> DayPhase:
    if hour < 5:
        return "pre_dawn"
    if hour < 7:
        return "sunrise"
    if hour < 9:
        return "breakfast"
    if hour < 11:
        return "morning"
    if hour < 14:
        return "midday"
    if hour < 17:
        return "afternoon"
    if hour < 19:
        return "golden_hour"
    if hour < 21:
        return "dinner"
    if hour < 23:
        return "night"
    return "late_night"


def _resolve_posture(fatigue: float, weather_risk: float) -> FlowPosture:
    if fatigue >= 0.85:
        return "recover"
    if fatigue >= 0.65 or weather_risk >= 0.75:
        return "rest"
    if fatigue >= 0.40 or weather_risk >= 0.50:
        return "sustain"
    if fatigue < 0.30:
        return "energize"
    return "flexible"


def _phase_progress(phase: DayPhase) -> float:
    order = ["pre_dawn", "sunrise", "breakfast", "morning", "midday",
             "afternoon", "golden_hour", "dinner", "night", "late_night"]
    idx = order.index(phase) if phase in order else 0
    return round(idx / (len(order) - 1), 2)


def _build_hint(
    phase: DayPhase,
    posture: FlowPosture,
    fatigue: float,
    weather_risk: float,
    suggestions: list[FlowActivity],
) -> str:
    if posture == "recover":
        return "Bạn đang khá mệt — mình gợi ý nghỉ ngơi, lấy lại sức trước khi tiếp tục."
    if posture == "rest" and weather_risk > 0.6:
        return "Thời tiết không thuận lắm, mình nghĩ ở trong cafe hoặc nghỉ tại khách sạn sẽ tốt hơn."
    if posture == "rest":
        return "Mình thấy bạn đang hơi mệt — nên giảm nhịp lại, chọn chỗ thoải mái hơn."
    if phase == "midday" and fatigue > 0.4:
        return "Khung giờ này khá nắng và đông — phù hợp để nghỉ trưa hoặc ngồi cafe nhẹ nhàng."
    if phase == "golden_hour":
        return "Đây là khung giờ vàng — hợp nhất để ra biển hoặc chụp ảnh hoàng hôn."
    if phase == "breakfast":
        return "Bắt đầu ngày mới — bữa sáng local sẽ là trải nghiệm tốt để khởi động."
    if suggestions:
        return f"Gợi ý tiếp theo: {suggestions[0].name_vn}."
    return "Mình đang theo dõi để hỗ trợ bạn tốt nhất."


def _build_signals(phase: DayPhase, posture: FlowPosture, fatigue: float, weather: float) -> list[str]:
    signals = [f"phase_{phase}", f"posture_{posture}"]
    if fatigue > 0.7:
        signals.append("high_fatigue")
    if weather > 0.6:
        signals.append("weather_risk")
    return signals


def _beach_activities(phase: DayPhase, density: float) -> list[FlowActivity]:
    quiet = density < 0.5
    activities = []
    if phase in ("sunrise", "morning"):
        activities.append(FlowActivity("Gành Đá Đĩa", "Gành Đá Đĩa — đá bazan tuyệt đẹp", phase, 0.6, 120, "An Ninh Đông", weather_sensitive=True))
        if quiet:
            activities.append(FlowActivity("Hòn Yến", "Hòn Yến — san hô, lặn ngắm", phase, 0.7, 150, "Hòn Yến", weather_sensitive=True))
    if phase in ("morning", "afternoon"):
        activities.append(FlowActivity("Bãi Xép", "Bãi Xép — bãi phim Hoa Vàng", phase, 0.5, 120, "Bãi Xép", weather_sensitive=True))
        activities.append(FlowActivity("Vịnh Hòa", "Vịnh Hòa — ít người, yên tĩnh", phase, 0.5, 120, "Vịnh Hòa", weather_sensitive=True, crowd_sensitive=True))
    if phase == "golden_hour":
        activities.append(FlowActivity("Sunset Bãi Xép", "Hoàng hôn Bãi Xép", phase, 0.3, 60, "Bãi Xép"))
        activities.append(FlowActivity("Sunset Tuy Hòa", "Hoàng hôn bãi biển Tuy Hòa", phase, 0.2, 60, "Tuy Hòa Beach"))
    return activities


def _food_activities(phase: DayPhase) -> list[FlowActivity]:
    if phase == "breakfast":
        return [
            FlowActivity("Bún cá ngừ", "Bún cá ngừ sáng — đặc sản Phú Yên", phase, 0.1, 45, "Phố Trần Phú"),
            FlowActivity("Bánh mì Phú Yên", "Bánh mì local buổi sáng", phase, 0.1, 20, "Tuy Hòa"),
        ]
    if phase in ("midday", "afternoon"):
        return [
            FlowActivity("Cơm hến", "Cơm hến đặc sản trưa", phase, 0.1, 45, "Tuy Hòa"),
            FlowActivity("Bún sứa", "Bún sứa Phú Yên", phase, 0.1, 45, "Tuy Hòa"),
        ]
    if phase in ("dinner", "golden_hour"):
        return [
            FlowActivity("Hải sản Sông Cầu", "Hải sản Sông Cầu — tôm hùm, mực", phase, 0.2, 90, "Sông Cầu"),
            FlowActivity("Cá ngừ đại dương", "Cá ngừ câu tay sashimi/nướng", phase, 0.2, 90, "Tuy Hòa"),
        ]
    return []


def _cafe_activities(phase: DayPhase) -> list[FlowActivity]:
    return [
        FlowActivity("Local cafe", "Cafe local yên tĩnh", phase, 0.1, 60, "Tuy Hòa"),
        FlowActivity("View cafe", "Cafe view biển", phase, 0.1, 60, "Tuy Hòa Beach"),
    ]


def _rest_activities(phase: DayPhase) -> list[FlowActivity]:
    return [
        FlowActivity("Hotel pool", "Hồ bơi khách sạn — nghỉ nhẹ nhàng", phase, 0.1, 90, "Khách sạn"),
        FlowActivity("Indoor cafe", "Cafe mát, yên tĩnh", phase, 0.1, 60, "Tuy Hòa"),
    ]


def _default_activities(phase: DayPhase, weather: float, density: float) -> list[FlowActivity]:
    if weather > 0.6:
        return _rest_activities(phase) + _cafe_activities(phase)
    options = (
        _beach_activities(phase, density)
        or _food_activities(phase)
        or _cafe_activities(phase)
        or _rest_activities(phase)
    )
    return options
