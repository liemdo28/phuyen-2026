from __future__ import annotations

from dataclasses import dataclass, field

from app.models.domain import UserContext

ARCHETYPE_MARKERS = {
    "explorer": ["đi đâu", "ẩn", "hidden", "khám phá", "xa chút", "view đẹp"],
    "foodie": ["ăn", "quán", "cafe", "cà phê", "hải sản", "đặc sản"],
    "relax_traveler": ["nghỉ", "chill", "nhẹ nhàng", "yên tĩnh", "thư giãn"],
    "photographer": ["ảnh", "hình", "sunset", "hoàng hôn", "check-in", "view"],
    "luxury_traveler": ["resort", "luxury", "sang", "xịn", "cao cấp"],
    "spontaneous_traveler": ["gần đây", "bây giờ", "liền", "nhanh", "quyết luôn"],
}


@dataclass
class TravelBehaviorProfile:
    primary_style: str = "balanced"
    scores: dict[str, float] = field(default_factory=dict)
    crowd_tolerance: float = 0.5
    comfort_bias: float = 0.5
    photo_bias: float = 0.0
    food_bias: float = 0.0


class TravelBehaviorEngine:
    def assess(self, context: UserContext, incoming_text: str) -> TravelBehaviorProfile:
        text = incoming_text.lower()
        scores: dict[str, float] = {}
        history = " ".join(turn.text.lower() for turn in context.conversation[-12:] if turn.role == "user")
        combined = f"{history} {text}".strip()

        for archetype, markers in ARCHETYPE_MARKERS.items():
            scores[archetype] = min(sum(1 for marker in markers if marker in combined) * 0.2, 1.0)

        profile = TravelBehaviorProfile(scores=scores)
        profile.primary_style = max(scores.items(), key=lambda item: item[1])[0] if scores else "balanced"
        profile.photo_bias = scores.get("photographer", 0.0)
        profile.food_bias = scores.get("foodie", 0.0)
        profile.comfort_bias = min(1.0, scores.get("relax_traveler", 0.0) + 0.3)
        profile.crowd_tolerance = max(0.1, 0.75 - scores.get("relax_traveler", 0.0) * 0.4)
        return profile
