from __future__ import annotations

import re

from app.nlp.slang_dictionary import SLANG_PATTERNS


def normalize_vietnamese_text(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.replace("đ", "d")
    normalized = re.sub(r"\s+", " ", normalized)
    for source, target in SLANG_PATTERNS:
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

