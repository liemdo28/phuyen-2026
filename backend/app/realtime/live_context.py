from __future__ import annotations

from dataclasses import dataclass, field

from app.realtime.provider_registry import ProviderSignal


@dataclass
class LiveTravelContext:
    weather_pressure: float = 0.0
    traffic_pressure: float = 0.0
    event_pressure: float = 0.0
    local_activity: float = 0.0
    safety_pressure: float = 0.0
    summaries: list[str] = field(default_factory=list)


def build_live_travel_context(signals: list[ProviderSignal]) -> LiveTravelContext:
    ctx = LiveTravelContext()
    for signal in signals:
        ctx.summaries.append(f"{signal.provider}:{signal.summary}")
        if signal.category == "weather":
            ctx.weather_pressure = max(ctx.weather_pressure, signal.score)
        elif signal.category == "traffic":
            ctx.traffic_pressure = max(ctx.traffic_pressure, signal.score)
        elif signal.category == "events":
            ctx.event_pressure = max(ctx.event_pressure, signal.score)
        elif signal.category == "business":
            ctx.local_activity = max(ctx.local_activity, signal.score)
        elif signal.category == "safety":
            ctx.safety_pressure = max(ctx.safety_pressure, signal.score)
    return ctx
