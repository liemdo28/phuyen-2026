"""
No-Accent Engine — Strips Vietnamese diacritics to simulate users
who type without accents (very common on mobile / quick typing).
"""

import re
import unicodedata


# Vietnamese accent → base letter mapping
ACCENT_MAP = {
    # a variants
    'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
    'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
    'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
    'Á': 'A', 'À': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
    'Ă': 'A', 'Ắ': 'A', 'Ằ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
    'Â': 'A', 'Ấ': 'A', 'Ầ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',

    # e variants
    'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
    'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
    'É': 'E', 'È': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
    'Ê': 'E', 'Ế': 'E', 'Ề': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',

    # i variants
    'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    'Í': 'I', 'Ì': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',

    # o variants
    'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
    'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
    'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
    'Ó': 'O', 'Ò': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
    'Ô': 'O', 'Ố': 'O', 'Ồ': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
    'Ơ': 'O', 'Ớ': 'O', 'Ờ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',

    # u variants
    'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
    'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
    'Ú': 'U', 'Ù': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
    'Ư': 'U', 'Ứ': 'U', 'Ừ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',

    # y variants
    'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    'Ý': 'Y', 'Ỳ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',

    # d variants
    'đ': 'd', 'Đ': 'D',
}

# Common shorthand expansions used by no-accent typers
NO_ACCENT_SHORTHAND = {
    'ko': 'không',
    'k': 'không',
    'dc': 'được',
    'dk': 'được',
    'bt': 'biết',
    'biet': 'biết',
    'ko biet': 'không biết',
    'kg': 'không',
    'mn': 'mọi người',
    'mk': 'mình',
    'tks': 'cảm ơn',
    'ths': 'cảm ơn',
    'vs': 'với',
    'ntn': 'như thế nào',
    'ntv': 'như thế vậy',
    'lm': 'làm',
    'ht': 'hết',
    'oke': 'được',
    'ok': 'được',
    'cx': 'cũng',
    'cug': 'cũng',
    'hm': 'hôm',
    'hqua': 'hôm qua',
    'hna': 'hôm nay',
    'mai': 'ngày mai',
    'ch': 'chưa',
    'chua': 'chưa',
    'oj': 'ơi',
    'r': 'rồi',
    'j': 'gì',
    'z': 'vậy',
    'v': 'vậy',
    'vay': 'vậy',
    'wa': 'quá',
    'qua': 'quá',
    'kb': 'không biết',
    'tq': 'tổng quát',
    'nha': 'nhé',
    'nhe': 'nhé',
}


class NoAccentEngine:
    """Strips Vietnamese diacritics and applies no-accent shorthand."""

    def strip_accents(self, text: str) -> str:
        """Remove all Vietnamese diacritics."""
        result = []
        for char in text:
            result.append(ACCENT_MAP.get(char, char))
        return ''.join(result)

    def partial_strip(self, text: str, strip_probability: float = 0.5) -> str:
        """Partially strip accents — some words keep accents, some don't."""
        import random
        words = text.split()
        result = []
        for word in words:
            if random.random() < strip_probability:
                stripped = ''.join(ACCENT_MAP.get(c, c) for c in word)
                result.append(stripped)
            else:
                result.append(word)
        return ' '.join(result)

    def apply_shorthand(self, text: str) -> str:
        """Apply common Vietnamese no-accent shorthand."""
        # Already no-accent text, apply shorthand
        text_lower = text.lower()
        for shorthand, full in NO_ACCENT_SHORTHAND.items():
            # Replace whole words only
            pattern = r'\b' + re.escape(shorthand) + r'\b'
            if re.search(pattern, text_lower):
                text = re.sub(pattern, shorthand, text, flags=re.IGNORECASE)
        return text

    def generate_no_accent_message(self, original: str) -> str:
        """Generate a realistic no-accent version of a Vietnamese message."""
        stripped = self.strip_accents(original)

        # Apply common shorthand
        import random
        replacements = {
            'khong': random.choice(['ko', 'k', 'khong']),
            'duoc': random.choice(['dc', 'dk', 'duoc']),
            'biet': random.choice(['bt', 'biet']),
            'minh': random.choice(['mk', 'minh']),
            'gi': random.choice(['j', 'gi']),
            'vay': random.choice(['v', 'z', 'vay']),
            'roi': random.choice(['r', 'roi']),
            'nhe': random.choice(['nha', 'nhe']),
        }

        for formal, short in replacements.items():
            if random.random() < 0.5:
                pattern = r'\b' + re.escape(formal) + r'\b'
                stripped = re.sub(pattern, short, stripped, flags=re.IGNORECASE)

        return stripped.lower()

    def is_no_accent(self, text: str) -> bool:
        """Detect if text is typed without Vietnamese accents."""
        vietnamese_accents = set(ACCENT_MAP.keys())
        for char in text:
            if char in vietnamese_accents:
                return False
        return True

    def decode_no_accent_intent(self, text: str) -> str:
        """Try to decode the intended message from no-accent text."""
        # Expand shorthand
        words = text.lower().split()
        expanded = []
        for word in words:
            expanded.append(NO_ACCENT_SHORTHAND.get(word, word))
        return ' '.join(expanded)
