"""Vietnamese Social Energy Detection System.

Detects:
- Casual mood
- Chill mood
- Stressed mood
- Tired mood
- Excited mood
- Introvert mode
- Social mode

Adapts response style accordingly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Social energy patterns
SOCIAL_ENERGY_PATTERNS = {
    "casual": [
        "bình thường", "bình thường thôi", "cũng được", "cũng ok",
        "ok", "okay", "ổn", "ổn á", "bình thường nha",
    ],
    "chill": [
        "chill", "chilll", "thư giãn", "nhàn", "nhàn nhã",
        "rảnh", "rảnh rỗi", "không vội", "thong thả",
        "từ từ", "từ từ thôi", "không cần vội",
    ],
    "stressed": [
        "vội", "gấp", "gấp lắm", "hối", "hối lắm",
        "cần gấp", "phải gấp", "cực kỳ gấp", "sắp hết giờ",
        "chạy deadline", "deadline", "đang vội", "hết giờ rồi",
    ],
    "tired": [
        "mệt", "mệt lắm", "mệt quá", "mệt xỉu", "đói",
        "đói lắm", "buồn ngủ", "ngủ đi", "nghỉ thôi",
        "lười", "lười quá", "không muốn làm gì",
        "chán nói", "chẳng muốn", "hấp hối",
    ],
    "excited": [
        "vui", "vui quá", "hí", "phê", "tuyệt", "đỉnh",
        "bá đạo", "hứng", "hứng lắm", "thích quá",
        "yêu", "thích thú", "hào hứng", "nôn nao",
        "mong chờ", "期待", "ước ao",
    ],
    "introvert": [
        "im", "im đi", "câm", "câm miệng", "bớt nói",
        "ít thôi", "bớt thôi", "ngắn gọn thôi",
        "nói ít thôi", "không cần nói nhiều",
    ],
    "social": [
        "nói chuyện", "trò chuyện", "tám", "gossip",
        "ríu rít", "hát", "hát hò", "kể", "kể chuyện",
        "bạn bè", "đi chơi", "gặp nhau", "họp mặt",
    ],
}


# Response style adaptations
RESPONSE_STYLES = {
    "casual": {
        "length": "medium",
        "formality": "casual",
        "enthusiasm": "normal",
        "suggestions": True,
    },
    "chill": {
        "length": "short",
        "formality": "very_casual",
        "enthusiasm": "low",
        "suggestions": False,
    },
    "stressed": {
        "length": "short",
        "formality": "neutral",
        "enthusiasm": "low",
        "suggestions": True,
        "urgency": True,
    },
    "tired": {
        "length": "very_short",
        "formality": "very_casual",
        "enthusiasm": "low",
        "suggestions": False,
        "comfort": True,
    },
    "excited": {
        "length": "medium",
        "formality": "casual",
        "enthusiasm": "high",
        "suggestions": True,
        "celebrate": True,
    },
    "introvert": {
        "length": "very_short",
        "formality": "neutral",
        "enthusiasm": "low",
        "suggestions": False,
        "minimal": True,
    },
    "social": {
        "length": "long",
        "formality": "casual",
        "enthusiasm": "high",
        "suggestions": True,
        "engaging": True,
    },
}


@dataclass
class SocialEnergyInfo:
    """Information about detected social energy."""
    primary_mode: str = "casual"
    intensity: float = 0.5  # 0.0 - 1.0
    detected_modes: list[str] = None
    response_style: dict = None
    needs_comfort: bool = False
    needs_urgency: bool = False
    needs_engagement: bool = False
    needs_celebration: bool = False
    
    def __post_init__(self):
        if self.detected_modes is None:
            self.detected_modes = []
        if self.response_style is None:
            self.response_style = RESPONSE_STYLES.get(self.primary_mode, RESPONSE_STYLES["casual"])


class SocialEnergyDetector:
    """Detects social energy and mood in Vietnamese text."""
    
    def __init__(self) -> None:
        self._patterns = SOCIAL_ENERGY_PATTERNS
        self._styles = RESPONSE_STYLES
    
    def detect(self, text: str) -> SocialEnergyInfo:
        """
        Detect social energy in text.
        
        Args:
            text: The text to analyze
            
        Returns:
            SocialEnergyInfo with detected social energy and recommended response style
        """
        text_lower = text.lower()
        info = SocialEnergyInfo()
        detected = []
        energy_scores: dict[str, float] = {}
        
        # Check for each social energy pattern
        for mode, patterns in self._patterns.items():
            score = 0.0
            for pattern in patterns:
                if pattern in text_lower:
                    score += 1.0
            if score > 0:
                energy_scores[mode] = score
                detected.append(mode)
        
        # Determine primary social energy
        if energy_scores:
            primary = max(energy_scores, key=energy_scores.get)
            info.primary_mode = primary
            info.detected_modes = detected
            
            # Calculate intensity
            max_score = max(energy_scores.values())
            info.intensity = min(1.0, max_score / 3.0)
            
            # Set response style
            info.response_style = self._styles.get(primary, self._styles["casual"])
            
            # Set special needs
            if primary == "tired":
                info.needs_comfort = True
            elif primary == "stressed":
                info.needs_urgency = True
            elif primary == "social":
                info.needs_engagement = True
            elif primary == "excited":
                info.needs_celebration = True
        
        return info
    
    def get_response_style(self, text: str) -> dict:
        """
        Get recommended response style for text.
        
        Returns:
            Dictionary with response style recommendations
        """
        info = self.detect(text)
        return info.response_style
    
    def adapt_response(
        self,
        response: str,
        social_energy: SocialEnergyInfo
    ) -> str:
        """
        Adapt a response based on detected social energy.
        
        Args:
            response: The base response
            social_energy: Detected social energy info
            
        Returns:
            Adapted response
        """
        style = social_energy.response_style
        primary = social_energy.primary_mode
        
        # Adapt based on mode
        if primary == "chill":
            # Make shorter and less enthusiastic
            response = self._shorten_response(response)
            response = self._remove_exclamation_marks(response)
            
        elif primary == "stressed":
            # Make concise and urgent
            response = self._shorten_response(response)
            if "gấp" not in response.lower() and "vội" not in response.lower():
                # Add urgency marker if appropriate
                pass
                
        elif primary == "tired":
            # Keep very short, add comfort
            response = self._shorten_response(response)
            if social_energy.needs_comfort:
                if not any(word in response.lower() for word in ["nghỉ", "thư giãn", "ok", "ổn"]):
                    response = response + " 💙"
                    
        elif primary == "excited":
            # Match enthusiasm
            if social_energy.needs_celebration:
                if not any(word in response.lower() for word in ["tuyệt", "vui", "đỉnh", "hay"]):
                    response = response.replace(".", "!")
                    
        elif primary == "introvert":
            # Keep minimal
            response = self._shorten_response(response)
            
        elif primary == "social":
            # Make engaging
            if not any(word in response.lower() for word in ["cùng", "với", "bạn", "chúng ta"]):
                response = response + " 😊"
        
        return response
    
    def _shorten_response(self, response: str) -> str:
        """Shorten a response."""
        # Split into sentences
        sentences = response.split(". ")
        if len(sentences) > 2:
            return ". ".join(sentences[:2]) + "."
        return response
    
    def _remove_exclamation_marks(self, response: str) -> str:
        """Remove exclamation marks to reduce enthusiasm."""
        return response.replace("!", ".").replace("!!", ".")
    
    def detect_multiple_messages(self, messages: list[str]) -> SocialEnergyInfo:
        """
        Detect social energy from multiple messages in conversation.
        
        Args:
            messages: List of recent messages
            
        Returns:
            SocialEnergyInfo with aggregated social energy
        """
        all_info = [self.detect(msg) for msg in messages]
        
        # Aggregate results
        mode_counts: dict[str, int] = {}
        total_intensity = 0.0
        
        for info in all_info:
            for mode in info.detected_modes:
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
            total_intensity += info.intensity
        
        if mode_counts:
            primary = max(mode_counts, key=mode_counts.get)
            avg_intensity = total_intensity / len(all_info)
            
            result = SocialEnergyInfo(
                primary_mode=primary,
                intensity=avg_intensity,
                detected_modes=list(mode_counts.keys()),
                response_style=self._styles.get(primary, self._styles["casual"]),
            )
            
            # Set special needs based on aggregated result
            if primary == "tired":
                result.needs_comfort = True
            elif primary == "stressed":
                result.needs_urgency = True
            elif primary == "social":
                result.needs_engagement = True
            elif primary == "excited":
                result.needs_celebration = True
                
            return result
        
        return SocialEnergyInfo()