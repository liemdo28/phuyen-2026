"""
Vietnamese Message Intelligence Analyzer

Main NLP pipeline:
  raw_message
      ↓ normalization
      ↓ accent reconstruction
      ↓ slang resolution
      ↓ typo / no-accent correction
      ↓ regional resolution
      ↓ emotion extraction
      ↓ social context inference
      ↓ intent extraction
      ↓ travel context merge
      ↓ behavior graph lookup
      ↓ → VietnameseMessageAnalysis

This is injected into the NLU pipeline and enriches AssistantIntent
with deep cultural, emotional, and behavioral context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.intelligence.patterns.emotions import (
    score_confusion,
    score_excitement,
    score_fatigue,
    score_hunger,
    score_recovery_need,
    score_stress,
    detect_sarcasm,
    detect_social_context,
)
from app.intelligence.patterns.food import (
    detect_food_type,
    detect_meal_time,
    detect_price_preference,
    is_drinking_context,
)
from app.intelligence.patterns.regional import detect_dialect
from app.intelligence.patterns.slang import (
    ABBREVIATIONS,
    INTERNET_SLANG,
    NO_ACCENT_MAP,
    WANT_MARKERS,
)
from app.intelligence.patterns.social import (
    detect_group_type,
    is_romantic_context,
    needs_child_friendly,
    prefers_local,
    score_crowd_tolerance,
    score_movement_tolerance,
    score_social_energy,
)
from app.intelligence.patterns.travel import (
    detect_time_preference,
    detect_travel_intent,
    get_max_distance_km,
)
from app.intelligence.patterns.weather import (
    get_weather_action,
    score_good_weather,
    score_heat,
    score_rain,
    score_sea_danger,
    score_wind,
)

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


@dataclass
class VietnameseMessageAnalysis:
    """
    Structured output of Vietnamese intelligence pipeline.
    Rich cultural, emotional, and behavioral context for each message.
    """
    # ── Text Processing ────────────────────────────────────────────────────────
    original: str = ""
    normalized: str = ""
    dialect: str = "unknown"              # central | southern | northern | gen_z

    # ── Emotional State ────────────────────────────────────────────────────────
    fatigue: float = 0.0                  # 0.0–1.0
    stress: float = 0.0                   # 0.0–1.0
    hunger: float = 0.0                   # 0.0–1.0
    excitement: float = 0.0              # 0.0–1.0
    confusion: float = 0.0               # 0.0–1.0
    recovery_need: float = 0.0           # 0.0–1.0
    dominant_emotion: str = "neutral"    # neutral | hungry | tired | excited | stressed | confused

    # ── Sarcasm ───────────────────────────────────────────────────────────────
    sarcasm_detected: bool = False
    sarcasm_confidence: float = 0.0

    # ── Social Context ─────────────────────────────────────────────────────────
    group_type: str = "unknown"          # solo | couple | family | group | unknown
    social_energy: str = "medium"        # low | medium | high
    movement_tolerance: str = "medium"   # low | medium | high
    crowd_tolerance: str = "medium"      # low | medium | high
    max_distance_km: int = 20            # recommended max distance given energy
    is_romantic: bool = False
    prefers_local_food: bool = False
    needs_child_friendly: bool = False

    # ── Intent Classification ──────────────────────────────────────────────────
    has_want_intent: bool = False        # explicit "I want" marker present
    travel_intents: list[str] = field(default_factory=list)  # beach | attraction | food_tour...
    food_types: list[str] = field(default_factory=list)       # seafood | cafe | street_food...
    meal_time: str = "any"               # breakfast | lunch | dinner | late_night | any
    price_preference: str = "any"        # budget | midrange | upscale | any
    is_drinking: bool = False            # alcohol/nightlife drinking
    social_context_type: str = ""        # social_drinking | nightlife | social_decompression

    # ── Weather Intelligence ───────────────────────────────────────────────────
    heat_level: float = 0.0
    rain_level: float = 0.0
    wind_level: float = 0.0
    sea_danger: float = 0.0
    good_weather: float = 0.0
    weather_action: str = "proceed_normal"  # redirect_indoor | avoid_beach | warn_heat_midday

    # ── Time Awareness ────────────────────────────────────────────────────────
    time_preference: str = "any"         # morning | golden_hour | midday_avoid | night | any
    current_hour: int = 12               # local VN hour when analyzed

    # ── Enriched Context for OpenAI Prompt ────────────────────────────────────
    context_tags: list[str] = field(default_factory=list)  # summary tags for prompt injection
    routing_hints: list[str] = field(default_factory=list) # routing suggestions


def analyze_message(text: str) -> VietnameseMessageAnalysis:
    """
    Full Vietnamese intelligence pipeline.
    Returns VietnameseMessageAnalysis with all context signals.
    """
    analysis = VietnameseMessageAnalysis(original=text)

    # ── Step 1: Normalize ─────────────────────────────────────────────────────
    normalized = _normalize(text)
    analysis.normalized = normalized

    # ── Step 2: Detect dialect / regional ─────────────────────────────────────
    analysis.dialect = detect_dialect(normalized)

    # ── Step 3: Emotion extraction ────────────────────────────────────────────
    analysis.fatigue = score_fatigue(normalized)
    analysis.stress = score_stress(normalized)
    analysis.hunger = score_hunger(normalized)
    analysis.excitement = score_excitement(normalized)
    analysis.confusion = score_confusion(normalized)
    analysis.recovery_need = score_recovery_need(normalized)
    analysis.dominant_emotion = _dominant_emotion(analysis)

    # ── Step 4: Sarcasm detection ─────────────────────────────────────────────
    analysis.sarcasm_detected, analysis.sarcasm_confidence = detect_sarcasm(normalized)

    # ── Step 5: Social context ────────────────────────────────────────────────
    analysis.group_type = detect_group_type(normalized)
    analysis.social_energy = score_social_energy(normalized)
    analysis.movement_tolerance = score_movement_tolerance(normalized)
    analysis.crowd_tolerance = score_crowd_tolerance(normalized)
    analysis.is_romantic = is_romantic_context(normalized)
    analysis.prefers_local_food = prefers_local(normalized)
    analysis.needs_child_friendly = needs_child_friendly(normalized)

    # ── Step 6: Intent extraction ─────────────────────────────────────────────
    analysis.has_want_intent = any(marker in normalized for marker in WANT_MARKERS)
    analysis.travel_intents = detect_travel_intent(normalized)
    analysis.food_types = detect_food_type(normalized)
    analysis.meal_time = detect_meal_time(normalized)
    analysis.price_preference = detect_price_preference(normalized)
    analysis.is_drinking = is_drinking_context(normalized)
    analysis.social_context_type = detect_social_context(normalized)

    # ── Step 7: Weather analysis ──────────────────────────────────────────────
    analysis.heat_level = score_heat(normalized)
    analysis.rain_level = score_rain(normalized)
    analysis.wind_level = score_wind(normalized)
    analysis.sea_danger = score_sea_danger(normalized)
    analysis.good_weather = score_good_weather(normalized)
    analysis.weather_action = get_weather_action(
        analysis.heat_level, analysis.rain_level, analysis.sea_danger
    )

    # ── Step 8: Time awareness ────────────────────────────────────────────────
    now = datetime.now(VN_TZ)
    analysis.current_hour = now.hour
    analysis.time_preference = detect_time_preference(normalized)

    # ── Step 9: Distance tolerance ────────────────────────────────────────────
    analysis.max_distance_km = get_max_distance_km(analysis.fatigue, analysis.movement_tolerance)

    # ── Step 10: Build context tags & routing hints ───────────────────────────
    analysis.context_tags = _build_context_tags(analysis)
    analysis.routing_hints = _build_routing_hints(analysis)

    return analysis


def build_prompt_context(analysis: VietnameseMessageAnalysis) -> str:
    """
    Build a compact context string to inject into the OpenAI system prompt.
    Gives the AI deep cultural/behavioral context without overwhelming it.
    """
    lines = []

    # Emotional state
    if analysis.fatigue >= 0.6:
        lines.append(f"⚡ NGƯỜI DÙNG ĐANG MỆT MỎI (mức {analysis.fatigue:.0%}) — ưu tiên gợi ý đơn giản, gần, ít di chuyển")
    if analysis.stress >= 0.5:
        lines.append(f"😤 NGƯỜI DÙNG ĐANG STRESS — không đưa nhiều lựa chọn, chốt nhanh 1-2 phương án")
    if analysis.hunger >= 0.7:
        lines.append(f"🍜 NGƯỜI DÙNG ĐÓI — ưu tiên gợi ý ăn uống ngay, gần nhất")
    if analysis.confusion >= 0.5:
        lines.append(f"🤷 NGƯỜI DÙNG RỐI — cần câu trả lời rõ ràng, cụ thể, không mơ hồ")
    if analysis.excitement >= 0.6:
        lines.append(f"🎉 NGƯỜI DÙNG ĐANG HỨNG KHỞI — có thể gợi ý thêm một chút, tông vui")

    # Social context
    if analysis.group_type == "family":
        lines.append("👨‍👩‍👧 ĐI GIA ĐÌNH — chú ý an toàn cho bé, chỗ đậu xe, không quá cay")
    elif analysis.group_type == "couple":
        lines.append("💑 ĐI CẶP ĐÔI — có thể gợi ý không khí lãng mạn, riêng tư")
    elif analysis.group_type == "solo":
        lines.append("🧍 ĐI MỘT MÌNH — điều chỉnh gợi ý phù hợp solo")

    # Movement & crowd
    if analysis.movement_tolerance == "low":
        lines.append(f"📍 KHÔNG MUỐN ĐI XA — tối đa ~{analysis.max_distance_km}km, ưu tiên gần")
    if analysis.crowd_tolerance == "low":
        lines.append("🔇 TRÁNH CHỖ ĐÔNG — tìm chỗ vắng hơn, ít khách")

    # Weather
    if analysis.weather_action == "redirect_indoor":
        lines.append("🌧️ ĐANG MƯA — chuyển hướng vào trong, quán cafe, nhà hàng")
    elif analysis.weather_action == "avoid_beach":
        lines.append("🌊 BIỂN ĐỘNG — không gợi ý tắm biển, đảo")
    elif analysis.weather_action == "suggest_cool_indoor":
        lines.append("🌡️ RẤT NÓNG — ưu tiên máy lạnh, đồ mát, không di chuyển nhiều")

    # Local preference
    if analysis.prefers_local_food:
        lines.append("🏠 THÍCH LOCAL — người địa phương ăn, tránh tourist trap")

    # Drinking / nightlife
    if analysis.is_drinking or analysis.social_context_type in ("social_drinking", "nightlife"):
        lines.append("🍺 NGỮ CẢNH NHẬU / NIGHTLIFE — gợi ý quán nhậu, mồi, bia lạnh")

    # Child-friendly
    if analysis.needs_child_friendly:
        lines.append("🧒 CÓ TRẺ EM — chỗ an toàn, không cay, chỗ rộng")

    # Romantic
    if analysis.is_romantic:
        lines.append("🌅 KHÔNG KHÍ LÃNG MẠN — hoàng hôn, view đẹp, riêng tư")

    # Time
    if analysis.time_preference == "golden_hour":
        lines.append("🌇 MUỐN CHỤP HOÀNG HÔN — giữ kịp trước 18:30")
    elif analysis.meal_time == "late_night":
        lines.append("🌙 ĂN KHUYA — quán mở khuya sau 22h")

    if not lines:
        return ""
    return "## Tín hiệu hành vi người dùng (từ phân tích ngôn ngữ)\n" + "\n".join(lines)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """
    Multi-layer normalization pipeline:
    1. Lowercase + collapse whitespace
    2. No-accent reconstruction (longest multi-word phrases first, pure ASCII source → safe)
    3. Short abbreviation expansion (strict word-boundary regex)

    Internet slang (INTERNET_SLANG) is intentionally NOT expanded here to avoid
    cascading replacements (e.g. 'hông' inside 'không'). Pattern detectors in the
    patterns/ modules already match slang terms directly against the raw/semi-normalized text.
    """
    t = text.strip().lower()
    t = re.sub(r"\s+", " ", t)

    # Step 1: No-accent reconstruction.
    # Source strings are pure ASCII, so there is zero risk of cascading on accented Vietnamese.
    # Longest patterns first prevents "khong muon" from stealing "khong muon di xa".
    for src, tgt in sorted(NO_ACCENT_MAP.items(), key=lambda x: -len(x[0])):
        if src in t:
            t = t.replace(src, tgt)

    # Step 2: Safe abbreviations (strict non-word-character boundaries).
    # Keep only multi-character abbreviations that are safe (≥ 2 chars, not substrings of Vietnamese).
    safe_abbrevs = {k: v for k, v in ABBREVIATIONS.items() if len(k) >= 2}
    for src, tgt in sorted(safe_abbrevs.items(), key=lambda x: -len(x[0])):
        t = re.sub(rf"(?<!\w){re.escape(src)}(?!\w)", tgt, t)

    t = re.sub(r"\s+", " ", t).strip()
    return t


def _dominant_emotion(a: VietnameseMessageAnalysis) -> str:
    """Infer dominant emotion from scores."""
    scores = {
        "hungry": a.hunger,
        "tired": a.fatigue,
        "stressed": a.stress,
        "excited": a.excitement,
        "confused": a.confusion,
        "need_rest": a.recovery_need,
    }
    best = max(scores, key=lambda k: scores[k])
    if scores[best] >= 0.4:
        return best
    return "neutral"


def _build_context_tags(a: VietnameseMessageAnalysis) -> list[str]:
    """Build summary tag list for logging / analytics."""
    tags = []
    if a.fatigue >= 0.5:
        tags.append("fatigued")
    if a.stress >= 0.5:
        tags.append("stressed")
    if a.hunger >= 0.5:
        tags.append("hungry")
    if a.excitement >= 0.5:
        tags.append("excited")
    if a.confusion >= 0.5:
        tags.append("confused")
    if a.recovery_need >= 0.5:
        tags.append("needs_rest")
    if a.is_drinking:
        tags.append("drinking_context")
    if a.is_romantic:
        tags.append("romantic")
    if a.needs_child_friendly:
        tags.append("family_with_children")
    if a.movement_tolerance == "low":
        tags.append("low_movement")
    if a.crowd_tolerance == "low":
        tags.append("crowd_averse")
    if a.prefers_local_food:
        tags.append("local_preference")
    if a.weather_action != "proceed_normal":
        tags.append(f"weather:{a.weather_action}")
    if a.dialect != "unknown":
        tags.append(f"dialect:{a.dialect}")
    if a.group_type != "unknown":
        tags.append(f"group:{a.group_type}")
    tags.extend(a.travel_intents)
    tags.extend(a.food_types)
    return tags


def _build_routing_hints(a: VietnameseMessageAnalysis) -> list[str]:
    """Build routing hints for the orchestrator."""
    hints = []
    if a.fatigue >= 0.7 or a.recovery_need >= 0.7:
        hints.append("SIMPLIFY: user needs rest, max 1-2 options, nearby only")
    if a.weather_action == "redirect_indoor":
        hints.append("REDIRECT: rain detected, suggest indoor alternatives")
    if a.weather_action == "avoid_beach":
        hints.append("REDIRECT: sea conditions bad, avoid beach/island suggestions")
    if a.is_drinking:
        hints.append("ROUTE: nightlife/drinking context, suggest nhậu spots + seafood pairing")
    if a.movement_tolerance == "low":
        hints.append(f"FILTER: max distance {a.max_distance_km}km")
    if a.crowd_tolerance == "low":
        hints.append("FILTER: avoid crowded places, suggest hidden/quiet alternatives")
    if a.needs_child_friendly:
        hints.append("FILTER: child-safe places only")
    if a.is_romantic:
        hints.append("ENHANCE: romantic atmosphere, sunset timing, private settings")
    if a.hunger >= 0.7:
        hints.append("PRIORITIZE: food/restaurant recommendations immediately")
    return hints
