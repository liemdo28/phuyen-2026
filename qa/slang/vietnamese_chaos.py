"""
Vietnamese Language Chaos Engine — Gen Z slang, internet memes,
regional shorthand, and internet culture for real human simulation.
"""

import random
import re
from typing import Optional


# ── Gen Z Slang Dictionary ─────────────────────────────────

GEN_Z_SLANG = {
    # Intensity amplifiers
    "rất": random.choice(["vl", "vcl", "cực", "siêu", "quá trời"]),
    "quá": "vl",
    "lắm": random.choice(["vl", "kinh", "xịn"]),

    # Agreement/Confirmation
    "được": random.choice(["dc", "oke", "ok", "ez"]),
    "tốt": random.choice(["xịn", "đỉnh", "ok", "oke"]),
    "đúng": random.choice(["chính xác", "ừ đúng", "ừa"]),

    # Expressions
    "tuyệt vời": random.choice(["đỉnh vl", "xịn xò", "chill", "ngon lành"]),
    "không tốt": random.choice(["tệ vl", "fail", "cringe"]),

    # Actions
    "đi ăn": random.choice(["ra ăn", "đập đồ ăn", "bão đồ ăn"]),
    "tìm kiếm": random.choice(["search", "tìm", "lùng"]),
}

INTERNET_SLANG_POOL = [
    # Vietnamese internet expressions
    ("vl", "intensifier — very/extremely"),
    ("vcl", "intensifier — very/extremely (stronger)"),
    ("lol", "lol"),
    ("haha", "laughter"),
    ("oke", "ok"),
    ("ez", "easy/no problem"),
    ("chill", "relaxed/laid-back"),
    ("flex", "show off"),
    ("vibe", "vibe/atmosphere"),
    ("trip", "bad experience or journey"),
    ("rep", "respond"),
    ("dm", "direct message"),
    ("ngl", "not gonna lie"),
    ("tbh", "to be honest"),
    ("imo", "in my opinion"),
    ("fam", "family/friends"),
    ("bro", "friend"),
    ("bae", "close friend/partner"),
    ("mood", "mood/feeling"),
    ("sus", "suspicious"),
    ("cap", "lie/fake"),
    ("no cap", "truth"),
    ("lit", "exciting"),
    ("slay", "doing great"),
    ("lowkey", "somewhat/secretly"),
    ("highkey", "very much"),
    ("bet", "sure/agreed"),
    ("vibe check", "checking the atmosphere"),
    ("npc", "robotic/generic person"),
    ("main character", "the protagonist"),
    ("side quest", "side task"),
    ("unlocked", "discovered"),
    ("skill issue", "user's fault"),
]

MONEY_SHORTHAND = {
    "nghìn đồng": "k",
    "ngàn đồng": "k",
    "nghìn": "k",
    "100 nghìn": "100k",
    "200 nghìn": "200k",
    "500 nghìn": "500k",
    "1 triệu": "1tr",
    "2 triệu": "2tr",
    "triệu đồng": "tr",
    "triệu": "tr",
    "đồng": "đ",
}

EMOTIONAL_SHORTHAND = {
    "tôi mệt": "mệt vl",
    "tôi đói": "đói vl luôn",
    "rất tốt": "đỉnh vl",
    "không biết": "ko bt",
    "không hiểu": "ko hỉu",
    "cảm ơn": "cảm ơn nha / cảm ơn bro",
    "xin lỗi": "sorry nha",
}

REGIONAL_EXPRESSIONS = {
    "south_central": {
        # Phú Yên / Bình Định / Khánh Hòa expressions
        "affirmatives": ["ừa", "ừ hén", "đúng hén", "vậy hả", "vậy à"],
        "negatives": ["hông", "không có đâu", "hổng có"],
        "questions": ["đâu nà?", "sao vậy?", "được hông?", "có hông?"],
        "interjections": ["eo ơi", "trời đất", "cha mẹ ơi", "thôi chết"],
    },
    "northern": {
        "affirmatives": ["ừ", "đúng rồi", "vâng", "ờ"],
        "negatives": ["không", "chẳng có", "không có đâu"],
        "questions": ["thế à?", "thật không?", "được không?"],
        "interjections": ["ôi giời", "thôi chết", "ối dồi ôi"],
    },
    "southern": {
        "affirmatives": ["ừ", "ừa", "đúng đó", "vậy đó"],
        "negatives": ["hông có", "không có", "không"],
        "questions": ["sao vậy?", "được không?", "vậy hả?", "thiệt không?"],
        "interjections": ["ôi thôi", "trời ơi", "chèn ơi"],
    },
}

MEME_PHRASES = [
    "đây là bình thường mới",
    "hệ thống đang xử lý",
    "NPC mode activated",
    "unlocked new location",
    "side quest accepted",
    "skill issue",
    "gg easy",
    "no cap fr fr",
    "lowkey đỉnh",
    "vibe check passed",
    "main character moment",
    "lore drop",
    "plot twist",
    "this is fine 🔥",
    "404 not found",
    "loading...",
    "respawn incoming",
    "quest completed",
]

SARCASM_MARKERS = [
    "Ừ đúng rồi 🙄",
    "Hay thật đấy",
    "Chắc chắn rồi",
    "Tuyệt vời lắm",
    "Wow ấn tượng ghê",
    "Cảm ơn nhiều lắm",
    "Không ngờ AI biết điều này",
    "Thật sự là đỉnh",
    "AI này thông minh thật",
]

FRAGMENTED_PATTERNS = [
    # Money → food type → time
    ("{budget}", "{food}", "{time}"),
    # Location → action → constraint
    ("{location}", "{action}", "{limit}"),
    # State → need → urgency
    ("{state}", "{need}", "nhanh"),
    # Intent → clarification → followup
    ("{intent}", "à {clarify}", "còn gì nữa không"),
]


class VietnameseChaosEngine:
    """Applies Vietnamese language chaos transformations."""

    def inject_slang(self, text: str, persona_type=None) -> str:
        """Inject appropriate slang into text based on persona type."""
        from ..simulation.persona_engine import PersonaType

        if persona_type == PersonaType.GEN_Z:
            return self._apply_gen_z(text)
        elif persona_type == PersonaType.MEME_USER:
            return self._apply_meme(text)
        elif persona_type == PersonaType.DRUNK_USER:
            return self._apply_drunk(text)
        elif persona_type == PersonaType.LOCAL_USER:
            return self._apply_regional(text, "south_central")
        else:
            return self._apply_generic_slang(text)

    def _apply_gen_z(self, text: str) -> str:
        """Apply Gen Z language patterns."""
        # Add intensifier
        intensifiers = ["vl", "vcl", "quá trời", "cực kỳ", "đỉnh"]
        if random.random() < 0.4:
            text = f"{text} {random.choice(intensifiers)}"

        # Replace formal words
        replacements = {
            r'\bđược\b': random.choice(["dc", "oke", "ez"]),
            r'\bkhông\b': random.choice(["ko", "hông", "không"]),
            r'\bcảm ơn\b': random.choice(["cảm ơn nha", "thanks", "cảm ơn bro"]),
            r'\btốt\b': random.choice(["đỉnh", "xịn", "oke"]),
        }
        for pattern, replacement in replacements.items():
            if random.random() < 0.5:
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Maybe add bro/fam
        if random.random() < 0.3:
            text = f"{text} {random.choice(['bro', 'fam', 'oke'])}"

        return text

    def _apply_meme(self, text: str) -> str:
        """Apply meme culture language."""
        if random.random() < 0.4:
            meme = random.choice(MEME_PHRASES)
            if random.random() < 0.5:
                return f"{meme} — {text}"
            else:
                return f"{text} ({meme})"
        return text

    def _apply_drunk(self, text: str) -> str:
        """Apply drunk user language patterns."""
        # Repeat words
        words = text.split()
        if len(words) > 2 and random.random() < 0.4:
            repeat_idx = random.randint(0, len(words) - 1)
            words.insert(repeat_idx + 1, words[repeat_idx])

        # Add filler sounds
        fillers = ["ehe", "hehe", "oi", "ừ ừ", "ha ha"]
        if random.random() < 0.5:
            words.insert(0, random.choice(fillers))

        # Mix up some letters
        result = " ".join(words)
        return result.lower()

    def _apply_regional(self, text: str, region: str) -> str:
        """Apply regional dialect markers."""
        dialect = REGIONAL_EXPRESSIONS.get(region, {})

        # Add regional affirmative
        if random.random() < 0.3 and dialect.get("affirmatives"):
            text = f"{text} {random.choice(dialect['affirmatives'])}"

        # Replace standard endings with regional ones
        if "không" in text.lower() and dialect.get("negatives"):
            if random.random() < 0.4:
                text = text.replace("không", random.choice(dialect["negatives"]))

        return text

    def _apply_generic_slang(self, text: str) -> str:
        """Apply generic internet slang."""
        # Money shorthand
        for formal, short in MONEY_SHORTHAND.items():
            if formal in text:
                text = text.replace(formal, short, 1)

        # Common replacements
        text = re.sub(r'\bkhông\b', random.choice(["ko", "k", "không"]), text,
                      flags=re.IGNORECASE, count=1)

        return text

    def generate_no_accent(self, text: str) -> str:
        """Strip all Vietnamese diacritics."""
        from ..no_accent.no_accent_engine import NoAccentEngine
        return NoAccentEngine().strip_accents(text)

    def generate_fragmented_sequence(self, full_intent: str) -> list:
        """Break a coherent message into fragmented pieces."""
        words = full_intent.split()
        if len(words) <= 2:
            return [full_intent]

        # Split into 2-4 fragments
        num_fragments = random.randint(2, min(4, len(words)))
        chunk_size = max(1, len(words) // num_fragments)

        fragments = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                fragments.append(chunk)

        return fragments[:num_fragments]

    def get_money_shorthand(self, amount: int) -> str:
        """Convert amount to Vietnamese shorthand."""
        if amount >= 1_000_000:
            return f"{amount // 1_000_000}tr"
        elif amount >= 1_000:
            return f"{amount // 1_000}k"
        return str(amount)
