"""
Collective Experience Tracker — Phase 7 MVP.

Tracks group feedback signals (positive/negative reactions) to learn
which places, activities, and timing patterns create joy vs. fatigue.
Works per-trip context to avoid cross-user privacy issues.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

# Phú Yên location tags for signal mapping
PLACE_TAGS = {
    "Gành Đá Đĩa": ["gành đá đĩa", "đá đĩa", "ganh da dia"],
    "Vịnh Hòa": ["vịnh hòa", "bãi vịnh hòa", "vinh hoa"],
    "Bãi Xép": ["bãi xép", "bai xep", "hoa vàng"],
    "Mũi Điện": ["mũi điện", "cực đông", "mui dien"],
    "Tuy Hòa": ["tuy hòa", "tuy hoa", "thành phố"],
    "Sông Cầu": ["sông cầu", "song cau"],
    "Đầm Ô Loan": ["đầm ô loan", "đầm", "dam o loan"],
    "Tháp Nhạn": ["tháp nhạn", "thap nhan"],
    "Bún cá ngừ": ["bún cá ngừ", "bún cá", "bun ca nu"],
    "Hải sản Sông Cầu": ["hải sản", "tôm hùm", "seafood", "hai san"],
    "Bánh hỏi": ["bánh hỏi", "banh hoi"],
    "Cà phê": ["cà phê", "cafe", "càfe", "café"],
}

POSITIVE_SIGNALS = [
    "tuyệt", "wow", "ngon", "đẹp", "thích", "vui", "hài lòng",
    "perfect", "amazing", "happy", "đã", "đáng", "xuất sắc",
    "ấn tượng", "hay", "cool", "wow", "oke", "ok", "👍", "❤️",
    "bún cá ngừ", "gỏi cá mai", "sò huyết", "tôm hùm", "ngon quá",
    "view đẹp", "đẹp quá", "chill", "thư giãn", "yên bình",
]

NEGATIVE_SIGNALS = [
    "mệt", "chán", "dở", "đông", "bực", "nóng", "mưa",
    "tệ", "bad", "terrible", "disappointed", "exhausted",
    "crowded", "đông nghịt", "kẹt xe", "mất", "quên",
    "lạc", "buồn", "khó chịu", "stress",
]

ENERGY_DRAIN_ACTIVITIES = [
    "dậy sớm", "4h", "4 giờ", "5h", "5 giờ", "sớm",
    "nhiều chỗ", "nhiều km", "đi xa", "leo núi",
]

ENERGY_RESTORE_ACTIVITIES = [
    "nghỉ", "ngồi", "chill", "cafe", "cà phê", "ngắm",
    "thư giãn", "bơi", "tắm biển nhẹ", "nghỉ trưa",
]


@dataclass
class ExperienceSignal:
    timestamp: datetime
    signal_type: str  # "positive", "negative", "energy_drain", "energy_restore"
    location: str | None
    activity: str | None
    intensity: float = 1.0  # 0.0 - 1.0


@dataclass
class CollectiveExperienceState:
    trip_day: int
    signals: list[ExperienceSignal]
    location_sentiment: dict[str, float] = field(default_factory=dict)
    timing_insights: list[str] = field(default_factory=list)
    collective_mood: str = "unknown"  # "positive", "cautious", "tired", "energized"
    energy_trend: str = "stable"  # "rising", "stable", "dipping"
    top_experiences: list[str] = field(default_factory=list)


class CollectiveExperienceTracker:
    """
    Tracks experience signals during a trip to build collective intelligence.

    Privacy: Only tracks signals from the current trip context (in-memory).
    No cross-user data collection.
    """

    def __init__(self) -> None:
        self._signals: list[ExperienceSignal] = []
        self._last_assessment: datetime | None = None

    def track(self, incoming_text: str, now: datetime, trip_day: int = 1) -> None:
        """Extract and store experience signals from user message."""
        text = incoming_text.lower()
        intensity = 1.0

        # Detect intensity
        if any(p in text for p in ["tuyệt vời", "wow", "xuất sắc", "perfect"]):
            intensity = 1.0
        elif any(p in text for p in ["ngon", "đẹp", "thích", "vui"]):
            intensity = 0.7
        elif any(p in text for p in ["mệt", "chán", "bực", "đông"]):
            intensity = 0.8
        elif any(p in text for p in ["hơi", "ít"]):
            intensity = 0.4

        # Positive signals
        if any(s in text for s in POSITIVE_SIGNALS):
            location = self._extract_location(text)
            activity = self._extract_activity(text)
            self._signals.append(ExperienceSignal(
                timestamp=now,
                signal_type="positive",
                location=location,
                activity=activity,
                intensity=intensity,
            ))

        # Negative signals
        if any(s in text for s in NEGATIVE_SIGNALS):
            location = self._extract_location(text)
            activity = self._extract_activity(text)
            self._signals.append(ExperienceSignal(
                timestamp=now,
                signal_type="negative",
                location=location,
                activity=activity,
                intensity=intensity,
            ))

        # Energy drain
        if any(s in text for s in ENERGY_DRAIN_ACTIVITIES):
            self._signals.append(ExperienceSignal(
                timestamp=now,
                signal_type="energy_drain",
                location=None,
                activity="early_start_or_long_distance",
                intensity=min(intensity + 0.2, 1.0),
            ))

        # Energy restore
        if any(s in text for s in ENERGY_RESTORE_ACTIVITIES):
            self._signals.append(ExperienceSignal(
                timestamp=now,
                signal_type="energy_restore",
                location=None,
                activity="rest_or_light_activity",
                intensity=min(intensity + 0.2, 1.0),
            ))

    def _extract_location(self, text: str) -> str | None:
        for loc, tags in PLACE_TAGS.items():
            if any(tag in text for tag in tags):
                return loc
        return None

    def _extract_activity(self, text: str) -> str | None:
        if any(t in text for t in ["ăn", "sáng", "trưa", "tối"]):
            return "meal"
        if any(t in text for t in ["tắm biển", "bơi", "biển"]):
            return "beach"
        if any(t in text for t in ["chụp", "ảnh", "view", "check-in"]):
            return "photo"
        if any(t in text for t in ["cafe", "cà phê"]):
            return "cafe"
        if any(t in text for t in ["nghỉ", "ngủ", "trưa"]):
            return "rest"
        return None

    def assess(self, now: datetime, trip_day: int = 1) -> CollectiveExperienceState:
        """Aggregate signals into actionable collective intelligence."""
        self._last_assessment = now

        # Compute location sentiment
        location_sentiment: dict[str, float] = defaultdict(float)
        location_count: dict[str, int] = defaultdict(int)
        for sig in self._signals[-20:]:
            if sig.location:
                if sig.signal_type == "positive":
                    location_sentiment[sig.location] += sig.intensity
                elif sig.signal_type == "negative":
                    location_sentiment[sig.location] -= sig.intensity * 0.7
                location_count[sig.location] += 1

        for loc in location_sentiment:
            count = location_count[loc]
            location_sentiment[loc] /= max(count, 1)

        # Compute collective mood from recent signals (last 3 hours)
        recent = [s for s in self._signals[-20:] if now - s.timestamp < timedelta(hours=3)]
        pos = sum(1 for s in recent if s.signal_type == "positive")
        neg = sum(1 for s in recent if s.signal_type == "negative")
        energy_drain = sum(1 for s in recent if s.signal_type == "energy_drain")
        energy_restore = sum(1 for s in recent if s.signal_type == "energy_restore")

        if pos > neg * 1.5 and energy_drain <= energy_restore:
            collective_mood = "positive"
        elif neg > pos * 1.5 or energy_drain > energy_restore * 2:
            collective_mood = "tired"
        elif neg > pos:
            collective_mood = "cautious"
        elif energy_restore > energy_drain:
            collective_mood = "energized"
        else:
            collective_mood = "unknown"

        # Energy trend
        recent_hour = [s for s in self._signals[-20:] if now - s.timestamp < timedelta(hours=1)]
        prev_hour = [s for s in self._signals[-20:-len(recent_hour) or None]
                     if now - s.timestamp < timedelta(hours=2)]
        drain_now = sum(1 for s in recent_hour if s.signal_type == "energy_drain")
        restore_now = sum(1 for s in recent_hour if s.signal_type == "energy_restore")
        drain_prev = sum(1 for s in prev_hour if s.signal_type == "energy_drain")
        restore_prev = sum(1 for s in prev_hour if s.signal_type == "energy_restore")

        net_now = restore_now - drain_now
        net_prev = restore_prev - drain_prev
        if net_now > net_prev + 1:
            energy_trend = "rising"
        elif net_now < net_prev - 1:
            energy_trend = "dipping"
        else:
            energy_trend = "stable"

        # Timing insights
        timing_insights: list[str] = []
        if energy_drain > energy_restore:
            timing_insights.append("Nhóm đang tiêu tốn năng lượng — ưu tiên nghỉ ngơi ở activity tiếp theo.")
        if neg > pos and neg > 3:
            timing_insights.append("Có tín hiệu tiêu cực tích lũy — nên giảm density hoạt động.")
        if collective_mood == "positive" and energy_trend == "rising":
            timing_insights.append("Nhóm đang có năng lượng tốt — có thể tăng thêm lựa chọn.")

        # Top experiences (locations with highest positive sentiment)
        top_locs = sorted(location_sentiment.items(), key=lambda x: x[1], reverse=True)[:3]
        top_experiences = [f"{loc} ({'+' if score > 0 else ''}{score:.1f})" for loc, score in top_locs if score != 0]

        return CollectiveExperienceState(
            trip_day=trip_day,
            signals=self._signals[-20:],
            location_sentiment=dict(location_sentiment),
            timing_insights=timing_insights,
            collective_mood=collective_mood,
            energy_trend=energy_trend,
            top_experiences=top_experiences,
        )