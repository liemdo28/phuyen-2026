from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.adapters.sheets_api_client import SheetsApiClient, SheetsApiError
from app.services.sheet_mapping import get_sheet_mapping

logger = logging.getLogger(__name__)


@dataclass
class SheetsActionResult:
    success: bool
    message: str
    rows: list[dict[str, Any]] = field(default_factory=list)


class GoogleSheetsAdapter:
    """
    Google Sheets adapter using SheetsApiClient for real Google Sheets operations.
    Falls back to in-memory RAM for domains not yet mapped to the API.
    """

    def __init__(self) -> None:
        self._api = SheetsApiClient()
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

        try:
            if domain == "expenses":
                await self._api.write_expense(record)
            elif domain == "inventory":
                await self._api.write_packing(record)
            elif domain == "contributions":
                await self._api.write_contribution(record)
            elif domain == "restaurants":
                await self._api.write_restaurant(record)
            else:
                self._memory_db.setdefault(domain, []).append(record)
        except SheetsApiError as exc:
            logger.warning(
                "Sheets API write failed for domain=%s: %s. Falling back to RAM.",
                domain, exc,
            )
            self._memory_db.setdefault(domain, []).append(record)
            return SheetsActionResult(
                success=True,
                message=f"Lưu vào RAM (API lỗi: {exc}). Sẽ sync lại sau.",
                rows=[record],
            )

        self._memory_db.setdefault(domain, []).append(record)
        return SheetsActionResult(success=True, message="Đã lưu vào Google Sheet.", rows=[record])

    async def query_records(self, domain: str, filters: dict[str, Any]) -> SheetsActionResult:
        try:
            if domain == "expenses":
                result = await self._api.expenses_recent(limit=20)
                rows = result.get("rows", [])
            elif domain == "inventory":
                result = await self._api.packing_status()
                rows = result.get("rows", [])
            elif domain == "contributions":
                result = await self._api.contributions()
                rows = result.get("rows", [])
            elif domain == "restaurants":
                result = await self._api.restaurants()
                rows = result.get("rows", [])
            elif domain == "members":
                result = await self._api.members()
                rows = result.get("rows", [])
            else:
                rows = self._memory_db.get(domain, [])

            filtered = [
                row
                for row in rows
                if all(
                    str(row.get(key, "")).lower() == str(value).lower()
                    for key, value in filters.items()
                    if value not in (None, "")
                )
            ]
            return SheetsActionResult(
                success=True,
                message=f"Tìm thấy {len(filtered)} bản ghi.",
                rows=filtered,
            )
        except SheetsApiError as exc:
            logger.warning(
                "Sheets API query failed for domain=%s: %s. Falling back to RAM.",
                domain, exc,
            )
            rows = self._memory_db.get(domain, [])
            return SheetsActionResult(
                success=True,
                message="Đọc từ RAM (API lỗi).",
                rows=rows,
            )

    async def update_latest_record(self, domain: str, payload: dict[str, Any]) -> SheetsActionResult:
        rows = self._memory_db.get(domain, [])
        if not rows:
            return SheetsActionResult(
                success=False,
                message="Không có bản ghi nào để cập nhật.",
            )
        target = self._resolve_target_row(rows, payload)
        if not target:
            return SheetsActionResult(
                success=False,
                message="Không tìm thấy bản ghi phù hợp để cập nhật.",
            )
        target.update(payload)
        target["updated_at"] = datetime.utcnow().isoformat()
        return SheetsActionResult(
            success=True,
            message="Đã cập nhật bản ghi.",
            rows=[target],
        )

    def _resolve_target_row(
        self, rows: list[dict[str, Any]], payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        entity_reference = str(payload.get("entity_reference") or "").lower()
        entity_name = str(payload.get("entity_name") or "").lower()
        if entity_reference in {
            "cái hôm qua", "hôm qua", "cái trên", "task kia", "task này",
            "bill này", "khoản đó",
        }:
            return rows[-1]
        if entity_name:
            for row in reversed(rows):
                if entity_name in str(row.get("entity_name", "")).lower():
                    return row
        return rows[-1]