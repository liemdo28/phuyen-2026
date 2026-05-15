"""
Weather Intelligence Service for Phu Yen 2026.
Fetches realtime weather from Open-Meteo and provides travel-aware context.
"""

from __future__ import annotations

import httpx
from dataclasses import dataclass


@dataclass
class WeatherContext:
    """Contextual weather data for travel recommendations."""
    place: str
    temperature_max: float
    temperature_min: float
    weather_label: str
    precipitation_mm: float
    uv_index: float | None
    wind_kmh: float | None
    assessment: str  # "dep", "duoc", "xau"

    def travel_warning(self) -> str | None:
        """Return a warning string if weather is bad for outdoor activities."""
        if self.assessment == "xau":
            if self.precipitation_mm > 10:
                return "Rain - prioritize indoor activities or shelter."
            if self.uv_index and self.uv_index > 8:
                return "Very high UV - wear sunscreen, long sleeves, wide-brimmed hat."
            return "Bad weather - consider changing outdoor plans."
        if self.precipitation_mm > 5:
            return "Light rain expected - bring raincoat or umbrella."
        return None

    def swimming_warning(self) -> str | None:
        """Return swimming safety warning."""
        if self.assessment == "xau":
            return "Sea conditions unsafe today - avoid swimming."
        return None

    def sunset_time_context(self, hour: int) -> str | None:
        """Suggest timing based on sunset and current hour."""
        if 15 <= hour <= 17 and self.assessment != "xau":
            return "Sunset in ~1.5-2h - should go early."
        return None

    def short_label(self) -> str:
        return (
            f"{self.weather_label} {int(self.temperature_max)}C "
            f"(rain {self.precipitation_mm:.1f}mm)"
        )


# Phu Yen key locations
PHUYEN_LOCATIONS = {
    "Tuy Hoa":          {"lat": 13.0955, "lon": 109.3028},
    "Ganh Da Di":      {"lat": 14.3912, "lon": 109.2144},
    "Dam O Loan":       {"lat": 13.4200, "lon": 109.2500},
    "Mui Dien":         {"lat": 12.8667, "lon": 109.4500},
    "Bai Xep":          {"lat": 13.0150, "lon": 109.3280},
}

# Trip dates: 23-27/05/2026
TRIP_START = "2026-05-23"
TRIP_END = "2026-05-27"

WX_LABEL = {
    0: "Clear sky",        1: "Partly cloudy",   2: "Cloudy",
    3: "Overcast",
    45: "Fog",             48: "Rime fog",
    51: "Light drizzle",   53: "Drizzle",         55: "Heavy drizzle",
    61: "Light rain",      63: "Rain",             65: "Heavy rain",
    80: "Light showers",   81: "Rain showers",    82: "Heavy showers",
    95: "Thunderstorm",    96: "Thunderstorm+Hail", 99: "Severe thunderstorm",
}


def _wx_label(code: int) -> str:
    return WX_LABEL.get(code, f"({code})")


def _wx_ok(code: int, precip: float) -> str:
    if code <= 3 and precip < 5:
        return "dep"
    if code <= 55 and precip < 15:
        return "duoc"
    return "xau"


async def fetch_weather_for_place(place: str) -> WeatherContext | None:
    """
    Fetch weather for a specific Phu Yen location.
    Falls back to Tuy Hoa as default.
    """
    coord = PHUYEN_LOCATIONS.get(place, PHUYEN_LOCATIONS["Tuy Hoa"])

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={coord['lat']}&longitude={coord['lon']}"
        f"&daily=weathercode,temperature_2m_max,temperature_2m_min,"
        f"precipitation_sum,windspeed_10m_max,uv_index_max"
        f"&timezone=Asia%2FHo_Chi_Minh"
        f"&start_date={TRIP_START}&end_date={TRIP_END}"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        daily = data.get("daily")
        if not daily:
            return None

        times = daily.get("time", [])
        if not times:
            return None

        idx = 0  # Today
        code    = daily["weathercode"][idx]
        tmax    = daily["temperature_2m_max"][idx]
        tmin    = daily["temperature_2m_min"][idx]
        precip  = daily["precipitation_sum"][idx] or 0.0
        wind    = daily["windspeed_10m_max"][idx]
        uv      = daily["uv_index_max"][idx] if daily.get("uv_index_max") else None

        assessment = _wx_ok(code, precip)
        label = _wx_label(code)

        return WeatherContext(
            place=place,
            temperature_max=float(tmax),
            temperature_min=float(tmin),
            weather_label=label,
            precipitation_mm=float(precip),
            uv_index=float(uv) if uv else None,
            wind_kmh=float(wind) if wind else None,
            assessment=assessment,
        )
    except httpx.HTTPError:
        return None


async def fetch_all_weather() -> dict[str, WeatherContext | None]:
    """Fetch weather for all Phu Yen locations."""
    results = {}
    for place in PHUYEN_LOCATIONS:
        results[place] = await fetch_weather_for_place(place)
    return results


def build_weather_context_text(context: WeatherContext | None, include_warning: bool = True) -> str:
    """
    Build a natural language weather context string for AI prompts.
    Example: "Sunny 34C (rain 0.0mm) - weather good."
    """
    if not context:
        return ""

    parts = [f"{context.weather_label} {int(context.temperature_max)}C"]

    if context.precipitation_mm > 0:
        parts.append(f"rain {context.precipitation_mm:.1f}mm")

    text = f"{' '.join(parts)} - weather {context.assessment}."

    if include_warning:
        warning = context.travel_warning()
        if warning:
            text += f" {warning}"

    return text
