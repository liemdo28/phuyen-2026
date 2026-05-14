from __future__ import annotations

import re


def parse_money_amount(text: str) -> int | None:
    normalized = text.lower().strip()
    compact = normalized.replace(" ", "")

    billion_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(ty|tỷ)\b(?:\s*(\d{1,3}))?", normalized, re.IGNORECASE)
    if billion_match:
        major = float(billion_match.group(1).replace(",", "."))
        minor = billion_match.group(3)
        amount = int(round(major * 1_000_000_000))
        if minor:
            amount += int(minor.ljust(3, "0")[:3]) * 1_000_000
        return amount

    mixed_million_match = re.search(r"(\d+)\s*(?:tr|triệu|trieu|cu|củ)\s*(\d{1,3})(?!\d)", normalized, re.IGNORECASE)
    if mixed_million_match:
        major = int(mixed_million_match.group(1))
        minor = int(mixed_million_match.group(2).ljust(3, "0")[:3])
        return major * 1_000_000 + minor * 1_000

    compact_million_match = re.search(r"(\d+)tr(\d{1,3})(?!\d)", compact, re.IGNORECASE)
    if compact_million_match:
        major = int(compact_million_match.group(1))
        minor = int(compact_million_match.group(2).ljust(3, "0")[:3])
        return major * 1_000_000 + minor * 1_000

    standard_patterns = [
        (re.compile(r"(\d+(?:[\.,]\d+)?)\s*(tr|triệu|trieu|cu|củ)\b", re.IGNORECASE), 1_000_000),
        (re.compile(r"(\d+(?:[\.,]\d+)?)\s*(k|nghin|nghìn)\b", re.IGNORECASE), 1_000),
    ]
    for pattern, multiplier in standard_patterns:
        found = pattern.search(normalized)
        if found:
            value = float(found.group(1).replace(",", "."))
            return int(round(value * multiplier))

    raw_digits = re.search(r"\b(\d{4,12})\b", normalized)
    if raw_digits:
        return int(raw_digits.group(1))
    return None


def strip_money_phrases(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"\d+\s*(?:tr|triệu|trieu|cu|củ)\s*\d{1,3}(?!\d)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\d+tr\d{1,3}(?!\d)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\d+(?:[\.,]\d+)?\s*(?:ty|tỷ)(?:\s*\d{1,3})?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\d+(?:[\.,]\d+)?\s*(?:tr|triệu|trieu|cu|củ|k|nghin|nghìn)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d{4,12}\b", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip(" -,:")

