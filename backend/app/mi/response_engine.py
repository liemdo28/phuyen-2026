"""
Mi Response Engine — Human-like response shaping + Telegram inline buttons.

Follows Mi's 5-step response shape:
1. Emotional acknowledgement
2. Context understanding
3. Best low-friction suggestion
4. Why it fits
5. Action support (buttons)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from app.mi.emotion_engine import EmotionState, EmotionLevel, ResponseMode
from app.mi.pronoun_engine import PronounContext
from app.mi.slang_engine import detect_dialect

logger = logging.getLogger(__name__)


# ── Telegram button helpers ────────────────────────────────────────────────────

def make_button(text: str, url: str | None = None, callback: str | None = None) -> dict:
    if url:
        return {"text": text, "url": url}
    return {"text": text, "callback_data": callback or text}


def make_inline_keyboard(rows: list[list[dict]]) -> dict:
    return {"inline_keyboard": rows}


def location_buttons(lat: float, lon: float, place_name: str = "") -> dict:
    """Standard location action buttons."""
    maps_url = f"https://maps.google.com/?q={lat},{lon}"
    label = f"📍 {place_name}" if place_name else "📍 Mở Maps"
    return make_inline_keyboard([[
        make_button(label, url=maps_url),
    ]])


def travel_buttons(
    lat: float | None = None,
    lon: float | None = None,
    show_cafe: bool = False,
    show_sunset: bool = False,
    show_food: bool = False,
    show_route: bool = False,
) -> dict:
    """
    Context-aware action buttons for Mi's travel suggestions.
    Only shows relevant buttons based on user context.
    """
    buttons: list[dict] = []

    if lat and lon:
        maps_url = f"https://maps.google.com/?q={lat},{lon}"
        buttons.append(make_button("📍 Mở Maps", url=maps_url))

    if show_cafe:
        cafe_url = "https://maps.google.com/?q=cafe+near+me&near=Tuy+Hoa+Phu+Yen"
        buttons.append(make_button("☕ Cafe gần đây", url=cafe_url))

    if show_food:
        food_url = "https://maps.google.com/?q=quan+an+near+me&near=Tuy+Hoa+Phu+Yen"
        buttons.append(make_button("🍜 Quán ăn gần đây", url=food_url))

    if show_sunset:
        sunset_url = "https://maps.google.com/?q=Bai+Xep+Phu+Yen"
        buttons.append(make_button("🌅 Sunset gần nhất", url=sunset_url))

    if show_route:
        buttons.append(make_button("🧭 Route nhẹ", callback="route_light"))

    if not buttons:
        return None

    # Split into rows of max 2
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return make_inline_keyboard(rows)


# ── Response shape builder ─────────────────────────────────────────────────────

@dataclass
class MiResponse:
    text: str
    keyboard: dict | None = None
    place_name: str | None = None

    def has_buttons(self) -> bool:
        return self.keyboard is not None

    def keyboard_json(self) -> str | None:
        if self.keyboard:
            return json.dumps(self.keyboard, ensure_ascii=False)
        return None


def shape_response(
    raw_reply: str,
    emotion: EmotionState,
    pronoun: PronounContext,
    user_lat: float | None = None,
    user_lon: float | None = None,
    place_name: str | None = None,
    place_lat: float | None = None,
    place_lon: float | None = None,
) -> MiResponse:
    """
    Take a raw LLM reply and shape it for Mi's voice:
    - Enforce length limits based on emotion/response_mode
    - Add appropriate Telegram buttons
    - Ensure Mi's pronoun is correct
    """
    text = _enforce_length(raw_reply, emotion.response_mode)
    text = _ensure_mi_pronoun(text, pronoun)

    # Build buttons
    keyboard = None
    if emotion.response_mode not in (ResponseMode.ULTRA_SHORT,):
        show_cafe = emotion.healing_mood or emotion.social_fatigue != EmotionLevel.NONE
        show_food = emotion.hunger != EmotionLevel.NONE
        show_sunset = emotion.hype_mood or emotion.healing_mood
        show_route = emotion.movement_resistance

        if place_lat and place_lon:
            keyboard = travel_buttons(
                lat=place_lat, lon=place_lon,
                show_cafe=show_cafe,
                show_food=show_food,
                show_sunset=show_sunset,
                show_route=show_route,
            )
        elif user_lat and user_lon and show_food:
            keyboard = travel_buttons(
                lat=user_lat, lon=user_lon,
                show_food=True,
                show_cafe=show_cafe,
            )
        elif show_cafe or show_food or show_sunset:
            keyboard = travel_buttons(
                show_cafe=show_cafe,
                show_food=show_food,
                show_sunset=show_sunset,
            )

    return MiResponse(text=text, keyboard=keyboard, place_name=place_name)


def _enforce_length(text: str, mode: ResponseMode) -> str:
    """
    Truncate or trim response based on mode.
    Does not cut mid-sentence.
    """
    if mode == ResponseMode.ULTRA_SHORT:
        # Max 1 sentence
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if sentences:
            return sentences[0] + "."
        return text[:100]

    if mode == ResponseMode.SIMPLIFIED:
        # Max 3 sentences
        sentences = []
        for s in text.replace("!", ".|").replace("?", "?|").split("|"):
            s = s.strip()
            if s:
                sentences.append(s)
            if len(sentences) >= 3:
                break
        return " ".join(sentences) if sentences else text

    return text  # BALANCED / EXPANDED: return as-is


def _ensure_mi_pronoun(text: str, pronoun: PronounContext) -> str:
    """
    Basic check: replace "tôi " with "mình " in Mi's response text.
    The LLM should do this, but this is a safety net.
    """
    return text.replace("tôi ", "mình ").replace("Tôi ", "Mình ")


# ── Miền Tây response warmer ───────────────────────────────────────────────────

def warm_mien_tay(text: str) -> str:
    """
    Add miền Tây warmth to a response if user is Southern.
    Adds 'nhen' or 'nha' ending where natural.
    """
    text = text.rstrip(".")
    if not text.endswith(("nhen", "nha", "nhé", "😊", "😄", "nè")):
        if len(text) < 150:  # Only short responses
            text += " nhen 😊"
    return text


def get_dialect_warmth(dialect: str, text: str) -> str:
    """Apply dialect-specific warmth to Mi's response."""
    if dialect == "mien_tay":
        return warm_mien_tay(text)
    return text
