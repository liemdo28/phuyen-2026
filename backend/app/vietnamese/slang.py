"""Vietnamese Slang and Internet Language Resolution System.

Supports:
- Gen Z slang
- Internet slang
- TikTok slang
- Gaming slang
- Local/casual Vietnamese slang
- Contextual interpretation (same slang can be positive/negative/joking)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SlangInfo:
    """Information about detected slang."""
    original: str = ""
    resolved: str = ""
    category: str = ""  # gen_z, internet, tiktok, gaming, local, casual
    sentiment: str = "neutral"  # positive, negative, neutral
    is_joking: bool = False
    confidence: float = 1.0


# Comprehensive slang dictionary
SLANG_MAP = {
    # Gen Z / Internet slang
    "chill": {"resolved": "thư giãn", "category": "gen_z", "sentiment": "positive"},
    "chilll": {"resolved": "thư giãn", "category": "gen_z", "sentiment": "positive"},
    "flex": {"resolved": "khoe", "category": "gen_z", "sentiment": "neutral"},
    "flexin": {"resolved": "khoe", "category": "gen_z", "sentiment": "neutral"},
    "toang": {"resolved": "hỏng", "category": "gen_z", "sentiment": "negative"},
    "toang rồi": {"resolved": "hỏng rồi", "category": "gen_z", "sentiment": "negative"},
    "toang vl": {"resolved": "hỏng quá", "category": "gen_z", "sentiment": "negative"},
    "xịn": {"resolved": "tốt", "category": "gen_z", "sentiment": "positive"},
    "xịn sò": {"resolved": "rất tốt", "category": "gen_z", "sentiment": "positive"},
    "xịn xò": {"resolved": "rất tốt", "category": "gen_z", "sentiment": "positive"},
    "lụi": {"resolved": "ngẫu nhiên", "category": "gen_z", "sentiment": "neutral"},
    "cháy": {"resolved": "rất vui/nhiệt tình", "category": "gen_z", "sentiment": "positive"},
    "cháy hết mình": {"resolved": "rất nhiệt tình", "category": "gen_z", "sentiment": "positive"},
    "căng": {"resolved": "nghiêm trọng/căng thẳng", "category": "gen_z", "sentiment": "negative"},
    "căng lắm": {"resolved": "rất căng thẳng", "category": "gen_z", "sentiment": "negative"},
    "ngon": {"resolved": "tốt/rất ngon", "category": "gen_z", "sentiment": "positive"},
    "ngon lành": {"resolved": "rất tốt", "category": "gen_z", "sentiment": "positive"},
    "bựa": {"resolved": "vui/hài hước", "category": "gen_z", "sentiment": "positive"},
    "bựa vl": {"resolved": "rất vui", "category": "gen_z", "sentiment": "positive"},
    "drama": {"resolved": "drama/dramatic", "category": "internet", "sentiment": "negative"},
    "drama queen": {"resolved": "người hay drama", "category": "internet", "sentiment": "negative"},
    "toxic": {"resolved": "độc hại", "category": "internet", "sentiment": "negative"},
    "lmao": {"resolved": "cười lắm", "category": "internet", "sentiment": "positive"},
    "lol": {"resolved": "cười", "category": "internet", "sentiment": "positive"},
    "bruh": {"resolved": "trời ơi", "category": "internet", "sentiment": "neutral"},
    "rip": {"resolved": "tiếc quá", "category": "internet", "sentiment": "negative"},
    "pog": {"resolved": "tuyệt vời", "category": "gaming", "sentiment": "positive"},
    "poggers": {"resolved": "tuyệt vời", "category": "gaming", "sentiment": "positive"},
    
    # TikTok slang
    "skibidi": {"resolved": "thú vị", "category": "tiktok", "sentiment": "positive"},
    "uhhh": {"resolved": "huh", "category": "tiktok", "sentiment": "neutral"},
    "ngẫu": {"resolved": "ngẫu nhiên", "category": "tiktok", "sentiment": "neutral"},
    "sigma": {"resolved": "mạnh mẽ/độc lập", "category": "tiktok", "sentiment": "positive"},
    "ohio": {"resolved": "bất ngờ", "category": "tiktok", "sentiment": "neutral"},
    "fr": {"resolved": "thật sự", "category": "tiktok", "sentiment": "neutral"},
    "no cap": {"resolved": "nói thật", "category": "tiktok", "sentiment": "positive"},
    "lit": {"resolved": "vui/vibrant", "category": "tiktok", "sentiment": "positive"},
    "slay": {"resolved": "tuyệt vời", "category": "tiktok", "sentiment": "positive"},
    "slayqueen": {"resolved": "tuyệt vời", "category": "tiktok", "sentiment": "positive"},
    "slay king": {"resolved": "tuyệt vời", "category": "tiktok", "sentiment": "positive"},
    "bestie": {"resolved": "bạn thân", "category": "tiktok", "sentiment": "positive"},
    "bff": {"resolved": "bạn thân", "category": "tiktok", "sentiment": "positive"},
    
    # Gaming slang
    "gg": {"resolved": "game hay", "category": "gaming", "sentiment": "positive"},
    "wp": {"resolved": "chơi tốt", "category": "gaming", "sentiment": "positive"},
    "gg wp": {"resolved": "chơi tốt lắm", "category": "gaming", "sentiment": "positive"},
    "diff": {"resolved": "khác biệt", "category": "gaming", "sentiment": "neutral"},
    "diff check": {"resolved": "so sánh đi", "category": "gaming", "sentiment": "neutral"},
    "clutch": {"resolved": "chiến thắng kịch tính", "category": "gaming", "sentiment": "positive"},
    "noob": {"resolved": "người mới", "category": "gaming", "sentiment": "negative"},
    "pro": {"resolved": "chuyên nghiệp", "category": "gaming", "sentiment": "positive"},
    "feed": {"resolved": "chơi dở", "category": "gaming", "sentiment": "negative"},
    "troll": {"resolved": "trêu đùa", "category": "gaming", "sentiment": "neutral"},
    "afk": {"resolved": "đi vắng", "category": "gaming", "sentiment": "neutral"},
    "xp": {"resolved": "kinh nghiệm", "category": "gaming", "sentiment": "neutral"},
    
    # Local / casual Vietnamese slang
    "vl": {"resolved": "vãi", "category": "casual", "sentiment": "negative"},
    "vãi": {"resolved": "quá/khủng", "category": "casual", "sentiment": "neutral"},
    "vãi chưởng": {"resolved": "rất nhiều", "category": "casual", "sentiment": "negative"},
    "vãi lúa": {"resolved": "rất nhiều", "category": "casual", "sentiment": "positive"},
    "sốc": {"resolved": "bất ngờ", "category": "casual", "sentiment": "neutral"},
    "phê": {"resolved": "rất vui/sướng", "category": "casual", "sentiment": "positive"},
    "phê lắm": {"resolved": "rất vui", "category": "casual", "sentiment": "positive"},
    "mệt": {"resolved": "mệt mỏi", "category": "casual", "sentiment": "negative"},
    "mệt xỉu": {"resolved": "mệt lắm", "category": "casual", "sentiment": "negative"},
    "mệt ơi là mệt": {"resolved": "mệt lắm", "category": "casual", "sentiment": "negative"},
    "đói": {"resolved": "đói bụng", "category": "casual", "sentiment": "negative"},
    "đói chết": {"resolved": "đói lắm", "category": "casual", "sentiment": "negative"},
    "quá trời": {"resolved": "rất nhiều", "category": "casual", "sentiment": "positive"},
    "quá đáng": {"resolved": "quá mức", "category": "casual", "sentiment": "negative"},
    "đỉnh": {"resolved": "rất tốt", "category": "casual", "sentiment": "positive"},
    "đỉnh lắm": {"resolved": "rất tốt", "category": "casual", "sentiment": "positive"},
    "đỉnh của đỉnh": {"resolved": "tuyệt vời nhất", "category": "casual", "sentiment": "positive"},
    "bá": {"resolved": "rất giỏi", "category": "casual", "sentiment": "positive"},
    "bá đạo": {"resolved": "rất giỏi", "category": "casual", "sentiment": "positive"},
    "chất": {"resolved": "tốt/dễ thương", "category": "casual", "sentiment": "positive"},
    "chất lượng": {"resolved": "tốt", "category": "casual", "sentiment": "positive"},
    "cute": {"resolved": "dễ thương", "category": "casual", "sentiment": "positive"},
    "xinh": {"resolved": "đẹp", "category": "casual", "sentiment": "positive"},
    "xinh xinh": {"resolved": "đẹp đẽ", "category": "casual", "sentiment": "positive"},
    "đẹp": {"resolved": "đẹp", "category": "casual", "sentiment": "positive"},
    "đẹp trai": {"resolved": "đẹp", "category": "casual", "sentiment": "positive"},
    "dở": {"resolved": "không tốt", "category": "casual", "sentiment": "negative"},
    "dở ẹc": {"resolved": "rất dở", "category": "casual", "sentiment": "negative"},
    "tệ": {"resolved": "không tốt", "category": "casual", "sentiment": "negative"},
    "tệ lắm": {"resolved": "rất dở", "category": "casual", "sentiment": "negative"},
    "khủng": {"resolved": "lớn/ấn tượng", "category": "casual", "sentiment": "positive"},
    "khủng khiếp": {"resolved": "rất lớn", "category": "casual", "sentiment": "positive"},
    "bom": {"resolved": "rất rẻ", "category": "casual", "sentiment": "positive"},
    "bom tấn": {"resolved": "rất tốt", "category": "casual", "sentiment": "positive"},
    "sale": {"resolved": "giảm giá", "category": "casual", "sentiment": "positive"},
    "free": {"resolved": "miễn phí", "category": "casual", "sentiment": "positive"},
    "vip": {"resolved": "đặc biệt", "category": "casual", "sentiment": "positive"},
    "hot": {"resolved": "nổi tiếng/thu hút", "category": "casual", "sentiment": "positive"},
    "hotte": {"resolved": "nóng", "category": "casual", "sentiment": "negative"},
    "cool": {"resolved": "ngầu", "category": "casual", "sentiment": "positive"},
    "ngầu": {"resolved": "đẹp trai", "category": "casual", "sentiment": "positive"},
    "ngầu lắm": {"resolved": "rất đẹp trai", "category": "casual", "sentiment": "positive"},
    
    # Vietnamese internet abbreviations
    "vs": {"resolved": "với", "category": "casual", "sentiment": "neutral"},
    "tk": {"resolved": "tk", "category": "casual", "sentiment": "neutral"},
    "acc": {"resolved": "tài khoản", "category": "casual", "sentiment": "neutral"},
    "cmt": {"resolved": "bình luận", "category": "casual", "sentiment": "neutral"},
    "nt": {"resolved": "nhắn tin", "category": "casual", "sentiment": "neutral"},
    "rep": {"resolved": "trả lời", "category": "casual", "sentiment": "neutral"},
    "inbox": {"resolved": "nhắn riêng", "category": "casual", "sentiment": "neutral"},
    "ib": {"resolved": "nhắn riêng", "category": "casual", "sentiment": "neutral"},
    "lm": {"resolved": "like", "category": "casual", "sentiment": "positive"},
    "lmk": {"resolved": "cho tôi biết", "category": "casual", "sentiment": "neutral"},
    "b4": {"resolved": "trước", "category": "casual", "sentiment": "neutral"},
    "2moro": {"resolved": "ngày mai", "category": "casual", "sentiment": "neutral"},
    "2day": {"resolved": "hôm nay", "category": "casual", "sentiment": "neutral"},
    "bro": {"resolved": "bạn", "category": "casual", "sentiment": "positive"},
    "sis": {"resolved": "bạn", "category": "casual", "sentiment": "positive"},
    "homie": {"resolved": "bạn thân", "category": "casual", "sentiment": "positive"},
    "w": {"resolved": "với", "category": "casual", "sentiment": "neutral"},
    "g": {"resolved": "gì", "category": "casual", "sentiment": "neutral"},
    "j": {"resolved": "gì", "category": "casual", "sentiment": "neutral"},
    "ng": {"resolved": "người", "category": "casual", "sentiment": "neutral"},
    "k": {"resolved": "không", "category": "casual", "sentiment": "negative"},
    "kh": {"resolved": "không", "category": "casual", "sentiment": "negative"},
    "hok": {"resolved": "không", "category": "casual", "sentiment": "negative"},
    "dc": {"resolved": "được", "category": "casual", "sentiment": "positive"},
    "dk": {"resolved": "được", "category": "casual", "sentiment": "positive"},
    "r": {"resolved": "rồi", "category": "casual", "sentiment": "neutral"},
    "z": {"resolved": "rồi", "category": "casual", "sentiment": "neutral"},
    "zo": {"resolved": "vào", "category": "casual", "sentiment": "neutral"},
    "wa": {"resolved": "quá", "category": "casual", "sentiment": "positive"},
    "wá": {"resolved": "quá", "category": "casual", "sentiment": "positive"},
    "iu": {"resolved": "yêu", "category": "casual", "sentiment": "positive"},
    "yt": {"resolved": "youtube", "category": "casual", "sentiment": "neutral"},
    "fb": {"resolved": "facebook", "category": "casual", "sentiment": "neutral"},
    "ig": {"resolved": "instagram", "category": "casual", "sentiment": "neutral"},
    "tt": {"resolved": "tin nhắn", "category": "casual", "sentiment": "neutral"},
    
    # More local expressions
    "trẩu": {"resolved": "khó hiểu", "category": "casual", "sentiment": "negative"},
    "trẩu lắm": {"resolved": "rất khó hiểu", "category": "casual", "sentiment": "negative"},
    "củ chuối": {"resolved": "hỗn loạn", "category": "casual", "sentiment": "negative"},
    "bánh bèo": {"resolved": "yếu đuối", "category": "casual", "sentiment": "negative"},
    "gà": {"resolved": "dở", "category": "casual", "sentiment": "negative"},
    "gà vl": {"resolved": "rất dở", "category": "casual", "sentiment": "negative"},
    "dế": {"resolved": "điện thoại", "category": "casual", "sentiment": "neutral"},
    "mlem": {"resolved": "ngon", "category": "casual", "sentiment": "positive"},
    "hột me": {"resolved": "mệt", "category": "casual", "sentiment": "negative"},
    "hự": {"resolved": "au", "category": "casual", "sentiment": "neutral"},
}

# Contextual meanings - same slang can have different meanings
CONTEXTUAL_SENTIMENT = {
    "chill": {
        "positive": ["thư giãn", "bình thường thôi", "ok"],
        "negative": ["lạnh", "không quan tâm"],
    },
    "ngon": {
        "positive": ["tốt", "ngon", "dễ"],
        "negative": ["bình thường", "không có gì đặc biệt"],
    },
    "bom": {
        "positive": ["rất rẻ", "giá tốt"],
        "negative": ["bom tấn", "phim hay"],
    },
    "toang": {
        "positive": ["hỏng", "thất bại"],
        "negative": ["hỏng nặng"],
    },
}


class SlangResolver:
    """Resolves Vietnamese slang and internet language."""
    
    def __init__(self) -> None:
        self._slang_map = SLANG_MAP
        self._contextual = CONTEXTUAL_SENTIMENT
    
    def resolve(self, text: str, context: Optional[str] = None) -> SlangInfo:
        """
        Resolve slang in text with optional context for disambiguation.
        
        Args:
            text: The text containing slang
            context: Optional context for disambiguation
            
        Returns:
            SlangInfo with resolved text and metadata
        """
        text_lower = text.lower().strip()
        info = SlangInfo()
        info.original = text
        
        # Try to match multi-word slang first (longer matches)
        words = text_lower.split()
        for i in range(len(words)):
            for j in range(i + 1, len(words) + 1):
                phrase = " ".join(words[i:j])
                if phrase in self._slang_map:
                    entry = self._slang_map[phrase]
                    info.resolved = entry["resolved"]
                    info.category = entry["category"]
                    info.sentiment = entry["sentiment"]
                    info.confidence = 1.0
                    return info
        
        # Try single word matches
        for word in words:
            if word in self._slang_map:
                entry = self._slang_map[word]
                info.resolved = entry["resolved"]
                info.category = entry["category"]
                info.sentiment = entry["sentiment"]
                info.confidence = 1.0
                return info
        
        # No slang found
        info.resolved = text
        return info
    
    def resolve_all(self, text: str) -> tuple[str, list[SlangInfo]]:
        """
        Resolve all slang in text.
        
        Returns:
            Tuple of (resolved_text, list of SlangInfo)
        """
        text_lower = text.lower()
        words = text_lower.split()
        resolved_words = list(words)
        all_info: list[SlangInfo] = []
        
        # Find all slang phrases
        for i in range(len(words)):
            for j in range(i + 1, len(words) + 1):
                phrase = " ".join(words[i:j])
                if phrase in self._slang_map:
                    entry = self._slang_map[phrase]
                    info = SlangInfo(
                        original=phrase,
                        resolved=entry["resolved"],
                        category=entry["category"],
                        sentiment=entry["sentiment"],
                        confidence=1.0,
                    )
                    all_info.append(info)
        
        # If no multi-word matches, try single words
        if not all_info:
            for word in words:
                if word in self._slang_map:
                    entry = self._slang_map[word]
                    info = SlangInfo(
                        original=word,
                        resolved=entry["resolved"],
                        category=entry["category"],
                        sentiment=entry["sentiment"],
                        confidence=1.0,
                    )
                    all_info.append(info)
        
        # Build resolved text
        resolved_text = text
        for slang_info in all_info:
            resolved_text = resolved_text.replace(slang_info.original, slang_info.resolved)
        
        return resolved_text, all_info
    
    def is_slang(self, word: str) -> bool:
        """Check if a word is slang."""
        return word.lower().strip() in self._slang_map
    
    def get_sentiment(self, word: str, context: Optional[str] = None) -> str:
        """Get the sentiment of a slang word."""
        word_lower = word.lower().strip()
        
        if word_lower in self._slang_map:
            return self._slang_map[word_lower]["sentiment"]
        
        # Try contextual sentiment
        if context and word_lower in self._contextual:
            # Simple context-based disambiguation
            context_lower = context.lower()
            if "tốt" in context_lower or "ngon" in context_lower or "vui" in context_lower:
                return "positive"
            elif "dở" in context_lower or "tệ" in context_lower or "hỏng" in context_lower:
                return "negative"
        
        return "neutral"