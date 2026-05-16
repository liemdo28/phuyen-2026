"""Vietnamese Emotional Language Detection and Analysis System.

Supports:
- Frustration detection
- Excitement detection
- Exhaustion detection
- Sarcasm detection
- Joking tone detection
- Passive-aggressive tone detection
- Emotional overload detection
- Emotional intensity scoring
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Emotional language patterns
EMOTIONAL_PATTERNS = {
    # Frustration patterns
    "frustration": [
        "bực", "bực bội", "khó chịu", "tức", "tức lắm", "tức quá",
        "mệt", "mệt mỏi", "chán", "chán đời", "chán lắm", "thất vọng",
        "thất vọng quá", "失望", " không chịu nổi", "chịu không nổi",
        "sao mà", "sao vậy", "sao thế", "làm sao", "làm ằng được",
        "mắc cái gì", "vì sao", "tại sao", "sao mày", "sao vậy",
        "ối dào", "trời ơi", "trời ơi là trời", "chết tiệt", "đcm",
        "dm", "đm", "cc", "cl", "cặc", "lồn", "buồn", "buồn lắm",
        "buồn quá", "mệt quá", "mệt lắm", "stress", "stressa", "stressed",
    ],
    
    # Excitement patterns
    "excitement": [
        "vui", "vui quá", "vui lắm", "hí", "hú", "hú hía", "hohoho",
        "yêu", "thích", "thích quá", "tuyệt", "tuyệt vời", "tuyệt cú mèo",
        "đỉnh", "đỉnh lắm", "bá", "bá đạo", "phê", "phê lắm",
        "sướng", "sướng quá", "hạnh phúc", "vui ghê", "vui gì á",
        "wfh", "khoái", "khoái lắm", "thích thú", "hào hứng",
        "náo nức", "mong chờ", "期待", "ước ao", "ước mơ",
        "lên đây", "lên nào", "nào", "đi thôi", "đi nào",
        "xông pha", "chiến thôi", "chiến đi", "fight", "fightting",
    ],
    
    # Exhaustion patterns
    "exhaustion": [
        "mệt", "mệt lắm", "mệt quá", "mệt xỉu", "mệt ù", "đói", "đói lắm",
        "đói chết", "buồn ngủ", "ngủ đi", "ngủ thôi", "nghỉ đi",
        "nghỉ thôi", "nghỉ nào", "nghỉ đi", "chán nói", "chẳng muốn",
        "chẳng muốn làm", "lười", "lười quá", "lười lắm", "lười biếng",
        "mệt như con kiến", "mệt như dog", "dog quá", "hấp hối",
        "hấp hối rồi", "sắp chết", "chết đi được", "chết đi",
        "ôm xác", "ôm đất", "nằm đất", "nằm thôi", "nằm nghỉ",
    ],
    
    # Sarcasm patterns
    "sarcasm": [
        "ừ", "ừ thì", "ừa", "ừa ừa", "ok", "okay", "ờ", "ồ",
        "ồ ồ", "giỏi", "giỏi lắm", "hay lắm", "hay ghê",
        "tài ghê", "tài lắm", "khôn ghê", "khôn lắm",
        "dễ ợt", "dễ quá", "có gì đâu", "chả có gì",
        "thế thôi", "vậy thôi", "đấy", "đấy nhé", "thế nhé",
        "nhé", "nha", "hoho", "hê hê", "hì hì", "hichic",
    ],
    
    # Joking patterns
    "joking": [
        "haha", "hahaha", "hahahaha", "lol", "lmao", "rofl",
        "hí hí", "hí hí hí", "hô hô", "hô hô hô",
        "đùa", "đùa thôi", "chơi", "chơi đùa", "giỡn",
        "trêu", "trêu đùa", "bông", "bông lắm", "bông bổng",
        "hài", "hài lắm", "cười", "cười đi", "cười lên",
        "vui", "vui ghê", "vui vẻ", "vui vẻ lắm",
    ],
    
    # Passive-aggressive patterns
    "passive_aggressive": [
        "ừ", "ừ cũng được", "cũng được", "thích thì thích",
        "muốn thì muốn", "cứ việc", "cứ đi", "chẳng sao",
        "chả sao", "không sao", "không sao đâu", "sao cũng được",
        "thế thôi", "vậy thôi", "thôi được rồi", "được rồi",
        "ok đi", "ok luôn", "ồ", "ồ ồ", "ồ hay nhỉ",
        "hay ghê", "giỏi ghê", "báo cáo", "báo cáo",
    ],
    
    # Aggressive patterns
    "aggressive": [
        "cút", "cút đi", "biến", "biến đi", "ra đi", "ra đi cho",
        "đm", "dm", "đcm", "cl", "cc", "con mẹ mày",
        "đụ má", "đụ", "mẹ mày", "bố mày", "tao đây",
        "tao cho", "tao bảo", "nghe chưa", "nghe rõ chưa",
        "im", "im đi", "câm miệng", "câm đi", "shut up",
    ],
    
    # Positive/emotional overload
    "emotional_overload": [
        "quá trời", "quá đáng", "quá lắm", "quá xá", "quá chén",
        "khủng khiếp", "kinh khủng", "khủng bỏ", "sợ bỏ xừ",
        "điên", "điên rồi", "phát điên", "phát khóc", "khóc",
        "khóc đi", "mếu", "mếu máo", "bật khóc", "sụt sịt",
    ],
}


# Intensity modifiers
INTENSITY_MODIFIERS = {
    "very_high": [
        "quá", "lắm", "ghê", "bỏ xừ", "sợ", "điên", "chết",
        "lì", "bỏ rồi", "xong", "rồi", "cm", "cmm", "clmm",
    ],
    "high": [
        "rất", "lắm", "hơi", "khá", "nghiêm trọng",
    ],
    "medium": [
        "có", "cũng", "đang", "vẫn",
    ],
    "low": [
        "hơi", "chút", "chút xíu", "một chút", "tý",
    ],
}


# Emoji sentiment mapping
EMOJI_SENTIMENT = {
    "😀": "positive", "😃": "positive", "😄": "positive", "😁": "positive",
    "😆": "positive", "😅": "positive", "🤣": "positive", "😂": "positive",
    "😊": "positive", "🙂": "positive", "😇": "positive", "🥰": "positive",
    "😍": "positive", "🤩": "positive", "😘": "positive", "😋": "positive",
    "😛": "positive", "😜": "positive", "🤪": "positive", "😝": "positive",
    "🤑": "positive", "🤗": "positive", "🤭": "positive", "🤫": "positive",
    "🤔": "neutral", "🤐": "neutral", "🤨": "neutral", "😐": "neutral",
    "😑": "neutral", "😶": "neutral", "😏": "neutral", "😒": "neutral",
    "🙄": "neutral", "😬": "neutral", "😮": "negative", "😯": "negative",
    "😦": "negative", "😧": "negative", "😨": "negative", "😰": "negative",
    "😥": "negative", "😢": "negative", "😭": "negative", "😱": "negative",
    "😖": "negative", "😣": "negative", "😞": "negative", "😓": "negative",
    "😩": "negative", "😫": "negative", "🥱": "negative", "😤": "negative",
    "😡": "negative", "😠": "negative", "🤬": "negative", "😈": "negative",
    "🎃": "neutral", "💀": "negative", "👻": "negative", "💩": "negative",
    "🤡": "negative", "👹": "negative", "👺": "negative", "👽": "neutral",
    "👾": "neutral", "🤖": "neutral", "😺": "positive", "😸": "positive",
    "😹": "positive", "😻": "positive", "😼": "neutral", "😽": "positive",
    "🙀": "negative", "😿": "negative", "😾": "negative",
}


@dataclass
class EmotionalInfo:
    """Information about detected emotions."""
    primary_emotion: str = "neutral"
    intensity: float = 0.0  # 0.0 - 1.0
    sentiment: str = "neutral"  # positive, negative, neutral
    detected_emotions: list[str] = None
    is_sarcastic: bool = False
    is_joking: bool = False
    is_aggressive: bool = False
    is_passive_aggressive: bool = False
    emoji_sentiment: str = "neutral"
    
    def __post_init__(self):
        if self.detected_emotions is None:
            self.detected_emotions = []


class EmotionalAnalyzer:
    """Analyzes emotional content in Vietnamese text."""
    
    def __init__(self) -> None:
        self._patterns = EMOTIONAL_PATTERNS
        self._intensity = INTENSITY_MODIFIERS
        self._emoji_sentiment = EMOJI_SENTIMENT
    
    def analyze(self, text: str) -> EmotionalInfo:
        """
        Analyze emotional content in text.
        
        Args:
            text: The text to analyze
            
        Returns:
            EmotionalInfo with detected emotions and metadata
        """
        text_lower = text.lower()
        info = EmotionalInfo()
        detected = []
        emotion_scores: dict[str, float] = {}
        
        # Check for each emotion category
        for emotion, patterns in self._patterns.items():
            score = 0.0
            matches = []
            for pattern in patterns:
                if pattern in text_lower:
                    # Check for intensity modifier
                    intensity_bonus = self._get_intensity_score(text_lower, pattern)
                    score += 1.0 + intensity_bonus
                    matches.append(pattern)
            
            if score > 0:
                emotion_scores[emotion] = score
                detected.append(emotion)
        
        # Determine primary emotion
        if emotion_scores:
            primary = max(emotion_scores, key=emotion_scores.get)
            info.primary_emotion = primary
            info.detected_emotions = detected
            
            # Calculate intensity (normalize to 0-1)
            max_score = max(emotion_scores.values())
            info.intensity = min(1.0, max_score / 5.0)
            
            # Determine sentiment based on emotion type
            if primary in ["excitement", "joking"]:
                info.sentiment = "positive"
            elif primary in ["frustration", "exhaustion", "aggressive"]:
                info.sentiment = "negative"
            elif primary == "sarcasm":
                info.is_sarcastic = True
            elif primary == "joking":
                info.is_joking = True
            elif primary == "passive_aggressive":
                info.is_passive_aggressive = True
            elif primary == "aggressive":
                info.is_aggressive = True
        
        # Check for emojis
        info.emoji_sentiment = self._analyze_emoji_sentiment(text)
        
        # Override sentiment based on emoji if strong signal
        if info.emoji_sentiment != "neutral":
            if info.emoji_sentiment == "positive" and info.sentiment == "neutral":
                info.sentiment = "positive"
            elif info.emoji_sentiment == "negative" and info.sentiment == "neutral":
                info.sentiment = "negative"
        
        # Calculate overall sentiment
        info.sentiment = self._calculate_sentiment(info)
        
        return info
    
    def _get_intensity_score(self, text: str, pattern: str) -> float:
        """Get intensity bonus based on presence of intensity modifiers."""
        score = 0.0
        
        for level, modifiers in self._intensity.items():
            for modifier in modifiers:
                if modifier in text:
                    if level == "very_high":
                        score += 0.5
                    elif level == "high":
                        score += 0.3
                    elif level == "medium":
                        score += 0.1
        
        return score
    
    def _analyze_emoji_sentiment(self, text: str) -> str:
        """Analyze sentiment from emojis in text."""
        scores = {"positive": 0, "negative": 0, "neutral": 0}
        
        for char in text:
            if char in self._emoji_sentiment:
                scores[self._emoji_sentiment[char]] += 1
        
        if scores["positive"] > scores["negative"] and scores["positive"] > scores["neutral"]:
            return "positive"
        elif scores["negative"] > scores["positive"] and scores["negative"] > scores["neutral"]:
            return "negative"
        return "neutral"
    
    def _calculate_sentiment(self, info: EmotionalInfo) -> str:
        """Calculate overall sentiment from emotion info."""
        # Check for strong indicators
        if info.is_aggressive:
            return "negative"
        if info.is_joking:
            return "positive"
        if info.is_sarcastic:
            # Sarcasm can be positive or negative, default to mixed
            return "neutral"
        if info.is_passive_aggressive:
            return "negative"
        
        # Based on primary emotion
        positive_emotions = ["excitement", "joking"]
        negative_emotions = ["frustration", "exhaustion", "aggressive"]
        
        if info.primary_emotion in positive_emotions:
            return "positive"
        elif info.primary_emotion in negative_emotions:
            return "negative"
        
        return "neutral"
    
    def get_emotional_intensity(self, text: str) -> float:
        """Get a 0-1 score of emotional intensity."""
        info = self.analyze(text)
        return info.intensity
    
    def detect_tone(self, text: str) -> str:
        """
        Detect the overall tone of the text.
        
        Returns: casual, formal, emotional, sarcastic, joking, aggressive, neutral
        """
        info = self.analyze(text)
        
        if info.is_aggressive:
            return "aggressive"
        elif info.is_sarcastic:
            return "sarcastic"
        elif info.is_joking:
            return "joking"
        elif info.is_passive_aggressive:
            return "passive_aggressive"
        elif info.intensity > 0.7:
            return "emotional"
        elif info.primary_emotion != "neutral":
            return info.primary_emotion
        
        return "neutral"