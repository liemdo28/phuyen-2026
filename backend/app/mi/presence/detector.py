"""
Mi Presence — emotional state detector.
Reads Vietnamese text and produces EmotionalSnapshot.
"""
from __future__ import annotations
import re
from app.mi.presence.state import EmotionalSnapshot, LifePhase

# ── Fatigue signals ────────────────────────────────────────────────────────────
_FATIGUE_HIGH = frozenset([
    "mệt thiệt luôn", "mệt quá trời", "kiệt sức", "không đi nổi",
    "đuối lắm", "sắp xỉu", "xỉu up xỉu down", "nằm luôn",
    "chân không bước nổi", "mệt muốn chết", "mệt bã người",
    "không còn sức", "hết pin", "hết xí xơi", "bã người",
])

_FATIGUE_MODERATE = frozenset([
    "mệt", "mệt mệt", "mệt chút", "khá mệt", "hơi mệt",
    "cũng mệt", "mệt rồi", "mệt ngang", "thấy mệt",
    "muốn nghỉ", "nghỉ chút", "ngồi nghỉ", "cần nghỉ",
    "buồn ngủ", "졸리다", "ngủ gật", "muốn ngủ", "ngủ tí",
    "zzz", "zz", "ngáp", "đừng mà",
])

_FATIGUE_MILD = frozenset([
    "hơi mệt", "chút mệt", "thấy hơi", "đi nhiều", "đi mãi",
    "nhiều rồi", "lâu rồi", "cũng được", "ổn thôi",
])

# ── Stress / overwhelm signals ─────────────────────────────────────────────────
_STRESS_HIGH = frozenset([
    "bực", "bực bội", "chán ghê", "căng thẳng", "stress", "áp lực",
    "mệt mỏi tinh thần", "muốn về", "thôi bỏ", "kệ đi",
    "không chịu nổi", "quá nhiều", "lộn xộn", "rối", "confused",
    "wtf", "ugh", ":((", "T_T", "TT", "huhu",
])

_STRESS_MODERATE = frozenset([
    "lo", "lo lắng", "không biết", "phân vân", "khó chịu",
    "hơi lo", "hơi bực", "chán chút", "ngán", "nản",
    "hic", ":(", "hmm lâu rồi",
])

# ── Excitement signals ─────────────────────────────────────────────────────────
_EXCITEMENT = frozenset([
    "vui", "vui quá", "thích", "thích lắm", "hay ghê",
    "ngon", "ngon quá", "đỉnh", "xịn", "tuyệt",
    "wow", "ồ", "ôi trời", "quá trời", "siêu",
    "haha", "hihi", "hehe", "kkk", "muốn đi",
    "đi thôi", "ok đi", "được rồi", "tốt quá",
])

# ── Quiet / low-stim signals ───────────────────────────────────────────────────
_QUIET_SIGNALS = frozenset([
    "cũng được", "cũng mệt", "kệ", "thôi kệ", "tùy",
    "tùy mi", "ok thôi", "ừ thôi", "vậy thôi",
    "gì cũng được", "sao cũng được", "không quan trọng",
    "mình không biết", "mình không care", "thôi mình",
])

# ── Comfort / healing signals ──────────────────────────────────────────────────
_COMFORT_SIGNALS = frozenset([
    "cần nghỉ", "nghỉ ngơi", "muốn yên", "yên lặng",
    "ngồi đây thôi", "không muốn đi đâu", "ở lại đây",
    "mình cần", "cần chút không gian", "thở được",
    "bình yên", "yên tĩnh", "mát mẻ", "chill",
])

# ── Hunger signals ─────────────────────────────────────────────────────────────
_HUNGER = frozenset([
    "đói", "đói bụng", "đói rồi", "đói quá", "bụng đói",
    "muốn ăn", "ăn gì", "ăn đi", "đi ăn", "kiếm ăn",
])

# ── Heat signals ───────────────────────────────────────────────────────────────
_HEAT = frozenset([
    "nóng", "nóng quá", "nóng bức", "nắng", "nắng quá",
    "nóng chảy người", "nóng chịu không nổi", "đổ mồ hôi",
    "muốn vào chỗ mát", "cần chỗ mát", "điều hòa",
])

# ── Night / reflective signals ─────────────────────────────────────────────────
_REFLECTIVE = frozenset([
    "tối rồi", "đêm rồi", "khuya", "buồn buồn", "nghĩ nhiều",
    "nhớ nhà", "nhớ nhà quá", "thương", "cảm giác",
    "tự nhiên thấy", "không biết sao", "lạ lạ",
])


def detect(text: str) -> EmotionalSnapshot:
    """Analyze text and return an EmotionalSnapshot."""
    t = text.lower().strip()
    snap = EmotionalSnapshot()
    signals: list[str] = []

    # Fatigue scoring
    if any(p in t for p in _FATIGUE_HIGH):
        snap.fatigue = max(snap.fatigue, 0.85)
        signals.append("fatigue_high")
    if any(p in t for p in _FATIGUE_MODERATE):
        snap.fatigue = max(snap.fatigue, 0.55)
        signals.append("fatigue_moderate")
    if any(p in t for p in _FATIGUE_MILD):
        snap.fatigue = max(snap.fatigue, 0.25)
        signals.append("fatigue_mild")

    # Stress scoring
    if any(p in t for p in _STRESS_HIGH):
        snap.stress = max(snap.stress, 0.75)
        signals.append("stress_high")
    if any(p in t for p in _STRESS_MODERATE):
        snap.stress = max(snap.stress, 0.45)
        signals.append("stress_moderate")

    # Excitement
    if any(p in t for p in _EXCITEMENT):
        snap.excitement = min(1.0, snap.excitement + 0.5)
        signals.append("excitement")

    # Quiet mode
    if any(p in t for p in _QUIET_SIGNALS):
        snap.wants_quiet = True
        snap.social_battery = min(snap.social_battery, 0.3)
        signals.append("wants_quiet")

    # Comfort / healing
    if any(p in t for p in _COMFORT_SIGNALS):
        snap.needs_comfort = True
        snap.in_healing = True
        signals.append("healing")

    # Social battery — long sentences = still engaged; very short = low battery
    words = t.split()
    if len(words) <= 3 and snap.fatigue > 0.3:
        snap.social_battery = min(snap.social_battery, 0.4)

    # Reflective mood
    if any(p in t for p in _REFLECTIVE):
        snap.reflective = True
        signals.append("reflective")

    # Life phase detection
    if any(p in t for p in _HUNGER):
        snap.life_phase = LifePhase.HUNGRY
        signals.append("hungry")
    elif any(p in t for p in _HEAT):
        snap.life_phase = LifePhase.OVERHEATING
        signals.append("overheating")
    elif snap.reflective:
        snap.life_phase = LifePhase.REFLECTIVE_NIGHT
    elif snap.fatigue >= 0.7:
        snap.life_phase = LifePhase.HEALING
    elif snap.stress >= 0.5:
        snap.life_phase = LifePhase.MENTALLY_OVERLOADED
    elif snap.wants_quiet:
        snap.life_phase = LifePhase.SOCIALLY_TIRED

    snap.detected_signals = signals
    return snap
