"""Pronoun/Address Detection System for Vietnamese.

Detects and normalizes Vietnamese pronouns used in casual conversation:
- Northern/Central/Southern variants
- Gen Z vs older generation
- Casual vs formal
- Romantic tone
- Friend vs stranger
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PronounInfo:
    """Information about detected pronouns."""
    speaker_pronoun: str = ""  # What user calls themselves
    listener_pronoun: str = ""  # What user calls the AI
    normalized_speaker: str = ""  # Standard form
    normalized_listener: str = ""  # Standard form
    tone: str = "casual"  # casual, formal, romantic, respectful
    intimacy_level: float = 0.5  # 0.0-1.0
    regional_hint: str = ""  # northern, central, southern


# Pronoun mappings by region and generation
PRONOUN_MAP = {
    # First person - "I"
    "tao": {"normalized": "tôi", "tone": "casual", "region": "common"},
    "t": {"normalized": "tôi", "tone": "casual", "region": "common"},
    "tôi": {"normalized": "tôi", "tone": "formal", "region": "common"},
    "tui": {"normalized": "tôi", "tone": "casual", "region": "southern"},
    "toy": {"normalized": "tôi", "tone": "casual", "region": "common"},
    "tớ": {"normalized": "tôi", "tone": "casual", "region": "common"},
    "tui": {"normalized": "tôi", "tone": "casual", "region": "southern"},
    "tao": {"normalized": "tôi", "tone": "casual", "region": "common"},
    "bọn tao": {"normalized": "tôi", "tone": "casual", "region": "southern"},
    "bọn tui": {"normalized": "tôi", "tone": "casual", "region": "southern"},
    "hỏa": {"normalized": "tôi", "tone": "casual", "region": "southern"},
    "g": {"normalized": "tôi", "tone": "casual", "region": "common"},  # gamer slang
    "em": {"normalized": "tôi", "tone": "formal", "region": "common"},  # to younger
    "minh": {"normalized": "tôi", "tone": "casual", "region": "northern"},
    
    # Second person - "You"
    "mày": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "m": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "may": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "mik": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "mi": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "b": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "bn": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "ban": {"normalized": "bạn", "tone": "formal", "region": "common"},
    "anh": {"normalized": "bạn", "tone": "formal", "region": "common"},
    "chi": {"normalized": "bạn", "tone": "formal", "region": "common"},
    "co": {"normalized": "bạn", "tone": "formal", "region": "central"},
    "cô": {"normalized": "bạn", "tone": "formal", "region": "central"},
    "bác": {"normalized": "bạn", "tone": "respectful", "region": "common"},
    "chú": {"normalized": "bạn", "tone": "respectful", "region": "common"},
    "cậu": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "ui": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "ê": {"normalized": "bạn", "tone": "casual", "region": "common"},
    "ơi": {"normalized": "bạn", "tone": "casual", "region": "common"},
    
    # Third person pronouns
    "thằng nó": {"normalized": "họ", "tone": "casual", "region": "common"},
    "con nó": {"normalized": "họ", "tone": "casual", "region": "common"},
    "nó": {"normalized": "họ", "tone": "casual", "region": "common"},
    "hắn": {"normalized": "họ", "tone": "casual", "region": "common"},
    "hắc": {"normalized": "họ", "tone": "casual", "region": "common"},
    "đứa nó": {"normalized": "họ", "tone": "casual", "region": "southern"},
    "người ta": {"normalized": "họ", "tone": "formal", "region": "common"},
    
    # Relationship-based pronouns
    "vk": {"normalized": "vợ", "tone": "romantic", "region": "common"},
    "vo": {"normalized": "vợ", "tone": "romantic", "region": "common"},
    "ck": {"normalized": "chồng", "tone": "romantic", "region": "common"},
    "chong": {"normalized": "chồng", "tone": "romantic", "region": "common"},
    "ny": {"normalized": "bạn gái/người yêu", "tone": "romantic", "region": "common"},
    "bf": {"normalized": "bạn trai", "tone": "romantic", "region": "common"},
    "gf": {"normalized": "bạn gái", "tone": "romantic", "region": "common"},
    "ex": {"normalized": "người yêu cũ", "tone": "neutral", "region": "common"},
    
    # Plurals
    "bọn m": {"normalized": "bọn bạn", "tone": "casual", "region": "southern"},
    "bọn tao": {"normalized": "bọn tôi", "tone": "casual", "region": "southern"},
    "chúng mày": {"normalized": "bọn bạn", "tone": "casual", "region": "common"},
    "chúng tôi": {"normalized": "bọn tôi", "tone": "formal", "region": "common"},
    "bọn này": {"normalized": "bọn tôi", "tone": "casual", "region": "common"},
}


# Relationship inference patterns
RELATIONSHIP_PATTERNS = {
    "close_friend": [
        "bestie", "bff", "bn", "bạn thân", "đồng nhi", 
        "thằng", "con", "tụi", "bọn"
    ],
    "romantic": [
        "ny", "bf", "gf", "vk", "ck", "người iu", 
        "người yêu", "vợ", "chồng", "honey", "baby"
    ],
    "respectful": [
        "anh", "chị", "em", "bác", "chú", "cô", "dì", "chị"
    ],
    "casual_stranger": [
        "bạn", "b", "mày", "m"
    ],
    "customer_service": [
        "bạn", "bạn ơi", "alo", "này", "nghe nè"
    ],
}


class PronounResolver:
    """Resolves Vietnamese pronouns and infers relationship tone."""
    
    def __init__(self) -> None:
        self._pronoun_map = PRONOUN_MAP
        self._relationship_patterns = RELATIONSHIP_PATTERNS
    
    def resolve(self, text: str) -> PronounInfo:
        """
        Analyze text to detect pronouns and infer relationship tone.
        
        Returns PronounInfo with speaker/listener pronouns and metadata.
        """
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        info = PronounInfo()
        
        # Look for first person pronouns (speaker calling themselves)
        for word in words:
            if word in self._pronoun_map:
                entry = self._pronoun_map[word]
                info.speaker_pronoun = word
                info.normalized_speaker = entry["normalized"]
                
                # Update tone based on pronoun
                if entry["tone"] == "casual":
                    info.intimacy_level = 0.7
                elif entry["tone"] == "formal":
                    info.intimacy_level = 0.4
                elif entry["tone"] == "romantic":
                    info.intimacy_level = 0.9
                    info.tone = "romantic"
                
                # Regional hint
                if entry["region"] != "common":
                    info.regional_hint = entry["region"]
                break
        
        # Look for second person pronouns (speaker calling listener)
        for word in words:
            if word in self._pronoun_map:
                entry = self._pronoun_map[word]
                # Skip first person pronouns
                if entry["normalized"] == "tôi":
                    continue
                if entry["normalized"] == "bọn tôi":
                    continue
                    
                info.listener_pronoun = word
                info.normalized_listener = entry["normalized"]
                break
        
        # Infer relationship from patterns
        info.tone = self._infer_relationship(text_lower, info)
        
        return info
    
    def _infer_relationship(self, text: str, info: PronounInfo) -> str:
        """Infer relationship type from text patterns."""
        text_lower = text.lower()
        
        # Check romantic patterns
        for pattern in self._relationship_patterns["romantic"]:
            if pattern in text_lower:
                return "romantic"
        
        # Check close friend patterns
        for pattern in self._relationship_patterns["close_friend"]:
            if pattern in text_lower:
                return "casual"
        
        # Check respectful patterns
        for pattern in self._relationship_patterns["respectful"]:
            if pattern in text_lower:
                return "respectful"
        
        # Default based on pronoun
        if info.intimacy_level >= 0.7:
            return "casual"
        elif info.intimacy_level >= 0.5:
            return "neutral"
        else:
            return "formal"
    
    def normalize_pronoun(self, word: str) -> str:
        """Normalize a single pronoun to standard form."""
        word_lower = word.lower().strip()
        if word_lower in self._pronoun_map:
            return self._pronoun_map[word_lower]["normalized"]
        return word
    
    def get_tone_from_pronoun(self, word: str) -> str:
        """Get the tone associated with a pronoun."""
        word_lower = word.lower().strip()
        if word_lower in self._pronoun_map:
            return self._pronoun_map[word_lower]["tone"]
        return "neutral"
    
    def adapt_response_tone(self, base_response: str, pronoun_info: PronounInfo) -> str:
        """
        Adapt response tone based on detected pronouns.
        
        This helps the AI respond in a more natural, matching tone.
        """
        if pronoun_info.tone == "casual":
            # Use casual endings
            casual_endings = [" nhé", " nha", " đó", " vậy"]
            for ending in casual_endings:
                if not base_response.endswith(ending):
                    if base_response.endswith("."):
                        base_response = base_response[:-1] + ending + "."
                    elif base_response.endswith("!"):
                        base_response = base_response[:-1] + ending + "!"
        
        elif pronoun_info.tone == "romantic":
            # Add caring, warm tone
            warm_prefixes = ["Em ơi, ", "Này anh/em, ", "Hey, "]
            for prefix in warm_prefixes:
                if not base_response.startswith(prefix):
                    base_response = warm_prefixes[0] + base_response
                    break
        
        elif pronoun_info.tone == "respectful":
            # Add polite, formal tone
            formal_suffixes = [" ạ", " nhé bạn"]
            if not any(base_response.endswith(s) for s in formal_suffixes):
                base_response = base_response + " ạ"
        
        return base_response