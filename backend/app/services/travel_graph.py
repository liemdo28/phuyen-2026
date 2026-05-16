"""Travel Graph — Living Travel Knowledge Graph & Realtime Orchestration Engine.

Provides:
- KnowledgeGraph: Rich entity-to-entity relationships (nearby_to, good_after, sunset_chain, etc.)
- LocationNode: Experiential nodes with energy/fatigue attributes
- FatigueAccumulationModel: Track walking, heat, social, decision, traffic fatigue
- EmotionalTransitionEngine: Optimize emotional sequencing between places
- RecoveryNodeSystem: Identify and inject recovery-friendly stops
- TripFlowEngine: Unified orchestration of pacing, energy, weather, timing
- WeatherOrchestration: Adaptive routing based on weather evolution
- TimeAwareExperience: Time-based location scoring and recommendations
- TravelDNA: Traveler personality matching
- RealtimeScoringEngine: Dynamic location scoring based on context
- TripMemoryGraph: Cross-trip memory of preferences and experiences

The AI evolves from static place lookup → realtime travel orchestration intelligence.
"""
from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from pathlib import Path
from typing import Optional

from app.schemas.travel_entity import (
    TravelEntity,
    VIBE_TAGS, TRAVELER_TYPES, ENERGY_FIT_TAGS,
    WEATHER_FIT_TAGS, EMOTIONAL_VIBE,
)

# ── Cache ──────────────────────────────────────────────────────────────────────
_CACHE_DIR = Path(os.environ.get("STATE_DIR", "/data"))
_GRAPH_FILE = _CACHE_DIR / "travel_graph.json"
_GRAPH_VERSION = 2  # Bumped for new knowledge graph format

# ── Relationship Types ───────────────────────────────────────────────────────────

class RelationshipType(str, Enum):
    """All supported relationship types between locations."""
    NEARBY_TO = "nearby_to"              # Physical proximity
    GOOD_AFTER = "good_after"            # Natural sequencing
    SUNSET_CHAIN = "sunset_chain"        # Sunset viewing sequence
    BREAKFAST_CHAIN = "breakfast_chain"  # Morning eating sequence
    RECOVERY_CHAIN = "recovery_chain"    # Recovery flow
    RAINY_DAY_ALTERNATIVE = "rainy_day_alternative"  # Indoor substitute
    PARKING_NEARBY = "parking_nearby"    # Parking availability
    LOW_ENERGY_ALTERNATIVE = "low_energy_alternative"  # Easy access
    LOCAL_HIDDEN_PAIR = "local_hidden_pair"  # Hidden gem connections
    NIGHTLIFE_TRANSITION = "nightlife_transition"  # Evening flow
    CAFE_AFTER_MEAL = "cafe_after_meal"  # Post-meal coffee
    BEACH_AFTER_BREAKFAST = "beach_after_breakfast"  # Morning beach

    # Extended relationship types
    MORNING_CHAIN = "morning_chain"
    LUNCH_CHAIN = "lunch_chain"
    DINNER_CHAIN = "dinner_chain"
    HEAT_RECOVERY = "heat_recovery"
    SHADE_PAIR = "shade_pair"
    SCENIC_ROUTE = "scenic_route"
    TRAFFIC_FREE_ROUTE = "traffic_free_route"
    CROWD_AVOIDANCE = "crowd_avoidance"
    PHOTO_OPPORTUNITY = "photo_opportunity"


# ── Energy Levels ───────────────────────────────────────────────────────────────

class EnergyLevel(str, Enum):
    """Energy cost/load levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ── Fatigue Types ──────────────────────────────────────────────────────────────

class FatigueType(str, Enum):
    """Types of fatigue the system tracks."""
    WALKING = "walking"
    HEAT = "heat"
    SOCIAL = "social"
    DECISION = "decision"
    TRAFFIC = "traffic"
    MENTAL = "mental"


# ── Recovery Types ──────────────────────────────────────────────────────────────

class RecoveryType(str, Enum):
    """Types of recovery nodes."""
    QUIET_CAFE = "quiet_cafe"
    CALM_BEACH = "calm_beach"
    LOW_NOISE_RESTAURANT = "low_noise_restaurant"
    SHADED_LOCATION = "shaded_location"
    AIR_CONDITIONED = "air_conditioned"
    HIDDEN_LOCAL_SPOT = "hidden_local_spot"
    NATURE_SPOT = "nature_spot"


# ── Travel DNA Types ────────────────────────────────────────────────────────────

class TravelDNA(str, Enum):
    """Traveler personality types."""
    EXPLORER = "explorer"
    RELAX_TRAVELER = "relax_traveler"
    FOODIE = "foodie"
    PHOTOGRAPHER = "photographer"
    INTROVERT_TRAVELER = "introvert_traveler"
    SOCIAL_TRAVELER = "social_traveler"
    SLOW_TRAVELER = "slow_traveler"
    ADVENTURE_TRAVELER = "adventure_traveler"


# ── Travel Context ──────────────────────────────────────────────────────────────

@dataclass
class TravelContext:
    """Dynamic context for ranking and orchestration decisions."""
    weather: str = "hot_weather"          # WEATHER_FIT_TAGS
    fatigue: float = 0.0                   # 0.0 (fresh) → 1.0 (exhausted)
    emotion: str = "peaceful"             # EMOTIONAL_VIBE
    time_of_day: str = "morning"          # morning|afternoon|sunset|evening|night
    day: int = 1                          # trip day (1-5)
    crowd_tolerance: float = 0.5           # 0.0 (avoid crowds) → 1.0 (embrace)
    budget_level: str = "mid"              # budget|mid|upscale|luxury
    # Extended context
    travel_dna: str = ""                   # TravelDNA type
    heat_index: float = 0.0               # 0.0-1.0 heat stress
    traffic_level: float = 0.0            # 0.0-1.0 traffic stress
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    trip_stage: str = "beginning"         # beginning|middle|end
    sunset_time: Optional[str] = None     # e.g. "18:30"
    user_mood_trend: str = "stable"       # improving|stable|declining

    @classmethod
    def from_dict(cls, d: dict) -> "TravelContext":
        return cls(
            weather=d.get("weather", "hot_weather"),
            fatigue=float(d.get("fatigue", 0.0)),
            emotion=d.get("emotion", "peaceful"),
            time_of_day=d.get("time_of_day", "morning"),
            day=int(d.get("day", 1)),
            crowd_tolerance=float(d.get("crowd_tolerance", 0.5)),
            budget_level=d.get("budget_level", "mid"),
            travel_dna=d.get("travel_dna", ""),
            heat_index=float(d.get("heat_index", 0.0)),
            traffic_level=float(d.get("traffic_level", 0.0)),
            current_lat=d.get("current_lat"),
            current_lng=d.get("current_lng"),
            trip_stage=d.get("trip_stage", "beginning"),
            sunset_time=d.get("sunset_time"),
            user_mood_trend=d.get("user_mood_trend", "stable"),
        )

    def to_dict(self) -> dict:
        return {
            "weather": self.weather,
            "fatigue": self.fatigue,
            "emotion": self.emotion,
            "time_of_day": self.time_of_day,
            "day": self.day,
            "crowd_tolerance": self.crowd_tolerance,
            "budget_level": self.budget_level,
            "travel_dna": self.travel_dna,
            "heat_index": self.heat_index,
            "traffic_level": self.traffic_level,
            "current_lat": self.current_lat,
            "current_lng": self.current_lng,
            "trip_stage": self.trip_stage,
            "sunset_time": self.sunset_time,
            "user_mood_trend": self.user_mood_trend,
        }


# ── Energy Graph ───────────────────────────────────────────────────────────────

@dataclass
class EnergyGraph:
    """Energy cost profile for a location."""
    energy_cost: EnergyLevel = EnergyLevel.MEDIUM
    walking_load: EnergyLevel = EnergyLevel.MEDIUM
    social_load: EnergyLevel = EnergyLevel.LOW
    recovery_score: EnergyLevel = EnergyLevel.LOW  # How restorative
    heat_exposure: EnergyLevel = EnergyLevel.MEDIUM

    # Extended energy metrics
    mental_load: EnergyLevel = EnergyLevel.LOW
    decision_complexity: EnergyLevel = EnergyLevel.LOW  # Menu size, choices
    noise_level: EnergyLevel = EnergyLevel.LOW
    standing_required: bool = False
    shade_available: bool = True
    seating_available: bool = True
    air_conditioned: bool = False

    def to_dict(self) -> dict:
        return {
            "energy_cost": self.energy_cost.value,
            "walking_load": self.walking_load.value,
            "social_load": self.social_load.value,
            "recovery_score": self.recovery_score.value,
            "heat_exposure": self.heat_exposure.value,
            "mental_load": self.mental_load.value,
            "decision_complexity": self.decision_complexity.value,
            "noise_level": self.noise_level.value,
            "standing_required": self.standing_required,
            "shade_available": self.shade_available,
            "seating_available": self.seating_available,
            "air_conditioned": self.air_conditioned,
        }

    @classmethod
    def from_entity(cls, entity: TravelEntity) -> "EnergyGraph":
        """Derive energy graph from TravelEntity attributes."""
        # Parse energy_fit tags
        walking = EnergyLevel.MEDIUM
        social = EnergyLevel.LOW
        recovery = EnergyLevel.LOW
        heat = EnergyLevel.MEDIUM

        for tag in entity.energy_fit:
            if tag == "walking_heavy":
                walking = EnergyLevel.HIGH
            elif tag == "high_energy":
                walking = EnergyLevel.HIGH
            elif tag == "low_energy":
                walking = EnergyLevel.LOW
            elif tag == "recovery_friendly":
                recovery = EnergyLevel.HIGH
            elif tag == "calming":
                recovery = EnergyLevel.HIGH
            elif tag == "crowded_exhausting":
                social = EnergyLevel.HIGH
            elif tag == "social_heavy":
                social = EnergyLevel.HIGH

        # Heat exposure from weather_fit
        if "indoor_safe" in entity.weather_fit:
            heat = EnergyLevel.LOW
        elif entity.category == "beach":
            heat = EnergyLevel.HIGH

        return cls(
            energy_cost=walking,
            walking_load=walking,
            social_load=social,
            recovery_score=recovery,
            heat_exposure=heat,
            noise_level=EnergyLevel.HIGH if entity.noise_level == "loud" else EnergyLevel.LOW,
            air_conditioned=entity.air_conditioning,
            seating_available=entity.category in {"restaurant", "cafe", "hotel"},
        )


# ── Time-Aware Experience ───────────────────────────────────────────────────────

@dataclass
class TimeAwareExperience:
    """Time-based experience metadata for a location."""
    best_times: list[str] = field(default_factory=list)  # ["sunrise", "sunset", "morning"]
    peak_crowd_times: list[str] = field(default_factory=list)  # ["18:00-20:00"]
    quiet_times: list[str] = field(default_factory=list)  # ["09:00-11:00"]
    worst_times: list[str] = field(default_factory=list)  # ["12:00-14:00"]

    # Time-based vibes
    morning_vibes: list[str] = field(default_factory=list)
    sunset_vibes: list[str] = field(default_factory=list)
    night_vibes: list[str] = field(default_factory=list)

    def is_good_time(self, time_of_day: str) -> bool:
        """Check if given time of day is good for this location."""
        return time_of_day in self.best_times

    def crowd_risk(self, time_of_day: str) -> float:
        """Return 0.0-1.0 crowd risk for given time (1.0 = crowded)."""
        # Parse peak crowd times
        for peak in self.peak_crowd_times:
            if time_of_day in peak:
                return 0.8
        for quiet in self.quiet_times:
            if time_of_day in quiet:
                return 0.2
        return 0.5  # Medium by default

    def to_dict(self) -> dict:
        return {
            "best_times": self.best_times,
            "peak_crowd_times": self.peak_crowd_times,
            "quiet_times": self.quiet_times,
            "worst_times": self.worst_times,
            "morning_vibes": self.morning_vibes,
            "sunset_vibes": self.sunset_vibes,
            "night_vibes": self.night_vibes,
        }

    @classmethod
    def from_entity(cls, entity: TravelEntity) -> "TimeAwareExperience":
        """Derive time-aware experience from TravelEntity."""
        best_times = []
        sunset_vibes = []
        morning_vibes = []
        night_vibes = []

        # From best_visit_time
        for t in entity.best_visit_time:
            t_lower = t.lower()
            if "morning" in t_lower or "sáng" in t_lower:
                best_times.append("morning")
                morning_vibes.append("peaceful_start")
            elif "sunset" in t_lower or "hoàng hôn" in t_lower:
                best_times.append("sunset")
                sunset_vibes.append("golden_hour")
            elif "night" in t_lower or "đêm" in t_lower:
                best_times.append("night")
                night_vibes.append("evening_glow")
            elif "afternoon" in t_lower or "chiều" in t_lower:
                best_times.append("afternoon")

        # From trip_fits
        for fit in entity.trip_fits:
            if fit == "breakfast_stop":
                best_times.append("morning")
                morning_vibes.append("fresh_start")
            elif fit == "sunset_stop":
                best_times.append("sunset")
                sunset_vibes.append("golden_hour")
            elif fit == "night_activity":
                best_times.append("night")
                night_vibes.append("evening_vibe")
            elif fit == "recovery_stop":
                morning_vibes.append("peaceful")
                sunset_vibes.append("calming")

        # From vibes
        for vibe in entity.vibe_tags:
            if vibe in {"sunset", "romantic"}:
                sunset_vibes.append("romantic")
            elif vibe in {"quiet", "chill", "calm"}:
                morning_vibes.append("peaceful")
                sunset_vibes.append("peaceful")
            elif vibe in {"night_vibe", "energetic"}:
                night_vibes.append("energetic")

        return cls(
            best_times=best_times,
            sunset_vibes=list(set(sunset_vibes)),
            morning_vibes=list(set(morning_vibes)),
            night_vibes=list(set(night_vibes)),
        )


# ── Location Node ──────────────────────────────────────────────────────────────

@dataclass
class LocationNode:
    """
    An experiential node in the knowledge graph.
    Every location becomes a connected experiential node with rich metadata.
    """
    entity_id: str
    name: str
    category: str

    # Relationships
    relationships: dict[RelationshipType, list[str]] = field(default_factory=dict)

    # Energy profile
    energy_graph: EnergyGraph = field(default_factory=EnergyGraph)

    # Time awareness
    time_experience: TimeAwareExperience = field(default_factory=TimeAwareExperience)

    # Emotional impact
    emotional_impact: list[str] = field(default_factory=list)  # ["calming", "overwhelming"]
    emotional_aftermath: str = "neutral"  # How user feels after leaving

    # Recovery properties
    recovery_types: list[RecoveryType] = field(default_factory=list)
    is_recovery_node: bool = False

    # Physical properties
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    parking_available: bool = False
    distance_from_main_road_km: float = 0.0

    # Weather sensitivity
    weather_dependencies: list[str] = field(default_factory=list)  # ["sunset", "sunny"]
    indoor_safe: bool = False

    # Hidden gem properties
    is_hidden_gem: bool = False
    local_knowledge_bonus: float = 0.0  # 0.0-1.0 how much locals value this

    # Flow properties
    ideal_flow_before: list[str] = field(default_factory=list)
    ideal_flow_after: list[str] = field(default_factory=list)
    bad_flow_before: list[str] = field(default_factory=list)  # What not to do before

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "category": self.category,
            "relationships": {k.value: v for k, v in self.relationships.items()},
            "energy_graph": self.energy_graph.to_dict(),
            "time_experience": self.time_experience.to_dict(),
            "emotional_impact": self.emotional_impact,
            "emotional_aftermath": self.emotional_aftermath,
            "recovery_types": [r.value for r in self.recovery_types],
            "is_recovery_node": self.is_recovery_node,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "parking_available": self.parking_available,
            "distance_from_main_road_km": self.distance_from_main_road_km,
            "weather_dependencies": self.weather_dependencies,
            "indoor_safe": self.indoor_safe,
            "is_hidden_gem": self.is_hidden_gem,
            "local_knowledge_bonus": self.local_knowledge_bonus,
            "ideal_flow_before": self.ideal_flow_before,
            "ideal_flow_after": self.ideal_flow_after,
            "bad_flow_before": self.bad_flow_before,
        }

    @classmethod
    def from_entity(cls, entity: TravelEntity) -> "LocationNode":
        """Create a LocationNode from a TravelEntity."""
        # Determine recovery types
        recovery_types = []
        is_recovery = False

        if "quiet" in entity.vibe_tags or "chill" in entity.vibe_tags:
            recovery_types.append(RecoveryType.QUIET_CAFE)
            is_recovery = True
        if entity.category == "beach" and "quiet" in entity.vibe_tags:
            recovery_types.append(RecoveryType.CALM_BEACH)
            is_recovery = True
        if entity.noise_level == "quiet":
            recovery_types.append(RecoveryType.LOW_NOISE_RESTAURANT)
        if not entity.energy_fit or "low_energy" in entity.energy_fit:
            recovery_types.append(RecoveryType.SHADED_LOCATION)
            is_recovery = True
        if entity.air_conditioning:
            recovery_types.append(RecoveryType.AIR_CONDITIONED)
        if entity.hidden_local_spot:
            recovery_types.append(RecoveryType.HIDDEN_LOCAL_SPOT)
            is_recovery = True

        # Emotional impact
        emotional_impact = []
        emotional_aftermath = "neutral"

        for vibe in entity.vibe_tags:
            if vibe in {"calm", "peaceful", "healing"}:
                emotional_impact.append("calming")
                emotional_aftermath = "refreshed"
            elif vibe in {"crowded", "energetic"}:
                emotional_impact.append("energizing")
                emotional_aftermath = "stimulated"
            elif vibe in {"romantic", "sunset"}:
                emotional_impact.append("romantic")
                emotional_aftermath = "content"
            elif vibe in {"hidden", "local"}:
                emotional_impact.append("nostalgic")
                emotional_aftermath = "fulfilled"
            elif vibe in {"overwhelming", "touristy"}:
                emotional_impact.append("overwhelming")
                emotional_aftermath = "tired"

        if entity.category == "beach":
            emotional_impact.append("healing")
        if entity.weather_fit and "indoor_safe" in entity.weather_fit:
            pass  # Indoor safe doesn't add emotional impact

        return cls(
            entity_id=entity.id,
            name=entity.name,
            category=entity.category,
            energy_graph=EnergyGraph.from_entity(entity),
            time_experience=TimeAwareExperience.from_entity(entity),
            emotional_impact=emotional_impact,
            emotional_aftermath=emotional_aftermath,
            recovery_types=recovery_types,
            is_recovery_node=is_recovery,
            latitude=entity.lat,
            longitude=entity.lng,
            parking_available=entity.parking.has_parking,
            distance_from_main_road_km=0.0,  # TODO: Calculate from geocoding
            indoor_safe="indoor_safe" in entity.weather_fit,
            is_hidden_gem=entity.hidden_local_spot,
            local_knowledge_bonus=0.8 if entity.hidden_local_spot else 0.2,
        )


# ── Relationship ───────────────────────────────────────────────────────────────

@dataclass
class Relationship:
    """A typed relationship between two nodes."""
    from_node: str
    to_node: str
    relationship_type: RelationshipType
    strength: float = 1.0  # 0.0-1.0 how strong the relationship is
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "type": self.relationship_type.value,
            "strength": self.strength,
            "metadata": self.metadata,
        }


# ── Travel Intent ──────────────────────────────────────────────────────────────

@dataclass
class TravelIntent:
    """Extracted intent signals from a natural language query."""
    intent_type: str = "location_search"  # location_search|food|attraction|shopping|hotel|weather|budget|itinerary|suggestion
    extracted_vibes: list[str] = field(default_factory=list)
    extracted_traveler_types: list[str] = field(default_factory=list)
    extracted_energy: list[str] = field(default_factory=list)
    extracted_weather: list[str] = field(default_factory=list)
    extracted_emotion: str = ""
    extracted_location: str = ""
    extracted_price: str = ""             # budget|mid|upscale|luxury
    extracted_travel_dna: str = ""
    confidence: float = 0.0
    raw_query: str = ""

    def has_signals(self) -> bool:
        return bool(
            self.extracted_vibes
            or self.extracted_traveler_types
            or self.extracted_energy
            or self.extracted_weather
            or self.extracted_emotion
        )


# ── Fatigue Accumulation Model ─────────────────────────────────────────────────

@dataclass
class FatigueState:
    """Current state of all fatigue types."""
    walking: float = 0.0     # 0.0-1.0
    heat: float = 0.0       # 0.0-1.0
    social: float = 0.0      # 0.0-1.0
    decision: float = 0.0   # 0.0-1.0
    traffic: float = 0.0    # 0.0-1.0
    mental: float = 0.0     # 0.0-1.0

    @property
    def total(self) -> float:
        """Overall fatigue (weighted average)."""
        weights = {"walking": 0.25, "heat": 0.20, "social": 0.15, "decision": 0.15, "traffic": 0.15, "mental": 0.10}
        return sum(getattr(self, k) * v for k, v in weights.items())

    def to_dict(self) -> dict:
        return {
            "walking": self.walking,
            "heat": self.heat,
            "social": self.social,
            "decision": self.decision,
            "traffic": self.traffic,
            "mental": self.mental,
            "total": self.total,
        }


class FatigueAccumulationModel:
    """
    Models fatigue accumulation across the day.
    Tracks walking, heat, social, decision, traffic, and mental fatigue.
    """

    # Base fatigue costs by energy level
    _WALKING_COSTS = {
        EnergyLevel.VERY_LOW: 0.01,
        EnergyLevel.LOW: 0.03,
        EnergyLevel.MEDIUM: 0.08,
        EnergyLevel.HIGH: 0.15,
        EnergyLevel.VERY_HIGH: 0.25,
    }

    # Heat fatigue multipliers by weather
    _HEAT_MULTIPLIERS = {
        "hot_weather": 1.5,
        "indoor_safe": 0.3,
        "windy_weather": 0.7,
        "sunset_best": 0.5,
    }

    # Recovery rates by activity type
    _RECOVERY_RATES = {
        RecoveryType.QUIET_CAFE: 0.15,
        RecoveryType.CALM_BEACH: 0.20,
        RecoveryType.LOW_NOISE_RESTAURANT: 0.12,
        RecoveryType.SHADED_LOCATION: 0.10,
        RecoveryType.AIR_CONDITIONED: 0.18,
        RecoveryType.HIDDEN_LOCAL_SPOT: 0.15,
        RecoveryType.NATURE_SPOT: 0.22,
    }

    def __init__(self) -> None:
        self.state = FatigueState()
        self.history: list[FatigueState] = []

    def reset(self) -> None:
        """Reset fatigue state (e.g., new day)."""
        self.history.append(self.state)
        self.state = FatigueState()

    def accumulate_from_node(self, node: LocationNode, context: TravelContext) -> None:
        """Accumulate fatigue from visiting a location node."""
        # Walking fatigue
        walking_cost = self._WALKING_COSTS.get(node.energy_graph.walking_load, 0.08)
        if node.energy_graph.standing_required:
            walking_cost *= 1.5
        self.state.walking = min(1.0, self.state.walking + walking_cost)

        # Heat fatigue
        heat_mult = self._HEAT_MULTIPLIERS.get(context.weather, 1.0)
        heat_cost = 0.05 * heat_mult if node.energy_graph.heat_exposure in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH} else 0.02
        if not node.energy_graph.shade_available:
            heat_cost *= 1.5
        self.state.heat = min(1.0, self.state.heat + heat_cost)

        # Social fatigue
        if node.energy_graph.social_load in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}:
            self.state.social = min(1.0, self.state.social + 0.12)
        if node.energy_graph.noise_level in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}:
            self.state.social = min(1.0, self.state.social + 0.08)

        # Decision fatigue
        if node.energy_graph.decision_complexity in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}:
            self.state.decision = min(1.0, self.state.decision + 0.08)

        # Traffic fatigue (context-dependent)
        traffic_cost = context.traffic_level * 0.05
        self.state.traffic = min(1.0, self.state.traffic + traffic_cost)

        # Mental fatigue
        if node.energy_graph.mental_load in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}:
            self.state.mental = min(1.0, self.state.mental + 0.10)

    def apply_recovery(self, node: LocationNode) -> None:
        """Apply recovery from visiting a recovery node."""
        for recovery_type in node.recovery_types:
            rate = self._RECOVERY_RATES.get(recovery_type, 0.10)
            # Recovery applies to multiple fatigue types
            self.state.walking = max(0, self.state.walking - rate * 0.8)
            self.state.heat = max(0, self.state.heat - rate * 0.6)
            self.state.social = max(0, self.state.social - rate * 0.7)
            self.state.decision = max(0, self.state.decision - rate * 0.5)
            self.state.mental = max(0, self.state.mental - rate * 0.9)

    def get_recovery_recommendation(self) -> tuple[bool, str]:
        """
        Determine if recovery is needed and recommend next steps.
        Returns (needs_recovery, recommendation).
        """
        total = self.state.total

        if total >= 0.75:
            return True, "critical_recovery"  # Need immediate rest
        elif total >= 0.50:
            return True, "moderate_recovery"  # Should find recovery spot
        elif self.state.heat >= 0.60:
            return True, "heat_recovery"  # Need cooling
        elif self.state.walking >= 0.60:
            return True, "movement_recovery"  # Need to reduce walking

        return False, ""

    def get_context_fatigue(self) -> float:
        """Return fatigue level formatted for TravelContext."""
        return self.state.total


# ── Emotional Transition Engine ────────────────────────────────────────────────

@dataclass
class EmotionalTransition:
    """Represents an emotional transition between two nodes."""
    from_emotion: str
    to_emotion: str
    quality: float  # -1.0 (bad) to 1.0 (great)
    explanation: str = ""


_EMOTIONAL_TRANSITION_MAP = {
    # (from_impact, to_impact) -> (quality, explanation)
    ("calming", "calming"): (0.8, "Smooth transition into relaxation"),
    ("calming", "energizing"): (0.6, "Good build-up from calm to energy"),
    ("calming", "healing"): (0.9, "Perfect recovery flow"),
    ("calming", "overwhelming"): (-0.3, "Sudden contrast may feel jarring"),
    ("energizing", "calming"): (0.7, "Nice wind-down after energy"),
    ("energizing", "energizing"): (0.2, "May feel monotonous"),
    ("energizing", "romantic"): (0.8, "Excitement transitioning to romance"),
    ("energizing", "overwhelming"): (-0.5, "Risk of overstimulation"),
    ("overwhelming", "calming"): (0.9, "Perfect relief after intensity"),
    ("overwhelming", "healing"): (0.8, "Good recovery path"),
    ("overwhelming", "overwhelming"): (-0.8, "Risk of burnout"),
    ("healing", "calming"): (0.9, "Deep restoration flow"),
    ("healing", "romantic"): (0.8, "Peaceful emotional build-up"),
    ("healing", "energizing"): (0.5, "Rejuvenated energy emerging"),
    ("romantic", "romantic"): (0.6, "Sustained romantic atmosphere"),
    ("romantic", "calming"): (0.7, "Peaceful romantic conclusion"),
}


class EmotionalTransitionEngine:
    """
    Optimizes emotional sequencing between places.
    Understands which places emotionally fit together.
    """

    def evaluate_transition(
        self,
        from_node: Optional[LocationNode],
        to_node: LocationNode,
    ) -> EmotionalTransition:
        """Evaluate the emotional quality of transitioning from one node to another."""
        if from_node is None:
            return EmotionalTransition(
                from_emotion="none",
                to_emotion=", ".join(to_node.emotional_impact) or "neutral",
                quality=0.5,
                explanation="Starting point - no prior context",
            )

        # Get primary emotional impacts
        from_impact = from_node.emotional_aftermath
        to_impacts = to_node.emotional_impact
        to_primary = to_impacts[0] if to_impacts else "neutral"

        # Look up transition quality
        key = (from_impact, to_primary)
        quality, explanation = _EMOTIONAL_TRANSITION_MAP.get(key, (0.0, "Neutral transition"))

        # Adjust for timing
        if to_node.time_experience.is_good_time("sunset"):
            quality += 0.1  # Sunset bonus
        if to_node.is_hidden_gem:
            quality += 0.1  # Hidden gem bonus

        quality = max(-1.0, min(1.0, quality))

        return EmotionalTransition(
            from_emotion=from_impact,
            to_emotion=to_primary,
            quality=quality,
            explanation=explanation,
        )

    def optimize_sequence(self, nodes: list[LocationNode]) -> list[tuple[LocationNode, EmotionalTransition]]:
        """
        Optimize a sequence of nodes for emotional flow.
        Returns nodes with their transition qualities.
        """
        if not nodes:
            return []

        optimized: list[tuple[LocationNode, EmotionalTransition]] = []

        for i, node in enumerate(nodes):
            prev = nodes[i - 1] if i > 0 else None
            transition = self.evaluate_transition(prev, node)
            optimized.append((node, transition))

        return optimized

    def get_bad_sequences(self) -> list[tuple[str, str]]:
        """Return known bad emotional transitions to avoid."""
        return [
            ("overwhelming", "overwhelming"),
            ("overwhelming", "energizing"),
            ("calming", "overwhelming"),
        ]


# ── Recovery Node System ────────────────────────────────────────────────────────

@dataclass
class RecoveryRecommendation:
    """A recommended recovery stop."""
    node: LocationNode
    recovery_types: list[RecoveryType]
    priority: int  # 1 = highest priority
    reasoning: str = ""


class RecoveryNodeSystem:
    """
    Identifies and recommends recovery-friendly places.
    Automatically injects recovery nodes when fatigue is high.
    """

    def find_recovery_nodes(
        self,
        nodes: list[LocationNode],
        fatigue_state: FatigueState,
        context: TravelContext,
    ) -> list[RecoveryRecommendation]:
        """Find appropriate recovery nodes based on current fatigue."""
        recommendations = []

        for node in nodes:
            if not node.is_recovery_node and not node.recovery_types:
                continue

            priority = self._calculate_priority(node, fatigue_state, context)
            if priority > 0:
                reasoning = self._generate_reasoning(node, fatigue_state)
                recommendations.append(RecoveryRecommendation(
                    node=node,
                    recovery_types=node.recovery_types,
                    priority=priority,
                    reasoning=reasoning,
                ))

        # Sort by priority (higher first)
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        return recommendations

    def _calculate_priority(
        self,
        node: LocationNode,
        fatigue_state: FatigueState,
        context: TravelContext,
    ) -> int:
        """Calculate recovery priority (1-10)."""
        priority = 5  # Base priority

        # Heat recovery
        if fatigue_state.heat > 0.5:
            if node.energy_graph.heat_exposure == EnergyLevel.LOW:
                priority += 3
            if node.energy_graph.shade_available:
                priority += 2
            if node.energy_graph.air_conditioned:
                priority += 2

        # Walking recovery
        if fatigue_state.walking > 0.5:
            if node.energy_graph.walking_load in {EnergyLevel.LOW, EnergyLevel.VERY_LOW}:
                priority += 2
            if node.energy_graph.seating_available:
                priority += 2

        # Social recovery
        if fatigue_state.social > 0.5:
            if node.energy_graph.noise_level in {EnergyLevel.LOW, EnergyLevel.VERY_LOW}:
                priority += 3

        # Mental recovery
        if fatigue_state.mental > 0.4:
            if node.energy_graph.decision_complexity in {EnergyLevel.LOW, EnergyLevel.VERY_LOW}:
                priority += 2

        # Recovery type bonus
        for rt in node.recovery_types:
            if rt == RecoveryType.QUIET_CAFE:
                priority += 1
            elif rt == RecoveryType.AIR_CONDITIONED:
                priority += 2
            elif rt == RecoveryType.NATURE_SPOT:
                priority += 2

        return min(10, priority)

    def _generate_reasoning(self, node: LocationNode, fatigue_state: FatigueState) -> str:
        """Generate human-readable reasoning for recovery recommendation."""
        reasons = []

        if fatigue_state.heat > 0.5:
            if node.energy_graph.shade_available:
                reasons.append("escape from heat")
            if node.energy_graph.air_conditioned:
                reasons.append("air-conditioned comfort")

        if fatigue_state.walking > 0.5:
            if node.energy_graph.seating_available:
                reasons.append("chỗ ngồi thoải mái")

        if fatigue_state.social > 0.5:
            if node.energy_graph.noise_level == EnergyLevel.LOW:
                reasons.append("yên tĩnh, giảm tiếng ồn")

        if not reasons:
            reasons.append("khôi phục năng lượng")

        return " · ".join(reasons)

    def should_inject_recovery(
        self,
        fatigue_state: FatigueState,
        next_node: Optional[LocationNode],
    ) -> tuple[bool, str]:
        """Determine if recovery should be injected before next node."""
        total_fatigue = fatigue_state.total

        # Critical fatigue - always inject
        if total_fatigue >= 0.75:
            return True, "critical_fatigue"

        # High heat - inject if next activity is hot
        if fatigue_state.heat >= 0.6 and next_node and next_node.energy_graph.heat_exposure in {
            EnergyLevel.HIGH, EnergyLevel.VERY_HIGH
        }:
            return True, "heat_prevention"

        # High walking - inject before more walking
        if fatigue_state.walking >= 0.6 and next_node and next_node.energy_graph.walking_load in {
            EnergyLevel.HIGH, EnergyLevel.VERY_HIGH
        }:
            return True, "walking_prevention"

        # Declining mood trend
        if fatigue_state.total >= 0.5 and next_node and next_node.emotional_aftermath == "tired":
            return True, "mood_protection"

        return False, ""


# ── Trip Flow Engine ────────────────────────────────────────────────────────────

@dataclass
class TripFlowSegment:
    """A segment of the trip with orchestrated flow."""
    node: LocationNode
    arrival_time: str = ""
    departure_time: str = ""
    activity: str = ""
    emotional_transition: Optional[EmotionalTransition] = None
    fatigue_before: float = 0.0
    fatigue_after: float = 0.0
    recovery_injected: bool = False
    weather_notes: str = ""
    flow_quality: float = 0.0  # -1.0 to 1.0


@dataclass
class TripFlowPlan:
    """A complete trip flow plan."""
    segments: list[TripFlowSegment]
    overall_quality: float = 0.0
    total_fatigue_end: float = 0.0
    recovery_stops_count: int = 0
    emotional_balance: float = 0.0
    warnings: list[str] = field(default_factory=list)


class TripFlowEngine:
    """
    Unified orchestration of pacing, energy, weather, timing, recovery,
    transportation, and emotional flow as ONE system.
    """

    def __init__(self) -> None:
        self.fatigue_model = FatigueAccumulationModel()
        self.emotional_engine = EmotionalTransitionEngine()
        self.recovery_system = RecoveryNodeSystem()

    def orchestrate_trip(
        self,
        nodes: list[LocationNode],
        context: TravelContext,
        available_recovery_nodes: list[LocationNode],
    ) -> TripFlowPlan:
        """
        Orchestrate a complete trip flow optimizing all dimensions.
        """
        segments: list[TripFlowSegment] = []
        plan_quality_scores = []
        emotional_balance_sum = 0.0

        prev_node: Optional[LocationNode] = None

        for node in nodes:
            segment = TripFlowSegment(
                node=node,
                activity=self._get_activity_description(node, context),
            )

            # Evaluate emotional transition
            transition = self.emotional_engine.evaluate_transition(prev_node, node)
            segment.emotional_transition = transition
            emotional_balance_sum += transition.quality
            plan_quality_scores.append(transition.quality)

            # Check if recovery should be injected
            should_recover, recovery_reason = self.recovery_system.should_inject_recovery(
                self.fatigue_model.state, node
            )

            if should_recover:
                # Find best recovery node
                recovery_recs = self.recovery_system.find_recovery_nodes(
                    available_recovery_nodes,
                    self.fatigue_model.state,
                    context,
                )
                if recovery_recs:
                    best_recovery = recovery_recs[0]
                    recovery_segment = TripFlowSegment(
                        node=best_recovery.node,
                        arrival_time=segment.arrival_time,
                        activity=f"Recovery: {recovery_reason}",
                        fatigue_before=self.fatigue_model.state.total,
                        recovery_injected=True,
                        weather_notes="Auto-injected recovery stop",
                    )
                    self.fatigue_model.apply_recovery(best_recovery.node)
                    recovery_segment.fatigue_after = self.fatigue_model.state.total
                    segments.append(recovery_segment)

            # Accumulate fatigue
            segment.fatigue_before = self.fatigue_model.state.total
            self.fatigue_model.accumulate_from_node(node, context)
            segment.fatigue_after = self.fatigue_model.state.total

            # Weather adaptation
            segment.weather_notes = self._adapt_for_weather(node, context)

            # Calculate segment quality
            segment.flow_quality = self._calculate_segment_quality(segment, context)

            segments.append(segment)
            prev_node = node

        # Calculate overall plan quality
        overall_quality = sum(plan_quality_scores) / len(plan_quality_scores) if plan_quality_scores else 0.0
        recovery_count = sum(1 for s in segments if s.recovery_injected)

        # Generate warnings
        warnings = self._generate_warnings(segments, context)

        return TripFlowPlan(
            segments=segments,
            overall_quality=overall_quality,
            total_fatigue_end=self.fatigue_model.state.total,
            recovery_stops_count=recovery_count,
            emotional_balance=emotional_balance_sum / len(segments) if segments else 0.0,
            warnings=warnings,
        )

    def _get_activity_description(self, node: LocationNode, context: TravelContext) -> str:
        """Get appropriate activity description for node and context."""
        time = context.time_of_day

        activity_map = {
            "morning": ["breakfast", "coffee", "morning walk", "exploration"],
            "afternoon": ["lunch", "exploration", "rest", "shopping"],
            "sunset": ["sunset viewing", "evening walk", "photo opportunity"],
            "evening": ["dinner", "entertainment", "relaxing"],
            "night": ["nightlife", "drinks", "night market"],
        }

        activities = activity_map.get(time, ["activity"])

        # Category-specific
        if node.category == "restaurant":
            return "dinner" if time in {"evening", "night"} else "lunch"
        elif node.category == "cafe":
            return "coffee break" if "break" in activities else "cafe visit"
        elif node.category == "beach":
            return "beach time" if time in {"morning", "afternoon"} else "sunset viewing"
        elif node.category == "attraction":
            return "exploration"

        return activities[0]

    def _adapt_for_weather(self, node: LocationNode, context: TravelContext) -> str:
        """Adapt segment for weather conditions."""
        notes = []

        if context.weather == "rainy_weather":
            if node.indoor_safe:
                notes.append("Indoor - rain safe")
            else:
                notes.append("⚠️ Outdoor - check rain status")
        elif context.weather == "hot_weather":
            if node.energy_graph.shade_available:
                notes.append("Shade available")
            elif node.energy_graph.air_conditioned:
                notes.append("Air-conditioned")
            else:
                notes.append("⚠️ Heat exposure")

        return " | ".join(notes) if notes else ""

    def _calculate_segment_quality(self, segment: TripFlowSegment, context: TravelContext) -> float:
        """Calculate overall quality of a segment (0.0-1.0)."""
        quality = 0.5

        # Emotional transition quality
        if segment.emotional_transition:
            quality += segment.emotional_transition.quality * 0.3

        # Time appropriateness
        if segment.node.time_experience.is_good_time(context.time_of_day):
            quality += 0.2

        # Recovery if needed
        if self.fatigue_model.state.total > 0.5 and segment.node.is_recovery_node:
            quality += 0.2

        # Hidden gem bonus
        if segment.node.is_hidden_gem and context.travel_dna == TravelDNA.EXPLORER.value:
            quality += 0.1

        return max(0.0, min(1.0, quality))

    def _generate_warnings(self, segments: list[TripFlowSegment], context: TravelContext) -> list[str]:
        """Generate warnings for potential issues."""
        warnings = []

        # Check for consecutive high-energy activities
        for i in range(len(segments) - 1):
            curr = segments[i]
            next_seg = segments[i + 1]
            if (curr.node.energy_graph.energy_cost in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH} and
                next_seg.node.energy_graph.energy_cost in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}):
                warnings.append(f"⚠️ Consecutive high-energy activities at {curr.node.name} and {next_seg.node.name}")

        # Check for bad emotional transitions
        for seg in segments:
            if seg.emotional_transition and seg.emotional_transition.quality < -0.3:
                warnings.append(f"⚠️ Potentially jarring transition to {seg.node.name}")

        # Check end-of-day fatigue
        if segments and segments[-1].fatigue_after > 0.8:
            warnings.append("⚠️ High fatigue at end of day - consider lighter evening activity")

        # Check sunset timing
        if context.sunset_time:
            sunset_nodes = [s for s in segments if s.node.time_experience.is_good_time("sunset")]
            if not sunset_nodes and context.time_of_day == "sunset":
                warnings.append("🌅 No sunset-optimal stop planned for golden hour")

        return warnings


# ── Weather Orchestration ────────────────────────────────────────────────────

@dataclass
class WeatherAdaptation:
    """Weather-based adaptation recommendation."""
    action: str  # "route_to_indoor", "shade_break", "delay", "cancel_beach"
    reasoning: str = ""
    urgency: str = "normal"  # low, normal, high, critical


class WeatherOrchestration:
    """
    Adaptive routing and pacing based on weather evolution.
    """

    def adapt_for_weather(
        self,
        planned_nodes: list[LocationNode],
        weather: str,
        context: TravelContext,
    ) -> list[tuple[LocationNode, WeatherAdaptation]]:
        """Adapt planned nodes for current weather conditions."""
        adapted = []

        for node in planned_nodes:
            adaptation = self._evaluate_weather_fit(node, weather, context)
            adapted.append((node, adaptation))

        return adapted

    def _evaluate_weather_fit(
        self,
        node: LocationNode,
        weather: str,
        context: TravelContext,
    ) -> WeatherAdaptation:
        """Evaluate how well a node fits current weather."""
        # Rainy weather
        if weather == "rainy_weather":
            if node.indoor_safe:
                return WeatherAdaptation(
                    action="proceed_indoor",
                    reasoning="Indoor location - rain safe",
                    urgency="low",
                )
            elif node.category == "beach":
                return WeatherAdaptation(
                    action="cancel_beach",
                    reasoning="Beach not suitable in rain",
                    urgency="high",
                )
            else:
                return WeatherAdaptation(
                    action="route_to_indoor",
                    reasoning="Find indoor alternative",
                    urgency="normal",
                )

        # Hot weather
        if weather == "hot_weather":
            if context.heat_index > 0.7:
                if node.energy_graph.heat_exposure in {EnergyLevel.LOW, EnergyLevel.VERY_LOW}:
                    return WeatherAdaptation(
                        action="proceed_shade",
                        reasoning="Shaded/air-conditioned location",
                        urgency="low",
                    )
                else:
                    return WeatherAdaptation(
                        action="shade_break",
                        reasoning="Hot weather - need cooling",
                        urgency="high",
                    )

        # Sunny with sunset dependency
        if node.weather_dependencies and "sunset" in node.weather_dependencies:
            if weather in {"hot_weather", "windy_weather"}:
                return WeatherAdaptation(
                    action="proceed",
                    reasoning="Good conditions for sunset",
                    urgency="low",
                )

        return WeatherAdaptation(
            action="proceed",
            reasoning="Weather suitable",
            urgency="low",
        )

    def suggest_rainy_alternatives(
        self,
        node: LocationNode,
        all_nodes: list[LocationNode],
    ) -> list[LocationNode]:
        """Find rainy day alternatives for a node."""
        # Find nodes with rainy_day_alternative relationship
        alternatives = []

        for rel_type, related_ids in node.relationships.items():
            if rel_type == RelationshipType.RAINY_DAY_ALTERNATIVE:
                for related_id in related_ids:
                    for n in all_nodes:
                        if n.entity_id == related_id:
                            alternatives.append(n)

        # If no explicit alternatives, find indoor nodes of same category
        if not alternatives:
            for n in all_nodes:
                if n.indoor_safe and n.category == node.category and n.entity_id != node.entity_id:
                    alternatives.append(n)

        return alternatives[:3]


# ── Time-Aware Experience Engine ──────────────────────────────────────────────

class TimeAwareExperienceEngine:
    """
    Time-based location scoring and recommendations.
    Same place can feel amazing at one time and terrible at another.
    """

    def score_for_time(
        self,
        node: LocationNode,
        time_of_day: str,
    ) -> float:
        """Score a node for a specific time of day (0.0-1.0)."""
        score = 0.5

        # Best time match
        if node.time_experience.is_good_time(time_of_day):
            score += 0.3

        # Crowd risk
        crowd_risk = node.time_experience.crowd_risk(time_of_day)
        score -= crowd_risk * 0.2

        return max(0.0, min(1.0, score))

    def suggest_optimal_time(
        self,
        node: LocationNode,
        context: TravelContext,
    ) -> list[str]:
        """Suggest optimal times to visit a node."""
        optimal = []

        # Check best times
        for best in node.time_experience.best_times:
            score = self.score_for_time(node, best)
            if score >= 0.7:
                optimal.append(best)

        # Check sunset
        if "sunset" in node.time_experience.sunset_vibes:
            optimal.append("sunset")

        # Check morning
        if "peaceful_start" in node.time_experience.morning_vibes:
            optimal.append("morning")

        return list(set(optimal))

    def get_quiet_window(
        self,
        node: LocationNode,
    ) -> str:
        """Get the quietest time window for a node."""
        if node.time_experience.quiet_times:
            return node.time_experience.quiet_times[0]

        # Default quiet times by category
        defaults = {
            "restaurant": "14:00-17:00",
            "cafe": "09:00-11:00",
            "beach": "06:00-09:00",
            "attraction": "09:00-11:00",
            "market": "06:00-09:00",
        }
        return defaults.get(node.category, "09:00-11:00")


# ── Travel DNA Matching ────────────────────────────────────────────────────────

@dataclass
class TravelDNAMatch:
    """How well a node matches the user's travel DNA."""
    travel_dna: str
    match_score: float  # 0.0-1.0
    recommendations: list[str] = field(default_factory=list)


_TRAVEL_DNA_PREFERENCES = {
    TravelDNA.EXPLORER: {
        "vibes": ["hidden", "authentic", "local", "adventurous"],
        "categories": ["hidden_spot", "attraction", "viewpoint"],
        "avoid": ["touristy", "crowded"],
    },
    TravelDNA.RELAX_TRAVELER: {
        "vibes": ["chill", "quiet", "calm", "peaceful", "recovery"],
        "categories": ["beach", "cafe", "restaurant"],
        "avoid": ["energetic", "crowded"],
    },
    TravelDNA.FOODIE: {
        "vibes": ["authentic", "local", "foodie"],
        "categories": ["restaurant", "local_market"],
        "avoid": [],
    },
    TravelDNA.PHOTOGRAPHER: {
        "vibes": ["sunset", "instagrammable", "romantic", "scenic"],
        "categories": ["viewpoint", "beach", "attraction"],
        "avoid": [],
    },
    TravelDNA.INTROVERT_TRAVELER: {
        "vibes": ["quiet", "hidden", "calm", "peaceful"],
        "categories": ["hidden_spot", "cafe"],
        "avoid": ["crowded", "social_heavy", "nightlife"],
    },
    TravelDNA.SOCIAL_TRAVELER: {
        "vibes": ["social_heavy", "crowded", "energetic", "local"],
        "categories": ["nightlife", "local_market", "restaurant"],
        "avoid": [],
    },
    TravelDNA.SLOW_TRAVELER: {
        "vibes": ["calm", "recovery", "chill", "peaceful"],
        "categories": ["cafe", "beach", "hotel"],
        "avoid": ["high_energy", "walking_heavy"],
    },
    TravelDNA.ADVENTURE_TRAVELER: {
        "vibes": ["adventurous", "hidden", "energetic"],
        "categories": ["attraction", "viewpoint"],
        "avoid": ["recovery", "quiet"],
    },
}


class TravelDNAMatching:
    """
    Match locations, timing, pacing, and routes to traveler personalities.
    """

    def match_node(
        self,
        node: LocationNode,
        travel_dna: str,
    ) -> TravelDNAMatch:
        """Match a node to the user's travel DNA."""
        if not travel_dna or travel_dna not in [d.value for d in TravelDNA]:
            return TravelDNAMatch(travel_dna=travel_dna, match_score=0.5)

        prefs = _TRAVEL_DNA_PREFERENCES.get(TravelDNA(travel_dna), {})
        match_score = 0.5
        recommendations = []

        # Check vibes
        vibe_matches = set(node.emotional_impact) & set(prefs.get("vibes", []))
        match_score += len(vibe_matches) * 0.15

        # Check category
        if node.category in prefs.get("categories", []):
            match_score += 0.2

        # Check avoid
        for avoid in prefs.get("avoid", []):
            if avoid in node.emotional_impact:
                match_score -= 0.2

        # Hidden gem bonus for explorers
        if travel_dna == TravelDNA.EXPLORER.value and node.is_hidden_gem:
            match_score += 0.15
            recommendations.append("Hidden gem - perfect for exploration")

        # Recovery bonus for relax/slow travelers
        if travel_dna in {TravelDNA.RELAX_TRAVELER.value, TravelDNA.SLOW_TRAVELER.value}:
            if node.is_recovery_node:
                match_score += 0.15
                recommendations.append("Recovery-friendly - ideal for your pace")

        return TravelDNAMatch(
            travel_dna=travel_dna,
            match_score=max(0.0, min(1.0, match_score)),
            recommendations=recommendations,
        )

    def suggest_based_on_dna(
        self,
        nodes: list[LocationNode],
        travel_dna: str,
        top_k: int = 5,
    ) -> list[LocationNode]:
        """Suggest top nodes matching the user's travel DNA."""
        matches = [(n, self.match_node(n, travel_dna).match_score) for n in nodes]
        matches.sort(key=lambda x: x[1], reverse=True)
        return [n for n, _ in matches[:top_k]]


# ── Realtime Location Scoring ───────────────────────────────────────────────────

@dataclass
class LocationScore:
    """Dynamic location score with breakdown."""
    node: LocationNode
    overall_score: float  # 0.0-10.0
    fatigue_fit: float = 0.0
    weather_fit: float = 0.0
    sunset_fit: float = 0.0
    time_fit: float = 0.0
    crowd_penalty: float = 0.0
    emotional_fit: float = 0.0
    dna_match: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node.entity_id,
            "node_name": self.node.name,
            "overall_score": round(self.overall_score, 1),
            "fatigue_fit": round(self.fatigue_fit, 1),
            "weather_fit": round(self.weather_fit, 1),
            "sunset_fit": round(self.sunset_fit, 1),
            "time_fit": round(self.time_fit, 1),
            "crowd_penalty": round(self.crowd_penalty, 1),
            "emotional_fit": round(self.emotional_fit, 1),
            "dna_match": round(self.dna_match, 1),
            "warnings": self.warnings,
        }


class RealtimeScoringEngine:
    """
    Dynamic location scoring based on weather, crowding, fatigue,
    current trip stage, emotional state, traffic, sunset timing, traveler type.
    """

    def score_node(
        self,
        node: LocationNode,
        context: TravelContext,
        fatigue_state: Optional[FatigueState] = None,
    ) -> LocationScore:
        """Score a node with all real-time factors."""
        score = LocationScore(node=node, overall_score=5.0)

        # Fatigue fit
        if fatigue_state:
            score.fatigue_fit = self._score_fatigue_fit(node, fatigue_state)
        else:
            score.fatigue_fit = self._score_default_fatigue_fit(node, context)
        score.overall_score += score.fatigue_fit * 0.3

        # Weather fit
        score.weather_fit = self._score_weather_fit(node, context)
        score.overall_score += score.weather_fit * 0.2

        # Sunset fit
        if context.time_of_day == "sunset" or context.sunset_time:
            score.sunset_fit = self._score_sunset_fit(node, context)
            score.overall_score += score.sunset_fit * 0.15

        # Time fit
        score.time_fit = self._score_time_fit(node, context)
        score.overall_score += score.time_fit * 0.15

        # Crowd penalty
        score.crowd_penalty = self._score_crowd_penalty(node, context)
        score.overall_score -= abs(score.crowd_penalty) * 0.1

        # Emotional fit
        score.emotional_fit = self._score_emotional_fit(node, context)
        score.overall_score += score.emotional_fit * 0.1

        # DNA match
        if context.travel_dna:
            dna_matcher = TravelDNAMatching()
            dna_match = dna_matcher.match_node(node, context.travel_dna)
            score.dna_match = dna_match.match_score * 10
            score.overall_score += score.dna_match * 0.1

        # Clamp to 0-10
        score.overall_score = max(0.0, min(10.0, score.overall_score))

        # Generate warnings
        score.warnings = self._generate_warnings(node, context, fatigue_state)

        return score

    def _score_fatigue_fit(self, node: LocationNode, fatigue: FatigueState) -> float:
        """Score based on current fatigue state."""
        score = 5.0

        # High overall fatigue - prefer recovery
        if fatigue.total > 0.5:
            if node.is_recovery_node:
                score += 3.0
            if node.energy_graph.recovery_score in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}:
                score += 2.0
            if node.energy_graph.walking_load in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}:
                score -= 2.0

        # High heat fatigue - prefer cooling
        if fatigue.heat > 0.5:
            if node.energy_graph.air_conditioned:
                score += 2.0
            if node.energy_graph.shade_available:
                score += 1.5
            if node.energy_graph.heat_exposure == EnergyLevel.HIGH:
                score -= 2.0

        # High social fatigue - prefer quiet
        if fatigue.social > 0.5:
            if node.energy_graph.noise_level in {EnergyLevel.LOW, EnergyLevel.VERY_LOW}:
                score += 2.0

        return max(0.0, min(10.0, score))

    def _score_default_fatigue_fit(self, node: LocationNode, context: TravelContext) -> float:
        """Score fatigue fit when no fatigue state available."""
        score = 5.0

        if context.fatigue > 0.5:
            if node.is_recovery_node:
                score += 2.0
            if node.energy_graph.walking_load in {EnergyLevel.LOW, EnergyLevel.VERY_LOW}:
                score += 1.0
        elif context.fatigue < 0.3:
            if node.energy_graph.energy_cost in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}:
                score += 1.5

        return max(0.0, min(10.0, score))

    def _score_weather_fit(self, node: LocationNode, context: TravelContext) -> float:
        """Score based on weather conditions."""
        score = 5.0

        weather_map = {
            "rainy_weather": {
                "indoor_safe": 3.0,
                "beach": -3.0,
                "outdoor_attraction": -2.0,
            },
            "hot_weather": {
                "air_conditioned": 2.0,
                "shade_available": 1.5,
                "beach": 2.0,  # Beach is ok in hot weather
                "heat_exposure_high": -2.0,
            },
        }

        if context.weather in weather_map:
            adjustments = weather_map[context.weather]
            if node.indoor_safe and "indoor_safe" in adjustments:
                score += adjustments["indoor_safe"]
            if node.category == "beach" and "beach" in adjustments:
                score += adjustments["beach"]

        return max(0.0, min(10.0, score))

    def _score_sunset_fit(self, node: LocationNode, context: TravelContext) -> float:
        """Score based on sunset appropriateness."""
        score = 5.0

        if node.time_experience.is_good_time("sunset"):
            score += 3.0
        if "sunset" in node.emotional_impact:
            score += 2.0
        if node.sunset_view:
            score += 2.0

        return max(0.0, min(10.0, score))

    def _score_time_fit(self, node: LocationNode, context: TravelContext) -> float:
        """Score based on time of day appropriateness."""
        engine = TimeAwareExperienceEngine()
        return engine.score_for_time(node, context.time_of_day) * 10

    def _score_crowd_penalty(self, node: LocationNode, context: TravelContext) -> float:
        """Score crowd penalty based on tolerance."""
        crowd_risk = node.time_experience.crowd_risk(context.time_of_day)
        penalty = 0.0

        if context.crowd_tolerance < 0.3 and crowd_risk > 0.6:
            penalty = 3.0
        elif context.crowd_tolerance > 0.7 and crowd_risk < 0.3:
            penalty = -1.0  # Slight bonus for quiet when seeking energy

        return penalty

    def _score_emotional_fit(self, node: LocationNode, context: TravelContext) -> float:
        """Score based on emotional state match."""
        emotion_map = {
            "peaceful": {"calming": 3.0, "healing": 2.0, "overwhelming": -2.0},
            "energetic": {"energizing": 3.0, "calming": -1.0},
            "healing": {"healing": 3.0, "calming": 2.0, "overwhelming": -3.0},
            "romantic": {"romantic": 3.0, "calming": 1.0},
            "overwhelming": {"calming": 3.0, "healing": 2.0, "overwhelming": -3.0},
        }

        score = 5.0
        adjustments = emotion_map.get(context.emotion, {})

        for impact, adjustment in adjustments.items():
            if impact in node.emotional_impact:
                score += adjustment

        return max(0.0, min(10.0, score))

    def _generate_warnings(
        self,
        node: LocationNode,
        context: TravelContext,
        fatigue_state: Optional[FatigueState],
    ) -> list[str]:
        """Generate warnings for potential issues."""
        warnings = []

        # Weather warning
        if context.weather == "rainy_weather" and not node.indoor_safe:
            warnings.append("🌧️ Outdoor location - check rain forecast")
        elif context.heat_index > 0.7 and node.energy_graph.heat_exposure == EnergyLevel.HIGH:
            warnings.append("🥵 High heat exposure - bring water")

        # Fatigue warning
        if fatigue_state and fatigue_state.total > 0.6:
            if node.energy_graph.walking_load in {EnergyLevel.HIGH, EnergyLevel.VERY_HIGH}:
                warnings.append("🦵 High walking required - consider recovery first")

        # Time warning
        if node.time_experience.worst_times and context.time_of_day in node.time_experience.worst_times:
            warnings.append("⏰ Not optimal time - may be crowded")

        return warnings


# ── Trip Memory Graph ──────────────────────────────────────────────────────────

@dataclass
class TripMemory:
    """Memory of past trips and experiences."""
    entity_id: str
    visit_count: int = 0
    favorite: bool = False
    disliked: bool = False
    emotional_highlights: list[str] = field(default_factory=list)
    recovery_used: bool = False
    meaningful_moments: list[str] = field(default_factory=list)
    last_visited: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "visit_count": self.visit_count,
            "favorite": self.favorite,
            "disliked": self.disliked,
            "emotional_highlights": self.emotional_highlights,
            "recovery_used": self.recovery_used,
            "meaningful_moments": self.meaningful_moments,
            "last_visited": self.last_visited,
            "notes": self.notes,
        }


class TripMemoryGraph:
    """
    Cross-trip memory of preferences, favorites, dislikes, and experiences.
    """

    def __init__(self) -> None:
        self._memories: dict[str, TripMemory] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load memories from disk."""
        memory_file = _CACHE_DIR / "trip_memory.json"
        if memory_file.exists():
            try:
                data = json.loads(memory_file.read_text())
                for entity_id, mem_data in data.get("memories", {}).items():
                    self._memories[entity_id] = TripMemory(**mem_data)
            except (json.JSONDecodeError, TypeError):
                pass

    def _save_to_disk(self) -> None:
        """Save memories to disk."""
        try:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            memory_file = _CACHE_DIR / "trip_memory.json"
            data = {
                "memories": {k: v.to_dict() for k, v in self._memories.items()},
                "updated_at": datetime.now().isoformat(),
            }
            memory_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except OSError:
            pass

    def record_visit(self, entity_id: str, context: TravelContext) -> None:
        """Record a visit to a location."""
        if entity_id not in self._memories:
            self._memories[entity_id] = TripMemory(entity_id=entity_id)

        memory = self._memories[entity_id]
        memory.visit_count += 1
        memory.last_visited = datetime.now().isoformat()

        self._save_to_disk()

    def mark_favorite(self, entity_id: str) -> None:
        """Mark a location as favorite."""
        if entity_id not in self._memories:
            self._memories[entity_id] = TripMemory(entity_id=entity_id)
        self._memories[entity_id].favorite = True
        self._memories[entity_id].disliked = False
        self._save_to_disk()

    def mark_disliked(self, entity_id: str) -> None:
        """Mark a location as disliked."""
        if entity_id not in self._memories:
            self._memories[entity_id] = TripMemory(entity_id=entity_id)
        self._memories[entity_id].disliked = True
        self._memories[entity_id].favorite = False
        self._save_to_disk()

    def add_emotional_highlight(self, entity_id: str, highlight: str) -> None:
        """Add an emotional highlight for a location."""
        if entity_id not in self._memories:
            self._memories[entity_id] = TripMemory(entity_id=entity_id)
        if highlight not in self._memories[entity_id].emotional_highlights:
            self._memories[entity_id].emotional_highlights.append(highlight)
        self._save_to_disk()

    def get_memory(self, entity_id: str) -> Optional[TripMemory]:
        """Get memory for a location."""
        return self._memories.get(entity_id)

    def get_favorites(self) -> list[str]:
        """Get list of favorite location IDs."""
        return [eid for eid, m in self._memories.items() if m.favorite]

    def get_disliked(self) -> list[str]:
        """Get list of disliked location IDs."""
        return [eid for eid, m in self._memories.items() if m.disliked]

    def suggest_from_memory(
        self,
        nodes: list[LocationNode],
        context: TravelContext,
    ) -> list[LocationNode]:
        """Suggest nodes based on trip memory."""
        suggestions = []
        disliked_ids = set(self.get_disliked())

        for node in nodes:
            memory = self._memories.get(node.entity_id)

            if memory and memory.disliked:
                continue  # Skip disliked locations

            priority = 0
            notes = []

            if memory and memory.favorite:
                priority += 5
                notes.append("Favorite location")

            if memory and memory.emotional_highlights:
                priority += len(memory.emotional_highlights)
                notes.append("Past positive experiences")

            if memory and memory.visit_count > 3:
                priority += 2
                notes.append("Frequently visited")

            if priority > 0:
                suggestions.append((node, priority, notes))

        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in suggestions]


# ── Travel Graph (Enhanced) ─────────────────────────────────────────────────────

class TravelGraph:
    """Enhanced Knowledge Graph with rich entity-to-entity relationships."""

    def __init__(self) -> None:
        self._relations: dict[str, dict[RelationshipType, list[str]]] = {}
        self._nodes: dict[str, LocationNode] = {}
        self._loaded = False
        self._load_from_disk()

    # ── Persistence ──────────────────────────────────────────────────────────────

    def _load_from_disk(self) -> None:
        if _GRAPH_FILE.exists():
            try:
                data = json.loads(_GRAPH_FILE.read_text())
                if data.get("version") == _GRAPH_VERSION:
                    # Load relationships
                    self._relations = {}
                    for entity_id, rels in data.get("relations", {}).items():
                        self._relations[entity_id] = {
                            RelationshipType(k): v for k, v in rels.items()
                        }
                    # Load nodes
                    self._nodes = {}
                    for node_data in data.get("nodes", []):
                        node = self._deserialize_node(node_data)
                        self._nodes[node.entity_id] = node
                    self._loaded = True
            except (json.JSONDecodeError, TypeError):
                pass

    def _save_to_disk(self) -> None:
        try:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "version": _GRAPH_VERSION,
                "relations": {
                    k: {rk.value: rv for rk, rv in v.items()}
                    for k, v in self._relations.items()
                },
                "nodes": [self._serialize_node(n) for n in self._nodes.values()],
                "updated_at": datetime.now().isoformat(),
            }
            _GRAPH_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except OSError:
            pass

    def _serialize_node(self, node: LocationNode) -> dict:
        return node.to_dict()

    def _deserialize_node(self, data: dict) -> LocationNode:
        # Convert relationship type strings back to enum
        rels = {}
        for rel_type_str, related_ids in data.get("relationships", {}).items():
            try:
                rel_type = RelationshipType(rel_type_str)
                rels[rel_type] = related_ids
            except ValueError:
                pass

        # Convert recovery type strings back to enum
        recovery_types = []
        for rt_str in data.get("recovery_types", []):
            try:
                recovery_types.append(RecoveryType(rt_str))
            except ValueError:
                pass

        energy_data = data.get("energy_graph", {})
        energy_graph = EnergyGraph(
            energy_cost=EnergyLevel(energy_data.get("energy_cost", "medium")),
            walking_load=EnergyLevel(energy_data.get("walking_load", "medium")),
            social_load=EnergyLevel(energy_data.get("social_load", "low")),
            recovery_score=EnergyLevel(energy_data.get("recovery_score", "low")),
            heat_exposure=EnergyLevel(energy_data.get("heat_exposure", "medium")),
            mental_load=EnergyLevel(energy_data.get("mental_load", "low")),
            decision_complexity=EnergyLevel(energy_data.get("decision_complexity", "low")),
            noise_level=EnergyLevel(energy_data.get("noise_level", "low")),
            standing_required=energy_data.get("standing_required", False),
            shade_available=energy_data.get("shade_available", True),
            seating_available=energy_data.get("seating_available", True),
            air_conditioned=energy_data.get("air_conditioned", False),
        )

        time_data = data.get("time_experience", {})
        time_experience = TimeAwareExperience(
            best_times=time_data.get("best_times", []),
            peak_crowd_times=time_data.get("peak_crowd_times", []),
            quiet_times=time_data.get("quiet_times", []),
            worst_times=time_data.get("worst_times", []),
            morning_vibes=time_data.get("morning_vibes", []),
            sunset_vibes=time_data.get("sunset_vibes", []),
            night_vibes=time_data.get("night_vibes", []),
        )

        return LocationNode(
            entity_id=data.get("entity_id", ""),
            name=data.get("name", ""),
            category=data.get("category", ""),
            relationships=rels,
            energy_graph=energy_graph,
            time_experience=time_experience,
            emotional_impact=data.get("emotional_impact", []),
            emotional_aftermath=data.get("emotional_aftermath", "neutral"),
            recovery_types=recovery_types,
            is_recovery_node=data.get("is_recovery_node", False),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            parking_available=data.get("parking_available", False),
            distance_from_main_road_km=data.get("distance_from_main_road_km", 0.0),
            weather_dependencies=data.get("weather_dependencies", []),
            indoor_safe=data.get("indoor_safe", False),
            is_hidden_gem=data.get("is_hidden_gem", False),
            local_knowledge_bonus=data.get("local_knowledge_bonus", 0.0),
            ideal_flow_before=data.get("ideal_flow_before", []),
            ideal_flow_after=data.get("ideal_flow_after", []),
            bad_flow_before=data.get("bad_flow_before", []),
        )

    # ── Node Management ─────────────────────────────────────────────────────────

    def add_node(self, node: LocationNode) -> None:
        """Add a location node to the graph."""
        self._nodes[node.entity_id] = node
        self._relations.setdefault(node.entity_id, {})
        self._save_to_disk()

    def add_entity_as_node(self, entity: TravelEntity) -> LocationNode:
        """Convert a TravelEntity to a LocationNode and add to graph."""
        node = LocationNode.from_entity(entity)
        self.add_node(node)
        return node

    def get_node(self, entity_id: str) -> Optional[LocationNode]:
        """Get a node by entity ID."""
        return self._nodes.get(entity_id)

    def get_all_nodes(self) -> list[LocationNode]:
        """Get all nodes in the graph."""
        return list(self._nodes.values())

    # ── Relations ────────────────────────────────────────────────────────────────

    def add_relation(
        self,
        entity_a: str,
        entity_b: str,
        relation_type: RelationshipType,
        strength: float = 1.0,
    ) -> None:
        """Add a typed relationship between two entities."""
        aid = self._normalize_id(entity_a)
        bid = self._normalize_id(entity_b)

        self._relations.setdefault(aid, {}).setdefault(relation_type, []).append(bid)
        self._relations.setdefault(bid, {}).setdefault(relation_type, []).append(aid)
        self._save_to_disk()

    def get_related(
        self,
        entity_id: str,
        relation_type: Optional[RelationshipType] = None,
        limit: int = 10,
    ) -> list[str]:
        """Get related entity IDs, optionally filtered by relation type."""
        eid = self._normalize_id(entity_id)
        relations = self._relations.get(eid, {})

        if relation_type:
            return relations.get(relation_type, [])[:limit]

        # Return all related
        all_related = []
        for related_list in relations.values():
            all_related.extend(related_list)
        return all_related[:limit]

    def get_nodes_by_relation(
        self,
        entity_id: str,
        relation_type: RelationshipType,
        limit: int = 10,
    ) -> list[LocationNode]:
        """Get LocationNodes related by a specific relation type."""
        related_ids = self.get_related(entity_id, relation_type, limit)
        return [self._nodes[rid] for rid in related_ids if rid in self._nodes]

    def build_auto_relations(self, entities: list[TravelEntity]) -> int:
        """Auto-discover relationships based on shared attributes."""
        count = 0

        # First, create nodes for all entities
        for entity in entities:
            if entity.id not in self._nodes:
                self.add_entity_as_node(entity)

        # Category clusters → nearby_to
        by_category: dict[str, list[str]] = {}
        for e in entities:
            by_category.setdefault(e.category, []).append(e.id)

        for cat, eids in by_category.items():
            for i, a in enumerate(eids):
                for b in eids[i + 1:]:
                    self.add_relation(a, b, RelationshipType.NEARBY_TO, strength=0.5)
                    count += 1

        # Vibe clusters → local_hidden_pair
        by_vibe: dict[str, list[str]] = {}
        for e in entities:
            for v in e.vibe_tags:
                by_vibe.setdefault(v, []).append(e.id)

        for vibe, eids in by_vibe.items():
            if vibe in {"hidden", "local", "authentic"}:
                rel_type = RelationshipType.LOCAL_HIDDEN_PAIR
            else:
                rel_type = RelationshipType.NEARBY_TO

            for i, a in enumerate(eids):
                for b in eids[i + 1:]:
                    self.add_relation(a, b, rel_type, strength=0.6)
                    count += 1

        # Trip fit chains
        by_trip_fit: dict[str, list[str]] = {}
        for e in entities:
            for tf in e.trip_fits:
                by_trip_fit.setdefault(tf, []).append(e.id)

        for fit, eids in by_trip_fit.items():
            if fit == "breakfast_stop":
                rel_type = RelationshipType.BREAKFAST_CHAIN
            elif fit == "sunset_stop":
                rel_type = RelationshipType.SUNSET_CHAIN
            elif fit == "recovery_stop":
                rel_type = RelationshipType.RECOVERY_CHAIN
            else:
                rel_type = RelationshipType.GOOD_AFTER

            for i, a in enumerate(eids):
                for b in eids[i + 1:]:
                    self.add_relation(a, b, rel_type, strength=0.7)
                    count += 1

        # Weather fit → rainy_day_alternative
        by_weather: dict[str, list[str]] = {}
        for e in entities:
            for wf in e.weather_fit:
                by_weather.setdefault(wf, []).append(e.id)

        if "indoor_safe" in by_weather and "beach" in by_category:
            for indoor_id in by_weather["indoor_safe"]:
                for beach_id in by_category.get("beach", []):
                    self.add_relation(indoor_id, beach_id, RelationshipType.RAINY_DAY_ALTERNATIVE, strength=0.8)
                    count += 1

        self._save_to_disk()
        return count

    def suggest_next(
        self,
        current_entity_id: str,
        visited_ids: list[str],
        context: TravelContext,
    ) -> list[LocationNode]:
        """Recommend next unvisited entities based on current context."""
        all_related = self.get_related(current_entity_id, limit=20)
        unvisited = [rid for rid in all_related if rid not in visited_ids]

        # Score unvisited nodes
        scoring_engine = RealtimeScoringEngine()
        scored = []

        for rid in unvisited:
            node = self._nodes.get(rid)
            if node:
                score = scoring_engine.score_node(node, context)
                scored.append((node, score.overall_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [n for n, _ in scored[:5]]

    def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5.0,
        category: Optional[str] = None,
    ) -> list[LocationNode]:
        """Find nodes near a location."""
        nearby = []

        for node in self._nodes.values():
            if node.latitude is None or node.longitude is None:
                continue
            if category and node.category != category:
                continue

            dist = self._haversine(lat, lon, node.latitude, node.longitude)
            if dist <= radius_km:
                nearby.append(node)

        nearby.sort(key=lambda n: self._haversine(lat, lon, n.latitude or 0, n.longitude or 0))
        return nearby

    def stats(self) -> dict:
        return {
            "total_nodes": len(self._nodes),
            "entities_with_relations": len(self._relations),
            "total_connections": sum(len(v) for rels in self._relations.values() for v in rels.values()) // 2,
            "recovery_nodes": sum(1 for n in self._nodes.values() if n.is_recovery_node),
            "hidden_gems": sum(1 for n in self._nodes.values() if n.is_hidden_gem),
        }

    # ── Helpers ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_id(entity_id: str) -> str:
        return entity_id.strip().lower().replace(" ", "-")

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))


# ── Ranking Engine ─────────────────────────────────────────────────────────────

class RankingEngine:
    """Multi-signal ranking engine for travel context."""

    _TIME_SLOTS: dict[str, list[str]] = {
        "morning": ["breakfast_stop", "cafe_break", "quick_stop"],
        "afternoon": ["lunch_stop", "recovery_stop"],
        "sunset": ["sunset_stop"],
        "evening": ["dinner_stop", "night_activity"],
        "night": ["night_activity", "dinner_stop"],
    }

    _EMOTION_VIBE_MAP: dict[str, list[str]] = {
        "peaceful": ["chill", "calm", "quiet"],
        "energetic": ["energetic", "social_heavy", "crowded"],
        "nostalgic": ["authentic", "local", "hidden"],
        "romantic": ["romantic", "sunset", "quiet"],
        "healing": ["chill", "recovery", "ocean_vibe"],
        "social": ["crowded", "social_heavy", "local"],
        "adventurous": ["hidden", "energetic", "authentic"],
        "overwhelming": ["chill", "quiet", "recovery"],
        "cozy": ["quiet", "chill", "local"],
    }

    _BUDGET_PRICE_MAP: dict[str, list[str]] = {
        "budget": ["budget"],
        "mid": ["budget", "mid"],
        "upscale": ["mid", "upscale"],
        "luxury": ["upscale", "luxury"],
    }

    def rank_for_context(
        self,
        entities: list[TravelEntity],
        context: TravelContext,
    ) -> list[TravelEntity]:
        """Rank entities by multi-signal context match."""
        if not entities:
            return []

        scored: list[tuple[float, TravelEntity]] = []
        for e in entities:
            score = self._compute_context_score(e, context)
            scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored]

    def _compute_context_score(self, e: TravelEntity, ctx: TravelContext) -> float:
        score = 0.0

        if ctx.weather in e.weather_fit:
            score += 0.25
        elif not e.weather_fit:
            score += 0.1

        score += self._fatigue_score(e, ctx.fatigue)
        score += self._emotion_score(e, ctx.emotion)
        score += self._time_score(e, ctx.time_of_day)
        score += self._budget_score(e, ctx.budget_level)
        score += self._crowd_score(e, ctx.crowd_tolerance)

        return score

    def _fatigue_score(self, e: TravelEntity, fatigue: float) -> float:
        if fatigue > 0.6:
            if "recovery_friendly" in e.energy_fit or "low_energy" in e.energy_fit:
                return 0.20
            if "crowded_exhausting" in e.energy_fit or "high_energy" in e.energy_fit:
                return 0.0
        elif fatigue < 0.3:
            if "high_energy" in e.energy_fit or "walking_heavy" in e.energy_fit:
                return 0.20
        if "calming" in e.energy_fit or "recovery_friendly" in e.energy_fit:
            return 0.10
        return 0.05

    def _emotion_score(self, e: TravelEntity, emotion: str) -> float:
        preferred_vibes = self._EMOTION_VIBE_MAP.get(emotion, [])
        if not preferred_vibes:
            return 0.10
        if any(v in e.vibe_tags for v in preferred_vibes):
            return 0.20
        if emotion in e.emotional_vibe:
            return 0.20
        return 0.0

    def _time_score(self, e: TravelEntity, time_of_day: str) -> float:
        slot_tags = self._TIME_SLOTS.get(time_of_day, [])
        if not slot_tags:
            return 0.075
        if any(t in e.trip_fits for t in slot_tags):
            return 0.15
        if any(time_of_day in t.lower() for t in e.best_visit_time):
            return 0.15
        return 0.075

    def _budget_score(self, e: TravelEntity, budget_level: str) -> float:
        allowed = set(self._BUDGET_PRICE_MAP.get(budget_level, ["mid"]))
        if e.price_level in allowed:
            return 0.10
        if not e.price_level:
            return 0.05
        return 0.0

    def _crowd_score(self, e: TravelEntity, tolerance: float) -> float:
        if not e.crowd_level:
            return 0.05
        if tolerance < 0.3 and e.crowd_level in ("crowded", "packed"):
            return 0.0
        if tolerance > 0.7 and e.crowd_level in ("quiet", "medium"):
            return 0.05
        return 0.10

    def re_rank(
        self,
        initial: list[TravelEntity],
        context: TravelContext,
    ) -> list[TravelEntity]:
        """Re-rank a list of pre-filtered entities by context."""
        return self.rank_for_context(initial, context)

    def best_for_weather(
        self,
        entities: list[TravelEntity],
        weather: str,
    ) -> list[TravelEntity]:
        """Filter and rank entities suitable for given weather."""
        suitable = [e for e in entities if weather in e.weather_fit or not e.weather_fit]
        return sorted(
            suitable,
            key=lambda e: 1.0 if weather in e.weather_fit else 0.0,
            reverse=True,
        )

    def suggest_recovery_stops(
        self,
        entities: list[TravelEntity],
    ) -> list[TravelEntity]:
        """Find low-energy, recovery-friendly stops."""
        recovery = [
            e for e in entities
            if "recovery_friendly" in e.energy_fit
            or "calming" in e.energy_fit
            or "low_energy" in e.energy_fit
        ]
        preferred_cats = {"cafe", "restaurant", "hotel"}
        return sorted(
            recovery,
            key=lambda e: (e.category in preferred_cats, e.crowd_level != "crowded"),
            reverse=True,
        )

    def best_for_time(
        self,
        entities: list[TravelEntity],
        time_of_day: str,
    ) -> list[TravelEntity]:
        """Find entities matching time-of-day slot."""
        slot_tags = self._TIME_SLOTS.get(time_of_day, [])
        if not slot_tags:
            return entities[:5]
        return sorted(
            entities,
            key=lambda e: any(t in e.trip_fits for t in slot_tags),
            reverse=True,
        )[:5]


# ── Intent Detection ───────────────────────────────────────────────────────────

class IntentDetector:
    """Extract travel intent signals from natural language queries."""

    _INTENT_PATTERNS: dict[str, list[str]] = {
        "location_search": ["ở đâu", "ở đây", "gần", "near", "tìm", "địa điểm", "đi đâu"],
        "food": ["ăn", "quán", "nhà hàng", "hải sản", "bún", "phở", "mì", "cơm", "bánh", "food", "restaurant"],
        "attraction": ["điểm tham quan", "tháp", "chùa", "bãi biển", "cảnh đẹp", "view", "du lịch", "attraction"],
        "shopping": ["mua", "chợ", "siêu thị", "shop", "đặc sản", "quà"],
        "hotel": ["khách sạn", "hotel", "homestay", "resort", "nghỉ", "ở", "lưu trú"],
        "weather": ["trời", "mưa", "nắng", "weather", "nóng", "gió"],
        "budget": ["giá", "tiền", "rẻ", "đắt", "budget", "bao nhiêu", "chi phí"],
        "itinerary": ["lịch trình", "ngày", "hành trình", "plan", "đi", "đến", "điểm"],
        "suggestion": ["gợi ý", "nên đi", "recommend", "suggest", "tốt nhất", "đẹp nhất"],
        "maps_direction": ["chỉ đường", "đường đi", "maps", "directions", "google maps", "dẫn đường"],
        "nearby_query": ["xung quanh", "gần đây", " nearby", "around", "khu vực"],
    }

    _VIBE_PATTERNS: dict[str, list[str]] = {
        "chill": ["chill", "yên tĩnh", "nhẹ nhàng", "thư giãn", "bình yên", "relax"],
        "local": ["local", "địa phương", "người dân", "bản địa"],
        "luxury": ["sang", "sang trọng", "luxury", "premium", "đắt tiền"],
        "quiet": ["yên", "quiet", "tĩnh lặng", "vắng", "ít người"],
        "crowded": ["đông", "đông đúc", "crowded", "đầy", "náo nhiệt"],
        "romantic": ["lãng mạn", "romantic", "tình nhân", " couple", "vợ chồng"],
        "sunset": ["hoàng hôn", "sunset", "dusk", "chiều tà"],
        "instagrammable": ["sống ảo", "đẹp", "insta", "check-in", "photogenic"],
        "family": ["gia đình", "family", "trẻ em", "cả nhà", "con nít"],
        "hidden": ["bí mật", "ẩn", "ít người biết", "bình thường"],
        "authentic": ["authentic", "thật", "nguyên bản", "truyền thống", "đặc sản"],
        "touristy": ["du lịch", "tourist", "khách", "nổi tiếng"],
        "ocean_vibe": ["biển", "ocean", "sea", "sóng", "bãi"],
        "night_vibe": ["đêm", "night", "quán nhậu", "bar"],
    }

    _TRAVELER_PATTERNS: dict[str, list[str]] = {
        "family": ["gia đình", "family", "trẻ em", "cả nhà", "con nít"],
        "couple": ["cặp đôi", "couple", "tình nhân", "yêu", "vợ chồng", "2 người"],
        "foodie": ["foodie", "sành ăn", "thích ăn", "美食", "hải sản"],
        "photographer": ["chụp ảnh", "photo", "sống ảo", "camera", "insta"],
        "backpacker": ["backpacker", "ba lô", "túi đeo", "bụi", "bình dân"],
        "digital_nomad": ["làm việc", "remote", "laptop", "wifi", "coworking"],
        "solo_traveler": ["một mình", "solo", "đi một mình", "đi riêng"],
        "luxury_traveler": ["sang", "luxury", "premium", "đắt", "cao cấp"],
    }

    _ENERGY_PATTERNS: dict[str, list[str]] = {
        "low_energy": ["nhẹ", "ít vận động", "ngồi", "nhanh", "quick", "nghỉ", "hồi phục"],
        "high_energy": ["năng động", "vui", "nhảy", "high energy", "phiêu", "máu"],
        "recovery_friendly": ["hồi phục", "recovery", "nghỉ ngơi", "nhẹ nhàng"],
        "walking_heavy": ["đi bộ", "walking", "leo", "đường dài", "trekking", "khám phá"],
        "crowded_exhausting": ["đông", "náo nhiệt", "náo loạn", "mệt", "đông đúc"],
        "calming": ["bình yên", "calm", "thư giãn", "relaxing", "yên bình"],
    }

    _WEATHER_PATTERNS: dict[str, list[str]] = {
        "hot_weather": ["nắng", "nóng", "hot", "mùa hè", "summer", "trời nắng"],
        "rainy_weather": ["mưa", "rainy", "trời mưa", "gió", "mưa to"],
        "indoor_safe": ["trong nhà", "indoor", "máy lạnh", "điều hòa", "mưa"],
        "windy_weather": ["gió", "windy", "lộng gió"],
        "sunset_best": ["hoàng hôn", "sunset", "chiều tà", "dusk"],
    }

    _EMOTION_PATTERNS: dict[str, list[str]] = {
        "peaceful": ["bình yên", "yên bình", "nhẹ nhàng", "thư giãn"],
        "energetic": ["năng động", "vui", "phấn khích", "hào hứng"],
        "nostalgic": ["hoài cổ", "cổ", "xưa", "hồi tưởng"],
        "romantic": ["lãng mạn", "romantic", "tình yêu"],
        "healing": ["hồi phục", "chữa lành", "bình yên", "nghỉ ngơi"],
        "social": ["giao lưu", "social", "nhiều người", "bạn bè"],
        "adventurous": ["phiêu lưu", "mạo hiểm", "khám phá", "adventure"],
        "cozy": ["ấm", "cozy", "thoải mái", "nhẹ nhàng"],
    }

    # Travel DNA patterns
    _TRAVEL_DNA_PATTERNS: dict[str, list[str]] = {
        "explorer": ["khám phá", "explore", "tìm tòi", "mới lạ", "bí ẩn"],
        "relax_traveler": ["nghỉ ngơi", "relax", "thư giãn", "nhẹ nhàng", "yên bình"],
        "foodie": ["ăn", "ẩm thực", "foodie", "美食", "hải sản", "đặc sản"],
        "photographer": ["chụp ảnh", "photo", "sống ảo", "view đẹp", "cảnh đẹp"],
        "introvert_traveler": ["yên tĩnh", "quiet", "vắng", "ít người", "một mình"],
        "social_traveler": ["đông vui", "giao lưu", "bạn bè", "náo nhiệt"],
        "slow_traveler": ["chậm", "slow", "thong thả", "từ từ", "nhàn nhã"],
        "adventure_traveler": ["phiêu lưu", "adventure", "mạo hiểm", "khám phá"],
    }

    def detect_travel_intent(self, query: str) -> TravelIntent:
        """Extract intent signals from a natural language query."""
        q = query.lower().strip()
        intent = TravelIntent(raw_query=query)

        # Detect intent type
        for intent_type, patterns in self._INTENT_PATTERNS.items():
            if any(p in q for p in patterns):
                intent.intent_type = intent_type
                intent.confidence = min(intent.confidence + 0.3, 1.0)

        # Extract vibes
        for vibe, patterns in self._VIBE_PATTERNS.items():
            if any(p in q for p in patterns):
                if vibe in VIBE_TAGS:
                    intent.extracted_vibes.append(vibe)
                intent.confidence = min(intent.confidence + 0.15, 1.0)

        # Extract traveler types
        for tt, patterns in self._TRAVELER_PATTERNS.items():
            if any(p in q for p in patterns):
                if tt in TRAVELER_TYPES:
                    intent.extracted_traveler_types.append(tt)
                intent.confidence = min(intent.confidence + 0.15, 1.0)

        # Extract energy signals
        for en, patterns in self._ENERGY_PATTERNS.items():
            if any(p in q for p in patterns):
                if en in ENERGY_FIT_TAGS:
                    intent.extracted_energy.append(en)
                intent.confidence = min(intent.confidence + 0.1, 1.0)

        # Extract weather signals
        for w, patterns in self._WEATHER_PATTERNS.items():
            if any(p in q for p in patterns):
                if w in WEATHER_FIT_TAGS:
                    intent.extracted_weather.append(w)
                intent.confidence = min(intent.confidence + 0.1, 1.0)

        # Extract emotion
        for em, patterns in self._EMOTION_PATTERNS.items():
            if any(p in q for p in patterns):
                if em in EMOTIONAL_VIBE:
                    intent.extracted_emotion = em
                    intent.confidence = min(intent.confidence + 0.15, 1.0)

        # Extract travel DNA
        for dna, patterns in self._TRAVEL_DNA_PATTERNS.items():
            if any(p in q for p in patterns):
                intent.extracted_travel_dna = dna
                intent.confidence = min(intent.confidence + 0.15, 1.0)

        # Extract location name
        location_match = re.search(
            r"(ở|gần|đến|tại)\s+([A-ZÀ-Ỹ][a-zà-ỹ\s]+)",
            query,
        )
        if location_match:
            intent.extracted_location = location_match.group(2).strip()

        # Extract price preference
        if any(w in q for w in ["rẻ", "tiết kiệm", "budget", "bình dân"]):
            intent.extracted_price = "budget"
            intent.confidence = min(intent.confidence + 0.1, 1.0)
        elif any(w in q for w in ["sang", "đắt", "luxury", "premium"]):
            intent.extracted_price = "luxury"
            intent.confidence = min(intent.confidence + 0.1, 1.0)

        return intent

    def build_context_from_query(
        self,
        query: str,
        default_time: str = "morning",
        default_day: int = 1,
    ) -> TravelContext:
        """Derive a TravelContext from a natural language query."""
        q = query.lower()

        time_map = {
            r"(sáng|morning|ban mai|buổi sáng)": "morning",
            r"(trưa|中午|noon|midday)": "afternoon",
            r"(chiều|afternoon|buổi chiều)": "afternoon",
            r"(hoàng hôn|sunset|tà|dusk)": "sunset",
            r"(tối|evening|đêm|night)": "evening",
            r"(khuya|đêm khuya|midnight)": "night",
        }
        time_of_day = default_time
        for pattern, slot in time_map.items():
            if re.search(pattern, q):
                time_of_day = slot
                break

        fatigue = 0.0
        fatigue_high = ["mệt", "uể oải", "mỏi", "nặng nề", "hết sức"]
        fatigue_low = ["khỏe", "năng lượng", "hào hứng", "phấn khích"]
        if any(f in q for f in fatigue_high):
            fatigue = 0.7
        elif any(f in q for f in fatigue_low):
            fatigue = 0.1

        emotion = "peaceful"
        for em, patterns in self._EMOTION_PATTERNS.items():
            if any(p in q for p in patterns):
                emotion = em
                break

        weather = "hot_weather"
        for w, patterns in self._WEATHER_PATTERNS.items():
            if any(p in q for p in patterns):
                weather = w
                break
        if "mưa" in q or "rain" in q:
            weather = "rainy_weather"

        budget_level = "mid"
        if any(w in q for w in ["rẻ", "tiết kiệm", "budget", "bình dân"]):
            budget_level = "budget"
        elif any(w in q for w in ["sang", "đắt", "luxury", "premium"]):
            budget_level = "luxury"

        travel_dna = ""
        for dna, patterns in self._TRAVEL_DNA_PATTERNS.items():
            if any(p in q for p in patterns):
                travel_dna = dna
                break

        return TravelContext(
            weather=weather,
            fatigue=fatigue,
            emotion=emotion,
            time_of_day=time_of_day,
            day=default_day,
            budget_level=budget_level,
            travel_dna=travel_dna,
        )

    def rank_for_query(
        self,
        entities: list[TravelEntity],
        query: str,
        context: Optional[TravelContext] = None,
    ) -> list[TravelEntity]:
        """Rank entities by query intent + context."""
        intent = self.detect_travel_intent(query)
        ctx = context or self.build_context_from_query(query)

        scored: list[tuple[float, TravelEntity]] = []
        for e in entities:
            score = self._intent_entity_score(intent, e)
            scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:5]]

    def _intent_entity_score(self, intent: TravelIntent, e: TravelEntity) -> float:
        """Score an entity based on travel intent."""
        score = 0.0

        # Vibe match
        if intent.extracted_vibes:
            matching = set(intent.extracted_vibes) & set(e.vibe_tags)
            score += len(matching) / len(intent.extracted_vibes) * 0.3

        # Traveler type match
        if intent.extracted_traveler_types:
            matching = set(intent.extracted_traveler_types) & set(e.traveler_types)
            score += len(matching) / len(intent.extracted_traveler_types) * 0.25

        # Energy match
        if intent.extracted_energy:
            matching = set(intent.extracted_energy) & set(e.energy_fit)
            score += len(matching) / len(intent.extracted_energy) * 0.2

        # Weather match
        if intent.extracted_weather:
            matching = set(intent.extracted_weather) & set(e.weather_fit)
            score += len(matching) / len(intent.extracted_weather) * 0.15

        # Price match
        if intent.extracted_price and e.price_level:
            if intent.extracted_price == e.price_level:
                score += 0.1

        return score


# ── Smart Orchestration Layer ─────────────────────────────────────────────────

class SmartTravelAssistant:
    """Unified layer combining graph, ranking, and intent detection."""

    def __init__(
        self,
        graph: Optional[TravelGraph] = None,
        ranker: Optional[RankingEngine] = None,
        detector: Optional[IntentDetector] = None,
    ) -> None:
        self.graph = graph or TravelGraph()
        self.ranker = ranker or RankingEngine()
        self.detector = detector or IntentDetector()
        self.trip_flow_engine = TripFlowEngine()
        self.fatigue_model = FatigueAccumulationModel()
        self.scoring_engine = RealtimeScoringEngine()
        self.memory_graph = TripMemoryGraph()
        self.weather_orchestration = WeatherOrchestration()
        self.travel_dna_matching = TravelDNAMatching()

    async def find_and_rank(
        self,
        query: str,
        entities: list[TravelEntity],
        context: TravelContext,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
    ) -> list[TravelEntity]:
        """Find entities matching query, rank by context, return top results."""
        intent = self.detector.detect_travel_intent(query)

        # Score by intent match
        intent_scored = self.detector.rank_for_query(entities, query, context)

        # Re-rank by context signals
        ranked = self.ranker.rank_for_context(intent_scored, context)

        return ranked[:5]

    async def orchestrate_flow(
        self,
        nodes: list[LocationNode],
        context: TravelContext,
    ) -> TripFlowPlan:
        """Orchestrate a complete trip flow with all systems."""
        # Get recovery nodes
        all_nodes = self.graph.get_all_nodes()
        recovery_nodes = [n for n in all_nodes if n.is_recovery_node]

        # Orchestrate the trip
        plan = self.trip_flow_engine.orchestrate_trip(nodes, context, recovery_nodes)

        return plan

    async def score_realtime(
        self,
        node: LocationNode,
        context: TravelContext,
    ) -> LocationScore:
        """Score a node with all real-time factors."""
        return self.scoring_engine.score_node(
            node, context, self.fatigue_model.state
        )

    async def adapt_for_weather(
        self,
        nodes: list[LocationNode],
        context: TravelContext,
    ) -> list[tuple[LocationNode, WeatherAdaptation]]:
        """Adapt planned nodes for weather conditions."""
        return self.weather_orchestration.adapt_for_weather(nodes, context.weather, context)

    async def suggest_by_dna(
        self,
        nodes: list[LocationNode],
        travel_dna: str,
        top_k: int = 5,
    ) -> list[LocationNode]:
        """Suggest nodes matching user's travel DNA."""
        return self.travel_dna_matching.suggest_based_on_dna(nodes, travel_dna, top_k)

    def record_memory(
        self,
        entity_id: str,
        context: TravelContext,
        favorite: bool = False,
        disliked: bool = False,
        emotional_highlight: str = "",
    ) -> None:
        """Record trip memory for a location."""
        self.memory_graph.record_visit(entity_id, context)
        if favorite:
            self.memory_graph.mark_favorite(entity_id)
        if disliked:
            self.memory_graph.mark_disliked(entity_id)
        if emotional_highlight:
            self.memory_graph.add_emotional_highlight(entity_id, emotional_highlight)

    def suggest_from_memory(
        self,
        nodes: list[LocationNode],
        context: TravelContext,
    ) -> list[LocationNode]:
        """Suggest nodes based on trip memory."""
        return self.memory_graph.suggest_from_memory(nodes, context)

    def explain_ranking(
        self,
        entity: TravelEntity,
        context: TravelContext,
    ) -> dict:
        """Return human-readable explanation of why an entity was ranked."""
        return {
            "entity": entity.name,
            "category": entity.category,
            "weather_fit": entity.weather_fit,
            "energy_fit": entity.energy_fit,
            "vibes": entity.vibe_tags,
            "context": context.to_dict(),
            "score_breakdown": {
                "fatigue": self.ranker._fatigue_score(entity, context.fatigue),
                "emotion": self.ranker._emotion_score(entity, context.emotion),
                "time": self.ranker._time_score(entity, context.time_of_day),
                "budget": self.ranker._budget_score(entity, context.budget_level),
            },
        }


# ── Singletons ─────────────────────────────────────────────────────────────────

_graph: Optional[TravelGraph] = None
_ranker: Optional[RankingEngine] = None
_detector: Optional[IntentDetector] = None
_assistant: Optional[SmartTravelAssistant] = None


def get_travel_graph() -> TravelGraph:
    global _graph
    if _graph is None:
        _graph = TravelGraph()
    return _graph


def get_ranking_engine() -> RankingEngine:
    global _ranker
    if _ranker is None:
        _ranker = RankingEngine()
    return _ranker


def get_intent_detector() -> IntentDetector:
    global _detector
    if _detector is None:
        _detector = IntentDetector()
    return _detector


def get_smart_assistant() -> SmartTravelAssistant:
    global _assistant
    if _assistant is None:
        _assistant = SmartTravelAssistant(
            graph=get_travel_graph(),
            ranker=get_ranking_engine(),
            detector=get_intent_detector(),
        )
    return _assistant


def get_trip_flow_engine() -> TripFlowEngine:
    """Get the unified trip flow orchestration engine."""
    return TripFlowEngine()


def get_fatigue_model() -> FatigueAccumulationModel:
    """Get the fatigue accumulation model."""
    return FatigueAccumulationModel()


def get_realtime_scoring_engine() -> RealtimeScoringEngine:
    """Get the realtime location scoring engine."""
    return RealtimeScoringEngine()


def get_trip_memory_graph() -> TripMemoryGraph:
    """Get the trip memory graph."""
    return TripMemoryGraph()


def get_emotional_transition_engine() -> EmotionalTransitionEngine:
    """Get the emotional transition engine."""
    return EmotionalTransitionEngine()


def get_recovery_node_system() -> RecoveryNodeSystem:
    """Get the recovery node system."""
    return RecoveryNodeSystem()


def get_weather_orchestration() -> WeatherOrchestration:
    """Get the weather orchestration system."""
    return WeatherOrchestration()


def get_time_aware_engine() -> TimeAwareExperienceEngine:
    """Get the time-aware experience engine."""
    return TimeAwareExperienceEngine()


def get_travel_dna_matching() -> TravelDNAMatching:
    """Get the travel DNA matching engine."""
    return TravelDNAMatching()
