from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.services.sheet_mapping import get_sheet_mapping


@dataclass
class SheetsActionResult:
    success: bool
    message: str
    rows: list[dict[str, Any]] = field(default_factory=list)


class GoogleSheetsAdapter:
    def __init__(self) -> None:
        self._memory_db: dict[str, list[dict[str, Any]]] = {
            "expenses": [],
            "tasks": [],
            "inventory": [],
            "revenue": [],
            "travel": [],
            "crm": [],
            "notes": [],
        }

    async def create_record(self, domain: str, payload: dict[str, Any]) -> SheetsActionResult:
        mapping = get_sheet_mapping(domain)
        record = {
            "id": f"{domain}-{len(self._memory_db.get(domain, [])) + 1}",
            "sheet_name": mapping.sheet_name if mapping else domain,
            **payload,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._memory_db.setdefault(domain, []).append(record)
        return SheetsActionResult(success=True, message=f"Created {domain} record.", rows=[record])

    async def query_records(self, domain: str, filters: dict[str, Any]) -> SheetsActionResult:
        rows = self._memory_db.get(domain, [])
        filtered = []
        for row in rows:
            if all(str(row.get(key, "")).lower() == str(value).lower() for key, value in filters.items() if value not in (None, "")):
                filtered.append(row)
        return SheetsActionResult(success=True, message=f"Found {len(filtered)} {domain} record(s).", rows=filtered)

    async def update_latest_record(self, domain: str, payload: dict[str, Any]) -> SheetsActionResult:
        rows = self._memory_db.get(domain, [])
        if not rows:
            return SheetsActionResult(success=False, message=f"No {domain} records available to update.")
        target = self._resolve_target_row(rows, payload)
        if not target:
            return SheetsActionResult(success=False, message=f"No {domain} record matched the requested update.")
        target.update(payload)
        target["updated_at"] = datetime.utcnow().isoformat()
        return SheetsActionResult(success=True, message=f"Updated latest {domain} record.", rows=[target])

    def _resolve_target_row(self, rows: list[dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any] | None:
        entity_reference = str(payload.get("entity_reference") or "").lower()
        entity_name = str(payload.get("entity_name") or "").lower()
        if entity_reference in {"cái hôm qua", "hôm qua", "cái trên", "task kia", "task này", "bill này", "khoản đó"}:
            return rows[-1]
        if entity_name:
            for row in reversed(rows):
                if entity_name in str(row.get("entity_name", "")).lower():
                    return row
        return rows[-1]
