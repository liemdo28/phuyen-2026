"""Vietnamese Human Language Intelligence - Main Normalizer Pipeline.

Complete processing pipeline:
1. Normalization (basic cleanup)
2. Slang resolution
3. Accent inference (no-accent typing)
4. Typo correction
5. Regional resolution
6. Intent inference
7. Emotional analysis
8. Context merge
9. Response orchestration

The system transforms raw, messy Vietnamese text into properly understood input
while preserving the natural, human feel of the communication.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.vietnamese.pronouns import PronounResolver, PronounInfo
from app.vietnamese.slang import SlangResolver, SlangInfo
from app.vietnamese.emotional import EmotionalAnalyzer, EmotionalInfo
from app.vietnamese.contextual import ContextualResolver, ContextMemory, ContextualInfo
from app.vietnamese.social_energy import SocialEnergyDetector, SocialEnergyInfo
from app.vietnamese.money_parser import MoneyParser, MoneyInfo


# No-accent Vietnamese mapping (critical for casual typing)
NO_ACCENT_MAP = {
    # Common no-accent words
    "an gi": "ăn gì",
    "di dau": "đi đâu",
    "quan ngon": "quán ngon",
    "troi nong": "trời nóng",
    "met qua": "mệt quá",
    "ngon": "ngon",
    "ngon lam": "ngon lắm",
    "oi": "ơi",
    "di": "đi",
    "den": "đến",
    "duoc": "được",
    "khong": "không",
    "hok": "không",
    "hông": "không",
    "may": "mày",
    "tao": "tao",
    "toi": "tôi",
    "minh": "mình",
    "ban": "bạn",
    "nhung": "nhưng",
    "trong": "trong",
    "thoi": "thôi",
    "roi": "rồi",
    "vay": "vậy",
    "the": "thế",
    "lam": "làm",
    "lam gi": "làm gì",
    "o dau": "ở đâu",
    "hinh nhu": "hình như",
    "co gi": "có gì",
    "chua": "chưa",
    "chua": "chưa",
    "mot": "một",
    "hai": "hai",
    "ba": "ba",
    "bon": "bốn",
    "nam": "năm",
    "sau": "sáu",
    "bay": "bảy",
    "tam": "tám",
    "chin": "chín",
    "muoi": "mười",
    "ngay": "ngày",
    "thang": "tháng",
    "nam": "năm",
    "gio": "giờ",
    "phut": "phút",
    "giay": "giây",
    "tuan": "tuần",
    "dau": "đầu",
    "cuoi": "cuối",
    "nay": "nay",
    "kia": "kia",
    "do": "đó",
    "day": "đây",
    "oi": "ơi",
    "a": "a",
    "uh": "ừ",
    "um": "ừm",
    "huh": "hả",
    "hm": "hm",
    "hm": "hm",
    "nha": "nhé",
    "nhe": "nhỉ",
    "nha": "nha",
    "di": "đi",
    "thoi": "thôi",
    "vay": "vậy",
    "the": "thế",
    "roi": "rồi",
    "xong": "xong",
    "ok": "ok",
    "okay": "okay",
    "on": "ổn",
}

# Common typos and their corrections
TYPO_MAP = {
    # Repeated characters
    "quann": "quán",
    "ann": "ăn",
    "dii": "đi",
    "troiii": "trời",
    "mettt": "mệt",
    "ngonn": "ngon",
    "toi": "tôi",
    "toois": "tôi",
    "banf": "bạn",
    "quanf": "quán",
    "ngonf": "ngon",
    "anwf": "ăn",
    "diif": "đi",
    "troii": "trời",
    "metf": "mệt",
    
    # Common keyboard swaps
    "quna": "quán",
    "quna": "quán",
    "quanj": "quán",
    "anf": "ăn",
    "anr": "ăn",
    "dif": "đi",
    "dir": "đi",
    "troif": "trời",
    "troir": "trời",
    
    # Missing accent marks
    "khong co": "không có",
    "duoc khong": "được không",
    "tot nhat": "tốt nhất",
    "ngon nhat": "ngon nhất",
    "re nhat": "rẻ nhất",
    
    # Common internet typos
    "ngta": "người ta",
    "nk": "người",
    "ng": "người",
    "t": "tôi",
    "m": "mày",
    "b": "bạn",
    "dc": "được",
    "ko": "không",
    "k": "không",
    "r": "rồi",
    "z": "rồi",
    "j": "gì",
    "g": "gì",
}

# Regional dialect mappings
REGIONAL_MAP = {
    # Northern
    "nhỉ": {"normalized": "nhỉ", "region": "northern"},
    "sao": {"normalized": "sao", "region": "northern"},
    "đấy": {"normalized": "đó", "region": "northern"},
    "ấy": {"normalized": "đó", "region": "northern"},
    "hỏi": {"normalized": "hỏi", "region": "northern"},
    
    # Central
    "răng": {"normalized": "sao", "region": "central"},
    "mô": {"normalized": "đâu", "region": "central"},
    "ri": {"normalized": "vậy", "region": "central"},
    "hỉ": {"normalized": "nhỉ", "region": "central"},
    "dzô": {"normalized": "vào", "region": "central"},
    "bển": {"normalized": "bên đó", "region": "central"},
    "hông": {"normalized": "không", "region": "central"},
    "co": {"normalized": "cô", "region": "central"},
    "cô": {"normalized": "cô", "region": "central"},
    "chi": {"normalized": "gì", "region": "central"},
    
    # Southern
    "dở": {"normalized": "dở", "region": "southern"},
    "nghỉ": {"normalized": "nghỉ", "region": "southern"},
    "bởi": {"normalized": "bởi", "region": "southern"},
    "bọn": {"normalized": "bọn", "region": "southern"},
    "tui": {"normalized": "tôi", "region": "southern"},
    "tui": {"normalized": "tôi", "region": "southern"},
    "bây": {"normalized": "bây giờ", "region": "southern"},
    "mìn": {"normalized": "mình", "region": "southern"},
    "hổ": {"normalized": "không", "region": "southern"},
    "hok": {"normalized": "không", "region": "southern"},
}

# Intent keywords and patterns
INTENT_PATTERNS = {
    "search_place": [
        "tìm", "tìm kiếm", "tìm quán", "tìm chỗ", "tìm nhà",
        "ở đâu", "quán nào", "chỗ nào", "nhà hàng nào",
        "quán", "nhà hàng", "cửa hàng", "shop", "cafe", "café",
        "quán ăn", "quán coffee", "quán trà", "quán nhậu",
        "địa điểm", "địa điểm ăn", "chỗ ngồi", "bàn",
    ],
    "get_recommendation": [
        "gợi ý", "recommend", "đề xuất", "recommend", "suggest",
        "nên đi", "nên ăn", "nên uống", "nên thử",
        "tốt nhất", "ngon nhất", "đẹp nhất", "nổi tiếng nhất",
        "popular", "best", "top", "hay nhất", "xịn nhất",
    ],
    "get_direction": [
        "chỉ đường", "đường đi", "hướng dẫn", "đi như nào",
        "ở đâu", "ở chỗ nào", "gần đây", "xa không",
        "cách", "khoảng cách", "bao xa", "đi bao lâu",
    ],
    "make_reservation": [
        "đặt bàn", "đặt chỗ", "booking", "reservation",
        "đặt trước", "giữ chỗ", "reserve",
    ],
    "ask_price": [
        "giá", "giá bao nhiêu", "bao nhiêu", "price",
        "chi phí", "tốn bao nhiêu", "hết bao nhiêu",
        "có đắt không", "rẻ không", "giá cả",
    ],
    "ask_hours": [
        "giờ mở", "giờ đóng", "mấy giờ", "giờ hoạt động",
        "open", "close", "buổi", "sáng", "trưa", "chiều", "tối",
    ],
    "ask_review": [
        "đánh giá", "review", "bình luận", "feedback",
        "ngon không", "tốt không", "có ngon không", "có tốt không",
        "ấn tượng", "review", "rating", "sao",
    ],
    "ask_menu": [
        "menu", "thực đơn", "danh sách món", "có món gì",
        "món ngon", "món đặc sản", "món nổi bật", "signature",
    ],
}


@dataclass
class ProcessingStep:
    """Information about each processing step."""
    step_name: str
    input_text: str
    output_text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class NormalizedOutput:
    """Complete normalized output from the pipeline."""
    original: str = ""
    normalized: str = ""
    normalized_with_accents: str = ""
    
    # Analysis results
    pronoun_info: Optional[PronounInfo] = None
    slang_info: Optional[list[SlangInfo]] = None
    emotional_info: Optional[EmotionalInfo] = None
    contextual_info: Optional[ContextualInfo] = None
    social_energy_info: Optional[SocialEnergyInfo] = None
    money_info: Optional[list[MoneyInfo]] = None
    
    # Intent and context
    detected_intent: str = ""
    intent_confidence: float = 0.0
    regional_hint: str = ""
    tone: str = "casual"
    
    # Processing history
    processing_steps: list[ProcessingStep] = field(default_factory=list)
    
    # Quality indicators
    is_heavy_slang: bool = False
    is_no_accent: bool = False
    is_heavy_typo: bool = False
    is_regional: bool = False
    is_emotional: bool = False
    is_formal: bool = False


class VietnameseNormalizer:
    """
    Main Vietnamese language intelligence normalizer.
    
    Processes raw Vietnamese text through a pipeline of:
    1. Basic normalization
    2. Typo correction
    3. No-accent inference
    4. Slang resolution
    5. Regional dialect normalization
    6. Contextual resolution
    7. Pronoun analysis
    8. Emotional analysis
    9. Intent inference
    10. Social energy detection
    
    The result is a fully analyzed, normalized output that preserves
    the natural human feel of the communication.
    """
    
    def __init__(self) -> None:
        # Initialize all sub-resolvers
        self._pronoun_resolver = PronounResolver()
        self._slang_resolver = SlangResolver()
        self._emotional_analyzer = EmotionalAnalyzer()
        self._contextual_resolver = ContextualResolver()
        self._social_energy_detector = SocialEnergyDetector()
        self._money_parser = MoneyParser()
        
        # Store reference maps
        self._no_accent_map = NO_ACCENT_MAP
        self._typo_map = TYPO_MAP
        self._regional_map = REGIONAL_MAP
        self._intent_patterns = INTENT_PATTERNS
        
        # User style memory
        self._user_style_memory: dict[str, any] = {}
    
    def normalize(self, text: str) -> NormalizedOutput:
        """
        Normalize Vietnamese text through the complete pipeline.
        
        Args:
            text: Raw Vietnamese text (may contain slang, typos, no accents, etc.)
            
        Returns:
            NormalizedOutput with all analysis results
        """
        output = NormalizedOutput(original=text)
        steps = []
        
        # Step 1: Basic normalization
        current = self._basic_normalize(text)
        steps.append(ProcessingStep(
            step_name="basic_normalization",
            input_text=text,
            output_text=current,
        ))
        
        # Step 2: Typo correction
        current = self._fix_typos(current)
        steps.append(ProcessingStep(
            step_name="typo_correction",
            input_text=steps[-1].output_text,
            output_text=current,
            metadata={"typos_fixed": self._count_changes(steps[-1].output_text, current)},
        ))
        
        # Step 3: No-accent inference
        accent_inferred, had_no_accent = self._infer_accents(current)
        if had_no_accent:
            output.is_no_accent = True
        current = accent_inferred
        steps.append(ProcessingStep(
            step_name="accent_inference",
            input_text=steps[-1].output_text,
            output_text=current,
            metadata={"was_no_accent": had_no_accent},
        ))
        
        # Step 4: Regional dialect normalization
        regional_normalized, regional_hint = self._normalize_regional(current)
        if regional_hint:
            output.is_regional = True
            output.regional_hint = regional_hint
        current = regional_normalized
        steps.append(ProcessingStep(
            step_name="regional_normalization",
            input_text=steps[-1].output_text,
            output_text=current,
            metadata={"regional_hint": regional_hint},
        ))
        
        # Step 5: Slang resolution
        slang_resolved, slang_infos = self._slang_resolver.resolve_all(current)
        output.slang_info = slang_infos
        if slang_infos:
            output.is_heavy_slang = len(slang_infos) > 2
        current = slang_resolved
        steps.append(ProcessingStep(
            step_name="slang_resolution",
            input_text=steps[-1].output_text,
            output_text=current,
            metadata={"slang_count": len(slang_infos)},
        ))
        
        # Step 6: Contextual resolution
        context_resolved, contextual_info = self._contextual_resolver.resolve(current)
        output.contextual_info = contextual_info
        current = context_resolved
        steps.append(ProcessingStep(
            step_name="contextual_resolution",
            input_text=steps[-1].output_text,
            output_text=current,
            metadata={"context_used": contextual_info.context_used},
        ))
        
        # Step 7: Pronoun analysis
        pronoun_info = self._pronoun_resolver.resolve(current)
        output.pronoun_info = pronoun_info
        output.tone = pronoun_info.tone
        if pronoun_info.tone == "formal":
            output.is_formal = True
        
        # Step 8: Emotional analysis
        emotional_info = self._emotional_analyzer.analyze(current)
        output.emotional_info = emotional_info
        output.is_emotional = emotional_info.intensity > 0.5
        
        # Step 9: Social energy detection
        social_energy_info = self._social_energy_detector.detect(current)
        output.social_energy_info = social_energy_info
        
        # Step 10: Money parsing
        money_infos = self._money_parser.parse(current)
        output.money_info = money_infos
        
        # Step 11: Intent inference
        intent, confidence = self._infer_intent(current)
        output.detected_intent = intent
        output.intent_confidence = confidence
        
        # Finalize
        output.normalized = current
        output.normalized_with_accents = self._ensure_accents(current)
        output.processing_steps = steps
        
        return output
    
    def _basic_normalize(self, text: str) -> str:
        """Basic text normalization."""
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Normalize quotes
        text = text.replace(""", "'").replace(""", "'")
        text = text.replace("„", '"').replace("‟", '"')
        
        # Normalize dashes
        text = text.replace("–", "-").replace("—", "-")
        
        # Remove zero-width characters
        text = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
        
        return text
    
    def _fix_typos(self, text: str) -> str:
        """Fix common typos in text."""
        result = text.lower()
        
        # Apply typo fixes
        for typo, correction in self._typo_map.items():
            # Use word boundary matching for short typos
            pattern = r'\b' + re.escape(typo) + r'\b'
            result = re.sub(pattern, correction, result)
        
        # Fix repeated characters (more than 2)
        result = re.sub(r'(.)\1{2,}', r'\1\1', result)
        
        return result
    
    def _infer_accents(self, text: str) -> tuple[str, bool]:
        """
        Infer accents from no-accent Vietnamese text.
        
        This is critical for casual typing.
        """
        text_lower = text.lower()
        result = text
        
        # Check if text has no accents at all
        has_any_accent = any(char in text_lower for char in "ăâđêôơưạảãấầẩẫậắằẳẵặẹẻẽếềểễệỉịỏõóốồổỗộớờởỡợụủũưứừửữựỷỹ")
        was_no_accent = not has_any_accent and len(text) > 3
        
        if was_no_accent:
            # Apply no-accent dictionary first
            for phrase, accented in self._no_accent_map.items():
                pattern = r'\b' + re.escape(phrase) + r'\b'
                result = re.sub(pattern, accented, result)
        
        # For remaining words without accents, use common patterns
        # This is a simplified version - production would use more sophisticated inference
        if was_no_accent:
            # Try to infer accents based on common patterns
            result = self._simple_accent_inference(result)
        
        return result, was_no_accent
    
    def _simple_accent_inference(self, text: str) -> str:
        """
        Simple accent inference for remaining words.
        
        This is a simplified version. Production would use:
        - Ngram models
        - Probabilistic inference
        - Context-aware correction
        """
        # Common patterns that help with inference
        replacements = {
            "khong": "không",
            "duoc": "được",
            "toi": "tôi",
            "ban": "bạn",
            "di": "đi",
            "den": "đến",
            "ra": "ra",
            "vao": "vào",
            "nguoi": "người",
            "ngon": "ngon",
            "an": "ăn",
            "uong": "uống",
            "o": "ở",
            "cho": "chỗ",
            "quan": "quán",
            "nha": "nhà",
            "hieu": "hiểu",
            "biet": "biết",
            "lam": "làm",
            "lam": "làm",
            "vay": "vậy",
            "roi": "rồi",
            "day": "đây",
            "do": "đó",
            "kia": "kia",
            "nay": "nay",
            "truoc": "trước",
            "sau": "sau",
        }
        
        result = text.lower()
        for word, accented in replacements.items():
            pattern = r'\b' + re.escape(word) + r'\b'
            result = re.sub(pattern, accented, result)
        
        return result
    
    def _normalize_regional(self, text: str) -> tuple[str, str]:
        """Normalize regional dialect variations."""
        result = text.lower()
        detected_region = ""
        
        for pattern, info in self._regional_map.items():
            if pattern in result:
                # Normalize to standard form
                result = result.replace(pattern, info["normalized"])
                if not detected_region:
                    detected_region = info["region"]
        
        return result, detected_region
    
    def _infer_intent(self, text: str) -> tuple[str, float]:
        """Infer user intent from text."""
        text_lower = text.lower()
        intent_scores: dict[str, float] = {}
        
        for intent, keywords in self._intent_patterns.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1.0
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(1.0, intent_scores[best_intent] / 3.0)
            return best_intent, confidence
        
        return "unknown", 0.0
    
    def _ensure_accents(self, text: str) -> str:
        """Ensure text has proper accents (for display)."""
        # This can be used to ensure normalized output has accents
        return text
    
    def _count_changes(self, before: str, after: str) -> int:
        """Count how many changes were made."""
        words_before = set(before.lower().split())
        words_after = set(after.lower().split())
        return len(words_after - words_before)
    
    def adapt_response_tone(
        self,
        response: str,
        normalized: NormalizedOutput
    ) -> str:
        """
        Adapt AI response tone based on user input analysis.
        
        Args:
            response: Base response text
            normalized: NormalizedOutput from normalize()
            
        Returns:
            Response adapted to match user's tone and style
        """
        # Adapt based on tone
        if normalized.pronoun_info:
            response = self._pronoun_resolver.adapt_response_tone(
                response, normalized.pronoun_info
            )
        
        # Adapt based on social energy
        if normalized.social_energy_info:
            response = self._social_energy_detector.adapt_response(
                response, normalized.social_energy_info
            )
        
        # Adapt based on emotional state
        if normalized.emotional_info and normalized.emotional_info.sentiment == "negative":
            # Add empathetic response
            if normalized.emotional_info.primary_emotion == "exhaustion":
                if not any(word in response.lower() for word in ["nghỉ", "thư giãn", "relax"]):
                    response = "Bạn mệt rồi, nghỉ ngơi đi nhé. " + response
        
        return response
    
    def learn_user_style(self, user_id: str, normalized: NormalizedOutput) -> None:
        """
        Learn and store user's communication style for future adaptation.
        """
        if user_id not in self._user_style_memory:
            self._user_style_memory[user_id] = {
                "pronoun_usage": [],
                "tone_history": [],
                "slang_usage": [],
                "regional_hints": [],
            }
        
        memory = self._user_style_memory[user_id]
        
        if normalized.pronoun_info:
            memory["pronoun_usage"].append(normalized.pronoun_info.speaker_pronoun)
            memory["tone_history"].append(normalized.tone)
        
        if normalized.slang_info:
            for slang in normalized.slang_info:
                memory["slang_usage"].append(slang.category)
        
        if normalized.regional_hint:
            memory["regional_hints"].append(normalized.regional_hint)
        
        # Keep only recent history
        for key in memory:
            memory[key] = memory[key][-50:]
    
    def get_user_style(self, user_id: str) -> dict:
        """
        Get learned user style preferences.
        """
        return self._user_style_memory.get(user_id, {})