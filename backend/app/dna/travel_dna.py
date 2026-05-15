from __future__ import annotations

from dataclasses import dataclass, field

from app.behavior.profile_engine import TravelBehaviorProfile
from app.life.context_engine import LifeContextState
from app.models.domain import UserContext
from app.personalization.human_rhythm import HumanRhythmProfile

# Travel DNA archetypes — richer than behavioral archetypes, includes life context
_DNA_PROFILES = {
    "calm_explorer": {
        "pacing": "slow",
        "density": "light",
        "atmosphere": "peaceful",
        "routing_style": "scenic_low_traffic",
        "interaction_style": "gentle_suggestions",
        "decision_tolerance": "low",
        "social_mode": "solo_or_small",
        "markers": ["yên tĩnh", "khám phá", "bình yên", "chill", "ít người"],
    },
    "energetic_foodie": {
        "pacing": "medium",
        "density": "medium",
        "atmosphere": "vibrant",
        "routing_style": "food_centric",
        "interaction_style": "enthusiastic",
        "decision_tolerance": "high",
        "social_mode": "group_friendly",
        "markers": ["ăn", "quán", "đặc sản", "hải sản", "cafe", "ăn gì", "ngon"],
    },
    "slow_traveler": {
        "pacing": "very_slow",
        "density": "minimal",
        "atmosphere": "local_authentic",
        "routing_style": "neighborhood_wander",
        "interaction_style": "minimal_push",
        "decision_tolerance": "very_low",
        "social_mode": "solo_preferred",
        "markers": ["chậm", "thư thả", "không vội", "tận hưởng", "từ từ", "ngày dài"],
    },
    "adventure_traveler": {
        "pacing": "fast",
        "density": "dense",
        "atmosphere": "exciting",
        "routing_style": "off_beaten_path",
        "interaction_style": "proactive_suggestions",
        "decision_tolerance": "high",
        "social_mode": "flexible",
        "markers": ["khám phá", "mạo hiểm", "hidden", "ẩn", "xa", "lạ", "độc đáo"],
    },
    "social_traveler": {
        "pacing": "medium",
        "density": "medium",
        "atmosphere": "lively",
        "routing_style": "social_hotspots",
        "interaction_style": "group_oriented",
        "decision_tolerance": "medium",
        "social_mode": "group_required",
        "markers": ["bạn bè", "nhóm", "cùng đi", "tụ tập", "vui vẻ", "sôi động"],
    },
    "reflective_traveler": {
        "pacing": "very_slow",
        "density": "minimal",
        "atmosphere": "contemplative",
        "routing_style": "meaningful_places",
        "interaction_style": "thoughtful",
        "decision_tolerance": "low",
        "social_mode": "solo_required",
        "markers": ["một mình", "suy nghĩ", "chiêm nghiệm", "ý nghĩa", "trải nghiệm sâu"],
    },
}

_PACING_SCORES = {"very_slow": 0.1, "slow": 0.3, "medium": 0.5, "fast": 0.7, "very_fast": 0.9}
_DENSITY_SCORES = {"minimal": 0.1, "light": 0.3, "medium": 0.5, "full": 0.7, "dense": 0.9}


@dataclass
class TravelDNAProfile:
    dna_type: str = "calm_explorer"
    pacing: str = "slow"
    density: str = "light"
    atmosphere: str = "peaceful"
    routing_style: str = "scenic_low_traffic"
    interaction_style: str = "gentle_suggestions"
    decision_tolerance: str = "low"
    social_mode: str = "solo_or_small"
    pacing_score: float = 0.3           # 0=very slow, 1=very fast
    density_score: float = 0.3          # 0=minimal, 1=dense
    confidence: float = 0.5
    dna_insights: list[str] = field(default_factory=list)
    personalization_hints: list[str] = field(default_factory=list)


class TravelDNAEngine:
    """
    Travel DNA Engine: builds a deep personal travel DNA beyond surface behavior.
    Models personality archetypes (calm_explorer, energetic_foodie, slow_traveler,
    adventure_traveler, social_traveler, reflective_traveler) with full personalization:
    pacing, recommendation density, atmosphere, routing style, and interaction style.
    """

    def assess(
        self,
        context: UserContext,
        behavior: TravelBehaviorProfile,
        life_context: LifeContextState,
        human_rhythm: HumanRhythmProfile,
    ) -> TravelDNAProfile:
        prefs = context.preferences
        text = " ".join(t.text.lower() for t in context.conversation[-20:] if t.role == "user")

        # Score each archetype
        scores: dict[str, float] = {}
        for dna_key, dna_data in _DNA_PROFILES.items():
            text_hits = sum(1 for m in dna_data["markers"] if m in text)
            scores[dna_key] = text_hits * 0.2

        # Boost based on behavior profile
        if behavior.primary_style in {"relax_traveler"}:
            scores["calm_explorer"] = scores.get("calm_explorer", 0) + 0.3
            scores["slow_traveler"] = scores.get("slow_traveler", 0) + 0.25
        if behavior.primary_style == "foodie":
            scores["energetic_foodie"] = scores.get("energetic_foodie", 0) + 0.4
        if behavior.primary_style == "explorer":
            scores["adventure_traveler"] = scores.get("adventure_traveler", 0) + 0.3
            scores["calm_explorer"] = scores.get("calm_explorer", 0) + 0.2
        if behavior.primary_style == "photographer":
            scores["reflective_traveler"] = scores.get("reflective_traveler", 0) + 0.2
            scores["calm_explorer"] = scores.get("calm_explorer", 0) + 0.2

        # Boost from life context
        if life_context.life_mode == "recovery":
            scores["calm_explorer"] = scores.get("calm_explorer", 0) + 0.35
            scores["slow_traveler"] = scores.get("slow_traveler", 0) + 0.3
        if life_context.life_mode == "social":
            scores["social_traveler"] = scores.get("social_traveler", 0) + 0.35
        if life_context.life_mode == "reflective":
            scores["reflective_traveler"] = scores.get("reflective_traveler", 0) + 0.4
        if life_context.life_mode == "escape":
            scores["slow_traveler"] = scores.get("slow_traveler", 0) + 0.25

        # Boost from human rhythm
        if human_rhythm.pacing_preference < 0.3:
            scores["slow_traveler"] = scores.get("slow_traveler", 0) + 0.2
        if human_rhythm.social_preference > 0.65:
            scores["social_traveler"] = scores.get("social_traveler", 0) + 0.2
        elif human_rhythm.social_preference < 0.35:
            scores["reflective_traveler"] = scores.get("reflective_traveler", 0) + 0.15
            scores["calm_explorer"] = scores.get("calm_explorer", 0) + 0.1

        # Retrieve persisted DNA
        persisted_dna = str(prefs.get("travel_dna_type", ""))
        if persisted_dna and persisted_dna in _DNA_PROFILES:
            scores[persisted_dna] = scores.get(persisted_dna, 0) + 0.15

        # Select dominant DNA
        if not scores or max(scores.values()) == 0:
            dna_key = "calm_explorer"
        else:
            dna_key = max(scores.items(), key=lambda x: x[1])[0]

        dna_data = _DNA_PROFILES[dna_key]
        total_score = sum(scores.values())
        confidence = min(1.0, scores[dna_key] / max(0.01, total_score) + len(context.conversation) * 0.01)

        pacing_score = _PACING_SCORES.get(dna_data["pacing"], 0.5)
        density_score = _DENSITY_SCORES.get(dna_data["density"], 0.5)

        # Build insights
        insights: list[str] = []
        hints: list[str] = []

        if dna_key == "calm_explorer":
            insights.append("Travel DNA: Calm Explorer — bạn thích khám phá theo nhịp riêng, trong không gian yên tĩnh.")
            hints.append("Mình sẽ ưu tiên điểm ít người, con đường đẹp nhưng không vội.")
        elif dna_key == "energetic_foodie":
            insights.append("Travel DNA: Energetic Foodie — chuyến đi của bạn luôn gắn với hương vị và trải nghiệm ẩm thực.")
            hints.append("Mình sẽ đan xen những quán ăn đặc sắc vào mọi lịch trình.")
        elif dna_key == "slow_traveler":
            insights.append("Travel DNA: Slow Traveler — bạn không cần nhiều điểm, chỉ cần một nơi thật sự trọn vẹn.")
            hints.append("Mình sẽ giảm số lượng gợi ý và tăng chiều sâu của từng trải nghiệm.")
        elif dna_key == "adventure_traveler":
            insights.append("Travel DNA: Adventure Traveler — bạn tìm kiếm những góc khuất mà người khác chưa biết.")
            hints.append("Mình sẽ gợi những tuyến đường ít người, điểm bí ẩn, và trải nghiệm độc đáo.")
        elif dna_key == "social_traveler":
            insights.append("Travel DNA: Social Traveler — hành trình tốt nhất của bạn là khi có người cùng chia sẻ.")
            hints.append("Mình sẽ ưu tiên điểm phù hợp nhóm và không gian có năng lượng xã hội cao.")
        elif dna_key == "reflective_traveler":
            insights.append("Travel DNA: Reflective Traveler — bạn du lịch để hiểu thêm về bản thân và thế giới.")
            hints.append("Mình sẽ gợi những nơi có ý nghĩa, câu chuyện địa phương và không gian để chiêm nghiệm.")

        return TravelDNAProfile(
            dna_type=dna_key,
            pacing=dna_data["pacing"],
            density=dna_data["density"],
            atmosphere=dna_data["atmosphere"],
            routing_style=dna_data["routing_style"],
            interaction_style=dna_data["interaction_style"],
            decision_tolerance=dna_data["decision_tolerance"],
            social_mode=dna_data["social_mode"],
            pacing_score=round(pacing_score, 2),
            density_score=round(density_score, 2),
            confidence=round(confidence, 3),
            dna_insights=insights,
            personalization_hints=hints,
        )
