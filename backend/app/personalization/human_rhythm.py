from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.fatigue.energy_engine import TravelEnergyState
from app.models.domain import UserContext

MORNING_TOKENS = ["sáng sớm", "buổi sáng", "cà phê sáng", "dậy sớm", "bình minh", "ăn sáng"]
NIGHT_OWL_TOKENS = ["đêm", "khuya", "tối muộn", "bar", "nhạc đêm", "chợ đêm"]
SOCIAL_TOKENS = ["bạn bè", "nhóm", "cùng nhau", "gia đình", "hội bạn", "đồng nghiệp"]
SOLO_TOKENS = ["một mình", "solo", "tự do", "tự đi", "không cần ai", "yên tĩnh thôi"]
DETAIL_TOKENS = ["chi tiết", "kỹ", "cẩn thận", "tìm hiểu", "đọc review", "research"]
SPONTANEOUS_TOKENS = ["tùy hứng", "liền thôi", "quyết nhanh", "không cần plan", "tự nhiên", "bất ngờ"]
DEEP_TOKENS = ["văn hóa", "lịch sử", "bản địa", "ngư dân", "cuộc sống địa phương", "thật sự"]
SURFACE_TOKENS = ["check in", "selfie", "ảnh đẹp", "sống ảo", "feed", "story"]


@dataclass
class HumanRhythmProfile:
    morning_energy: float = 0.5         # 0=night owl, 1=morning person
    walking_tolerance: float = 0.6      # 0=minimal walking, 1=loves walking
    social_preference: float = 0.5      # 0=solo, 1=social
    exploration_depth: float = 0.5      # 0=surface, 1=deep
    pacing_preference: float = 0.5      # 0=slow/relaxed, 1=fast/dense
    decision_tolerance: float = 0.6     # 0=low (needs simplicity), 1=high (enjoys choices)
    is_morning_person: bool = False
    is_social_traveler: bool = False
    is_deep_explorer: bool = False
    insights: list[str] = field(default_factory=list)


class HumanRhythmEngine:
    """
    Learns each traveler's unique biological and behavioral rhythm:
    morning energy, walking tolerance, social preference, exploration depth,
    pacing preference, and decision tolerance. Makes the trip feel naturally
    aligned with the traveler's personality.
    """

    _DECAY = 0.80

    def assess(
        self,
        context: UserContext,
        now: datetime,
        energy: TravelEnergyState,
    ) -> HumanRhythmProfile:
        prefs = context.preferences
        text = " ".join(
            t.text.lower() for t in context.conversation[-15:] if t.role == "user"
        )

        # Retrieve persisted rhythm state
        morning_energy = float(prefs.get("rhythm_morning_energy", 0.5))
        walking_tolerance = float(prefs.get("rhythm_walking_tolerance", 0.6))
        social_preference = float(prefs.get("rhythm_social_pref", 0.5))
        exploration_depth = float(prefs.get("rhythm_exploration_depth", 0.5))
        pacing_preference = float(prefs.get("rhythm_pacing_pref", 0.5))
        decision_tolerance = float(prefs.get("rhythm_decision_tolerance", 0.6))

        # Morning/night rhythm signal
        morning_signal = sum(1 for t in MORNING_TOKENS if t in text) * 0.18
        night_signal = sum(1 for t in NIGHT_OWL_TOKENS if t in text) * 0.15
        if morning_signal > 0:
            morning_energy = min(1.0, morning_energy * self._DECAY + morning_signal * (1 - self._DECAY))
        if night_signal > 0:
            morning_energy = max(0.0, morning_energy * self._DECAY - night_signal * (1 - self._DECAY) * 0.5)

        # Time-of-day inference
        hour = now.hour
        if hour < 8 and energy.physical_energy > 0.5:
            morning_energy = min(1.0, morning_energy + 0.05)
        if hour >= 22 and energy.emotional_energy > 0.4:
            morning_energy = max(0.0, morning_energy - 0.04)

        # Social preference
        social_signal = sum(1 for t in SOCIAL_TOKENS if t in text) * 0.2
        solo_signal = sum(1 for t in SOLO_TOKENS if t in text) * 0.25
        if social_signal > 0:
            social_preference = min(1.0, social_preference * self._DECAY + social_signal * (1 - self._DECAY))
        if solo_signal > 0:
            social_preference = max(0.0, social_preference * self._DECAY - solo_signal * (1 - self._DECAY))

        # Exploration depth
        deep_signal = sum(1 for t in DEEP_TOKENS if t in text) * 0.2
        surface_signal = sum(1 for t in SURFACE_TOKENS if t in text) * 0.15
        if deep_signal > 0:
            exploration_depth = min(1.0, exploration_depth * self._DECAY + deep_signal * (1 - self._DECAY))
        if surface_signal > 0:
            exploration_depth = max(0.0, exploration_depth * self._DECAY - surface_signal * (1 - self._DECAY) * 0.5)

        # Pacing from spontaneous vs detail tokens
        spontaneous_signal = sum(1 for t in SPONTANEOUS_TOKENS if t in text) * 0.18
        detail_signal = sum(1 for t in DETAIL_TOKENS if t in text) * 0.15
        if spontaneous_signal > 0:
            pacing_preference = min(1.0, pacing_preference * self._DECAY + spontaneous_signal * (1 - self._DECAY))
        if detail_signal > 0:
            pacing_preference = max(0.0, pacing_preference * self._DECAY - detail_signal * (1 - self._DECAY) * 0.4)

        # Energy-based walking tolerance
        if energy.physical_energy < 0.3:
            walking_tolerance = max(0.1, walking_tolerance - 0.08)
        elif energy.physical_energy > 0.7:
            walking_tolerance = min(1.0, walking_tolerance + 0.03)

        # Decision tolerance based on decision energy
        decision_tolerance = max(0.1, min(1.0, energy.decision_energy * 0.8 + decision_tolerance * 0.2))

        # Build insights
        insights: list[str] = []
        if morning_energy > 0.65:
            insights.append("Bạn là người buổi sáng — lên kế hoạch những điểm đẹp nhất vào đầu ngày.")
        elif morning_energy < 0.35:
            insights.append("Bạn thích bắt đầu từ từ — lịch sáng sẽ nhẹ nhàng, chiều mới đẩy mạnh.")
        if social_preference > 0.65:
            insights.append("Bạn thích đi cùng người khác — sẽ ưu tiên điểm phù hợp cho nhóm.")
        elif social_preference < 0.35:
            insights.append("Bạn thích không gian riêng — mình sẽ gợi những góc ít đông đúc hơn.")
        if exploration_depth > 0.6:
            insights.append("Bạn thích tìm hiểu chiều sâu — có thể mình gợi ý câu chuyện địa phương đi kèm.")

        profile = HumanRhythmProfile(
            morning_energy=round(morning_energy, 3),
            walking_tolerance=round(walking_tolerance, 3),
            social_preference=round(social_preference, 3),
            exploration_depth=round(exploration_depth, 3),
            pacing_preference=round(pacing_preference, 3),
            decision_tolerance=round(decision_tolerance, 3),
            is_morning_person=morning_energy > 0.6,
            is_social_traveler=social_preference > 0.6,
            is_deep_explorer=exploration_depth > 0.6,
            insights=insights[:2],
        )
        return profile
