"""
Conversation Merger — Phase: Human Chaos Understanding AI

Merges fragmented multi-message conversations into single coherent intents.
Handles: fragmented expense, delayed continuation, interruptions, corrections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.nlp.slang_dictionary import normalize_slang
from app.nlp.money_parser import parse_money_amount


@dataclass
class ConversationSnippet:
    text: str
    normalized: str
    timestamp: datetime
    role: str = "user"


@dataclass
class MergedIntent:
    """Result of merging fragmented conversation messages."""
    primary_type: str  # "expense", "packing", "travel", "general"
    amount: int | None = None
    category: str | None = None
    entity_name: str | None = None
    date: str | None = None
    meal: str | None = None  # "sáng", "trưa", "tối"
    food_type: str | None = None
    sentiment: str | None = None  # "positive", "negative", "neutral"
    crowd: str | None = None  # "đông", "vắng"
    items: list[str] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)
    confidence: float = 0.5  # 0.0 - 1.0
    raw_messages: list[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        if self.primary_type == "expense":
            return self.amount is not None and self.category is not None
        if self.primary_type == "packing":
            return len(self.items) > 0
        if self.primary_type == "travel":
            return self.entity_name is not None
        return False

    def soft_confirmation_text(self) -> str:
        parts = []
        if self.amount:
            amount_str = f"{self.amount // 1000}k"
            parts.append(f"{amount_str}")
        if self.category:
            parts.append(self.category)
        if self.food_type:
            parts.append(self.food_type)
        if self.meal:
            parts.append(f"bữa {self.meal}")
        if self.sentiment == "positive":
            parts.append("😄")
        elif self.sentiment == "negative":
            parts.append("😐")
        if not parts:
            return ""
        return " ".join(parts)


CORRECTION_PATTERNS = [
    "nhầm", "sửa lại", "à nhầm", "không", "sai", "đợi", "chờ",
    "à mà", "ý quên", "quên", "thêm",
]

INTERRUPTION_PATTERNS = [
    "trời", "nóng", "mệt", "bạn ơi", "mà", "nhỉ", "đúng không",
    "hay là", "hay", "hay sao", "không biết", "ở đâu",
]

EXPENSE_INDICATORS = [
    "k", "tr", "triệu", "củ", "đồng", "bill", "tiền", "thanh toán",
    "trả", "chỉ", "hết", "vừa",
]

PACKING_INDICATORS = [
    "đã đem", "mang theo", "đem", "quên", "chưa", "mang", "thêm",
    "ô", "kem", "thuốc", "áo", "quần", "vali", "đồ",
]


class ConversationMerger:
    """
    Merges fragmented user messages into coherent intents.

    Example:
      "500k" + "hải sản" + "ăn trưa" + "đắt mà ngon"
      → MergedIntent(amount=500000, category="food", food_type="seafood",
                     meal="trưa", sentiment="positive")
    """

    def __init__(self) -> None:
        self._sessions: dict[int, list[ConversationSnippet]] = {}  # chat_id -> snippets
        self._session_ttl = timedelta(minutes=10)

    def add_message(self, chat_id: int, text: str, timestamp: datetime) -> None:
        """Add a user message to the conversation session."""
        if chat_id not in self._sessions:
            self._sessions[chat_id] = []
        
        # Normalize slang
        normalized = normalize_slang(text)
        
        # Clean up old snippets
        cutoff = timestamp - self._session_ttl
        self._sessions[chat_id] = [
            s for s in self._sessions[chat_id]
            if s.timestamp > cutoff
        ]
        
        self._sessions[chat_id].append(ConversationSnippet(
            text=text,
            normalized=normalized,
            timestamp=timestamp,
            role="user",
        ))

    def merge(self, chat_id: int, current_text: str, now: datetime) -> MergedIntent:
        """
        Merge current message with recent conversation history into a single intent.
        """
        # Add current message
        self.add_message(chat_id, current_text, now)
        
        snippets = self._sessions.get(chat_id, [])
        recent = [s for s in snippets if now - s.timestamp < self._session_ttl]
        
        # Build merged result
        merged = MergedIntent(raw_messages=[s.text for s in recent])
        
        # Process each snippet
        for snippet in recent:
            text = snippet.text
            norm = snippet.normalized
            
            # Check for correction signals
            has_correction = any(p in norm for p in CORRECTION_PATTERNS)
            if has_correction and merged.amount:
                merged.corrections.append(f"old:{merged.amount}")
            
            # Check for interruption (not expense/packing related)
            is_interrupt = any(p in norm for p in INTERRUPTION_PATTERNS) and not any(
                e in norm for e in EXPENSE_INDICATORS + PACKING_INDICATORS
            )
            
            # Extract amount
            amount = parse_money_amount(text)
            if amount and amount > 0:
                merged.amount = amount
            
            # Detect type
            if any(p in norm for p in EXPENSE_INDICATORS):
                merged.primary_type = "expense"
            elif any(p in norm for p in PACKING_INDICATORS):
                merged.primary_type = "packing"
            elif any(p in norm for p in ["quán", "đi đâu", "bãi", "mũi", "vịnh", "ở đâu", "gợi"]):
                merged.primary_type = "travel"
            else:
                merged.primary_type = "general"
            
            # Detect meal time
            if any(m in norm for m in ["sáng", "ăn sáng", "breakfast"]):
                merged.meal = "sáng"
            elif any(m in norm for m in ["trưa", "ăn trưa", "lunch", "trua"]):
                merged.meal = "trưa"
            elif any(m in norm for m in ["tối", "ăn tối", "dinner", "toi"]):
                merged.meal = "tối"
            
            # Detect food type
            if any(f in norm for f in ["hải sản", "seafood", "hai san", "tôm", "mực", "cá"]):
                merged.food_type = "hải sản"
            elif any(f in norm for f in ["bún", "phở", "bánh", "bún đậu"]):
                merged.food_type = "đặc sản"
            elif any(f in norm for f in ["cafe", "cà phê", "cốc"]):
                merged.food_type = "cafe"
            elif any(f in norm for f in ["bữa", "ăn vặt", "snack"]):
                merged.food_type = "snack"
            
            # Detect sentiment
            if any(s in norm for s in ["ngon", "tuyệt", "đẹp", "vui", "wow", "hài lòng", "đáng"]):
                merged.sentiment = "positive"
            elif any(s in norm for s in ["đắt", "đông", "chờ", "mệt", "chán", "dở"]):
                merged.sentiment = "negative"
            
            # Detect crowd
            if any(c in norm for c in ["đông", "đông ghê", "đông nghịt", "kẹt"]):
                merged.crowd = "đông"
            elif any(c in norm for c in ["vắng", "yên", "chill", "ít người"]):
                merged.crowd = "vắng"
            
            # Detect packing items
            for item in ["ô", "kem chống nắng", "thuốc hạ sốt", "áo ấm", "dầu gội", "sữa tắm", "kem", "thuốc"]:
                if item in norm:
                    merged.items.append(item)
        
        # Compute confidence
        if merged.amount and merged.category:
            merged.confidence = 1.0
        elif merged.amount and merged.primary_type == "expense":
            merged.confidence = 0.7
        elif merged.items:
            merged.confidence = 0.8
        
        return merged

    def clear_session(self, chat_id: int) -> None:
        """Clear conversation session after intent is processed."""
        if chat_id in self._sessions:
            self._sessions[chat_id] = []