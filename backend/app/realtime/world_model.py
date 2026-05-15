from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.models.domain import UserContext

WEATHER_TOKENS = ["mưa", "nắng", "giông", "gió", "nóng", "ẩm", "thời tiết"]
TRAFFIC_TOKENS = ["kẹt xe", "traffic", "đường đông", "grab", "taxi", "di chuyển", "về khách sạn"]
BEACH_TOKENS = ["biển", "bãi", "tắm", "sóng", "hòn", "sunset", "hoàng hôn"]
EVENT_TOKENS = ["event", "lễ", "festival", "chợ đêm", "nhạc", "sự kiện"]
BUSINESS_TOKENS = ["quán", "nhà hàng", "cafe", "cà phê", "seafood", "hải sản", "ăn gì"]
SAFETY_TOKENS = ["an toàn", "nguy hiểm", "vắng", "tối quá", "đêm khuya"]


@dataclass
class RealtimeWorldModel:
    weather_risk: float = 0.0
    traffic_pressure: float = 0.0
    beach_quality: float = 0.5
    tourist_density: float = 0.0
    local_activity: float = 0.0
    event_intensity: float = 0.0
    safety_risk: float = 0.0
    transport_flow: float = 0.0
    heat_pressure: float = 0.0
    signals: list[str] = field(default_factory=list)


class RealtimeWorldModelEngine:
    def assess(
        self,
        context: UserContext,
        incoming_text: str,
        now: datetime,
    ) -> RealtimeWorldModel:
        t = incoming_text.lower()
        hour = now.hour
        state = RealtimeWorldModel()

        state.weather_risk += self._score_matches(t, WEATHER_TOKENS, 0.16, state, "weather_signal")
        state.traffic_pressure += self._score_matches(t, TRAFFIC_TOKENS, 0.18, state, "traffic_signal")
        state.event_intensity += self._score_matches(t, EVENT_TOKENS, 0.16, state, "event_signal")
        state.local_activity += self._score_matches(t, BUSINESS_TOKENS, 0.12, state, "business_signal")
        state.safety_risk += self._score_matches(t, SAFETY_TOKENS, 0.2, state, "safety_signal")

        if any(token in t for token in BEACH_TOKENS):
            state.signals.append("beach_context")
            state.beach_quality += 0.12

        if 11 <= hour <= 14:
            state.heat_pressure = 0.72
            state.tourist_density += 0.22
            state.local_activity += 0.14
            state.signals.append("midday_heat_window")
        elif 17 <= hour <= 19:
            state.traffic_pressure += 0.32
            state.tourist_density += 0.18
            state.local_activity += 0.18
            state.transport_flow += 0.28
            state.signals.append("evening_peak_window")
        elif 6 <= hour <= 9:
            state.local_activity += 0.2
            state.transport_flow += 0.08
            state.signals.append("local_breakfast_window")
        elif 21 <= hour or hour <= 5:
            state.safety_risk += 0.22
            state.transport_flow += 0.12
            state.signals.append("late_night_window")

        if "mưa" in t or "giông" in t:
            state.beach_quality -= 0.22
        if "nắng" in t or "nóng" in t:
            state.heat_pressure = max(state.heat_pressure, 0.62)
        if "hoàng hôn" in t or "sunset" in t:
            state.beach_quality += 0.18
            state.signals.append("sunset_interest")

        state.tourist_density = min(max(state.tourist_density, 0.0), 1.0)
        state.local_activity = min(max(state.local_activity, 0.0), 1.0)
        state.event_intensity = min(max(state.event_intensity, 0.0), 1.0)
        state.safety_risk = min(max(state.safety_risk, 0.0), 1.0)
        state.transport_flow = min(max(state.transport_flow, 0.0), 1.0)
        state.traffic_pressure = min(max(state.traffic_pressure, 0.0), 1.0)
        state.weather_risk = min(max(state.weather_risk, 0.0), 1.0)
        state.beach_quality = min(max(state.beach_quality, 0.0), 1.0)
        state.heat_pressure = min(max(state.heat_pressure, 0.0), 1.0)
        return state

    def _score_matches(
        self,
        text: str,
        tokens: list[str],
        step: float,
        state: RealtimeWorldModel,
        signal_name: str,
    ) -> float:
        hits = sum(1 for token in tokens if token in text)
        if hits:
            state.signals.append(signal_name)
        return min(hits * step, 0.48)
