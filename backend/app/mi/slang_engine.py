"""
Mi Slang Engine — Vietnamese internet culture, Gen Z, miền Tây, typos, no-accent.

Normalizes chaotic human input so Mi always understands real intent.
"""
from __future__ import annotations

import re
import unicodedata

# ── No-accent normalization map ────────────────────────────────────────────────
_NO_ACCENT: dict[str, str] = {
    # Common no-accent → accented
    "doi": "đói", "met": "mệt", "buon": "buồn", "ngu": "ngủ",
    "an": "ăn", "uong": "uống", "di": "đi", "ve": "về",
    "ngai": "ngại", "gan": "gần", "xa": "xa", "dau": "đâu",
    "sao": "sao", "lam": "làm", "biet": "biết", "hieu": "hiểu",
    "roi": "rồi", "nhe": "nhé", "oke": "ok", "thoi": "thôi",
    "may": "mày", "tau": "tao", "mi": "mi", "hen": "hén",
    "ko": "không", "k": "không", "kh": "không",
    "dc": "được", "đc": "được", "vs": "với",
    "ntn": "như thế nào", "ntm": "như thế này",
    "vl": "vãi", "vcl": "vãi", "dm": "(bực)",
    "mn": "mọi người", "mng": "mọi người",
    "nt": "nhắn tin",
}

# ── Gen Z slang normalization ──────────────────────────────────────────────────
_GEN_Z_SLANG: dict[str, str] = {
    "quẩy": "đi chơi/nhảy",
    "phê": "cảm giác thích thú",
    "chill": "thư giãn",
    "hype": "phấn khích",
    "siuuu": "tuyệt vời",
    "đỉnh kout": "rất tuyệt",
    "xịn sò": "tốt/ngon",
    "flex": "khoe",
    "sus": "đáng ngờ",
    "vibe": "cảm giác/không khí",
    "mood": "tâm trạng",
    "lowkey": "kiểu âm thầm",
    "fr fr": "thật sự",
    "no cap": "không nói đùa",
    "bet": "đồng ý",
    "lit": "vui/sôi động",
    "slay": "làm tốt",
    "oki doki": "oke",
    "oke bạn ei": "oke nhé",
    "chillax": "thư giãn",
}

# ── Miền Tây / Southern slang ──────────────────────────────────────────────────
_MIEN_TAY_SLANG: dict[str, str] = {
    "dzậy": "vậy",
    "dzô": "vô",
    "dzề": "về",
    "nhen": "nhé",
    "hen": "nhé/hén",
    "ổng": "ông ấy",
    "bả": "bà ấy",
    "tui": "tôi",
    "mầy": "mày",
    "hông": "không",
    "hổng": "không",
    "xí": "chút/tí",
    "dzữ": "dữ/kinh",
    "thía": "thế",
    "cái này nè": "cái này đây",
    "vậy nhen": "vậy nhé",
    "thôi nha": "thôi nhé",
    "mà nè": "mà đây",
    "hà": "(từ đệm miền Tây)",
    "nà": "(từ đệm miền Tây)",
    "nghen": "nhé",
}

# ── Internet meme / shorthand ──────────────────────────────────────────────────
_INTERNET_CULTURE: dict[str, str] = {
    "lmao": "(cười)",
    "lol": "(cười)",
    "omg": "(ngạc nhiên)",
    "wtf": "(bực/ngạc nhiên)",
    "brb": "quay lại sau",
    "gg": "tốt/xong rồi",
    "ez": "dễ",
    "asap": "ngay lập tức",
    "idk": "không biết",
    "tbh": "thật ra",
    "ngl": "thật lòng",
    "smh": "(lắc đầu)",
    "irl": "ngoài đời thật",
    "afk": "vắng mặt",
}

# ── Emotional shorthand ────────────────────────────────────────────────────────
_EMOTIONAL_SHORTHAND: dict[str, str] = {
    ":(": "buồn",
    ":((": "rất buồn",
    "T_T": "buồn/khóc",
    "TT": "buồn",
    "huhu": "buồn",
    "hic": "buồn",
    "ugh": "bực bội",
    "zzz": "buồn ngủ/chán",
    "kkk": "cười",
    "hehe": "cười nhẹ",
    "hihi": "cười dễ thương",
    "haha": "cười",
    "ahh": "ồ/ngạc nhiên",
    "uhm": "đang nghĩ",
    "hmm": "đang nghĩ",
}

# ── Typo patterns (common Vietnamese mobile typos) ────────────────────────────
_TYPO_CORRECTIONS: dict[str, str] = {
    "mét": "mệt",
    "méy": "mệt",
    "dói": "đói",
    "ddi": "đi",
    "ddau": "đâu",
    "nhe": "nhé",
    "ah": "à",
    "uh": "ừ",
    "okk": "ok",
    "ookk": "ok",
    "thoo": "thôi",
    "hehe": "hehe",
}

# ── Detection patterns ─────────────────────────────────────────────────────────
MIEN_TAY_MARKERS = frozenset([
    "hen", "nhen", "nghen", "dzậy", "dzô", "dzề",
    "hông", "hổng", "ổng", "bả", "tui", "mầy",
    "vậy nhen", "thôi nha", "cái này nè", "mà nè", "nà", "hà",
])

GEN_Z_MARKERS = frozenset([
    "quẩy", "phê", "siuuu", "đỉnh kout", "xịn sò", "flex",
    "sus", "vibe", "mood", "lowkey", "fr fr", "no cap", "bet",
    "lit", "slay", "oki doki", "oke bạn ei", "chillax",
])

OLDER_USER_MARKERS = frozenset([
    "cô cần", "chú cần", "bác cần", "dì cần",
    "cô muốn", "chú muốn", "bác muốn", "dì muốn",
    "cô ơi", "chú ơi", "bác ơi",
    "thưa", "dạ vâng", "kính",
])

NORTHERN_MARKERS = frozenset([
    "nhỉ", "nhé ạ", "thế ạ", "ấy", "ừ thế", "thế nhỉ",
    "kiểu như thế", "ừ ừ",
])

CENTRAL_MARKERS = frozenset([
    "mi", "tau", "mô", "răng", "rứa", "hè", "rứa hè",
    "tê", "nì", "mần", "ri", "ri nì",
])


def detect_dialect(text: str) -> str:
    """
    Returns: 'mien_tay' | 'gen_z' | 'older' | 'northern' | 'central' | 'neutral'
    Priority: mien_tay > older > gen_z > northern > central > neutral
    """
    t = text.lower()
    if any(m in t for m in MIEN_TAY_MARKERS):
        return "mien_tay"
    if any(m in t for m in OLDER_USER_MARKERS):
        return "older"
    if any(m in t for m in GEN_Z_MARKERS):
        return "gen_z"
    if any(m in t for m in NORTHERN_MARKERS):
        return "northern"
    if any(m in t for m in CENTRAL_MARKERS):
        return "central"
    return "neutral"


def normalize_slang(text: str) -> str:
    """
    Convert slang/typos/no-accent to normalized Vietnamese for intent detection.
    Does NOT change the text Mi will reply with — only for internal understanding.
    """
    t = text.lower().strip()

    # Emotional shorthand
    for k, v in _EMOTIONAL_SHORTHAND.items():
        t = t.replace(k, f" {v} ")

    # Internet culture
    for k, v in _INTERNET_CULTURE.items():
        t = t.replace(k, f" {v} ")

    # Miền Tây slang
    for k, v in _MIEN_TAY_SLANG.items():
        t = t.replace(k, f" {v} ")

    # Gen Z
    for k, v in _GEN_Z_SLANG.items():
        t = t.replace(k, f" {v} ")

    # Typos
    for k, v in _TYPO_CORRECTIONS.items():
        t = re.sub(rf"\b{re.escape(k)}\b", v, t)

    # No-accent words (word boundary)
    for k, v in _NO_ACCENT.items():
        t = re.sub(rf"\b{re.escape(k)}\b", v, t)

    return t.strip()


def is_mien_tay(text: str) -> bool:
    return detect_dialect(text) == "mien_tay"


def is_gen_z(text: str) -> bool:
    return detect_dialect(text) == "gen_z"


def is_older_user(text: str) -> bool:
    return detect_dialect(text) == "older"
