"""Vietnamese Contextual Short Phrase Resolution System.

Supports:
- Active context memory
- Reference resolution (cái kia, như cũ, etc.)
- Topic threading
- Deixis resolution
- Ellipsis handling
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# Common short phrases and their interpretations
SHORT_PHRASE_MAP = {
    # Demonstratives and references
    "cái kia": "điều đó",
    "cái này": "điều này",
    "cái gì": "điều gì",
    "chỗ kia": "ở đó",
    "chỗ này": "ở đây",
    "hôm kia": "ngày hôm trước",
    "hôm nọ": "ngày gần đây",
    "hôm qua": "ngày hôm trước",
    "ngày kia": "ngày mai",
    "lúc nãy": "vừa rồi",
    "tí nữa": "sau một chút",
    "một lát": "sau một chút",
    "vậy đi": "đồng ý",
    "thế đi": "đồng ý",
    "ổn đi": "đồng ý",
    "ok đi": "đồng ý",
    "thêm luôn": "tiếp tục",
    "nữa đi": "tiếp tục",
    "nữa không": "hỏi tiếp tục",
    "lần nữa": "lặp lại",
    "lại đi": "yêu cầu lặp lại",
    "làm lại": "yêu cầu lặp lại",
    "quán hôm qua": "quán đã đề cập",
    "như cũ": "giống trước",
    "như trước": "giống trước",
    "như trẻ": "giống trước",
    "bình thường": "không có gì đặc biệt",
    "bình thường thôi": "không có gì đặc biệt",
    "cũng được": "chấp nhận được",
    "cũng ok": "chấp nhận được",
    "cũng ổn": "chấp nhận được",
    "được rồi": "chấp nhận",
    "ok rồi": "chấp nhận",
    "ổn rồi": "chấp nhận",
    "xong rồi": "hoàn thành",
    "xong đi": "yêu cầu hoàn thành",
    "đi thôi": "bắt đầu",
    "đi nào": "bắt đầu",
    "nào": "kêu gọi hành động",
    "thôi": "dừng lại",
    "thôi không": "từ chối",
    "không thôi": "từ chối",
}


# Time-related short phrases
TIME_SHORTCUTS = {
    "bây giờ": "hiện tại",
    "bây": "bây giờ",
    "giờ": "bây giờ",
    "hôm nay": "ngày hiện tại",
    "nay": "hôm nay",
    "tối nay": "tối hôm nay",
    "sáng nay": "sáng hôm nay",
    "trưa nay": "trưa hôm nay",
    "chiều nay": "chiều hôm nay",
    "ngày mai": "ngày tới",
    "ngày mốt": "ngày sau ngày mai",
    "tuần này": "tuần hiện tại",
    "tuần sau": "tuần tới",
    "tuần trước": "tuần trước",
    "tháng này": "tháng hiện tại",
    "tháng sau": "tháng tới",
    "năm nay": "năm hiện tại",
    "sang năm": "năm tới",
}


# Location-related short phrases
LOCATION_SHORTCUTS = {
    "đây": "vị trí hiện tại",
    "đó": "vị trí kia",
    "kia": "vị trí xa",
    "ở đây": "vị trí hiện tại",
    "ở đó": "vị trí kia",
    "ở kia": "vị trí xa",
    "tại đây": "vị trí hiện tại",
    "tại đó": "vị trí kia",
    "quanh đây": "khu vực gần đây",
    "gần đây": "khu vực gần",
    "xa đây": "khu vực xa",
    "ở đây": "vị trí hiện tại",
}


@dataclass
class ContextMemory:
    """Memory of conversation context."""
    mentioned_locations: list[str] = field(default_factory=list)
    mentioned_foods: list[str] = field(default_factory=list)
    mentioned_people: list[str] = field(default_factory=list)
    mentioned_times: list[str] = field(default_factory=list)
    last_topic: str = ""
    last_location: str = ""
    last_action: str = ""
    user_preferences: dict[str, str] = field(default_factory=dict)
    
    def add_location(self, location: str) -> None:
        if location not in self.mentioned_locations:
            self.mentioned_locations.append(location)
            self.last_location = location
    
    def add_food(self, food: str) -> None:
        if food not in self.mentioned_foods:
            self.mentioned_foods.append(food)
    
    def add_person(self, person: str) -> None:
        if person not in self.mentioned_people:
            self.mentioned_people.append(person)
    
    def set_topic(self, topic: str) -> None:
        self.last_topic = topic
    
    def set_action(self, action: str) -> None:
        self.last_action = action


@dataclass
class ContextualInfo:
    """Information about contextual resolution."""
    original: str = ""
    resolved: str = ""
    resolved_with_context: bool = False
    context_used: Optional[str] = None
    is_reference: bool = False
    reference_type: str = ""  # location, time, person, object, action


class ContextualResolver:
    """Resolves contextual references in Vietnamese text."""
    
    def __init__(self) -> None:
        self._short_phrases = SHORT_PHRASE_MAP
        self._time_shortcuts = TIME_SHORTCUTS
        self._location_shortcuts = LOCATION_SHORTCUTS
        self._memory = ContextMemory()
    
    def resolve(self, text: str, context: Optional[ContextMemory] = None) -> tuple[str, ContextualInfo]:
        """
        Resolve contextual references in text.
        
        Args:
            text: The text to resolve
            context: Optional context memory for disambiguation
            
        Returns:
            Tuple of (resolved_text, ContextualInfo)
        """
        text_lower = text.lower().strip()
        info = ContextualInfo()
        info.original = text
        
        memory = context or self._memory
        
        resolved = text
        
        # Check for short phrases
        for phrase, resolution in self._short_phrases.items():
            if phrase in text_lower:
                resolved = resolved.replace(phrase, resolution)
                info.is_reference = True
                info.reference_type = "short_phrase"
                info.context_used = phrase
        
        # Check for time shortcuts
        for phrase, resolution in self._time_shortcuts.items():
            if phrase in text_lower:
                resolved = resolved.replace(phrase, resolution)
                info.is_reference = True
                info.reference_type = "time"
                info.context_used = phrase
        
        # Check for location shortcuts
        for phrase, resolution in self._location_shortcuts.items():
            if phrase in text_lower:
                resolved = resolved.replace(phrase, resolution)
                info.is_reference = True
                info.reference_type = "location"
                info.context_used = phrase
        
        # Resolve demonstrative references using context
        resolved, info = self._resolve_demonstratives(resolved, memory, info)
        
        # Resolve pronoun references using context
        resolved, info = self._resolve_pronoun_references(resolved, memory, info)
        
        info.resolved = resolved
        
        if resolved != text:
            info.resolved_with_context = True
        
        return resolved, info
    
    def _resolve_demonstratives(
        self, 
        text: str, 
        memory: ContextMemory,
        info: ContextualInfo
    ) -> tuple[str, ContextualInfo]:
        """Resolve demonstrative references using context."""
        text_lower = text.lower()
        
        # Resolve "cái đó" type references
        if "cái đó" in text_lower or "cái kia" in text_lower:
            if memory.last_location:
                text = text.replace("cái đó", memory.last_location)
                text = text.replace("cái kia", memory.last_location)
                info.is_reference = True
                info.reference_type = "object"
                info.context_used = "last_location"
        
        # Resolve "chỗ đó" type references
        if "chỗ đó" in text_lower or "chỗ kia" in text_lower:
            if memory.last_location:
                text = text.replace("chỗ đó", memory.last_location)
                text = text.replace("chỗ kia", memory.last_location)
                info.is_reference = True
                info.reference_type = "location"
                info.context_used = "last_location"
        
        # Resolve "người đó" type references
        if "người đó" in text_lower or "người kia" in text_lower:
            if memory.mentioned_people:
                last_person = memory.mentioned_people[-1]
                text = text.replace("người đó", last_person)
                text = text.replace("người kia", last_person)
                info.is_reference = True
                info.reference_type = "person"
                info.context_used = "mentioned_people"
        
        return text, info
    
    def _resolve_pronoun_references(
        self,
        text: str,
        memory: ContextMemory,
        info: ContextualInfo
    ) -> tuple[str, ContextualInfo]:
        """Resolve pronoun references using context."""
        text_lower = text.lower()
        
        # Resolve "như cũ" / "như trước"
        if "như cũ" in text_lower or "như trước" in text_lower:
            if memory.last_location:
                text = text.replace("như cũ", memory.last_location)
                text = text.replace("như trước", memory.last_location)
                info.is_reference = True
                info.reference_type = "location"
                info.context_used = "last_location"
        
        # Resolve ellipsis and incomplete sentences
        if text.endswith("...") or text.endswith("…"):
            info.is_reference = True
            info.reference_type = "ellipsis"
            # Ellipsis usually indicates continuation or trailing off
            # This could be expanded based on context
        
        return text, info
    
    def update_memory(self, text: str, entities: Optional[dict] = None) -> None:
        """Update context memory based on text and extracted entities."""
        text_lower = text.lower()
        
        # Update with extracted entities
        if entities:
            if "location" in entities:
                self._memory.add_location(entities["location"])
            if "food" in entities:
                self._memory.add_food(entities["food"])
            if "person" in entities:
                self._memory.add_person(entities["person"])
            if "time" in entities:
                self._memory.mentioned_times.append(entities["time"])
        
        # Auto-detect locations in text (simple pattern matching)
        location_indicators = ["ở", "tại", "đến", "ra", "vào", "đi"]
        for indicator in location_indicators:
            if indicator in text_lower:
                # This is a simplified detection - in production, use NER
                pass
        
        # Update last topic based on keywords
        if any(word in text_lower for word in ["quán", "nhà hàng", "cửa hàng", "shop"]):
            self._memory.set_topic("food_place")
        elif any(word in text_lower for word in ["đi", "đến", "du lịch", "tour"]):
            self._memory.set_topic("travel")
        elif any(word in text_lower for word in ["ăn", "uống", "món", "món ăn"]):
            self._memory.set_topic("food")
    
    def get_memory(self) -> ContextMemory:
        """Get current context memory."""
        return self._memory
    
    def set_memory(self, memory: ContextMemory) -> None:
        """Set context memory."""
        self._memory = memory
    
    def clear_memory(self) -> None:
        """Clear context memory."""
        self._memory = ContextMemory()