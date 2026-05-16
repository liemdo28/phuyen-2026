"""Vietnamese Travel Intent Graph - Semantic Intelligence for Travel Context.

Maps implied user needs to travel context through semantic relationships.

The graph connects:
- fatigue ↔ recovery cafe
- social drinking ↔ seafood/bbq
- romantic sunset ↔ beach/quiet cafe

This is the living intelligence that understands what users MEAN.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import json


# Semantic relationship graph
TRAVEL_INTENT_GRAPH = {
    # Fatigue/Recovery nodes
    "fatigue": {
        "synonyms": ["mệt", "lười", "đói", "mệt mỏi"],
        "connections": [
            "recovery_cafe",
            "indoor_place",
            "low_movement_route",
            "rest_stop",
        ],
        "recommendations": {
            "type": ["cafe", "restaurant"],
            "ambiance": ["quiet", "comfortable", "cozy"],
            "movement_cost": "low",
        },
    },
    "recovery": {
        "synonyms": ["nghỉ", "chill", "thư giãn", "phục hồi"],
        "connections": [
            "recovery_cafe",
            "indoor_place",
            "quiet_location",
            "rest_stop",
        ],
        "recommendations": {
            "type": ["cafe", "lounge"],
            "ambiance": ["calm", "peaceful", "low_noise"],
            "duration": "extended",
        },
    },
    
    # Social Drinking nodes
    "social_drinking": {
        "synonyms": ["nhậu", "làm vài lon", "quất", "beer", "rượu"],
        "connections": [
            "seafood",
            "bbq",
            "nightlife",
            "outdoor_tables",
            "social_ambiance",
        ],
        "recommendations": {
            "type": ["seafood", "bbq", "beer_place", "night_market"],
            "ambiance": ["social", "loud", "outdoor"],
            "timing": "evening",
            "group_size": "medium_to_large",
        },
    },
    "casual_drinking": {
        "synonyms": ["chill nhậu", "kiếm quán chill nhậu"],
        "connections": [
            "chill_drinks",
            "rooftop_bar",
            "beer_garden",
            "quiet_nightlife",
        ],
        "recommendations": {
            "type": ["beer_place", "cafe_bar", "rooftop"],
            "ambiance": ["relaxed", "chill", "semi_outdoor"],
            "timing": "evening",
        },
    },
    
    # Romantic/Sunset nodes
    "romantic": {
        "synonyms": ["lãng mạn", "với người yêu", "couple", "tình yêu"],
        "connections": [
            "sunset_view",
            "beach",
            "quiet_cafe",
            "intimate_restaurant",
        ],
        "recommendations": {
            "type": ["restaurant", "cafe", "beach_bar"],
            "ambiance": ["romantic", "quiet", "intimate"],
            "timing": "golden_hour",
            "privacy": "high",
        },
    },
    "sunset": {
        "synonyms": ["ngắm sunset", "hoàng hôn", "sunset đẹp"],
        "connections": [
            "sunset_view",
            "beach",
            "rooftop",
            "mountain_view",
        ],
        "recommendations": {
            "type": ["rooftop", "beach_bar", "view_point"],
            "ambiance": ["scenic", "romantic", "outdoor"],
            "timing": "golden_hour",
        },
    },
    
    # Heat/Cold nodes
    "heat_avoidance": {
        "synonyms": ["nóng", "oi bức", "nắng gắt", "mưa"],
        "connections": [
            "indoor_ac",
            "cafe",
            "shopping_mall",
            "cold_drinks",
        ],
        "recommendations": {
            "type": ["cafe", "restaurant", "mall"],
            "ambiance": ["air_conditioned", "indoor", "cool"],
            "movement_cost": "minimal",
        },
    },
    "cold_weather": {
        "synonyms": ["lạnh", "trời lạnh", "rét"],
        "connections": [
            "warm_food",
            "hotpot",
            "soup",
            "hot_beverages",
        ],
        "recommendations": {
            "type": ["hotpot", "soup", "warm_restaurant"],
            "ambiance": ["warm", "cozy", "indoor"],
            "food_temperature": "hot",
        },
    },
    
    # Crowd avoidance nodes
    "crowd_avoidance": {
        "synonyms": ["đông", "đông nghẹt", "hạn chế đông"],
        "connections": [
            "quiet_location",
            "local_spot",
            "off_peak_timing",
            "hidden_gem",
        ],
        "recommendations": {
            "type": ["local_restaurant", "hidden_cafe"],
            "crowd_level": "low",
            "timing": "off_peak",
        },
    },
    
    # Food mood nodes
    "light_food": {
        "synonyms": ["đói nhẹ", "ăn nhẹ", "snack"],
        "connections": [
            "street_food",
            "snacks",
            "beverages",
            "quick_bite",
        ],
        "recommendations": {
            "type": ["street_food", "snack_bar", "bubble_tea"],
            "portion": "small",
            "duration": "short",
        },
    },
    "heavy_food": {
        "synonyms": ["đói ghê", "đói chết", "ăn no"],
        "connections": [
            "full_meal",
            "restaurant",
            "local_food",
        ],
        "recommendations": {
            "type": ["restaurant", "local_food"],
            "portion": "large",
            "duration": "medium",
        },
    },
    
    # Movement resistance nodes
    "low_movement": {
        "synonyms": ["lười đi", "ngại đi xa", "gần đây", "không muốn di chuyển"],
        "connections": [
            "nearby_only",
            "stationary",
            "low_distance",
        ],
        "recommendations": {
            "distance": "very_close",
            "movement_cost": "none",
            "area_search": "immediate",
        },
    },
    
    # Time-based nodes
    "early_morning": {
        "synonyms": ["sáng sớm", "cafe sáng", "dawn"],
        "connections": [
            "morning_market",
            "early_cafe",
            "breakfast",
            "peaceful_location",
        ],
        "recommendations": {
            "type": ["cafe", "market"],
            "timing": "early_morning",
            "ambiance": ["quiet", "peaceful"],
        },
    },
    "late_night": {
        "synonyms": ["khuya", "ăn khuya", "đêm khuya"],
        "connections": [
            "night_market",
            "late_restaurant",
            "nightlife",
            "24h_place",
        ],
        "recommendations": {
            "type": ["night_market", "late_restaurant"],
            "timing": "late_night",
            "open_until": "late",
        },
    },
    
    # Local vs Tourist nodes
    "local_authentic": {
        "synonyms": ["local", "dân địa phương", "authentic", "hidden gem"],
        "connections": [
            "local_restaurant",
            "hidden_gem",
            "neighborhood_spot",
            "non_touristy",
        ],
        "recommendations": {
            "type": ["local_restaurant", "street_food"],
            "tourist_level": "none",
            "authenticity": "high",
        },
    },
    "tourist_spot": {
        "synonyms": ["nổi tiếng", "popular", "ai cũng biết"],
        "connections": [
            "famous_restaurant",
            "landmark",
            "reviewed_place",
        ],
        "recommendations": {
            "type": ["famous_restaurant"],
            "tourist_level": "high",
            "review_status": "popular",
        },
    },
    
    # Group/Solo nodes
    "group_travel": {
        "synonyms": ["đi đông", "team", "nhóm", "bạn bè"],
        "connections": [
            "group_restaurant",
            "social_ambiance",
            "large_table",
            "shared_dishes",
        ],
        "recommendations": {
            "group_size": "large",
            "seating": "large_table",
            "food_style": "sharing",
        },
    },
    "solo_travel": {
        "synonyms": ["đi một mình", "solo", "một mình"],
        "connections": [
            "solo_friendly",
            "counter_seating",
            "quick_meal",
        ],
        "recommendations": {
            "group_size": "solo",
            "seating": ["counter", "small_table"],
            "food_style": "individual",
        },
    },
    "couple_travel": {
        "synonyms": ["đi cặp đôi", "với người yêu", "2 người"],
        "connections": [
            "romantic_spot",
            "intimate_setting",
            "couple_table",
        ],
        "recommendations": {
            "group_size": "couple",
            "seating": "private_table",
            "ambiance": "romantic",
        },
    },
    
    # Chill variants
    "ocean_chill": {
        "synonyms": ["biển", "bãi biển", "beach chill"],
        "connections": [
            "beach_bar",
            "seaside_cafe",
            "ocean_view",
        ],
        "recommendations": {
            "type": ["beach_bar", "seaside_cafe"],
            "location": "beach",
            "ambiance": "relaxed_ocean",
        },
    },
    "cafe_chill": {
        "synonyms": ["cafe chill", "ngồi cafe", "chill cafe"],
        "connections": [
            "aesthetic_cafe",
            "cozy_cafe",
            "study_cafe",
        ],
        "recommendations": {
            "type": ["cafe"],
            "ambiance": ["cozy", "aesthetic", "quiet"],
            "duration": "extended",
        },
    },
    "sunset_chill": {
        "synonyms": ["sunset chill", "ngắm hoàng hôn"],
        "connections": [
            "sunset_view",
            "rooftop",
            "beach",
        ],
        "recommendations": {
            "type": ["rooftop", "beach_bar", "view_point"],
            "timing": "golden_hour",
            "ambiance": "scenic",
        },
    },
    "nightlife_chill": {
        "synonyms": ["khuya chill", "đêm chill"],
        "connections": [
            "quiet_bar",
            "beer_garden",
            "late_night_cafe",
        ],
        "recommendations": {
            "type": ["bar", "beer_place"],
            "timing": "late_night",
            "ambiance": "relaxed",
        },
    },
}


# Location type mappings
LOCATION_TYPES = {
    "cafe": {
        "tags": ["cafe", "coffee", "drinks"],
        "ambiance": ["casual", "cozy", "quiet"],
        "suitable_for": ["recovery", "chill", "work", "dates"],
    },
    "restaurant": {
        "tags": ["restaurant", "food", "dine"],
        "ambiance": ["casual", "formal", "family"],
        "suitable_for": ["meals", "groups", "celebrations"],
    },
    "seafood": {
        "tags": ["seafood", "fish", "crab", "shrimp"],
        "ambiance": ["casual", "outdoor", "social"],
        "suitable_for": ["social_drinking", "groups", "local_experience"],
    },
    "bbq": {
        "tags": ["bbq", "nướng", "grill"],
        "ambiance": ["casual", "outdoor", "social"],
        "suitable_for": ["social_drinking", "groups", "fun"],
    },
    "hotpot": {
        "tags": ["hotpot", "lẩu"],
        "ambiance": ["social", "warm", "group"],
        "suitable_for": ["cold_weather", "groups", "social"],
    },
    "street_food": {
        "tags": ["street_food", "đường phố", "vendor"],
        "ambiance": ["casual", "local", "quick"],
        "suitable_for": ["light_food", "local_authentic", "budget"],
    },
    "bar": {
        "tags": ["bar", "cocktail", "drinks"],
        "ambiance": ["moody", "dark", "social"],
        "suitable_for": ["nightlife", "romantic", "social"],
    },
    "beach_bar": {
        "tags": ["beach", "seaside", "tropical"],
        "ambiance": ["relaxed", "outdoor", "scenic"],
        "suitable_for": ["ocean_chill", "sunset", "romantic"],
    },
    "rooftop": {
        "tags": ["rooftop", "view", "sky"],
        "ambiance": ["scenic", "romantic", "trendy"],
        "suitable_for": ["sunset", "romantic", "celebrations"],
    },
}


@dataclass
class TravelIntent:
    """Complete travel intent from semantic analysis."""
    primary_intent: str = ""
    implied_needs: list[str] = field(default_factory=list)
    
    # Location preferences
    location_types: list[str] = field(default_factory=list)
    ambiance: list[str] = field(default_factory=list)
    crowd_level: str = ""  # low, medium, high
    
    # Physical preferences
    movement_cost: str = ""  # none, low, medium, high
    distance: str = ""  # immediate, close, medium, far
    indoor_outdoor: str = ""  # indoor, outdoor, both
    
    # Food preferences
    food_type: str = ""  # light, heavy, specific
    food_temperature: str = ""  # hot, cold, both
    
    # Social preferences
    group_size: str = ""  # solo, couple, small, large
    privacy_level: str = ""  # low, medium, high
    
    # Timing
    timing: str = ""  # morning, afternoon, evening, night, any
    duration: str = ""  # short, medium, extended
    
    # Emotional state
    emotional_state: str = ""
    recovery_needed: bool = False
    
    # Confidence
    confidence: float = 1.0


class TravelIntentGraph:
    """Semantic graph for travel intent resolution."""
    
    def __init__(self) -> None:
        self._graph = TRAVEL_INTENT_GRAPH
        self._location_types = LOCATION_TYPES
    
    def resolve(self, implied_intent: str, context: Optional[dict] = None) -> TravelIntent:
        """
        Resolve travel intent from implied intent.
        
        Args:
            implied_intent: The implied user intent
            context: Additional context from other resolvers
            
        Returns:
            TravelIntent with complete recommendations
        """
        intent = TravelIntent(primary_intent=implied_intent)
        
        # Find matching node in graph
        node = self._find_node(implied_intent)
        
        if node:
            self._apply_node(intent, node)
        
        # Apply context overrides
        if context:
            self._apply_context(intent, context)
        
        return intent
    
    def _find_node(self, intent: str) -> Optional[dict]:
        """Find matching node in semantic graph."""
        intent_lower = intent.lower()
        
        for node_name, node_data in self._graph.items():
            # Check direct match
            if node_name == intent_lower:
                return node_data
            
            # Check synonyms
            synonyms = node_data.get("synonyms", [])
            for syn in synonyms:
                if syn in intent_lower or intent_lower in syn:
                    return node_data
        
        return None
    
    def _apply_node(self, intent: TravelIntent, node: dict) -> None:
        """Apply node data to travel intent."""
        # Get recommendations
        recs = node.get("recommendations", {})
        
        if "type" in recs:
            intent.location_types = recs["type"]
        
        if "ambiance" in recs:
            intent.ambiance = recs["ambiance"]
        
        if "movement_cost" in recs:
            intent.movement_cost = recs["movement_cost"]
        
        if "crowd_level" in recs:
            intent.crowd_level = recs["crowd_level"]
        
        if "timing" in recs:
            intent.timing = recs["timing"]
        
        if "duration" in recs:
            intent.duration = recs["duration"]
        
        if "distance" in recs:
            intent.distance = recs["distance"]
        
        # Get connections (secondary intents)
        connections = node.get("connections", [])
        intent.implied_needs = connections
        
        # Infer physical preferences from connections
        if "indoor_place" in connections:
            intent.indoor_outdoor = "indoor"
        elif "outdoor_tables" in connections:
            intent.indoor_outdoor = "outdoor"
        
        # Infer group size from connections
        if "large_table" in connections:
            intent.group_size = "large"
        elif "couple_table" in connections:
            intent.group_size = "couple"
    
    def _apply_context(self, intent: TravelIntent, context: dict) -> None:
        """Apply context overrides to travel intent."""
        if "location_type" in context:
            intent.location_types = context["location_type"]
        
        if "ambiance" in context:
            intent.ambiance = context["ambiance"]
        
        if "movement_cost" in context:
            intent.movement_cost = context["movement_cost"]
        
        if "crowd_level" in context:
            intent.crowd_level = context["crowd_level"]
        
        if "timing" in context:
            intent.timing = context["timing"]
    
    def get_location_tags(self, location_type: str) -> dict:
        """Get tags for a location type."""
        return self._location_types.get(location_type.lower(), {})
    
    def match_location(self, location_tags: list[str], intent: TravelIntent) -> float:
        """
        Calculate match score between location and intent.
        
        Returns:
            Float score from 0.0 to 1.0
        """
        if not intent.location_types:
            return 0.5  # No preference, neutral
        
        score = 0.0
        matches = 0
        
        for loc_type in intent.location_types:
            if loc_type.lower() in [t.lower() for t in location_tags]:
                matches += 1
        
        if intent.location_types:
            score = matches / len(intent.location_types)
        
        # Bonus for ambiance match
        if intent.ambiance:
            loc_data = self._get_location_data(location_tags)
            if loc_data and "ambiance" in loc_data:
                amb_matches = sum(
                    1 for a in intent.ambiance
                    if a.lower() in [x.lower() for x in loc_data["ambiance"]]
                )
                score += (amb_matches / len(intent.ambiance)) * 0.3
        
        return min(1.0, score)
    
    def _get_location_data(self, tags: list[str]) -> Optional[dict]:
        """Get location data from tags."""
        for tag in tags:
            if tag.lower() in self._location_types:
                return self._location_types[tag.lower()]
        return None
    
    def get_recommendation_context(self, intent: TravelIntent) -> dict:
        """
        Get complete recommendation context for query.
        
        Returns dict ready for travel recommendation engine.
        """
        context = {
            "primary_intent": intent.primary_intent,
            "filters": {},
            "boost": {},
        }
        
        # Build filters
        if intent.location_types:
            context["filters"]["type"] = intent.location_types
        
        if intent.crowd_level:
            context["filters"]["crowd_level"] = intent.crowd_level
        
        if intent.indoor_outdoor:
            context["filters"]["indoor_outdoor"] = intent.indoor_outdoor
        
        if intent.timing:
            context["filters"]["timing"] = intent.timing
        
        if intent.distance:
            context["filters"]["distance"] = intent.distance
        
        # Build boost (preferences that improve ranking)
        if intent.ambiance:
            context["boost"]["ambiance"] = intent.ambiance
        
        if intent.group_size:
            context["boost"]["group_size"] = intent.group_size
        
        if intent.emotional_state:
            context["boost"]["emotional_state"] = intent.emotional_state
        
        # Special flags
        if intent.recovery_needed:
            context["special_flags"] = ["recovery_friendly", "low_energy"]
        
        return context