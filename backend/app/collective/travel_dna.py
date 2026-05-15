"""
Travel DNA Engine — Phase 7 MVP.

Builds persistent traveler DNA profile from conversation behavior patterns.
Stores learned preferences across trips for long-term personalization.

Privacy: Per-user, per-device only. No cross-user data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.behavior.profile_engine import TravelBehaviorProfile

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


@dataclass
class TravelDNA:
    """Persistent traveler DNA — evolves across trips."""
    # Core archetype
    primary_archetype: str = "balanced"
    archetype_scores: dict[str, float] = field(default_factory=dict)

    # Activity preferences (learned from behavior)
    prefers_beach: float = 0.5   # 0-1
    prefers_food: float = 0.5
    prefers_nature: float = 0.5
    prefers_culture: float = 0.5
    prefers_photo: float = 0.0
    prefers_chill: float = 0.5

    # Timing preferences (learned from feedback)
    prefers_early_start: float = 0.5  # 0.5 = neutral
    prefers_slow_pace: float = 0.5
    prefers_spontaneity: float = 0.3

    # Social preferences
    crowd_tolerance: float = 0.5  # from behavior engine
    comfort_bias: float = 0.5

    # Emotional patterns
    fatigue_threshold: float = 0.6  # at what point does user signal tiredness
    stress_triggers: list[str] = field(default_factory=list)
    joy_triggers: list[str] = field(default_factory=list)

    # Learning metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(VN_TZ))
    trip_count: int = 0
    signal_count: int = 0

    def summary_prompt(self) -> str:
        """Compact DNA summary for system prompt injection."""
        traits = []
        if self.primary_archetype != "balanced":
            traits.append(f"type:{self.primary_archetype}")
        if self.prefers_beach >= 0.7:
            traits.append("beach_lover")
        if self.prefers_food >= 0.7:
            traits.append("food_focused")
        if self.prefers_photo >= 0.6:
            traits.append("photo_oriented")
        if self.prefers_slow_pace >= 0.7:
            traits.append("slow_traveler")
        if self.prefers_chill >= 0.7:
            traits.append("chill_seeker")
        if self.prefers_spontaneity >= 0.6:
            traits.append("spontaneous")
        if self.fatigue_threshold <= 0.4:
            traits.append("low_fatigue_tolerance")
        if self.stress_triggers:
            triggers = ",".join(self.stress_triggers[:3])
            traits.append(f"stressors:{triggers}")
        return "; ".join(traits) if traits else "general_traveler"


# Phú Yên-specific archetypes for quick learning
ARCHETYPE_SIGNALS = {
    "beach": {
        "keywords": ["biển", "bãi", "tắm", "sóng", "bơi", "cát", "bãi xép", "vịnh"],
        "positive": ["yên bình", "thư giãn", "mát", "đẹp", "bình yên"],
        "negative": ["đông", "kẹt", "nóng quá"],
    },
    "foodie": {
        "keywords": ["ăn", "quán", "ngon", "hải sản", "đặc sản", "bún", "bánh", "cafe"],
        "positive": ["ngon quá", "tuyệt", "đáng", "wow", "hài lòng"],
        "negative": ["dở", "đắt", "chờ lâu"],
    },
    "nature": {
        "keywords": ["núi", "rừng", "hòn", "đá", "cây", "thác", "suối", "cảnh"],
        "positive": ["hoang sơ", "đẹp", "nguyên sơ", "tuyệt"],
        "negative": ["nóng", "mệt"],
    },
    "culture": {
        "keywords": ["tháp", "chùa", "đền", "lịch sử", "văn hóa", "cổ", "làng"],
        "positive": ["ấn tượng", "thú vị", "đẹp", "hay"],
        "negative": [],
    },
    "photo": {
        "keywords": ["chụp", "ảnh", "view", "hoàng hôn", "sunset", "check-in", "sống ảnh"],
        "positive": ["đẹp quá", "xịn", "perfect", "wow"],
        "negative": ["đông", "chờ", "mệt"],
    },
    "chill": {
        "keywords": ["nghỉ", "chill", "yên", "nhẹ", "thư giãn", "cafe"],
        "positive": ["chill", "yên bình", "thư giãn", "mát"],
        "negative": ["đông", "vội", "kẹt", "sớm"],
    },
}


class TravelDNAEngine:
    """
    Learns traveler DNA from behavior patterns and feedback signals.
    Persists to memory service for cross-session recall.
    """

    def __init__(self) -> None:
        self._dna: dict[int, TravelDNA] = {}  # key: user_id
        self._conversation_buffer: dict[int, list[str]] = {}  # user_id -> recent messages

    def learn_from_message(self, user_id: int, text: str, role: str = "user") -> None:
        """Buffer a message for DNA learning."""
        if role != "user":
            return
        if user_id not in self._conversation_buffer:
            self._conversation_buffer[user_id] = []
        self._conversation_buffer[user_id].append(text.lower())
        # Keep last 50 messages
        self._conversation_buffer[user_id] = self._conversation_buffer[user_id][-50:]

    def learn_from_behavior_profile(self, user_id: int, profile: TravelBehaviorProfile) -> None:
        """Update DNA from detected behavior profile."""
        if user_id not in self._dna:
            self._dna[user_id] = TravelDNA()
        dna = self._dna[user_id]

        dna.primary_archetype = profile.primary_style
        dna.archetype_scores = profile.scores.copy()
        dna.crowd_tolerance = profile.crowd_tolerance
        dna.comfort_bias = profile.comfort_bias
        dna.prefers_photo = profile.photo_bias
        dna.prefers_food = profile.food_bias
        dna.last_updated = datetime.now(VN_TZ)
        dna.signal_count += 1

    def learn_from_experience_signal(
        self, user_id: int, signal_type: str, text: str
    ) -> None:
        """Update DNA from a single experience signal."""
        if user_id not in self._dna:
            self._dna[user_id] = TravelDNA()

        dna = self._dna[user_id]
        words = text.lower()

        # Detect archetype from content
        for archetype, sigs in ARCHETYPE_SIGNALS.items():
            keyword_hit = any(k in words for k in sigs["keywords"])
            pos_hit = any(p in words for p in sigs.get("positive", []))
            neg_hit = any(n in words for n in sigs.get("negative", []))

            if keyword_hit:
                if signal_type == "positive" and pos_hit:
                    if archetype == "beach":
                        dna.prefers_beach = min(dna.prefers_beach + 0.1, 1.0)
                    elif archetype == "foodie":
                        dna.prefers_food = min(dna.prefers_food + 0.1, 1.0)
                    elif archetype == "nature":
                        dna.prefers_nature = min(dna.prefers_nature + 0.1, 1.0)
                    elif archetype == "photo":
                        dna.prefers_photo = min(dna.prefers_photo + 0.1, 1.0)
                    elif archetype == "chill":
                        dna.prefers_chill = min(dna.prefers_chill + 0.1, 1.0)

                elif signal_type == "negative" and neg_hit:
                    if archetype == "beach":
                        dna.prefers_beach = max(dna.prefers_beach - 0.1, 0.0)
                    elif archetype == "foodie":
                        dna.prefers_food = max(dna.prefers_food - 0.1, 0.0)

        # Detect fatigue threshold
        if signal_type == "negative" and any(w in words for w in ["mệt", "chán", "bực", "stress"]):
            dna.fatigue_threshold = min(dna.fatigue_threshold + 0.05, 1.0)
            if "mệt" in words:
                dna.stress_triggers = list(set(dna.stress_triggers + ["early_start", "long_distance"]))
            if "đông" in words:
                dna.stress_triggers = list(set(dna.stress_triggers + ["crowds"]))

        # Detect joy triggers
        if signal_type == "positive" and any(w in words for w in ["tuyệt", "wow", "ngon", "đẹp", "vui"]):
            for trigger in ["food", "beach", "view", "chill"]:
                if trigger in words:
                    dna.joy_triggers = list(set(dna.joy_triggers + [trigger]))[:5]

        # Detect pacing preference
        if any(w in words for w in ["sớm", "dậy sớm", "5h", "4h", "4 giờ"]):
            dna.prefers_early_start = min(dna.prefers_early_start + 0.1, 1.0)
        if any(w in words for w in ["chill", "từ từ", "không vội", "nhẹ nhàng"]):
            dna.prefers_slow_pace = min(dna.prefers_slow_pace + 0.1, 1.0)
        if any(w in words for w in ["quyết luôn", "liền", "nhanh", "ngay"]):
            dna.prefers_spontaneity = min(dna.prefers_spontaneity + 0.1, 1.0)

        dna.last_updated = datetime.now(VN_TZ)
        dna.signal_count += 1

    def get_dna(self, user_id: int) -> TravelDNA:
        """Get traveler DNA for a user."""
        if user_id not in self._dna:
            self._dna[user_id] = TravelDNA()
        return self._dna[user_id]

    def enrich_prompt(self, user_id: int) -> str:
        """Get DNA as enrichment text for system prompt."""
        dna = self.get_dna(user_id)
        return dna.summary_prompt()

    def get_travel_style_description(self, user_id: int) -> str:
        """Human-readable travel style description."""
        dna = self.get_dna(user_id)
        parts = []

        if dna.primary_archetype != "balanced":
            archetype_names = {
                "explorer": "thích khám phá",
                "foodie": "ưa ẩm thực",
                "relax_traveler": "thích thư giãn",
                "photographer": "thích chụp ảnh",
                "luxury_traveler": "thích sang trọng",
                "spontaneous_traveler": "tự phát",
            }
            parts.append(archetype_names.get(dna.primary_archetype, dna.primary_archetype))

        if dna.prefers_beach >= 0.7:
            parts.append("yêu biển")
        if dna.prefers_food >= 0.7:
            parts.append("đam mê ẩm thực")
        if dna.prefers_nature >= 0.7:
            parts.append("thích thiên nhiên")
        if dna.prefers_photo >= 0.6:
            parts.append("thích chụp ảnh")
        if dna.prefers_slow_pace >= 0.7:
            parts.append("thích nhịp chậm")
        if dna.fatigue_threshold <= 0.4:
            parts.append("dễ mệt, cần nghỉ sớm")

        if not parts:
            return "traveler thông thường"
        return ", ".join(parts)