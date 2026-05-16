"""
Mi Human Memory Engine — 10-dimensional persistent user profile.

Tracks: emotional rhythm, social patterns, food preferences, travel style,
vibe preferences, routing habits, pronoun context, conversation style,
recovery needs, and life rhythm.

Persists to SQLite via PersistenceStore under entity_type='mi_memory'.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EmotionalMemory:
    avg_fatigue_score: float = 0.0      # 0-1
    avg_stress_score: float = 0.0
    burnout_episodes: int = 0
    recovery_sessions: int = 0
    peak_energy_time: str = "morning"   # morning|afternoon|evening
    notes: list[str] = field(default_factory=list)


@dataclass
class SocialMemory:
    pronoun: str = "bạn"               # detected user pronoun
    mi_pronoun: str = "mình"           # how Mi refers to herself
    tone_level: int = 3                # 1-5
    dialect: str = "neutral"           # mien_tay|gen_z|older|northern|central|neutral
    crowd_tolerance: str = "medium"    # low|medium|high
    social_energy_pattern: str = "medium"
    prefers_small_groups: bool = False


@dataclass
class FoodMemory:
    favorite_types: list[str] = field(default_factory=list)   # seafood, street_food, etc.
    avoided_types: list[str] = field(default_factory=list)
    price_range: str = "mid"           # budget|mid|premium
    preferred_meal_times: list[str] = field(default_factory=list)
    child_friendly_needed: bool = True  # default True (group has a child)
    local_vs_tourist: str = "local"


@dataclass
class VibeMemory:
    preferred_vibes: list[str] = field(default_factory=list)  # chill|active|romantic|local
    avoided_vibes: list[str] = field(default_factory=list)
    chill_preference: str = "cafe"     # cafe|beach|nature|indoor
    nightlife_interest: str = "low"    # none|low|medium|high
    sunset_seeker: bool = False
    noise_tolerance: str = "medium"    # low|medium|high


@dataclass
class TravelMemory:
    movement_tolerance: str = "medium"  # low|medium|high
    max_preferred_distance_km: float = 20.0
    prefers_nearby: bool = False
    preferred_transport: str = "car"
    visited_places: list[str] = field(default_factory=list)
    avoided_places: list[str] = field(default_factory=list)
    travel_rhythm: str = "relaxed"     # rushed|balanced|relaxed


@dataclass
class RecoveryMemory:
    recovery_type_preference: str = "cafe"  # cafe|hotel|beach|nature
    recovery_triggers: list[str] = field(default_factory=list)
    typical_recovery_duration_min: int = 30
    heat_sensitive: bool = False
    needs_quiet: bool = False


@dataclass
class ConversationMemory:
    message_count: int = 0
    avg_message_length: int = 50
    uses_slang: bool = False
    uses_emoji: bool = False
    communication_style: str = "casual"  # casual|formal|fragmented|verbose
    last_active: str = ""


@dataclass
class LifeRhythmMemory:
    typical_wake_time: str = "07:00"
    typical_sleep_time: str = "23:00"
    midday_rest: bool = True
    activity_peak: str = "morning"    # morning|afternoon|evening


@dataclass
class MiMemoryProfile:
    """
    Complete 10-dimensional user memory for Mi.
    Loaded and saved per (chat_id, user_id) pair.
    """
    user_id: int = 0
    chat_id: int = 0
    created_at: str = ""
    updated_at: str = ""

    emotional: EmotionalMemory = field(default_factory=EmotionalMemory)
    social: SocialMemory = field(default_factory=SocialMemory)
    food: FoodMemory = field(default_factory=FoodMemory)
    vibe: VibeMemory = field(default_factory=VibeMemory)
    travel: TravelMemory = field(default_factory=TravelMemory)
    recovery: RecoveryMemory = field(default_factory=RecoveryMemory)
    conversation: ConversationMemory = field(default_factory=ConversationMemory)
    life_rhythm: LifeRhythmMemory = field(default_factory=LifeRhythmMemory)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "MiMemoryProfile":
        try:
            data = json.loads(raw)
            profile = cls()
            profile.emotional = EmotionalMemory(**data.get("emotional", {}))
            profile.social = SocialMemory(**data.get("social", {}))
            profile.food = FoodMemory(**data.get("food", {}))
            profile.vibe = VibeMemory(**data.get("vibe", {}))
            profile.travel = TravelMemory(**data.get("travel", {}))
            profile.recovery = RecoveryMemory(**data.get("recovery", {}))
            profile.conversation = ConversationMemory(**data.get("conversation", {}))
            profile.life_rhythm = LifeRhythmMemory(**data.get("life_rhythm", {}))
            profile.user_id = data.get("user_id", 0)
            profile.chat_id = data.get("chat_id", 0)
            profile.created_at = data.get("created_at", "")
            profile.updated_at = data.get("updated_at", "")
            return profile
        except Exception as e:
            logger.warning("Failed to parse MiMemoryProfile: %s", e)
            return cls()

    def build_prompt_context(self) -> str:
        """
        Build a compact context string to inject into Mi's system prompt,
        personalizing responses based on known user patterns.
        """
        parts = []

        if self.social.pronoun != "bạn":
            parts.append(f"User pronoun: '{self.social.pronoun}' | dialect: {self.social.dialect}")

        if self.food.favorite_types:
            parts.append(f"User likes: {', '.join(self.food.favorite_types[:3])}")

        if self.vibe.preferred_vibes:
            parts.append(f"User vibe: {', '.join(self.vibe.preferred_vibes[:2])}")

        if self.travel.prefers_nearby:
            parts.append("User prefers nearby places — don't suggest distant routes")

        if self.recovery.needs_quiet:
            parts.append("User is noise-sensitive — prioritize quiet spots")

        if self.emotional.burnout_episodes > 2:
            parts.append("User has had multiple burnout signals — keep recommendations light")

        if not parts:
            return ""

        return "## User Memory Context\n" + "\n".join(f"- {p}" for p in parts)


class MiMemoryService:
    """
    Loads, updates, and saves MiMemoryProfile via PersistenceStore.
    Designed to be called once per message, updated, then saved.
    """

    def __init__(self, store: Any) -> None:  # store: PersistenceStore
        self._store = store

    def load(self, chat_id: int, user_id: int) -> MiMemoryProfile:
        """Load profile or return fresh default."""
        try:
            entities = self._store.get_recent_entities(chat_id, user_id, limit=1)
            for e in entities:
                if e.entity_type == "mi_memory":
                    return MiMemoryProfile.from_json(json.dumps(e.payload))
        except Exception as e:
            logger.warning("MiMemoryService.load error: %s", e)
        profile = MiMemoryProfile(user_id=user_id, chat_id=chat_id)
        profile.created_at = datetime.now(timezone.utc).isoformat()
        return profile

    def save(self, profile: MiMemoryProfile) -> None:
        """Persist profile to store."""
        try:
            profile.updated_at = datetime.now(timezone.utc).isoformat()
            payload = json.loads(profile.to_json())
            self._store.append_entity(
                chat_id=profile.chat_id,
                user_id=profile.user_id,
                entity_type="mi_memory",
                entity_id=f"mi_memory_{profile.user_id}",
                payload=payload,
            )
        except Exception as e:
            logger.warning("MiMemoryService.save error: %s", e)

    def update_from_message(
        self,
        profile: MiMemoryProfile,
        text: str,
        pronoun_ctx: Any,  # PronounContext
        emotion_state: Any,  # EmotionState
        dialect: str,
    ) -> MiMemoryProfile:
        """
        Update profile from a single message interaction.
        Returns updated profile (not saved yet — call save() separately).
        """
        from app.mi.emotion_engine import EmotionLevel

        # Social
        if pronoun_ctx.user_address != "bạn":
            profile.social.pronoun = pronoun_ctx.user_address
        if dialect != "neutral":
            profile.social.dialect = dialect
        profile.social.tone_level = pronoun_ctx.tone_level

        # Conversation stats
        profile.conversation.message_count += 1
        profile.conversation.avg_message_length = int(
            (profile.conversation.avg_message_length * 0.9 + len(text) * 0.1)
        )
        profile.conversation.uses_slang = profile.conversation.uses_slang or (
            dialect in ("gen_z", "mien_tay")
        )

        # Emotional tracking
        if emotion_state.fatigue in (EmotionLevel.HIGH, EmotionLevel.CRITICAL):
            profile.emotional.avg_fatigue_score = min(
                1.0, profile.emotional.avg_fatigue_score * 0.8 + 0.2
            )
        if emotion_state.recovery_needed:
            profile.emotional.recovery_sessions += 1

        # Movement
        if emotion_state.movement_resistance:
            profile.travel.prefers_nearby = True

        # Social energy
        if emotion_state.social_fatigue == EmotionLevel.HIGH:
            profile.vibe.noise_tolerance = "low"
            profile.recovery.needs_quiet = True

        return profile
