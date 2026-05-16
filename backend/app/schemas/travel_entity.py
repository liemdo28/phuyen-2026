"""Travel Entity Schema — structured, AI-queryable travel location representation.

Replaces the basic IndexedLocation with a rich entity model that captures:
- Identity (id, name, slug, category, subcategory)
- Location (address, lat/lng, maps URLs)
- Logistics (parking, transport access, crowd level)
- Atmosphere (vibe tags, emotional vibe, energy fit, traveler types)
- Practicality (hours, price, amenities)
- Trip fit (weather, fatigue, time-of-day compatibility)
- AI metadata (confidence, source, auto-tags)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


# ── Canonical tag vocabularies ──────────────────────────────────────────────────

LEVEL1_CATEGORIES = {
    "restaurant", "cafe", "beach", "hotel", "attraction",
    "nightlife", "shopping", "local_market", "parking",
    "gas_station", "hospital", "pharmacy", "coworking",
    "hidden_spot", "viewpoint",
}

LEVEL2_FOOD_SUBCATEGORIES = {
    "seafood", "local_food", "breakfast", "street_food", "coffee",
    "ramen", "sushi", "bbq", "vegetarian", "dessert",
    "vietnamese_food", "western_food", "nightlife_food", "healthy_food",
}

VIBE_TAGS = {
    "chill", "local", "luxury", "quiet", "crowded", "romantic",
    "sunset", "instagrammable", "family", "hidden", "authentic",
    "touristy", "energetic", "calm", "recovery", "work_friendly",
    "night_vibe", "ocean_vibe",
}

TRAVELER_TYPES = {
    "backpacker", "family", "solo_traveler", "couple", "foodie",
    "digital_nomad", "luxury_traveler", "local_explorer", "photographer",
}

TRIP_FIT_TAGS = {
    "breakfast_stop", "lunch_stop", "dinner_stop", "cafe_break",
    "sunset_stop", "rain_safe", "recovery_stop", "night_activity",
    "quick_stop", "long_stay", "remote_work",
}

ENERGY_FIT_TAGS = {
    "low_energy", "high_energy", "recovery_friendly", "walking_heavy",
    "crowded_exhausting", "calming", "social_heavy",
}

WEATHER_FIT_TAGS = {
    "hot_weather", "rainy_weather", "indoor_safe", "windy_weather",
    "summer_best", "sunset_best",
}

LOCAL_VS_TOURIST = {
    "local_hidden", "mixed", "tourist_hotspot", "local_favorite",
}

EMOTIONAL_VIBE = {
    "peaceful", "energetic", "nostalgic", "romantic", "healing",
    "social", "adventurous", "overwhelming", "cozy",
}

CROWD_LEVELS = {"quiet", "medium", "busy", "crowded", "packed"}


# ── Sub-structs ────────────────────────────────────────────────────────────────

@dataclass
class ParkingInfo:
    has_parking: bool = False
    car_parking: bool = False
    motorbike_parking: bool = False
    parking_difficulty: str = ""  # "easy" | "medium" | "hard"
    parking_notes: str = ""


@dataclass
class TransportAccess:
    walking_friendly: bool = False
    grab_access: bool = False
    bus_access: bool = False
    easy_to_find: bool = False
    remote_area: bool = False


@dataclass
class CrowdInfo:
    morning: str = ""   # quiet | medium | busy | crowded | packed
    afternoon: str = ""
    sunset: str = ""
    night: str = ""


@dataclass
class OpeningHours:
    morning: str = ""   # e.g. "06:00-11:00"
    afternoon: str = ""
    evening: str = ""
    night: str = ""
    always_open: bool = False

    def to_dict(self) -> dict:
        return {
            "morning": self.morning, "afternoon": self.afternoon,
            "evening": self.evening, "night": self.night,
            "always_open": self.always_open,
        }

    @classmethod
    def from_str(cls, raw: str) -> "OpeningHours":
        """Parse a raw hours string like '06:00-14:00' into OpeningHours."""
        if not raw:
            return cls()
        return cls(morning=raw.strip())


# ── Main entity ───────────────────────────────────────────────────────────────

@dataclass
class TravelEntity:
    """A structured, AI-queryable travel location entity."""
    # Identity
    id: str = ""
    name: str = ""
    slug: str = ""
    category: str = ""          # Level 1
    subcategory: str = ""        # Level 2 (food type, etc.)

    # Location
    address: str = ""
    district: str = ""
    city: str = "Tuy Hòa"
    province: str = "Phú Yên"
    country: str = "Vietnam"
    lat: Optional[float] = None
    lng: Optional[float] = None
    maps_url: str = ""
    directions_url: str = ""

    # Price & Time
    price_level: str = ""       # "budget" | "mid" | "upscale" | "luxury"
    avg_price_vnd: int = 0
    currency: str = "VND"
    opening_hours: OpeningHours = field(default_factory=OpeningHours)

    # Food / Product
    signature_items: list[str] = field(default_factory=list)
    menu_tags: list[str] = field(default_factory=list)
    food_types: list[str] = field(default_factory=list)

    # Atmosphere
    vibe_tags: list[str] = field(default_factory=list)
    traveler_types: list[str] = field(default_factory=list)
    emotional_vibe: list[str] = field(default_factory=list)

    # Trip fit
    trip_fits: list[str] = field(default_factory=list)
    energy_fit: list[str] = field(default_factory=list)
    fatigue_fit: list[str] = field(default_factory=list)
    weather_fit: list[str] = field(default_factory=list)
    best_visit_time: list[str] = field(default_factory=list)

    # Logistics
    parking: ParkingInfo = field(default_factory=ParkingInfo)
    transport_access: TransportAccess = field(default_factory=TransportAccess)
    crowd_level: CrowdInfo = field(default_factory=CrowdInfo)
    local_vs_tourist: str = ""  # from LOCAL_VS_TOURIST
    noise_level: str = ""       # "quiet" | "moderate" | "loud"
    quietness_level: str = ""

    # Amenities
    sea_view: bool = False
    sunset_view: bool = False
    pet_friendly: bool = False
    cashless_support: bool = False
    reservation_needed: bool = False
    wifi_quality: str = ""       # "" | "poor" | "ok" | "good"
    air_conditioning: bool = False

    # Special flags
    photo_spot: bool = False
    hidden_local_spot: bool = False
    tourist_trap_risk: str = ""  # "" | "low" | "medium" | "high"
    kid_friendly: bool = False
    group_friendly: bool = False
    solo_friendly: bool = False
    couple_friendly: bool = False

    # Legacy compatibility (flattened fields used by existing code)
    area: str = ""              # maps to district/province
    note: str = ""
    on_route: bool = False
    child_safe: bool = False

    # AI metadata
    ai_confidence: float = 0.0  # 0.0–1.0
    auto_tagged: bool = False   # True if vibe/energy/etc. were AI-inferred
    source_sheet: str = ""
    source_row: int = 0
    geocode_source: str = ""
    geocode_confidence: float = 0.0
    last_updated: str = ""
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        # Serialize nested dataclasses
        d["opening_hours"] = self.opening_hours.to_dict()
        d["parking"] = asdict(self.parking)
        d["transport_access"] = asdict(self.transport_access)
        d["crowd_level"] = asdict(self.crowd_level)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "TravelEntity":
        data = dict(data)
        # Deserialize nested dataclasses
        if "opening_hours" in data and isinstance(data["opening_hours"], dict):
            data["opening_hours"] = OpeningHours(**data["opening_hours"])
        if "parking" in data and isinstance(data["parking"], dict):
            data["parking"] = ParkingInfo(**data["parking"])
        if "transport_access" in data and isinstance(data["transport_access"], dict):
            data["transport_access"] = TransportAccess(**data["transport_access"])
        if "crowd_level" in data and isinstance(data["crowd_level"], dict):
            data["crowd_level"] = CrowdInfo(**data["crowd_level"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_telegram_summary(self) -> str:
        """One-line summary for Telegram display."""
        emoji = _CATEGORY_EMOJI.get(self.category, "📍")
        parts = [f"{emoji} {self.name}"]
        if self.district or self.province:
            parts.append(f"{self.district or self.province}")
        if self.avg_price_vnd > 0:
            parts.append(f"~{self.avg_price_vnd:,}k")
        if self.opening_hours and not self.opening_hours.always_open:
            if self.opening_hours.morning:
                parts.append(self.opening_hours.morning)
        vibes = self.vibe_tags[:2]
        if vibes:
            parts.append(" · ".join(f"#{v}" for v in vibes))
        return " · ".join(parts)

    def matches_vibe(self, vibe: str) -> bool:
        return vibe in self.vibe_tags

    def matches_traveler(self, traveler: str) -> bool:
        return traveler in self.traveler_types

    def matches_energy(self, energy: str) -> bool:
        return energy in self.energy_fit

    def matches_weather(self, weather: str) -> bool:
        return weather in self.weather_fit


# ── Emoji map ────────────────────────────────────────────────────────────────

_CATEGORY_EMOJI = {
    "restaurant": "🍽️", "cafe": "☕", "beach": "🏖️",
    "hotel": "🏨", "attraction": "📍", "nightlife": "🌙",
    "shopping": "🛍️", "local_market": "🛒", "parking": "🅿️",
    "gas_station": "⛽", "hospital": "🏥", "pharmacy": "💊",
    "coworking": "💻", "hidden_spot": "🌿", "viewpoint": "🌅",
}