from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


# EMA decay for place-emotion learning
_DECAY = 0.80
_SIGNAL_STEP = 0.15

# Place categories and their baseline emotional profile
_BASELINE_CALM: dict[str, float] = {
    "beach": 0.65,
    "cafe": 0.60,
    "nature": 0.70,
    "market": 0.30,
    "restaurant": 0.40,
    "hotel": 0.55,
    "attraction": 0.45,
    "town": 0.35,
}

CALM_SIGNALS = [
    "yên tĩnh", "chill", "thoải mái", "thư giãn", "bình yên",
    "dễ chịu", "ổn áp", "lặng", "nhẹ nhàng", "vắng",
]
STRESS_SIGNALS = [
    "đông ghê", "ồn", "ồn ào", "nhiều người", "kẹt", "bực",
    "mệt", "nóng quá", "chật", "rối", "khó chịu",
]
JOY_SIGNALS = [
    "tuyệt", "đẹp", "hay quá", "thích", "ngon", "vui", "wow",
    "ngon quá", "chill", "đáng", "xứng đáng",
]
RECOVERY_SIGNALS = [
    "nghỉ", "tịnh dưỡng", "hồi phục", "ngủ", "nằm", "thư giãn",
    "lấy lại sức", "nạp năng lượng",
]


@dataclass
class PlaceEmotionalProfile:
    place_key: str
    place_name: str
    place_type: str           # beach|cafe|nature|etc.
    calm_score: float = 0.5   # 0=stressful, 1=very calm
    joy_score: float = 0.5    # 0=dull, 1=very joyful
    recovery_power: float = 0.5  # how well it restores energy
    visit_count: int = 0
    last_sentiment: str = "neutral"
    tags: list[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GeographyState:
    place_profiles: dict[str, PlaceEmotionalProfile] = field(default_factory=dict)
    # Signals emitted by this assessment
    signals: list[str] = field(default_factory=list)
    # Hint for the AI companion
    hint: str = ""
    # Best recovery spot known
    best_recovery_place: str | None = None
    # Best joy spot known
    best_joy_place: str | None = None


class EmotionalGeographyEngine:
    """
    Learns which places create calmness, stress, joy, or recovery
    for a specific user based on their conversational signals after visiting.

    The engine builds a persistent PlaceEmotionalProfile per place
    using EMA-based learning from sentiment signals in conversation.
    """

    def __init__(self) -> None:
        self._state = GeographyState()
        self._initialize_phu_yen_defaults()

    def _initialize_phu_yen_defaults(self) -> None:
        defaults = [
            ("bai_xep", "Bãi Xép", "beach", 0.80, 0.75, 0.72),
            ("ganh_da_dia", "Gành Đá Đĩa", "attraction", 0.55, 0.85, 0.50),
            ("mui_dien", "Mũi Điện", "attraction", 0.70, 0.90, 0.60),
            ("vinh_hoa", "Vịnh Hòa", "beach", 0.75, 0.70, 0.68),
            ("dam_o_loan", "Đầm Ô Loan", "nature", 0.80, 0.72, 0.70),
            ("thap_nhan", "Tháp Nhạn", "heritage", 0.65, 0.65, 0.50),
            ("tuy_hoa_beach", "Bãi biển Tuy Hòa", "beach", 0.60, 0.65, 0.60),
            ("song_cau", "Sông Cầu", "town", 0.45, 0.70, 0.40),
            ("hon_yen", "Hòn Yến", "island", 0.82, 0.85, 0.72),
        ]
        for key, name, ptype, calm, joy, recovery in defaults:
            self._state.place_profiles[key] = PlaceEmotionalProfile(
                place_key=key,
                place_name=name,
                place_type=ptype,
                calm_score=calm,
                joy_score=joy,
                recovery_power=recovery,
            )
        # Run initial state computation so best_recovery_place / hint are populated
        self._recompute_state()

    def observe(
        self,
        text: str,
        place_key: str,
        place_name: str | None = None,
        place_type: str | None = None,
    ) -> GeographyState:
        """
        Process a user message mentioning or following a place visit.
        Updates the emotional profile of that place.
        """
        t = text.lower().strip()
        profile = self._get_or_create(place_key, place_name or place_key, place_type or "unknown")
        profile.visit_count += 1

        # Detect signals
        calm_hits = sum(1 for s in CALM_SIGNALS if s in t)
        stress_hits = sum(1 for s in STRESS_SIGNALS if s in t)
        joy_hits = sum(1 for s in JOY_SIGNALS if s in t)
        recovery_hits = sum(1 for s in RECOVERY_SIGNALS if s in t)

        # EMA updates
        if calm_hits > 0:
            profile.calm_score = _ema(profile.calm_score, min(calm_hits * _SIGNAL_STEP + 0.5, 1.0))
        if stress_hits > 0:
            profile.calm_score = _ema(profile.calm_score, max(0.5 - stress_hits * _SIGNAL_STEP, 0.0))
        if joy_hits > 0:
            profile.joy_score = _ema(profile.joy_score, min(joy_hits * _SIGNAL_STEP + 0.5, 1.0))
        if recovery_hits > 0:
            profile.recovery_power = _ema(profile.recovery_power, min(recovery_hits * _SIGNAL_STEP + 0.5, 1.0))

        profile.last_sentiment = _resolve_sentiment(calm_hits, stress_hits, joy_hits)
        profile.updated_at = datetime.now(timezone.utc)

        self._recompute_state()
        return self._state

    def recommend_for_recovery(self) -> str | None:
        """Return the place key with highest recovery_power."""
        if not self._state.place_profiles:
            return None
        best = max(self._state.place_profiles.values(), key=lambda p: p.recovery_power)
        return best.place_key if best.recovery_power >= 0.55 else None

    def recommend_for_joy(self) -> str | None:
        """Return the place key with highest joy_score."""
        if not self._state.place_profiles:
            return None
        best = max(self._state.place_profiles.values(), key=lambda p: p.joy_score)
        return best.place_key if best.joy_score >= 0.55 else None

    def get_profile(self, place_key: str) -> PlaceEmotionalProfile | None:
        return self._state.place_profiles.get(place_key)

    def get_state(self) -> GeographyState:
        return self._state

    def to_preference_updates(self) -> dict[str, object]:
        """Serialize top-3 profiles for persistence in UserContext.preferences."""
        updates: dict[str, object] = {}
        sorted_profiles = sorted(
            self._state.place_profiles.values(),
            key=lambda p: p.visit_count,
            reverse=True,
        )
        for p in sorted_profiles[:5]:
            prefix = f"geo_{p.place_key}"
            updates[f"{prefix}_calm"] = round(p.calm_score, 3)
            updates[f"{prefix}_joy"] = round(p.joy_score, 3)
            updates[f"{prefix}_visits"] = p.visit_count
        return updates

    def load_from_preferences(self, preferences: dict[str, object]) -> None:
        for key, profile in self._state.place_profiles.items():
            calm_key = f"geo_{key}_calm"
            joy_key = f"geo_{key}_joy"
            visits_key = f"geo_{key}_visits"
            if calm_key in preferences:
                profile.calm_score = float(preferences[calm_key])
            if joy_key in preferences:
                profile.joy_score = float(preferences[joy_key])
            if visits_key in preferences:
                profile.visit_count = int(preferences[visits_key])

    # ------------------------------------------------------------------

    def _get_or_create(self, key: str, name: str, ptype: str) -> PlaceEmotionalProfile:
        if key not in self._state.place_profiles:
            baseline_calm = _BASELINE_CALM.get(ptype, 0.5)
            self._state.place_profiles[key] = PlaceEmotionalProfile(
                place_key=key,
                place_name=name,
                place_type=ptype,
                calm_score=baseline_calm,
                joy_score=0.5,
                recovery_power=0.5,
            )
        return self._state.place_profiles[key]

    def _recompute_state(self) -> None:
        profiles = self._state.place_profiles
        self._state.best_recovery_place = self.recommend_for_recovery()
        self._state.best_joy_place = self.recommend_for_joy()
        self._state.signals = []
        self._state.hint = ""

        # Generate insight hint
        if self._state.best_recovery_place:
            p = profiles[self._state.best_recovery_place]
            self._state.hint = f"Khi cần nghỉ ngơi, {p.place_name} thường giúp bạn lấy lại năng lượng tốt nhất."
            self._state.signals.append("recovery_spot_known")
        if self._state.best_joy_place and self._state.best_joy_place != self._state.best_recovery_place:
            p = profiles[self._state.best_joy_place]
            self._state.signals.append("joy_spot_known")


def _ema(current: float, signal: float) -> float:
    return round(current * _DECAY + signal * (1 - _DECAY), 4)


def _resolve_sentiment(calm: int, stress: int, joy: int) -> str:
    if stress > calm and stress > joy:
        return "negative"
    if joy > 0 or calm > 0:
        return "positive"
    return "neutral"
