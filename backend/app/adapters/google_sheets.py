from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


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
        record = {"id": f"{domain}-{len(self._memory_db.get(domain, [])) + 1}", **payload, "created_at": datetime.utcnow().isoformat()}
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
        rows[-1].update(payload)
        rows[-1]["updated_at"] = datetime.utcnow().isoformat()
        return SheetsActionResult(success=True, message=f"Updated latest {domain} record.", rows=[rows[-1]])

