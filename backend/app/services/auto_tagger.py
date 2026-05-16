"""Auto-Tagger — LLM-powered entity enrichment for the Travel Intelligence Graph.

Provides:
- AutoTagger: LLM inference to assign vibe_tags, energy_fit, weather_fit,
  emotional_vibe, traveler_types from raw entity name/note/address fields.
- TagAugmenter: end-to-end pipeline that refreshes EntityIndex and enriches
  entities with auto-generated tags.
- LLM client wrappers (OpenAI, Anthropic) with retry, rate limiting.
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from app.schemas.travel_entity import (
    TravelEntity,
    VIBE_TAGS, TRAVELER_TYPES, ENERGY_FIT_TAGS,
    WEATHER_FIT_TAGS, EMOTIONAL_VIBE,
)

logger = logging.getLogger(__name__)

# ── Tag Vocabularies ──────────────────────────────────────────────────────────

_VIBE_TAGS_LIST = sorted(VIBE_TAGS)
_TRAVELER_TYPES_LIST = sorted(TRAVELER_TYPES)
_ENERGY_FIT_LIST = sorted(ENERGY_FIT_TAGS)
_WEATHER_FIT_LIST = sorted(WEATHER_FIT_TAGS)
_EMOTIONAL_VIBE_LIST = sorted(EMOTIONAL_VIBE)

# ── Phú Yên Context Examples for Few-Shot Prompting ───────────────────────────

_EXAMPLES = """
## Ví dụ (Phú Yên context):

Entity: "Gành Đá Đĩa", note: "Địa điểm check-in nổi tiếng với cảnh hoàng hôn tuyệt đẹp"
→ vibe_tags: ["instagrammable", "ocean_vibe", "sunset", "touristy"]
→ traveler_types: ["photographer", "couple", "family"]
→ energy_fit: ["walking_heavy"]
→ weather_fit: ["sunset_best", "hot_weather"]
→ emotional_vibe: ["romantic", "adventurous"]

Entity: "Quán Bún Cá Ngừ Bà Hai", note: "Quán nổi tiếng địa phương, bún cá ngừ đặc sản"
→ vibe_tags: ["local", "authentic", "quiet"]
→ traveler_types: ["foodie", "backpacker", "local_explorer"]
→ energy_fit: ["low_energy"]
→ weather_fit: ["hot_weather"]
→ emotional_vibe: ["nostalgic", "cozy"]

Entity: "Mũi Điện", note: "Điểm cực Đông của Việt Nam, view biển hoang sơ"
→ vibe_tags: ["hidden", "ocean_vibe", "adventurous", "authentic"]
→ traveler_types: ["photographer", "backpacker", "adventurous"]
→ energy_fit: ["walking_heavy", "high_energy"]
→ weather_fit: ["windy_weather", "hot_weather"]
→ emotional_vibe: ["adventurous", "healing"]
"""


# ── LLM Client Interface ───────────────────────────────────────────────────────

class LLMError(Exception):
    """Raised when LLM inference fails after all retries."""
    pass


class LLMClient:
    """Generic LLM client wrapper."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._provider = "openai"  # default

    def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError

    def _retry(self, fn) -> str:
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                wait = 2 ** attempt
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s. Retrying in %ds...",
                    attempt + 1, self.max_retries, exc, wait,
                )
                time.sleep(wait)
        raise LLMError(f"LLM call failed after {self.max_retries} retries") from last_err


class OpenAIClient(LLMClient):
    """OpenAI API client with httpx."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs) -> None:
        super().__init__(api_key, model, **kwargs)
        self._provider = "openai"

    def chat(self, messages: list[dict]) -> str:
        import httpx

        def _call() -> str:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()

        return self._retry(_call)


class AnthropicClient(LLMClient):
    """Anthropic API client (Claude)."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", **kwargs) -> None:
        super().__init__(api_key, model, **kwargs)
        self._provider = "anthropic"

    def chat(self, messages: list[dict]) -> str:
        import httpx

        # Convert messages to Anthropic format
        system_msg = ""
        anthropic_msgs = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "assistant"
            content = m.get("content", "")
            if m.get("role") == "system":
                system_msg = content
            else:
                anthropic_msgs.append({"role": role, "content": content})

        def _call() -> str:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "messages": anthropic_msgs,
                    "temperature": 0.3,
                    "max_tokens": 2048,
                }
                if system_msg:
                    payload["system"] = system_msg
                resp = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                # Claude returns content blocks
                content = data.get("content", [])
                if isinstance(content, list) and content:
                    return content[0].get("text", "")
                return str(content)

        return self._retry(_call)


def build_llm_client(provider: str = "openai", **kwargs) -> LLMClient:
    """Factory: build an LLM client by provider name."""
    provider = provider.lower()
    if provider == "openai":
        key = kwargs.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        return OpenAIClient(key, model=kwargs.get("model", "gpt-4o-mini"),
                           timeout=kwargs.get("timeout", 30),
                           max_retries=kwargs.get("max_retries", 3))
    if provider in ("anthropic", "claude"):
        key = kwargs.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
        return AnthropicClient(key, model=kwargs.get("model", "claude-sonnet-4-20250514"),
                               timeout=kwargs.get("timeout", 30),
                               max_retries=kwargs.get("max_retries", 3))
    raise ValueError(f"Unknown LLM provider: {provider!r}")


# ── AutoTagger ────────────────────────────────────────────────────────────────

@dataclass
class EntityTags:
    """Tag assignments for a single entity."""
    vibe_tags: list[str] = field(default_factory=list)
    traveler_types: list[str] = field(default_factory=list)
    energy_fit: list[str] = field(default_factory=list)
    weather_fit: list[str] = field(default_factory=list)
    emotional_vibe: list[str] = field(default_factory=list)
    trip_fits: list[str] = field(default_factory=list)


class AutoTagger:
    """LLM-powered tag inference for TravelEntity objects."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        rate_limit_ms: int = 100,
    ) -> None:
        if llm_client is not None:
            self._client = llm_client
        else:
            try:
                self._client = build_llm_client(provider, model=model)
            except Exception as exc:
                logger.warning("Could not build LLM client: %s. Using mock.", exc)
                self._client = None
        self._rate_limit_ms = rate_limit_ms
        self._last_call = 0.0

    def _rate_limit(self) -> None:
        """Enforce rate limiting between calls."""
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._rate_limit_ms / 1000:
            time.sleep(self._rate_limit_ms / 1000 - elapsed)
        self._last_call = time.monotonic()

    def _build_prompt(self, entities: list[TravelEntity]) -> list[dict]:
        """Build a structured prompt for batch tag inference."""
        system_prompt = f"""Bạn là chuyên gia du lịch Phú Yên, Việt Nam. Nhiệm vụ: gán tag cho các địa điểm du lịch.

## Tag vocabulary:
- vibe_tags ({len(_VIBE_TAGS_LIST)} values): {', '.join(_VIBE_TAGS_LIST)}
- traveler_types ({len(_TRAVELER_TYPES_LIST)} values): {', '.join(_TRAVELER_TYPES_LIST)}
- energy_fit ({len(_ENERGY_FIT_LIST)} values): {', '.join(_ENERGY_FIT_LIST)}
- weather_fit ({len(_WEATHER_FIT_LIST)} values): {', '.join(_WEATHER_FIT_LIST)}
- emotional_vibe ({len(_EMOTIONAL_VIBE_LIST)} values): {', '.join(_EMOTIONAL_VIBE_LIST)}

## Rules:
1. Chỉ dùng các tag từ vocabulary trên (không tự thêm tag mới).
2. Nếu không có thông tin, để mảng rỗng [] (không bịa tag).
3. Trả lời CHỈ bằng JSON, không có giải thích.
4. Dùng tiếng Việt cho emotional_vibe.
{_EXAMPLES}

## Entities to tag ({len(entities)} total):"""

        entity_lines = []
        for i, e in enumerate(entities):
            entity_lines.append(
                f'{i + 1}. Tên: "{e.name}"\n'
                f'   Địa chỉ: {e.address or "(không có)"}\n'
                f'   Ghi chú: {e.note or "(không có)"}\n'
                f'   Loại: {e.category or "(không có)"}\n'
                f'   Giá TB: {e.avg_price_vnd:,} VND' if e.avg_price_vnd else ''
            )

        user_content = system_prompt + "\n\n" + "\n\n".join(entity_lines) + "\n\nTrả lời JSON format: {entity_name: {vibe_tags, traveler_types, energy_fit, weather_fit, emotional_vibe}}"

        return [
            {"role": "system", "content": "You are a helpful travel expert for Phú Yên, Vietnam. Return ONLY valid JSON, no extra text."},
            {"role": "user", "content": user_content},
        ]

    def _parse_response(self, response: str, entities: list[TravelEntity]) -> dict[str, EntityTags]:
        """Parse LLM JSON response into EntityTags dict keyed by entity name."""
        result: dict[str, EntityTags] = {}
        # Try to extract JSON block
        try:
            # Strip markdown code fences
            text = response.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            data = json.loads(text)
            for name, tags in data.items():
                result[name.strip()] = EntityTags(
                    vibe_tags=[v for v in tags.get("vibe_tags", []) if v in VIBE_TAGS],
                    traveler_types=[t for t in tags.get("traveler_types", []) if t in TRAVELER_TYPES],
                    energy_fit=[e for e in tags.get("energy_fit", []) if e in ENERGY_FIT_TAGS],
                    weather_fit=[w for w in tags.get("weather_fit", []) if w in WEATHER_FIT_TAGS],
                    emotional_vibe=[v for v in tags.get("emotional_vibe", []) if v in EMOTIONAL_VIBE],
                )
        except json.JSONDecodeError:
            # Try line-by-line fallback
            logger.warning("Could not parse LLM response as JSON. Trying fallback.")
            for e in entities:
                result[e.name] = EntityTags()

        # Fill missing entries with empty tags
        for e in entities:
            if e.name not in result:
                result[e.name] = EntityTags()

        return result

    def tag_entity(self, entity: TravelEntity) -> TravelEntity:
        """Tag a single entity using LLM inference."""
        if entity.vibe_tags and entity.traveler_types:
            # Already tagged — skip
            return entity

        if self._client is None:
            # No LLM client — use keyword-based fallback
            return self._tag_keyword_fallback(entity)

        self._rate_limit()
        try:
            messages = self._build_prompt([entity])
            response = self._client.chat(messages)
            parsed = self._parse_response(response, [entity])
            tags = parsed.get(entity.name, EntityTags())
            return self._apply_tags(entity, tags)
        except Exception as exc:
            logger.error("Failed to tag entity %r: %s", entity.name, exc)
            return self._tag_keyword_fallback(entity)

    def tag_batch(self, entities: list[TravelEntity], batch_size: int = 10) -> list[TravelEntity]:
        """Process entities in batches, applying LLM-generated tags."""
        if self._client is None:
            return [self._tag_keyword_fallback(e) for e in entities]

        needs_tagging = [e for e in entities if not e.vibe_tags]
        already_tagged = [e for e in entities if e.vibe_tags]
        result: list[TravelEntity] = already_tagged[:]

        for i in range(0, len(needs_tagging), batch_size):
            batch = needs_tagging[i:i + batch_size]
            self._rate_limit()
            try:
                messages = self._build_prompt(batch)
                response = self._client.chat(messages)
                parsed = self._parse_response(response, batch)
                for entity in batch:
                    tags = parsed.get(entity.name, EntityTags())
                    result.append(self._apply_tags(entity, tags))
            except Exception as exc:
                logger.error("Batch tagging failed at offset %d: %s", i, exc)
                for entity in batch:
                    result.append(self._tag_keyword_fallback(entity))

        return result

    def _apply_tags(self, entity: TravelEntity, tags: EntityTags) -> TravelEntity:
        """Apply inferred tags to an entity, preserving existing non-empty tags."""
        # Only fill in empty fields — manual tags always win
        import dataclasses
        patch: dict = {}
        if not entity.vibe_tags and tags.vibe_tags:
            patch["vibe_tags"] = tags.vibe_tags
        if not entity.traveler_types and tags.traveler_types:
            patch["traveler_types"] = tags.traveler_types
        if not entity.energy_fit and tags.energy_fit:
            patch["energy_fit"] = tags.energy_fit
        if not entity.weather_fit and tags.weather_fit:
            patch["weather_fit"] = tags.weather_fit
        if not entity.emotional_vibe and tags.emotional_vibe:
            patch["emotional_vibe"] = tags.emotional_vibe

        if patch:
            entity = dataclasses.replace(entity, **patch)

        # Always run trip_fits suggestion (additive)
        entity = dataclasses.replace(
            entity,
            trip_fits=entity.trip_fits or self.suggest_trip_fits(entity),
        )

        return entity

    def _tag_keyword_fallback(self, entity: TravelEntity) -> TravelEntity:
        """Keyword-based tag inference without LLM."""
        import dataclasses
        name = (entity.name + " " + entity.note).lower()
        tags = EntityTags()

        # Vibe from keywords
        vibe_map = {
            "chill": ["yên tĩnh", "nhẹ nhàng", "thư giãn", "chill"],
            "local": ["địa phương", "bản địa", "người dân", "local"],
            "hidden": ["bí mật", "ẩn", "ít người", "hoang sơ"],
            "ocean_vibe": ["biển", "bãi", "sea", "ocean"],
            "sunset": ["hoàng hôn", "sunset", "dusk"],
            "romantic": ["lãng mạn", "romantic", "tình nhân"],
            "authentic": ["đặc sản", "authentic", "truyền thống"],
            "touristy": ["nổi tiếng", "tourist", "khách du lịch"],
            "instagrammable": ["sống ảo", "check-in", "insta", "đẹp"],
        }
        for vibe, keywords in vibe_map.items():
            if any(kw in name for kw in keywords):
                tags.vibe_tags.append(vibe)

        # Traveler types
        if "food" in entity.category or any(f in name for f in ["ăn", "quán", "hải sản", "bún", "phở"]):
            tags.traveler_types.append("foodie")
        if any(kw in name for kw in ["chụp ảnh", "sống ảo", "insta", "camera"]):
            tags.traveler_types.append("photographer")
        if any(kw in name for kw in ["gia đình", "trẻ em", "cả nhà"]):
            tags.traveler_types.append("family")
        if any(kw in name for kw in ["cặp đôi", "vợ chồng", "yêu"]):
            tags.traveler_types.append("couple")
        if any(kw in name for kw in ["backpacker", "bụi", "ba lô"]):
            tags.traveler_types.append("backpacker")

        # Energy fit
        if any(kw in name for kw in ["ngồi", "nhẹ", "café", "cà phê"]):
            tags.energy_fit.append("low_energy")
        if any(kw in name for kw in ["đi bộ", "leo", "trekking", "khám phá"]):
            tags.energy_fit.append("walking_heavy")
        if any(kw in name for kw in ["hồi phục", "nghỉ", "recovery"]):
            tags.energy_fit.append("recovery_friendly")

        # Weather fit
        if any(kw in name for kw in ["nắng", "nóng", "summer"]):
            tags.weather_fit.append("hot_weather")
        if any(kw in name for kw in ["mưa", "rain", "indoor"]):
            tags.weather_fit.append("rainy_weather")
        if any(kw in name for kw in ["hoàng hôn", "sunset", "chiều"]):
            tags.weather_fit.append("sunset_best")

        # Emotional vibe
        if any(kw in name for kw in ["bình yên", "yên", "thư giãn"]):
            tags.emotional_vibe.append("peaceful")
        if any(kw in name for kw in ["lãng mạn", "tình yêu"]):
            tags.emotional_vibe.append("romantic")
        if any(kw in name for kw in ["hoang sơ", "mạo hiểm", "phiêu lưu"]):
            tags.emotional_vibe.append("adventurous")
        if any(kw in name for kw in ["hồi phục", "chữa lành"]):
            tags.emotional_vibe.append("healing")

        return self._apply_tags(entity, tags)

    @staticmethod
    def suggest_trip_fits(entity: TravelEntity) -> list[str]:
        """Keyword-based trip_fits suggestion for an entity."""
        text = (entity.name + " " + entity.note).lower()
        fits: list[str] = []

        if any(kw in text for kw in ["sáng", "bún", "phở", "bánh", "breakfast"]):
            fits.append("breakfast_stop")
        if any(kw in text for kw in ["trưa", "cơm", "lunch"]):
            fits.append("lunch_stop")
        if any(kw in text for kw in ["tối", "dinner", "ăn tối"]):
            fits.append("dinner_stop")
        if any(kw in text for kw in ["cà phê", "cafe", "café", "coffee"]):
            fits.append("cafe_break")
        if any(kw in text for kw in ["hoàng hôn", "sunset", "dusk"]):
            fits.append("sunset_stop")
        if any(kw in text for kw in ["mưa", "indoor", "máy lạnh", "điều hòa"]):
            fits.append("rain_safe")
        if any(kw in text for kw in ["ngồi", "nhẹ", "recovery", "hồi phục"]):
            fits.append("recovery_stop")
        if any(kw in text for kw in ["đêm", "night", "quán nhậu", "bar"]):
            fits.append("night_activity")
        if any(kw in text for kw in ["nhanh", "gần", "quick"]):
            fits.append("quick_stop")
        if any(kw in text for kw in ["ở", "resort", "nghỉ"]):
            fits.append("long_stay")

        return fits


# ── Tag Augmenter ─────────────────────────────────────────────────────────────

class TagAugmenter:
    """End-to-end pipeline: refresh EntityIndex + auto-tag entities."""

    def __init__(self, auto_tagger: Optional[AutoTagger] = None) -> None:
        self._tagger = auto_tagger or AutoTagger()

    async def augment_index(
        self,
        force: bool = False,
        batch_size: int = 10,
    ) -> dict:
        """Refresh EntityIndex from sheets and enrich with auto-tags."""
        try:
            from app.services.entity_index import get_entity_index
        except ImportError:
            logger.error("Could not import entity_index module")
            return {"error": "entity_index not available"}

        index = get_entity_index()
        count = await index.refresh(force=force)
        entities = index.get_all()

        augmented = 0
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            untagged = [e for e in batch if not e.vibe_tags]
            if untagged:
                tagged = self._tagger.tag_batch(untagged, batch_size=batch_size)
                # Update entities in index
                for tagged_e in tagged:
                    for j, e in enumerate(entities):
                        if e.id == tagged_e.id:
                            entities[j] = tagged_e
                            augmented += 1
                            break

        # Save updated index
        index._entities = entities
        index._rebuild_lookups()
        index._save_to_disk()

        return {
            "total_entities": count,
            "augmented": augmented,
            "already_tagged": count - augmented,
        }

    @staticmethod
    def reconcile_tags(
        sheet_tags: dict,
        llm_tags: dict,
    ) -> dict:
        """Merge manual (sheet) tags with LLM tags. Sheet always wins."""
        result: dict = {}
        for key in ("vibe_tags", "traveler_types", "energy_fit", "weather_fit", "emotional_vibe"):
            # Manual tags take precedence
            if sheet_tags.get(key):
                result[key] = sheet_tags[key]
            else:
                result[key] = llm_tags.get(key, [])
        return result


# ── Utilities ─────────────────────────────────────────────────────────────────

def infer_price_level(avg_price_vnd: int) -> str:
    """Infer price_level from average price in VND."""
    if avg_price_vnd <= 0:
        return ""
    if avg_price_vnd <= 50000:
        return "budget"
    if avg_price_vnd <= 150000:
        return "mid"
    if avg_price_vnd <= 500000:
        return "upscale"
    return "luxury"


def summarize_tags(entity: TravelEntity) -> str:
    """Return a human-readable emoji summary of entity tags."""
    parts: list[str] = []

    # Category icon
    cat_icons = {
        "restaurant": "🍜", "cafe": "☕", "beach": "🏖️",
        "hotel": "🏨", "attraction": "📍", "nightlife": "🌙",
        "shopping": "🛍️", "local_market": "🏪",
    }
    if entity.category in cat_icons:
        parts.append(cat_icons[entity.category])

    # Vibe tags
    vibe_icons = {
        "chill": "😌", "sunset": "🌅", "ocean_vibe": "🌊",
        "local": "🏘️", "hidden": "🤫", "romantic": "💑",
        "instagrammable": "📸", "family": "👨‍👩‍👧‍👦", "foodie": "😋",
        "photographer": "📷", "authentic": "✨", "quiet": "🤫",
        "touristy": "🗺️", "energetic": "⚡", "calm": "🧘",
    }
    for v in entity.vibe_tags[:3]:
        parts.append(vibe_icons.get(v, ""))

    return " • ".join(parts) if parts else ""