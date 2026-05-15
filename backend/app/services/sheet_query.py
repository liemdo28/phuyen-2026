from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any


def normalize_loose(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c)).replace("đ", "d")
    return re.sub(r"\s+", " ", ascii_text)


def extract_query_params(text: str, intent: str) -> dict[str, Any]:
    normalized = normalize_loose(text)
    params: dict[str, Any] = {"normalized_text": normalized}

    date_filter = _extract_date_filter(normalized)
    if date_filter:
        params["date_filter"] = date_filter

    if intent in {"food", "suggestion"}:
        area_filter = _extract_area_filter(normalized)
        if area_filter:
            params["area_filter"] = area_filter

    if intent in {"budget", "contribution", "packing", "expense_query"}:
        entity_filter = _extract_entity_filter(normalized)
        if entity_filter:
            params["entity_filter"] = entity_filter

    params["keywords"] = [part for part in normalized.split() if len(part) > 2][:5]
    return params


def row_matches_filter(row: dict[str, Any], needle: str) -> bool:
    haystack = " ".join(str(value or "") for value in row.values())
    return normalize_loose(needle) in normalize_loose(haystack)


def select_rows_by_filter(
    rows: list[dict[str, Any]],
    needle: str | None = None,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    filtered = rows
    if needle:
        filtered = [row for row in rows if row_matches_filter(row, needle)]
    if limit is not None:
        return filtered[:limit]
    return filtered


def _extract_date_filter(normalized: str) -> str | None:
    if "hom nay" in normalized:
        return datetime.now().strftime("%d/%m")
    if "ngay mai" in normalized:
        return (datetime.now() + timedelta(days=1)).strftime("%d/%m")
    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})\b", normalized)
    if match:
        return f"{int(match.group(1)):02d}/{int(match.group(2)):02d}"
    return None


def _extract_area_filter(normalized: str) -> str | None:
    patterns = [
        r"(?:gan|o|tai)\s+(.+)$",
        r"(?:near)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return match.group(1).strip()
    return None


def _extract_entity_filter(normalized: str) -> str | None:
    match = re.search(r"(sun village|nang ha|liem|linh|nhom lv|nhom lh|nhom cm)", normalized)
    if match:
        return match.group(1)
    return None
