"""
Mi Human Presence Engine — orchestrator.
Combines detection, memory, pacing, and guidance generation.
"""
from __future__ import annotations
from app.mi.presence.state import (
    EmotionalSnapshot, PresenceContext, ResponsePace, SocialMode, LifePhase
)
from app.mi.presence import detector, memory as mem_store


# ── Acknowledgment templates by state ─────────────────────────────────────────
_TIRED_ACK = [
    "Nghe là thấy đuối rồi 😊",
    "Mệt thật nhen —",
    "Ừ mệt vậy thì mình đi nhẹ thôi,",
    "Hiểu rồi, nghỉ thêm tí đi —",
]

_EXHAUSTED_ACK = [
    "Hết xí xơi rồi nè 😊",
    "Thôi nghỉ hết đi, không cần cố —",
    "Mệt vậy thì về nghỉ đi, mọi thứ tính sau —",
]

_STRESSED_ACK = [
    "Nghe hơi rối đó —",
    "Vậy thì mình đơn giản hóa lại nha,",
    "Không sao, Mi lo được —",
]

_COMFORT_ACK = [
    "Ừ, yên tĩnh một chút là đúng rồi —",
    "Mình cần không gian thì Mi hiểu 😊",
]

_QUIET_ACK = [
    "Ừ.",
    "Được nhen.",
    "Ok mình nghỉ thôi.",
]

_HUNGRY_ACK = [
    "Đói rồi thì đi kiếm ăn thôi 😄",
    "Bụng kêu rồi nè —",
]

_HEAT_ACK = [
    "Nóng quá thì vào chỗ mát đã 😊",
    "Trời này nóng thật, mình tìm chỗ mát liền —",
]


def _pick_acknowledgment(snap: EmotionalSnapshot) -> str:
    import random
    if snap.life_phase == LifePhase.HUNGRY:
        return random.choice(_HUNGRY_ACK)
    if snap.life_phase == LifePhase.OVERHEATING:
        return random.choice(_HEAT_ACK)
    if snap.wants_quiet:
        return random.choice(_QUIET_ACK)
    if snap.needs_comfort:
        return random.choice(_COMFORT_ACK)
    if snap.fatigue >= 0.8:
        return random.choice(_EXHAUSTED_ACK)
    if snap.fatigue >= 0.4:
        return random.choice(_TIRED_ACK)
    if snap.stress >= 0.5:
        return random.choice(_STRESSED_ACK)
    return ""


def _pick_pace(snap: EmotionalSnapshot, history_tired: bool) -> ResponsePace:
    if snap.wants_quiet:
        return ResponsePace.MINIMAL
    if snap.fatigue >= 0.7 or snap.life_phase == LifePhase.HEALING:
        return ResponsePace.SHORT
    if snap.is_tired or history_tired:
        return ResponsePace.SHORT
    if snap.excitement >= 0.5:
        return ResponsePace.ENGAGED
    return ResponsePace.NORMAL


def _pick_social_mode(snap: EmotionalSnapshot, history_stressed: bool) -> SocialMode:
    if snap.wants_quiet:
        return SocialMode.QUIET_COMPANION
    if snap.needs_comfort or snap.in_healing:
        return SocialMode.EMOTIONALLY_SUPPORTIVE
    if snap.fatigue >= 0.5 or history_stressed:
        return SocialMode.CALM_SUPPORTIVE
    if snap.excitement >= 0.5:
        return SocialMode.PLAYFUL
    return SocialMode.CASUAL


def _proactive_note(snap: EmotionalSnapshot, history: "mem_store.EmotionalHistory") -> str:
    """Generate a natural proactive observation if appropriate."""
    # Don't inject if already explicitly complained (they know they're tired)
    if snap.fatigue >= 0.6 and len(history.snapshots) >= 3:
        # User has been consistently tired — proactive recovery note
        return "Hôm nay mình đi khá nhiều rồi đó 😊 Mi nghĩ tối nên nghỉ nhẹ cho khỏe hơn."
    if snap.life_phase == LifePhase.OVERHEATING and snap.fatigue < 0.3:
        return "Trời đang nắng gắt — vào chỗ mát nghỉ một chút trước khi tiếp tục nha."
    return ""


def build_presence_context(text: str, chat_id: int) -> PresenceContext:
    """
    Main entry point. Detect current state, read history, build PresenceContext.
    """
    snap = detector.detect(text)
    history = mem_store.get(chat_id)

    # Push current snap AFTER reading history (so history = prior states)
    mem_store.push(chat_id, snap)

    ctx = PresenceContext(
        current=snap,
        recent_was_tired=history.was_recently_tired,
        recent_was_stressed=history.was_recently_stressed,
        recent_excitement=history.recent_excitement_avg,
        social_mode=_pick_social_mode(snap, history.was_recently_stressed),
        response_pace=_pick_pace(snap, history.was_recently_tired),
        acknowledgment=_pick_acknowledgment(snap),
        proactive_note=_proactive_note(snap, history),
        simplify_choices=snap.is_tired or snap.is_overwhelmed or snap.wants_quiet,
        max_suggestions=1 if snap.wants_quiet else (2 if snap.is_tired else 3),
    )

    if ctx.simplify_choices:
        if snap.wants_quiet:
            ctx.curate_message = "Mi chọn 1 chỗ phù hợp nhất lúc này cho mình nha 😊"
        else:
            ctx.curate_message = "Mi lọc còn 2 chỗ hợp nhất với mood và thời tiết lúc này nha 😊"

    return ctx
