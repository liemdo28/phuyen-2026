"""Vietnamese Indirect Request Resolution System.

Understands what users MEAN vs what they literally type.
Vietnamese users often do NOT directly ask - they imply.

Examples:
- "đói ghê" → suggest food nearby
- "nóng quá" → indoor cafe, cold drinks, low walking route
- "mệt muốn xỉu" → recovery needed, simplify itinerary
- "đông quá trời" → crowd avoidance, quieter alternatives
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# Indirect request patterns - what users imply vs what they say
INDIRECT_REQUESTS = {
    # Hunger → Food suggestions
    "đói": {
        "implied_intent": "food_search",
        "context_preference": "food_nearby",
        "urgency": "medium",
        "movement_cost": "low",
    },
    "đói ghê": {
        "implied_intent": "food_search",
        "context_preference": "food_nearby",
        "urgency": "high",
        "emotional_state": "urgent_hunger",
    },
    "đói chết": {
        "implied_intent": "food_search",
        "context_preference": "food_nearby",
        "urgency": "high",
        "emotional_state": "critical_hunger",
    },
    "đói nhẹ": {
        "implied_intent": "food_search",
        "context_preference": "snacks",
        "urgency": "low",
        "food_type": "light",
    },
    
    # Heat → Indoor/cooling preferences
    "nóng": {
        "implied_intent": "cooling",
        "context_preference": "indoor",
        "temperature": "cold",
        "movement_cost": "low",
    },
    "nóng quá": {
        "implied_intent": "cooling",
        "context_preference": "indoor_ac",
        "temperature": "very_cold",
        "movement_cost": "low",
        "avoid_walking": True,
    },
    "oi bức": {
        "implied_intent": "cooling",
        "context_preference": "indoor_ac",
        "temperature": "cold",
    },
    "nắng gắt": {
        "implied_intent": "shade",
        "context_preference": "indoor",
        "avoid_outdoor": True,
    },
    
    # Cold → Warm food preferences
    "lạnh": {
        "implied_intent": "warm_food",
        "context_preference": "hot_food",
        "temperature": "warm",
    },
    "trời lạnh": {
        "implied_intent": "warm_food",
        "context_preference": "soup_hotpot",
        "temperature": "warm",
    },
    
    # Rain → Indoor rerouting
    "mưa": {
        "implied_intent": "indoor",
        "context_preference": "indoor",
        "avoid_outdoor": True,
    },
    "mưa to": {
        "implied_intent": "indoor",
        "context_preference": "full_shelter",
        "avoid_outdoor": True,
    },
    
    # Fatigue → Recovery mode
    "mệt": {
        "implied_intent": "recovery",
        "context_preference": "low_energy",
        "movement_cost": "very_low",
        "recovery_needed": True,
    },
    "mệt quá": {
        "implied_intent": "recovery",
        "context_preference": "low_energy",
        "movement_cost": "minimal",
        "recovery_needed": True,
        "simplify_trip": True,
    },
    "mệt muốn xỉu": {
        "implied_intent": "recovery",
        "context_preference": "rest_stop",
        "movement_cost": "none",
        "recovery_needed": True,
        "urgent": True,
    },
    "lười": {
        "implied_intent": "low_effort",
        "movement_cost": "low",
        "prefer_nearby": True,
    },
    "lười đi quá": {
        "implied_intent": "low_effort",
        "movement_cost": "minimal",
        "prefer_nearby": True,
        "simplify_trip": True,
    },
    
    # Crowd avoidance
    "đông": {
        "implied_intent": "avoid_crowd",
        "context_preference": "quiet",
        "crowd_tolerance": "low",
    },
    "đông quá trời": {
        "implied_intent": "avoid_crowd",
        "context_preference": "very_quiet",
        "crowd_tolerance": "none",
    },
    "đông nghẹt": {
        "implied_intent": "avoid_crowd",
        "context_preference": "empty",
        "crowd_tolerance": "none",
        "urgent_avoidance": True,
    },
    
    # Movement resistance
    "ngại đi xa": {
        "implied_intent": "nearby_only",
        "movement_cost": "none",
        "distance_preference": "very_close",
    },
    "lười chạy": {
        "implied_intent": "low_movement",
        "movement_cost": "low",
        "prefer_nearby": True,
    },
    "gần đây thôi": {
        "implied_intent": "nearby_only",
        "movement_cost": "minimal",
        "distance_preference": "immediate",
    },
    "kiếm gần gần": {
        "implied_intent": "nearby_only",
        "movement_cost": "minimal",
        "distance_preference": "close",
    },
    "không muốn di chuyển nhiều": {
        "implied_intent": "minimal_movement",
        "movement_cost": "none",
        "stay_stationary": True,
    },
    
    # Social drinking
    "nhậu": {
        "implied_intent": "social_drinking",
        "context_preference": "seafood_bbq",
        "timing": "evening",
        "vibe": "social",
    },
    "làm vài lon": {
        "implied_intent": "social_drinking",
        "context_preference": "casual_drink",
        "timing": "evening",
        "group_vibe": True,
    },
    "quất vài chai": {
        "implied_intent": "social_drinking",
        "context_preference": "drinks",
        "timing": "evening",
        "group_vibe": True,
    },
    "beer không": {
        "implied_intent": "beer",
        "context_preference": "beer_place",
        "timing": "evening",
    },
    "kiếm quán chill nhậu": {
        "implied_intent": "casual_drinking",
        "context_preference": "chill_drinks",
        "vibe": "relaxed_social",
    },
    "kiếm mồi": {
        "implied_intent": "drinking_food",
        "context_preference": "snacks_drinks",
    },
    
    # Recovery/Rest
    "nghỉ tí": {
        "implied_intent": "rest",
        "movement_cost": "none",
        "recovery_needed": True,
    },
    "kiếm chỗ nằm": {
        "implied_intent": "rest_stop",
        "movement_cost": "none",
        "comfort_preference": "high",
    },
    "chill nhẹ": {
        "implied_intent": "relaxation",
        "vibe": "calm",
        "energy_level": "low",
    },
    "yên tĩnh tí": {
        "implied_intent": "quiet",
        "context_preference": "peaceful",
        "noise_level": "very_low",
    },
    "kiếm chỗ mát": {
        "implied_intent": "cooling_rest",
        "context_preference": "shade_ac",
        "movement_cost": "low",
    },
    "kiếm quán ngồi lâu được": {
        "implied_intent": "long_stay",
        "context_preference": "comfortable_seating",
        "duration": "extended",
    },
    
    # Beautiful weather → Scenic
    "trời đẹp ghê": {
        "implied_intent": "outdoor_scenic",
        "context_preference": "outdoor",
        "weather_ideal": True,
    },
    
    # Time-based
    "ăn khuya": {
        "implied_intent": "late_night_food",
        "timing": "khuya",
        "open_late": True,
    },
    "cafe sáng": {
        "implied_intent": "morning_cafe",
        "timing": "early_morning",
    },
    "sunset đẹp": {
        "implied_intent": "sunset_view",
        "timing": "evening_golden",
    },
    "sáng sớm": {
        "implied_intent": "early_morning",
        "timing": "dawn",
    },
    "khuya chill": {
        "implied_intent": "late_night_chill",
        "timing": "late_night",
        "vibe": "relaxed",
    },
}


@dataclass
class IndirectIntent:
    """Parsed indirect request with implied meaning."""
    original_text: str = ""
    literal_intent: str = ""
    implied_intent: str = ""
    
    # Context preferences
    context_preference: list = field(default_factory=list)
    temperature: str = ""  # cold, warm, hot
    movement_cost: str = ""  # none, low, medium, high
    distance_preference: str = ""  # immediate, close, medium, far
    
    # Emotional state
    emotional_state: str = ""
    urgency: str = ""  # low, medium, high, critical
    recovery_needed: bool = False
    simplify_trip: bool = False
    
    # Avoidance flags
    avoid_outdoor: bool = False
    avoid_walking: bool = False
    avoid_crowd: bool = False
    
    # Food preferences
    food_type: str = ""
    
    # Social preferences
    group_vibe: bool = False
    couple_friendly: bool = False
    family_friendly: bool = False
    solo_friendly: bool = False
    
    # Timing
    timing: str = ""  # morning, afternoon, evening, khuya
    
    # Vibes
    vibe: str = ""  # chill, social, romantic, quiet
    
    # Crowd tolerance
    crowd_tolerance: str = ""  # none, low, medium, high
    
    # Confidence score
    confidence: float = 1.0


class IndirectRequestResolver:
    """Resolves indirect Vietnamese requests to implied meaning."""
    
    def __init__(self) -> None:
        self._patterns = INDIRECT_REQUESTS
    
    def resolve(self, text: str) -> IndirectIntent:
        """
        Resolve indirect request from text.
        
        Args:
            text: Raw user input
            
        Returns:
            IndirectIntent with implied meaning
        """
        text_lower = text.lower().strip()
        intent = IndirectIntent(original_text=text)
        
        # Check for exact matches first
        for pattern, info in self._patterns.items():
            if pattern in text_lower:
                self._apply_pattern(intent, info, pattern)
                return intent
        
        # Try to find partial matches
        words = text_lower.split()
        matched_info = {}
        
        for word in words:
            for pattern, info in self._patterns.items():
                if word in pattern or pattern in text_lower:
                    matched_info = info.copy()
                    break
        
        if matched_info:
            self._apply_pattern(intent, matched_info, "")
        
        return intent
    
    def _apply_pattern(self, intent: IndirectIntent, info: dict, matched_pattern: str) -> None:
        """Apply pattern information to intent."""
        if not info:
            return
        
        # Set implied intent
        intent.implied_intent = info.get("implied_intent", "")
        intent.literal_intent = matched_pattern
        
        # Apply context preferences
        if "context_preference" in info:
            pref = info["context_preference"]
            if isinstance(pref, list):
                intent.context_preference = pref
            else:
                intent.context_preference = [pref]
        
        # Apply other attributes
        for key, value in info.items():
            if hasattr(intent, key):
                setattr(intent, key, value)
    
    def get_travel_context(self, text: str) -> dict:
        """
        Get travel context from indirect request.
        
        Returns dict with travel recommendations hints.
        """
        intent = self.resolve(text)
        
        context = {
            "intent": intent.implied_intent,
            "preferences": {},
            "avoid": [],
            "urgency": intent.urgency,
            "recovery": intent.recovery_needed,
        }
        
        # Build preferences
        if intent.temperature:
            context["preferences"]["temperature"] = intent.temperature
        
        if intent.movement_cost:
            context["preferences"]["movement_cost"] = intent.movement_cost
        
        if intent.distance_preference:
            context["preferences"]["distance"] = intent.distance_preference
        
        if intent.context_preference:
            context["preferences"]["type"] = intent.context_preference
        
        if intent.vibe:
            context["preferences"]["vibe"] = intent.vibe
        
        if intent.timing:
            context["preferences"]["timing"] = intent.timing
        
        # Build avoid list
        if intent.avoid_outdoor:
            context["avoid"].append("outdoor")
        if intent.avoid_walking:
            context["avoid"].append("walking")
        if intent.avoid_crowd:
            context["avoid"].append("crowded")
        
        return context