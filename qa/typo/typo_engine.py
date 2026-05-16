"""
Typo Engine — Generates realistic Vietnamese typing errors
matching how real humans type on mobile keyboards.
"""

import random
import re


# Common Vietnamese keyboard adjacency errors
KEYBOARD_ADJACENCY = {
    'a': ['s', 'q', 'z', 'á', 'à', 'ả'],
    'b': ['v', 'n', 'g', 'h'],
    'c': ['x', 'v', 'd', 'f'],
    'd': ['s', 'f', 'e', 'c', 'đ'],
    'e': ['w', 'r', 'd', 'ê', 'ế', 'ề'],
    'g': ['f', 'h', 't', 'y', 'b'],
    'h': ['g', 'j', 'y', 'u', 'n', 'b'],
    'i': ['u', 'o', 'k', 'j', 'ị', 'í'],
    'k': ['j', 'l', 'i', 'o', 'm'],
    'l': ['k', 'o', 'p', 'm', ';'],
    'm': ['n', 'j', 'k', ','],
    'n': ['b', 'm', 'h', 'j'],
    'o': ['i', 'p', 'l', 'k', 'ô', 'ơ', 'ó'],
    'p': ['o', 'l', ';', '['],
    'q': ['w', 'a', '1'],
    'r': ['e', 't', 'f', 'd'],
    's': ['a', 'd', 'w', 'x', 'z'],
    't': ['r', 'y', 'g', 'f'],
    'u': ['y', 'i', 'h', 'j', 'ư', 'ú', 'ù'],
    'v': ['c', 'b', 'f', 'g'],
    'w': ['q', 'e', 'a', 's'],
    'x': ['z', 'c', 's', 'd'],
    'y': ['t', 'u', 'h', 'g'],
    'z': ['x', 'a', 's'],
    'đ': ['d', 'g'],
    'ă': ['a', 'â'],
    'â': ['a', 'ă'],
    'ê': ['e', 'ế'],
    'ô': ['o', 'ơ'],
    'ơ': ['o', 'ô'],
    'ư': ['u', 'ú'],
}

# Common Vietnamese typo patterns (real-world observations)
COMMON_TYPOS = {
    'không': ['khong', 'ko', 'khong', 'khog', 'khôngg', 'khôg'],
    'được': ['duoc', 'dc', 'đuoc', 'duọc', 'đươc'],
    'biết': ['biet', 'bết', 'biêt', 'biet'],
    'muốn': ['muon', 'muôn', 'muốm'],
    'quán': ['quan', 'qán', 'quán'],
    'ăn': ['an', 'an', 'ănn'],
    'đi': ['di', 'đj', 'ddi'],
    'tôi': ['toi', 'tôi', 'tôj'],
    'bạn': ['ban', 'bạnn', 'bam'],
    'gần': ['gan', 'gân', 'gần'],
    'này': ['nay', 'naỳ', 'nàyy'],
    'những': ['nhung', 'nhưng', 'nhũng'],
    'giờ': ['gio', 'giờ', 'giờ'],
    'nơi': ['noi', 'nơj', 'nơi'],
    'mệt': ['met', 'mêt', 'mệtt'],
    'thôi': ['thoi', 'thội', 'thôj'],
    'chỗ': ['cho', 'chổ', 'chỗ'],
    'ngon': ['ngon', 'nong', 'ngom'],
    'hải': ['hai', 'hải', 'hảii'],
    'sản': ['san', 'sảm', 'sảnn'],
    'Phú Yên': ['Phu Yen', 'phu yen', 'Phú Yên', 'Phú yen'],
    'Tuy Hòa': ['Tuy Hoa', 'tuy hoa', 'Tuy hoa'],
}

# Double-tap errors (mobile specific)
DOUBLE_TAP_ERRORS = {
    'l': 'll',
    'n': 'nn',
    'a': 'aa',
    'e': 'ee',
    'o': 'oo',
    'i': 'ii',
    't': 'tt',
    'k': 'kk',
    'g': 'gg',
    'h': 'hh',
}

# Missing space patterns
MERGED_WORDS = [
    ("quán ăn", "quánăn"),
    ("đi đâu", "điđâu"),
    ("ăn gì", "ăngì"),
    ("gần đây", "gầnđây"),
    ("mấy giờ", "mấygiờ"),
    ("bao nhiêu", "baonhiêu"),
    ("thế nào", "thếnào"),
    ("như thế", "nhưthế"),
]


class TypoEngine:
    """Generates realistic Vietnamese mobile keyboard typos."""

    def apply(self, text: str, intensity: float = 0.3) -> str:
        """Apply typos to text with given intensity (0-1)."""
        if not text or intensity < 0.05:
            return text

        # Try known word typos first
        text = self._apply_known_typos(text, intensity)

        # Apply character-level errors
        text = self._apply_char_errors(text, intensity)

        # Apply spacing errors
        if random.random() < intensity * 0.3:
            text = self._apply_spacing_errors(text)

        # Apply double-tap errors
        if random.random() < intensity * 0.2:
            text = self._apply_double_tap(text)

        # Apply deletion errors
        if random.random() < intensity * 0.3:
            text = self._apply_deletions(text)

        return text

    def _apply_known_typos(self, text: str, intensity: float) -> str:
        """Replace known words with their common typos."""
        for correct, typos in COMMON_TYPOS.items():
            if correct.lower() in text.lower() and random.random() < intensity * 0.6:
                typo = random.choice(typos)
                # Case-insensitive replace
                pattern = re.compile(re.escape(correct), re.IGNORECASE)
                text = pattern.sub(typo, text, count=1)
        return text

    def _apply_char_errors(self, text: str, intensity: float) -> str:
        """Apply adjacent keyboard character errors."""
        chars = list(text)
        num_errors = max(0, int(len(chars) * intensity * 0.15))

        for _ in range(num_errors):
            if not chars:
                break
            idx = random.randint(0, len(chars) - 1)
            char = chars[idx].lower()
            if char in KEYBOARD_ADJACENCY and random.random() < 0.4:
                chars[idx] = random.choice(KEYBOARD_ADJACENCY[char])

        return "".join(chars)

    def _apply_spacing_errors(self, text: str) -> str:
        """Apply missing space errors between words."""
        for correct, merged in MERGED_WORDS:
            if correct in text and random.random() < 0.4:
                text = text.replace(correct, merged, 1)
        return text

    def _apply_double_tap(self, text: str) -> str:
        """Apply mobile double-tap errors."""
        chars = list(text)
        for i, char in enumerate(chars):
            if char.lower() in DOUBLE_TAP_ERRORS and random.random() < 0.15:
                chars[i] = DOUBLE_TAP_ERRORS[char.lower()]
        return "".join(chars)

    def _apply_deletions(self, text: str) -> str:
        """Apply random character deletions (fat finger missing key)."""
        if len(text) < 4:
            return text
        chars = list(text)
        # Delete 1-2 characters
        num_deletions = random.randint(1, 2)
        for _ in range(num_deletions):
            if len(chars) > 3:
                # Prefer deleting vowels (common typing error)
                vowel_indices = [
                    i for i, c in enumerate(chars)
                    if c.lower() in 'aeiouăâêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ'
                ]
                if vowel_indices and random.random() < 0.6:
                    del chars[random.choice(vowel_indices)]
                else:
                    del chars[random.randint(1, len(chars) - 2)]
        return "".join(chars)

    def generate_autocorrect_fail(self, text: str) -> str:
        """Simulate autocorrect gone wrong."""
        autocorrect_fails = {
            "mệt": "mét",
            "đói": "đổi",
            "ngon": "ngốn",
            "quán": "quận",
            "ăn": "ân",
            "cần": "cân",
            "nên": "nền",
            "bên": "bến",
            "được": "đước",
            "chỗ": "chổ",
        }
        for correct, wrong in autocorrect_fails.items():
            if correct in text and random.random() < 0.2:
                text = text.replace(correct, wrong, 1)
        return text
