"""
Regional Dialect Engine — Simulates Vietnamese regional speech patterns
including South Central coast dialects (native to Phú Yên region).
"""

import random
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


class Region(Enum):
    PHU_YEN_LOCAL = "phu_yen_local"
    BINH_DINH = "binh_dinh"
    KHANH_HOA = "khanh_hoa"
    NORTHERN = "northern"
    SOUTHERN_SAIGON = "southern_saigon"
    CENTRAL_DA_NANG = "central_da_nang"
    MEKONG_DELTA = "mekong_delta"


@dataclass
class DialectProfile:
    region: Region
    characteristic_words: List[str]
    replacements: Dict[str, str]
    sentence_endings: List[str]
    exclamations: List[str]
    question_forms: List[str]
    sample_phrases: List[str]


DIALECT_PROFILES = {
    Region.PHU_YEN_LOCAL: DialectProfile(
        region=Region.PHU_YEN_LOCAL,
        characteristic_words=["hén", "nghen", "đó nha", "vậy hả", "chứ", "mà"],
        replacements={
            "không": "hông",
            "được": "đặng",
            "bây giờ": "chừ",
            "thế nào": "ra sao",
            "ở đây": "ở đây nè",
            "biết không": "biết hông",
        },
        sentence_endings=["nghen", "hén", "nha", "đó", "đó nghen", "vậy"],
        exclamations=["eo ơi", "trời đất ơi", "cha mẹ ơi", "thôi chết"],
        question_forms=["vậy hả?", "đúng hông?", "được hông?", "có hông?", "biết hông?"],
        sample_phrases=[
            "Quán hải sản ở đây ngon hông?",
            "Đường ra biển đi như vậy được hông?",
            "Cha mẹ ơi đông quá chứ",
            "Bãi Xép giờ này vắng hông?",
            "Chỗ đó ăn được hông nghen",
            "Tụi mình đi Gành Đá Đĩa được hông",
            "Ở đây có quán cơm bình dân hông",
        ],
    ),

    Region.BINH_DINH: DialectProfile(
        region=Region.BINH_DINH,
        characteristic_words=["đó nghe", "thôi nghe", "rứa", "mô"],
        replacements={
            "ở đâu": "ở mô",
            "như vậy": "rứa",
            "không": "không có",
            "bây giờ": "chừ ni",
        },
        sentence_endings=["nghe", "đó nghe", "rứa"],
        exclamations=["ôi trời", "trời ơi", "ui cha"],
        question_forms=["rứa không?", "ở mô?", "có không nghe?"],
        sample_phrases=[
            "Ăn hải sản ở mô ngon rứa?",
            "Đường ra đó xa không nghe?",
            "Ôi trời đông quá rứa",
            "Chỗ đó giờ đóng cửa rứa không?",
        ],
    ),

    Region.NORTHERN: DialectProfile(
        region=Region.NORTHERN,
        characteristic_words=["nhỉ", "nhé", "chứ", "ấy", "thế"],
        replacements={
            "quán ăn": "quán ăn",
            "cảm ơn": "cảm ơn",
            "thế nào": "thế nào",
        },
        sentence_endings=["nhỉ", "nhé", "thế", "ấy"],
        exclamations=["ôi giời", "thôi chết", "ối dồi ôi"],
        question_forms=["thế à?", "thật không?", "được không?", "nhỉ?"],
        sample_phrases=[
            "Quán này ăn được không nhỉ?",
            "Thật không, ở đây ngon thế?",
            "Ôi giời đông quá thế này",
            "Đường đi thế nào nhỉ?",
            "Bãi biển đẹp thật nhỉ",
        ],
    ),

    Region.SOUTHERN_SAIGON: DialectProfile(
        region=Region.SOUTHERN_SAIGON,
        characteristic_words=["vậy đó", "đó nghen", "hổng có", "thiệt"],
        replacements={
            "không": "hổng",
            "như thế": "vậy đó",
            "thật": "thiệt",
        },
        sentence_endings=["vậy", "nghen", "đó", "nhe", "vậy đó"],
        exclamations=["trời ơi", "chèn ơi", "ôi thôi"],
        question_forms=["vậy hả?", "thiệt không?", "được không vậy?", "sao vậy?"],
        sample_phrases=[
            "Quán hải sản ở đây ngon thiệt không?",
            "Chèn ơi đông ghê vậy",
            "Trời ơi nắng quá vậy",
            "Đường xa hổng vậy?",
            "Chỗ này ăn được vậy hả?",
        ],
    ),

    Region.CENTRAL_DA_NANG: DialectProfile(
        region=Region.CENTRAL_DA_NANG,
        characteristic_words=["tau", "mi", "mô", "răng"],
        replacements={
            "tôi": "tau",
            "bạn": "mi",
            "ở đâu": "ở mô",
            "tại sao": "răng",
        },
        sentence_endings=["nghe", "hí", "tề"],
        exclamations=["cha mệ ơi", "ui chao", "trời hỡi"],
        question_forms=["răng rứa?", "ở mô?", "được không nghe?"],
        sample_phrases=[
            "Tau không biết đường, mi chỉ giúp nghe",
            "Quán ăn ở mô ngon đây",
            "Cha mệ ơi đông quá",
            "Răng mà đông rứa hè",
        ],
    ),
}


class DialectEngine:
    """Applies regional dialect transformations to Vietnamese text."""

    def apply_dialect(self, text: str, region: Region) -> str:
        """Apply dialect transformations to text."""
        profile = DIALECT_PROFILES.get(region)
        if not profile:
            return text

        # Apply word replacements
        for standard, dialect in profile.replacements.items():
            if standard in text.lower():
                text = text.replace(standard, dialect)

        # Add sentence ending
        if random.random() < 0.5:
            ending = random.choice(profile.sentence_endings)
            if not text.endswith(("?", "!", ".")):
                text = f"{text} {ending}"

        return text

    def get_sample_phrase(self, region: Region) -> str:
        """Get a sample phrase from the given region's dialect."""
        profile = DIALECT_PROFILES.get(region)
        if not profile:
            return "Xin chào"
        return random.choice(profile.sample_phrases)

    def get_random_region(self) -> Region:
        """Get a weighted random region (Phú Yên local context)."""
        weights = {
            Region.PHU_YEN_LOCAL: 30,
            Region.BINH_DINH: 15,
            Region.KHANH_HOA: 15,
            Region.NORTHERN: 20,
            Region.SOUTHERN_SAIGON: 15,
            Region.CENTRAL_DA_NANG: 5,
        }
        regions = list(weights.keys())
        probs = [weights.get(r, 5) for r in regions]
        total = sum(probs)
        probs = [p / total for p in probs]
        return random.choices(regions, weights=probs, k=1)[0]

    def detect_region(self, text: str) -> Region:
        """Attempt to detect region from text patterns."""
        text_lower = text.lower()

        signals = {
            Region.PHU_YEN_LOCAL: ["hông", "đặng", "chứ", "hén"],
            Region.BINH_DINH: ["mô", "rứa", "rứa không"],
            Region.NORTHERN: ["nhỉ", "nhé", "ấy", "ôi giời"],
            Region.SOUTHERN_SAIGON: ["thiệt", "chèn ơi", "hổng"],
            Region.CENTRAL_DA_NANG: ["tau", "mi", "răng", "cha mệ"],
        }

        for region, markers in signals.items():
            if any(m in text_lower for m in markers):
                return region

        return Region.NORTHERN  # Default

    def generate_dialect_confusion_test(self) -> dict:
        """Generate a test where AI must understand regional dialect."""
        region = self.get_random_region()
        phrase = self.get_sample_phrase(region)

        return {
            "region": region.value,
            "dialect_message": phrase,
            "standard_vietnamese": self._to_standard(phrase, region),
            "test_description": f"AI must understand {region.value} dialect and respond appropriately",
        }

    def _to_standard(self, text: str, region: Region) -> str:
        """Convert dialect back to standard Vietnamese."""
        profile = DIALECT_PROFILES.get(region)
        if not profile:
            return text

        result = text
        for standard, dialect in profile.replacements.items():
            result = result.replace(dialect, standard)

        for ending in profile.sentence_endings:
            result = result.replace(f" {ending}", "")

        return result.strip()
