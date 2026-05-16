"""
Vietnamese Regional Dialect & Cultural Intelligence Database

Covers:
- Northern dialect (Hà Nội, Hà Tây, Bắc Ninh...)
- Southern dialect (Sài Gòn, Mekong...)
- Central dialect (Đà Nẵng, Huế, Phú Yên, Bình Định...)
- Gen Z language patterns (nationwide but evolved from Southern internet culture)
- Mixed / transitional expressions
"""
from __future__ import annotations

# ── Central Vietnamese Dialect ────────────────────────────────────────────────
# Phú Yên is Central Vietnam — highest relevance for this bot
CENTRAL_DIALECT: dict[str, str] = {
    # Question words
    "mô": "đâu (where)",
    "răng": "sao / như thế nào (why/how)",
    "rứa": "vậy (so/like that)",
    "hỉ": "nhỉ (right?)",
    "hè": "nhé (okay?)",
    "ri": "thế này (like this)",
    "ni": "này (this)",
    "nớ": "đó (that)",
    "tê": "kia (that over there)",
    "cơ": "cơ mà (but)",
    "eng": "anh (brother/you)",
    "ả": "chị (sister/you)",
    "bọ": "bố (father)",
    "mạ": "mẹ (mother)",
    "o": "cô (aunt/miss)",
    "ôn": "ông (mister/grandfather)",
    "bầy": "bọn (they/group)",
    "tau": "tao (I/me - informal)",
    "mi": "mày (you - informal)",
    "hắn": "nó (he/she/it - informal)",
    # Common phrases
    "ăn chưa rứa": "ăn chưa vậy (have you eaten?)",
    "đi mô rứa": "đi đâu vậy (where are you going?)",
    "răng vậy": "tại sao vậy (why?)",
    "ổ ni": "ở đây (here)",
    "ổ nớ": "ở đó (there)",
    "đúng bài không": "đúng không (is that right?)",
    "kiệu": "thế (so)",
    "sấy": "phơi (dry)",
    "gấy": "gầy (thin)",
    "cấy": "cây (tree)",
    "mướp": "loại rau (vegetable type)",
}

# ── Southern Vietnamese Dialect ───────────────────────────────────────────────
SOUTHERN_DIALECT: dict[str, str] = {
    # Pronouns
    "tui": "tôi (I)",
    "mình": "tôi (I/me)",
    "tía": "bố (father)",
    "má": "mẹ (mother)",
    "ổng": "ông ấy (he - elderly)",
    "bả": "bà ấy (she - elderly)",
    "ảnh": "anh ấy (he - young)",
    "chỉ": "chị ấy (she - young)",
    "ảnh nói": "anh ấy nói (he said)",
    # Negation
    "hổng": "không (no/not)",
    "hổng có": "không có (don't have)",
    "hông": "không (no)",
    "không hà": "không mà (not at all)",
    "đâu có": "không có đâu (there isn't)",
    # Agreement
    "hen": "nhé (okay, agreement marker)",
    "nghen": "nhé / nhỉ (okay)",
    "nha": "nhé (okay)",
    "vậy nha": "vậy nhé (okay then)",
    # Particles
    "dzô": "vào (in/let's go)",
    "dìa": "về (go home/back)",
    "bển": "bên đó (over there)",
    "bển kia": "phía bên đó (that side)",
    "dzậy": "vậy (so/like that)",
    "dzui": "vui (fun/happy)",
    "dzòm": "dòm (look/see)",
    "chời": "trời ơi (oh heavens)",
    "chời đất ơi": "trời đất ơi (oh my god)",
    # Food terms
    "bánh bao": "bánh bao (bao bun)",
    "cơm tấm": "cơm tấm (broken rice dish)",
    "hủ tiếu": "hủ tiếu (pork noodle soup)",
    "bún mắm": "bún mắm (fermented fish noodle soup)",
    "chả cá": "chả cá (fish cake)",
    # Other
    "cộ": "cũng (also)",
    "dữ": "lắm / quá (very/a lot)",
    "nhậu dữ": "nhậu nhiều (drinking a lot)",
    "đặng": "để / được (so that / can)",
    "thẩy": "ném / quăng (throw)",
    "cà chớn": "vô duyên / bậy bạ (inappropriate)",
    "nhỏ": "người (referring to a person)",
    "con nhỏ đó": "người đó (that person - female)",
}

# ── Northern Vietnamese Dialect ───────────────────────────────────────────────
NORTHERN_DIALECT: dict[str, str] = {
    # Particles
    "nhỉ": "isn't it / right (tag question)",
    "nhé": "okay / alright (agreement)",
    "ấy": "that / him / her (reference)",
    "đấy": "that / there (emphasis)",
    "này": "this / here",
    "thế": "so / like that",
    "cơ": "but / however",
    "mà": "but / however / you see",
    # Food
    "bún chả": "bún chả (grilled pork with noodles - Hanoi specialty)",
    "bánh cuốn": "bánh cuốn (steamed rice rolls)",
    "phở bò": "phở bò (beef pho - Hanoi style)",
    "bún thang": "bún thang (Hanoi noodle soup)",
    "chả cá lã vọng": "chả cá (Hanoi fish cake)",
    "bia hơi": "bia hơi (draft beer - Hanoi culture)",
    "bia hơi vỉa hè": "bia hơi vỉa hè (sidewalk draft beer)",
    # Culture
    "chém gió": "nói nhiều / khoác lác (talk a lot/brag)",
    "đi chơi phố": "đi dạo phố (go for a walk in the city)",
    "ngắm hồ": "ngắm hồ (look at the lake)",
    "trà đá vỉa hè": "trà đá vỉa hè (sidewalk iced tea culture)",
}

# ── Gen Z Nationwide ──────────────────────────────────────────────────────────
GEN_Z_MARKERS: dict[str, str] = {
    # Approval
    "slay queen": "xuất sắc (excellent)",
    "ate": "đỉnh / làm tốt lắm (did great)",
    "mother": "thần tượng (idol/queen)",
    "bestie": "bạn thân (bestie)",
    "fam": "gia đình / bạn bè (family/friends)",
    "lmao": "cười vãi (laugh out loud)",
    "no cap": "không nói dối (for real)",
    "lowkey": "không ai biết / âm thầm (secretly/quietly)",
    "highkey": "rõ ràng / thật sự (obviously)",
    "vibe": "không khí / cảm giác (atmosphere/feeling)",
    "slay": "đỉnh cao (excellent performance)",
    "ate and left no crumbs": "làm quá đỉnh không còn gì để nói",
    "that's giving": "trông như (looks like/giving off vibes of)",
    "understood the assignment": "hiểu việc phải làm",
    "we're so back": "đã quay lại rồi",
    "it's giving": "toát ra vibe (giving off vibes)",
    # Negative
    "mid": "bình thường / tầm thường (mediocre)",
    "sus": "đáng ngờ (suspicious)",
    "cap": "nói dối (lying)",
    "ratio": "bị anti nhiều hơn like",
    "L": "thua (loss)",
    "W": "thắng / tốt (win)",
    "NPC": "người vô hồn / robot (mindless person)",
    "red flag": "dấu hiệu xấu (warning sign)",
    "toxic": "độc hại (toxic)",
    # Vietnamese Gen Z specific
    "xuất sắc luôn": "rất xuất sắc (excellent)",
    "gừng gừng": "sợ hãi / hoảng (scared)",
    "cháy": "hết hàng / đông nghẹt (sold out / very crowded)",
    "thả thính": "thu hút sự chú ý (attract attention)",
    "thả xích": "cho tự do (unleash/set free)",
    "giả trân": "giả tạo (fake/pretentious)",
    "chân thật": "thật lòng (genuine)",
    "hack não": "gây sốc / không hiểu được (mind-blowing)",
    "meme sống": "người hài hước như meme (living meme)",
    "người thật việc thật": "chuyện có thật (real story)",
    "ảo lòi": "ảo tưởng (delusional)",
    "phú hộ": "phú quý / giàu (rich)",
    "flex": "khoe (show off)",
    "unhinged": "hơi điên / mất kiểm soát (unhinged/wild)",
    "chaotic": "hỗn loạn / không kiểm soát (chaotic)",
    "hot take": "quan điểm gây tranh cãi (controversial opinion)",
    "main character": "nhân vật chính / trung tâm chú ý (main character energy)",
    "side character": "nhân vật phụ / không quan trọng (background person)",
    "glow up": "thay đổi tích cực (positive transformation)",
    "era": "giai đoạn / thời kỳ (era/phase - e.g., 'Phú Yên era')",
}

# ── Regional Pattern Lists for Detection ──────────────────────────────────────
CENTRAL_SIGNALS: list[str] = list(CENTRAL_DIALECT.keys())
SOUTHERN_SIGNALS: list[str] = list(SOUTHERN_DIALECT.keys())
NORTHERN_SIGNALS: list[str] = list(NORTHERN_DIALECT.keys())
GEN_Z_SIGNALS: list[str] = list(GEN_Z_MARKERS.keys())


def detect_dialect(text: str) -> str:
    """
    Returns detected regional dialect: central | southern | northern | gen_z | unknown
    Priority: most specific signals first.
    """
    central_hits = sum(1 for s in CENTRAL_SIGNALS if s in text)
    southern_hits = sum(1 for s in SOUTHERN_SIGNALS if s in text)
    northern_hits = sum(1 for s in NORTHERN_SIGNALS if s in text)
    gen_z_hits = sum(1 for s in GEN_Z_SIGNALS if s in text)

    scores = {
        "central": central_hits * 2,  # boost central since bot is in Phú Yên
        "southern": southern_hits,
        "northern": northern_hits,
        "gen_z": gen_z_hits,
    }
    max_dialect = max(scores, key=lambda k: scores[k])
    if scores[max_dialect] == 0:
        return "unknown"
    return max_dialect


def adapt_to_dialect(reply: str, dialect: str) -> str:
    """
    Optionally adapt reply warmth/tone based on detected dialect.
    Currently: add appropriate closing particle.
    """
    if dialect == "central":
        # Central Vietnamese often use 'hỉ', 'nghen', 'nha'
        return reply  # Let the AI handle this naturally
    if dialect == "southern":
        # Southern often use 'hen', 'nha', 'nghen'
        return reply
    return reply
