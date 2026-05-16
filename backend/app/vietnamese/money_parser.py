"""Vietnamese Money Parser and Normalization System.

Handles:
- Money shorthand parsing (xị, củ, chai, vé, triệu, tr, k)
- Money normalization
- Currency format detection
- Price range parsing
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# Money unit multipliers
MONEY_MULTIPLIERS = {
    # Main units
    "nghìn": 1_000,
    "ng": 1_000,
    "k": 1_000,
    "n": 1_000,
    "triệu": 1_000_000,
    "tr": 1_000_000,
    "tỷ": 1_000_000_000,
    "tỉ": 1_000_000_000,
    "t": 1_000_000_000,
    
    # Colloquial units
    "củ": 1_000_000,
    "xị": 100_000,
    "chai": 100_000,
    "vé": 100_000,
    "lít": 100_000,
    "cuốn": 100_000,
    "túi": 100_000,
    "bạc": 1_000_000,
    "vàng": 10_000_000,
}

# Unit aliases
UNIT_ALIASES = {
    "đ": "vnd",
    "d": "vnd",
    "vnd": "vnd",
    "usd": "usd",
    "$": "usd",
    "dollar": "usd",
    "đô": "usd",
}


@dataclass
class MoneyInfo:
    """Information about parsed money."""
    raw: str
    normalized_amount: Optional[int] = None
    currency: str = "vnd"
    unit_multiplier: Optional[int] = None
    is_price_range: bool = False
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    confidence: float = 1.0


class MoneyParser:
    """Parses and normalizes Vietnamese money expressions."""
    
    def __init__(self) -> None:
        self._multipliers = MONEY_MULTIPLIERS
        self._unit_aliases = UNIT_ALIASES
        
        # Regex patterns for money expressions
        self._patterns = [
            # Pattern: number + unit (e.g., "2tr6", "2tr", "500k")
            r"(\d+(?:[.,]\d+)?)\s*([a-zA-Zạăâàáảãảặẳẵẩđêèéẻẽẹệỉịìíỉọỏõỏơờóộổỗôồốổớữừưựửựùúủụưứừửữứừỹýỳỷỵ]+)",
            # Pattern: number with dots (e.g., "2.000.000")
            r"(\d{1,3}(?:[.,]\d{3})+)",
            # Pattern: short numbers with suffix (e.g., "2t6")
            r"(\d+)t(\d+)",
            # Pattern: explicit number (e.g., "2000000")
            r"(\d{6,12})",
        ]
    
    def parse(self, text: str) -> list[MoneyInfo]:
        """
        Parse money expressions from text.
        
        Args:
            text: The text containing money expressions
            
        Returns:
            List of MoneyInfo with parsed amounts
        """
        results = []
        text_lower = text.lower()
        
        # Track what parts of text we've already matched to avoid duplicates
        matched_ranges = set()
        
        # Find all money patterns
        # Pattern: 2tr6 (means 2 triệu 600 = 2,600,000) - NO SPACE between tr and digits
        tr_pattern = r"(\d+)tr(\d+)?"
        for match in re.finditer(tr_pattern, text_lower):
            start, end = match.span()
            # Skip if this overlaps with already matched range
            if any(start < m_end and end > m_start for m_start, m_end in matched_ranges):
                continue
            matched_ranges.add((start, end))
            
            info = MoneyInfo(raw=match.group(0))
            base = int(match.group(1)) * 1_000_000
            if match.group(2):
                # If there's digits after tr, they represent hundreds of thousands
                base += int(match.group(2)) * 100_000
            info.normalized_amount = base
            info.unit_multiplier = 1_000_000
            info.currency = "vnd"
            results.append(info)
        
        # Pattern: 2tr or 2 tr (means 2 triệu) - with space after tr
        tr_space_pattern = r"(\d+)\s+tr\b"
        for match in re.finditer(tr_space_pattern, text_lower):
            start, end = match.span()
            if any(start < m_end and end > m_start for m_start, m_end in matched_ranges):
                continue
            matched_ranges.add((start, end))
            
            info = MoneyInfo(raw=match.group(0))
            info.normalized_amount = int(match.group(1)) * 1_000_000
            info.unit_multiplier = 1_000_000
            info.currency = "vnd"
            results.append(info)
        
        # Pattern: number + unit (e.g., "2 củ", "500k", "3 triệu")
        # Exclude "tr" to avoid double-matching
        unit_pattern = r"(\d+(?:[.,]\d+)?)\s*(củ|xị|chai|vé|lít|cuốn|túi|triệu|nghìn|ng|tỷ|tỉ|k|n)\b"
        for match in re.finditer(unit_pattern, text_lower):
            start, end = match.span()
            if any(start < m_end and end > m_start for m_start, m_end in matched_ranges):
                continue
            matched_ranges.add((start, end))
            
            info = MoneyInfo(raw=match.group(0))
            num = float(match.group(1).replace(",", "."))
            unit = match.group(2)
            
            if unit in self._multipliers:
                info.normalized_amount = int(num * self._multipliers[unit])
                info.unit_multiplier = self._multipliers[unit]
            else:
                info.normalized_amount = int(num)
            
            info.currency = "vnd"
            results.append(info)
        
        # Pattern: numbers with dots (e.g., "2.000.000")
        dot_pattern = r"\d{1,3}(?:[.,]\d{3})+"
        for match in re.finditer(dot_pattern, text_lower):
            info = MoneyInfo(raw=match.group(0))
            amount_str = match.group(0).replace(".", "").replace(",", ".")
            try:
                info.normalized_amount = int(float(amount_str))
            except ValueError:
                continue
            info.currency = "vnd"
            results.append(info)
        
        # Pattern: price range (e.g., "2-3tr", "200k-500k")
        range_pattern = r"(\d+(?:[.,]\d+)?)\s*(tr|k|củ|xị)?\s*[-–—to]+\s*(\d+(?:[.,]\d+)?)\s*(tr|k|củ|xị)?"
        for match in re.finditer(range_pattern, text_lower):
            info = MoneyInfo(raw=match.group(0))
            info.is_price_range = True
            
            # Parse min amount
            min_num = float(match.group(1).replace(",", "."))
            min_unit = match.group(2)
            if min_unit and min_unit in self._multipliers:
                info.min_amount = int(min_num * self._multipliers[min_unit])
            else:
                info.min_amount = int(min_num)
            
            # Parse max amount
            max_num = float(match.group(3).replace(",", "."))
            max_unit = match.group(4)
            if max_unit and max_unit in self._multipliers:
                info.max_amount = int(max_num * self._multipliers[max_unit])
            else:
                if max_unit in self._multipliers:
                    info.max_amount = int(max_num * self._multipliers[max_unit])
                else:
                    info.max_amount = int(max_num)
            
            info.currency = "vnd"
            results.append(info)
        
        # Pattern: short number (6-12 digits)
        short_pattern = r"\b(\d{6,12})\b"
        for match in re.finditer(short_pattern, text_lower):
            info = MoneyInfo(raw=match.group(0))
            try:
                info.normalized_amount = int(match.group(1))
                info.currency = "vnd"
                results.append(info)
            except ValueError:
                continue
        
        return results
    
    def normalize(self, text: str) -> str:
        """
        Normalize money expressions in text to readable format.
        
        Args:
            text: The text containing money expressions
            
        Returns:
            Text with normalized money expressions
        """
        results = self.parse(text)
        normalized = text
        
        for info in results:
            if info.normalized_amount is not None:
                formatted = self._format_amount(info.normalized_amount)
                normalized = normalized.replace(info.raw, formatted)
        
        return normalized
    
    def _format_amount(self, amount: int) -> str:
        """Format amount with Vietnamese number format."""
        if amount >= 1_000_000_000:
            return f"{amount:,}".replace(",", ".") + "đ"
        elif amount >= 1_000_000:
            return f"{amount:,}".replace(",", ".") + "đ"
        elif amount >= 1_000:
            return f"{amount:,}".replace(",", ".") + "đ"
        return f"{amount}đ"
    
    def parse_single(self, text: str) -> Optional[MoneyInfo]:
        """Parse a single money expression."""
        results = self.parse(text)
        if results:
            # Return the most confident result
            return max(results, key=lambda x: x.confidence)
        return None
    
    def is_money(self, text: str) -> bool:
        """Check if text contains money expression."""
        return len(self.parse(text)) > 0