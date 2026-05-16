"""
Miền Tây Language Analyzer

Detects and interprets Southern Vietnamese communication patterns.
Returns a structured MienTayContext for downstream response shaping.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from app.mi.mien_tay.data import (
    SLANG, REACTIONS, SOFT_NEGOTIATION, HUMOR_MARKERS, SOCIAL_WARMTH,
    FOOD_CULTURE, PACING_MARKERS, EXAGGERATION_PHRASES,
    NO_ACCENT_MAP, TYPO_PATTERNS,
    SLANG_LOOKUP, REACTION_LOOKUP, SOFT_NEG_LOOKUP, HUMOR_LOOKUP, WARMTH_LOOKUP,
    DIALECT_MARKERS,
    EmotionalSignal, ResponseTone,
    EmotionalMarker, SlangEntry,
)


# ── Normalization ──────────────────────────────────────────────────────────────

def _strip_diacritics(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace("đ", "d")


def normalize_mien_tay(text: str) -> str:
    """
    Normalize Miền Tây text: fix typos, expand no-accent forms, standardize slang.
    Returns normalized text for intent detection (not for display to user).
    """
    t = text.lower().strip()

    # 1. Typo correction (elongated chars)
    for typo, correct in TYPO_PATTERNS.items():
        t = t.replace(typo.lower(), correct)

    # 2. No-accent → accented (longer phrases first to avoid partial matches)
    sorted_no_accent = sorted(NO_ACCENT_MAP.keys(), key=len, reverse=True)
    for no_acc, accented in [(k, NO_ACCENT_MAP[k]) for k in sorted_no_accent]:
        t = t.replace(no_acc, f" {accented} ")

    # 3. Slang normalization (term → standard Vietnamese)
    for entry in sorted(SLANG, key=lambda s: len(s.term), reverse=True):
        if entry.term.lower() in t:
            t = t.replace(entry.term.lower(), f" {entry.standard_vn} ")
        for form in entry.no_accent_forms:
            t = t.replace(form.lower(), f" {entry.standard_vn} ")

    return re.sub(r"\s+", " ", t).strip()


# ── Context dataclass ──────────────────────────────────────────────────────────

@dataclass
class MienTayContext:
    """Full Miền Tây analysis result for a single user message."""

    # Detection
    is_mien_tay: bool = False
    dialect_score: float = 0.0                       # 0.0–1.0 confidence

    # Dominant signals
    dominant_signal: EmotionalSignal | None = None
    emotional_intensity: float = 0.0                 # 0.0–1.0
    signals: list[EmotionalSignal] = field(default_factory=list)

    # Category flags
    is_reaction: bool = False                        # strong emotional outburst
    is_soft_negotiation: bool = False                # indirect communication
    is_humor: bool = False                           # playful/exaggeration
    is_social_warmth: bool = False                   # affection/warmth marker
    is_drinking_culture: bool = False                # lai rai / nhậu
    is_fatigue: bool = False                         # genuine or exaggerated fatigue
    is_exaggeration: bool = False                    # hyperbole — don't take literally
    is_soft_reject: bool = False                     # soft refusal/avoidance

    # Pacing
    desired_pace: str = "normal"                     # fast | normal | slow | deferred | closed

    # Response shaping
    response_tone: ResponseTone = ResponseTone.WARM_CASUAL
    warmth_suffix: str = "nhen 😊"
    detected_markers: list[str] = field(default_factory=list)

    # Normalized text
    normalized_text: str = ""

    def build_guidance(self) -> str:
        """
        Build LLM guidance string for Miền Tây context.
        Injected into system prompt as interaction guidance.
        """
        if not self.is_mien_tay:
            return ""

        parts = ["## Miền Tây Communication Context"]
        parts.append(f"Dialect confidence: {self.dialect_score:.0%}")

        if self.detected_markers:
            parts.append(f"Detected markers: {', '.join(self.detected_markers[:5])}")

        if self.is_exaggeration:
            parts.append(
                "⚠️ EXAGGERATION DETECTED: User is using hyperbole — do NOT interpret literally. "
                "Acknowledge the emotional state, not the literal words."
            )

        if self.is_soft_negotiation:
            parts.append(
                "SOFT NEGOTIATION: User is using indirect Southern communication — "
                "be soft, low-pressure, and collaborative. No direct push."
            )

        if self.is_humor:
            parts.append(
                "HUMOR DETECTED: User is being playful. Match with warmth + light touch. "
                "Don't be overly serious."
            )

        if self.is_fatigue:
            intensity_label = "extreme" if self.emotional_intensity > 0.75 else "moderate"
            parts.append(
                f"FATIGUE SIGNAL ({intensity_label}): Acknowledge tiredness first. "
                "Keep response SHORT. One suggestion max."
            )

        if self.is_drinking_culture:
            parts.append(
                "LAI RAI CULTURE: User is in social relaxed drinking/eating mode. "
                "Match slow pacing. Be warm, casual, no urgency."
            )

        if self.is_social_warmth:
            parts.append(
                "WARM SOCIAL MOOD: User is expressing affection/warmth. "
                "Mirror warmth. Use Southern endings (nhen, nha, hen)."
            )

        parts.append(
            f"Response tone: {self.response_tone.value}. "
            f"End sentences with: '{self.warmth_suffix}'"
        )

        if self.desired_pace != "normal":
            parts.append(f"Pacing: {self.desired_pace} — adjust response length accordingly.")

        return "\n".join(parts)


# ── Detection logic ────────────────────────────────────────────────────────────

def _score_dialect(text: str, norm: str) -> float:
    """Score Miền Tây dialect confidence 0.0–1.0."""
    t_lower = text.lower()
    norm_lower = norm.lower()
    hits = 0
    for marker in DIALECT_MARKERS:
        if len(marker) <= 4:
            # Short markers: require word boundaries to avoid false positives
            # e.g. "nha" should not match inside "xin chào" after normalization
            pattern = r"(?:^|[\s,!?.])" + re.escape(marker) + r"(?:$|[\s,!?.])"
            if re.search(pattern, t_lower) or re.search(pattern, norm_lower):
                hits += 1
        else:
            # Longer phrases/words: substring match is safe
            if marker in t_lower or marker in norm_lower:
                hits += 1
    return min(1.0, hits * 0.20)  # each marker = 0.20, capped at 1.0


def _find_reactions(text: str, norm: str) -> list[EmotionalMarker]:
    """Find reaction markers in text."""
    t = text.lower()
    found = []
    for r in REACTIONS:
        if r.phrase.lower() in t or r.no_accent.lower() in t:
            found.append(r)
            continue
        for tf in r.typo_forms:
            if tf.lower() in t:
                found.append(r)
                break
    return found


def _find_soft_negotiation(text: str) -> list[EmotionalMarker]:
    t = text.lower()
    return [n for n in SOFT_NEGOTIATION if n.phrase.lower() in t or n.no_accent.lower() in t]


def _find_humor(text: str) -> list[EmotionalMarker]:
    t = text.lower()
    return [h for h in HUMOR_MARKERS if h.phrase.lower() in t or h.no_accent.lower() in t]


def _find_social_warmth(text: str) -> list[EmotionalMarker]:
    t = text.lower()
    return [w for w in SOCIAL_WARMTH if w.phrase.lower() in t or w.no_accent.lower() in t]


def _find_food_culture(text: str) -> list[str]:
    t = text.lower()
    return [k for k in FOOD_CULTURE if k.lower() in t or FOOD_CULTURE[k].get("no_accent", "") in t]


def _detect_pacing(text: str) -> str:
    t = text.lower()
    for marker, info in PACING_MARKERS.items():
        if marker.lower() in t:
            return info["pace"]
    return "normal"


def _detect_fatigue(signals: list[EmotionalSignal]) -> bool:
    return EmotionalSignal.FATIGUE in signals


def _pick_response_tone(
    reactions: list[EmotionalMarker],
    soft_negs: list[EmotionalMarker],
    humors: list[EmotionalMarker],
    warmths: list[EmotionalMarker],
) -> ResponseTone:
    """Pick dominant response tone from all detected markers."""
    if soft_negs:
        return ResponseTone.SOFT
    # High-intensity reaction → empathetic
    if any(r.intensity > 0.75 for r in reactions):
        return ResponseTone.EMPATHETIC
    if humors:
        return ResponseTone.PLAYFUL
    if warmths:
        return ResponseTone.WARM_CASUAL
    if reactions:
        return ResponseTone.EMPATHETIC
    return ResponseTone.WARM_CASUAL


def _pick_warmth_suffix(tone: ResponseTone, pace: str) -> str:
    if pace in ("deferred", "closed"):
        return "nha"
    tone_map = {
        ResponseTone.WARM_CASUAL: "nhen 😊",
        ResponseTone.PLAYFUL:     "nhen 😄",
        ResponseTone.SOFT:        "nha",
        ResponseTone.EMPATHETIC:  "nhen",
        ResponseTone.LAI_RAI:     "nhen, từ từ thôi",
        ResponseTone.TEASING:     "nhen 😄",
    }
    return tone_map.get(tone, "nhen")


def _dominant_signal(all_signals: list[EmotionalSignal]) -> EmotionalSignal | None:
    if not all_signals:
        return None
    counts: dict[EmotionalSignal, int] = {}
    for s in all_signals:
        counts[s] = counts.get(s, 0) + 1
    return max(counts, key=lambda k: counts[k])


def analyze(text: str) -> MienTayContext:
    """
    Full Miền Tây analysis pipeline.

    Returns MienTayContext with all signals, flags, and response guidance.
    Call .build_guidance() to get the LLM injection string.
    """
    normalized = normalize_mien_tay(text)
    score = _score_dialect(text, normalized)

    ctx = MienTayContext(
        is_mien_tay=score > 0.0,
        dialect_score=score,
        normalized_text=normalized,
    )

    if not ctx.is_mien_tay:
        return ctx

    # Detect all marker categories
    reactions   = _find_reactions(text, normalized)
    soft_negs   = _find_soft_negotiation(text)
    humors      = _find_humor(text)
    warmths     = _find_social_warmth(text)
    food_keys   = _find_food_culture(text)

    # Collect all signals
    all_signals: list[EmotionalSignal] = []
    for r in reactions:
        all_signals.extend(r.signals)
    for n in soft_negs:
        all_signals.extend(n.signals)
    for h in humors:
        all_signals.extend(h.signals)
    for w in warmths:
        all_signals.extend(w.signals)
    for fk in food_keys:
        fc = FOOD_CULTURE[fk]
        all_signals.extend(fc.get("signals", []))

    # Set flags
    ctx.is_reaction        = bool(reactions)
    ctx.is_soft_negotiation = bool(soft_negs)
    ctx.is_humor           = bool(humors)
    ctx.is_social_warmth   = bool(warmths)
    ctx.is_drinking_culture = any(FOOD_CULTURE[k].get("category") in ("drinking", "cafe") for k in food_keys)
    ctx.is_fatigue         = _detect_fatigue(all_signals)
    ctx.is_exaggeration    = any(
        phrase in text.lower()
        for phrase in EXAGGERATION_PHRASES
    )
    ctx.is_soft_reject     = EmotionalSignal.SOFT_REJECT in all_signals
    ctx.signals            = list(set(all_signals))
    ctx.dominant_signal    = _dominant_signal(all_signals)

    # Emotional intensity = max across all detected markers
    all_markers: list[EmotionalMarker] = reactions + soft_negs + humors + warmths
    ctx.emotional_intensity = max((m.intensity for m in all_markers), default=0.0)

    # Pacing
    ctx.desired_pace = _detect_pacing(text)

    # Response tone + suffix
    ctx.response_tone   = _pick_response_tone(reactions, soft_negs, humors, warmths)
    ctx.warmth_suffix   = _pick_warmth_suffix(ctx.response_tone, ctx.desired_pace)

    # Detected markers for guidance string
    ctx.detected_markers = (
        [r.phrase for r in reactions] +
        [n.phrase for n in soft_negs] +
        [h.phrase for h in humors] +
        [w.phrase for w in warmths]
    )

    return ctx
