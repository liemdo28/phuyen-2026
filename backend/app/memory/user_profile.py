"""
UserMemoryProfile — persistent cross-session companion memory.

Tracks emotional rhythm, food preferences, movement tolerance,
social energy, and recovery patterns so the AI feels like it
truly knows the user across the entire trip.

Design principle: every signal the user emits updates this profile.
The profile is serialized into context.preferences so it persists
through MemoryService.update_preferences().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ── Snapshot keys stored in context.preferences ──────────────────────────────
_KEY_FOOD_LIKED       = "mem_food_liked"        # list[str]
_KEY_FOOD_TRIED       = "mem_food_tried"         # list[str]
_KEY_PLACES_VISITED   = "mem_places_visited"     # list[str]
_KEY_MOV_HISTORY      = "mem_movement_history"   # list[float] (recent tolerance scores)
_KEY_FATIGUE_PATTERN  = "mem_fatigue_pattern"    # list[int] (hours where fatigue peaked)
_KEY_CROWD_TOL        = "mem_crowd_tolerance"    # "low"|"medium"|"high"
_KEY_SOCIAL_MODE      = "mem_social_mode"        # "solo"|"couple"|"family"|"group"
_KEY_CHILL_PREF       = "mem_chill_preference"   # "cafe"|"beach"|"indoor"|"nightlife"
_KEY_RECOVERY_COUNT   = "mem_recovery_today"     # int
_KEY_LAST_EMOTION     = "mem_last_emotion"       # str
_KEY_CONVO_RHYTHM     = "mem_convo_rhythm"       # "chatty"|"terse"|"fragmented"


@dataclass
class UserMemoryProfile:
    """
    Snapshot of everything the AI knows about the user's preferences,
    habits, and emotional state accumulated over the trip.
    """
    # Food
    food_liked:     list[str] = field(default_factory=list)   # user expressed positive sentiment
    food_tried:     list[str] = field(default_factory=list)   # confirmed eaten

    # Places
    places_visited: list[str] = field(default_factory=list)

    # Movement
    movement_history:    list[float] = field(default_factory=list)  # recent tolerance 0-1
    movement_tolerance:  str = "medium"   # "high"|"medium"|"low"|"resistance"

    # Fatigue
    fatigue_peak_hours: list[int] = field(default_factory=list)  # hours (24h) where fatigue peaked
    current_fatigue:    float = 0.0

    # Social
    social_mode:    str = "family"    # "solo"|"couple"|"family"|"group"
    crowd_tolerance: str = "medium"  # "low"|"medium"|"high"

    # Chill / Recovery
    chill_preference:    str | None = None   # last resolved chill type
    recovery_count_today: int = 0

    # Conversation
    last_emotion:   str = "neutral"
    convo_rhythm:   str = "chatty"   # "chatty"|"terse"|"fragmented"

    # Meta
    profile_updated_at: datetime = field(default_factory=datetime.now)

    # ── Computed properties ────────────────────────────────────────────────

    @property
    def avg_movement_tolerance(self) -> float:
        if not self.movement_history:
            return 0.5
        return sum(self.movement_history[-5:]) / len(self.movement_history[-5:])

    @property
    def is_resistance_mode(self) -> bool:
        """True when user consistently resists movement this session."""
        return self.avg_movement_tolerance < 0.3

    @property
    def needs_recovery(self) -> bool:
        return self.current_fatigue >= 0.6 or self.recovery_count_today == 0

    @property
    def knows_food_preferences(self) -> bool:
        return len(self.food_liked) > 0

    def top_food_preference(self) -> str | None:
        return self.food_liked[0] if self.food_liked else None

    def has_visited(self, place: str) -> bool:
        place_lower = place.lower()
        return any(place_lower in v.lower() for v in self.places_visited)

    def format_for_prompt(self) -> str:
        """
        Compact string for injection into LLM system prompt.
        Only includes non-default, non-trivial knowledge.
        """
        parts: list[str] = []

        if self.food_liked:
            parts.append(f"Thích ăn: {', '.join(self.food_liked[:3])}")
        if self.food_tried:
            parts.append(f"Đã thử: {', '.join(self.food_tried[:4])}")
        if self.places_visited:
            parts.append(f"Đã ghé: {', '.join(self.places_visited[-4:])}")
        if self.is_resistance_mode:
            parts.append("Đang ngại di chuyển xa — ưu tiên gần.")
        elif self.movement_tolerance == "low":
            parts.append("Năng lượng di chuyển thấp hôm nay.")
        if self.crowd_tolerance == "low":
            parts.append("Không thích chỗ đông — ưu tiên yên tĩnh.")
        if self.chill_preference:
            parts.append(f"Kiểu chill ưa thích: {self.chill_preference}.")
        if self.current_fatigue >= 0.7:
            parts.append("Đang mệt — giảm tải, ưu tiên comfort.")
        if self.recovery_count_today == 0 and self.current_fatigue >= 0.4:
            parts.append("Chưa có recovery moment hôm nay.")
        if self.last_emotion not in {"neutral", ""}:
            parts.append(f"Cảm xúc hiện tại: {self.last_emotion}.")

        if not parts:
            return ""
        return "## User Memory\n" + "\n".join(f"- {p}" for p in parts)


# ── Load / Save from context.preferences ─────────────────────────────────────

def load_profile(preferences: dict[str, Any]) -> UserMemoryProfile:
    """Reconstruct UserMemoryProfile from persisted context.preferences."""
    return UserMemoryProfile(
        food_liked       = list(preferences.get(_KEY_FOOD_LIKED, [])),
        food_tried       = list(preferences.get(_KEY_FOOD_TRIED, [])),
        places_visited   = list(preferences.get(_KEY_PLACES_VISITED, [])),
        movement_history = list(preferences.get(_KEY_MOV_HISTORY, [])),
        fatigue_peak_hours = list(preferences.get(_KEY_FATIGUE_PATTERN, [])),
        crowd_tolerance  = str(preferences.get(_KEY_CROWD_TOL, "medium")),
        social_mode      = str(preferences.get(_KEY_SOCIAL_MODE, "family")),
        chill_preference = preferences.get(_KEY_CHILL_PREF) or None,
        recovery_count_today = int(preferences.get(_KEY_RECOVERY_COUNT, 0)),
        last_emotion     = str(preferences.get(_KEY_LAST_EMOTION, "neutral")),
        convo_rhythm     = str(preferences.get(_KEY_CONVO_RHYTHM, "chatty")),
    )


def build_profile_updates(
    profile: UserMemoryProfile,
    analysis,   # VietnameseMessageAnalysis
    now: datetime,
) -> dict[str, Any]:
    """
    Derive preference updates from new message analysis.
    Called after analyze_message() — updates the profile in context.preferences.
    """
    updates: dict[str, Any] = {}

    # Movement tolerance history
    if analysis.movement_tolerance in ("low", "resistance"):
        new_tol = 0.2
    elif analysis.movement_tolerance == "medium":
        new_tol = 0.5
    else:
        new_tol = 0.8
    history = list(profile.movement_history) + [new_tol]
    updates[_KEY_MOV_HISTORY] = history[-10:]

    # Derived movement_tolerance label
    avg = sum(history[-5:]) / len(history[-5:])
    if avg < 0.3:
        movement_label = "resistance"
    elif avg < 0.5:
        movement_label = "low"
    elif avg < 0.7:
        movement_label = "medium"
    else:
        movement_label = "high"

    # Fatigue peak hours
    if analysis.fatigue >= 0.6:
        peak_hours = list(profile.fatigue_peak_hours) + [now.hour]
        updates[_KEY_FATIGUE_PATTERN] = peak_hours[-10:]

    # Crowd tolerance
    if analysis.crowd_tolerance == "low":
        updates[_KEY_CROWD_TOL] = "low"
    elif analysis.crowd_tolerance == "high" and profile.crowd_tolerance != "low":
        updates[_KEY_CROWD_TOL] = "high"

    # Social mode
    if analysis.group_type and analysis.group_type != "unknown":
        updates[_KEY_SOCIAL_MODE] = analysis.group_type

    # Food liked: excitement >= 0.4 + food mentioned → user probably enjoyed it
    if analysis.excitement >= 0.4 and analysis.food_types:
        liked = list(profile.food_liked)
        for ft in analysis.food_types:
            if ft not in liked:
                liked.insert(0, ft)
        updates[_KEY_FOOD_LIKED] = liked[:8]

    # Last emotion
    updates[_KEY_LAST_EMOTION] = analysis.dominant_emotion or "neutral"

    # Conversation rhythm
    text_len = len(analysis.raw_text) if hasattr(analysis, "raw_text") else 0
    if text_len < 15:
        updates[_KEY_CONVO_RHYTHM] = "terse"
    elif text_len > 80:
        updates[_KEY_CONVO_RHYTHM] = "chatty"
    else:
        updates[_KEY_CONVO_RHYTHM] = profile.convo_rhythm  # preserve

    return updates


def record_place_visited(profile: UserMemoryProfile, place_name: str) -> dict[str, Any]:
    visited = list(profile.places_visited)
    if place_name not in visited:
        visited.append(place_name)
    return {_KEY_PLACES_VISITED: visited[-20:]}


def record_food_tried(profile: UserMemoryProfile, food_name: str) -> dict[str, Any]:
    tried = list(profile.food_tried)
    if food_name not in tried:
        tried.append(food_name)
    return {_KEY_FOOD_TRIED: tried[-20:]}


def record_recovery_moment(profile: UserMemoryProfile) -> dict[str, Any]:
    return {_KEY_RECOVERY_COUNT: profile.recovery_count_today + 1}
