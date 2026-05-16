from __future__ import annotations

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from app.adapters.sheet_cache import SheetCache
from app.adapters.sheets_api_client import SheetsApiClient, SheetsApiError
from app.core.config import settings
from app.services.sheet_mapping import get_sheet_mapping

logger = logging.getLogger(__name__)

_SPREADSHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")
_LINE_BASED_SHEETS = {"Gợi Ý Lịch Trình", "Tổng Hợp"}
_HEADER_LABELS = [
    "STT",
    "Tên quán",
    "Khu vực",
    "Loại",
    "Giá (k/ng)",
    "Lat",
    "Lon",
    "Đường về",
    "Ghi chú",
    "Day",
    "Date",
    "From",
    "To",
    "Expense",
    "Activity",
    "Destination",
    "Note",
    "Ngày",
    "Thời tiết",
    "Tmax",
    "Tmin",
    "Mưa (mm)",
    "Gió (km/h)",
    "UV",
    "Đánh giá",
    "Đồ vật",
    "Nhóm phụ trách",
    "Số lượng",
    "Đã đem",
    "Nhóm",
    "Đã góp (VNĐ)",
    "Trạng thái",
    "Khoản Chi",
    "Danh Mục",
    "Số Tiền (VNĐ)",
    "Nhóm Trả",
    "Ghi Chú 1",
    "Ghi Chú 2",
    "Mục",
    "Nội dung",
    "Chi tiết",
    "Tạm tính",
    "Thực tính",
    "Ứng trước",
]


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

    _shared_cache: SheetCache | None = None

    def __init__(self) -> None:
        self._api = SheetsApiClient()
        if GoogleSheetsAdapter._shared_cache is None:
            GoogleSheetsAdapter._shared_cache = SheetCache(
                ttl_seconds=settings.sheet_cache_ttl_seconds
            )
        self._cache = GoogleSheetsAdapter._shared_cache
        self._timeout = httpx.Timeout(20.0, connect=10.0)
        self._memory_db: dict[str, list[dict[str, Any]]] = {
            "expenses": [],
            "tasks": [],
            "inventory": [],
            "revenue": [],
            "travel": [],
            "crm": [],
            "notes": [],
        }

    async def read_sheet(self, sheet_name: str) -> list[dict[str, Any]]:
        spreadsheet_id = self._spreadsheet_id()
        if not spreadsheet_id:
            raise SheetsApiError(
                "Chưa cấu hình DEFAULT_SPREADSHEET_ID / DEFAULT_SPREADSHEET_URL trên môi trường deploy."
            )

        url = (
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq"
            f"?tqx=out:csv&sheet={quote(sheet_name)}"
        )
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SheetsApiError(f"Không đọc được tab {sheet_name}: {exc}") from exc

        text = response.text
        if not text.strip():
            return []
        matrix = self._parse_csv_matrix(text)
        return self._rows_from_matrix(sheet_name, matrix)

    async def read_sheet_cached(self, sheet_name: str) -> list[dict[str, Any]]:
        data, _ = await self.read_sheet_cached_with_meta(sheet_name)
        return data

    async def read_sheet_cached_with_meta(
        self, sheet_name: str
    ) -> tuple[list[dict[str, Any]], bool]:
        cache_key = f"sheet:{self._spreadsheet_id()}:{sheet_name}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached, True
        data = await self.read_sheet(sheet_name)
        self._cache.set(cache_key, data)
        return data, False

    def invalidate_cache(self, key: str | None = None) -> None:
        self._cache.invalidate(key)

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

    def _spreadsheet_id(self) -> str:
        if settings.default_spreadsheet_id:
            return settings.default_spreadsheet_id.strip()
        if settings.default_spreadsheet_url:
            match = _SPREADSHEET_ID_RE.search(settings.default_spreadsheet_url)
            if match:
                return match.group(1)
        return ""

    def _parse_csv_matrix(self, text: str) -> list[list[str]]:
        reader = csv.reader(io.StringIO(text))
        return [[cell.strip() for cell in row] for row in reader]

    def _rows_from_matrix(
        self, sheet_name: str, matrix: list[list[str]]
    ) -> list[dict[str, Any]]:
        if sheet_name == "Tổng Chi phí":
            return self._parse_budget_sheet(matrix)
        if sheet_name in _LINE_BASED_SHEETS:
            return self._parse_line_sheet(matrix)

        header_idx, headers = self._discover_headers(matrix)
        if headers is None:
            return self._parse_line_sheet(matrix)

        rows: list[dict[str, Any]] = []
        for raw_row in matrix[header_idx + 1 :]:
            if not any(cell.strip() for cell in raw_row):
                continue
            normalized = list(raw_row) + [""] * (len(headers) - len(raw_row))
            row = {
                header: value
                for header, value in zip(headers, normalized)
                if header and (value or header in {"Đã đem"})
            }
            if row:
                rows.append(row)
        return rows

    def _discover_headers(
        self, matrix: list[list[str]]
    ) -> tuple[int, list[str] | None]:
        best_idx = -1
        best_headers: list[str] | None = None
        best_score = 0

        for idx, row in enumerate(matrix[:6]):
            headers = [self._normalize_header_cell(cell, pos) for pos, cell in enumerate(row)]
            score = sum(
                1
                for header in headers
                if header and not header.startswith("col_")
            )
            if score > best_score:
                best_idx = idx
                best_headers = headers
                best_score = score

        if best_headers is None or best_score < 2:
            return 0, None
        return best_idx, best_headers

    def _normalize_header_cell(self, cell: str, pos: int) -> str:
        raw = (cell or "").strip()
        if not raw:
            return f"col_{pos}"
        lowered = raw.lower()
        for label in _HEADER_LABELS:
            if label.lower() in lowered:
                return label
        return raw

    def _parse_line_sheet(self, matrix: list[list[str]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for raw_row in matrix:
            values = [cell.strip() for cell in raw_row if cell.strip()]
            if not values:
                continue
            rows.append({"line": " ".join(values)})
        return rows

    def _parse_budget_sheet(self, matrix: list[list[str]]) -> list[dict[str, Any]]:
        metadata: dict[str, str] = {}
        metadata_rows = matrix[:8]
        for row in metadata_rows:
            values = [cell.strip() for cell in row if cell.strip()]
            if not values:
                continue
            if len(values) >= 2:
                metadata[values[0].rstrip(":")] = values[1]
            elif len(values) == 1:
                metadata[f"meta_{len(metadata)}"] = values[0]

        header_idx = 8 if len(matrix) > 8 else 0
        headers = [
            self._normalize_header_cell(cell, pos)
            for pos, cell in enumerate(matrix[header_idx] if matrix else [])
        ]

        rows: list[dict[str, Any]] = [{"_kind": "metadata", **metadata}]
        for raw_row in matrix[header_idx + 1 :]:
            if not any(cell.strip() for cell in raw_row):
                continue
            normalized = list(raw_row) + [""] * (len(headers) - len(raw_row))
            row = {
                header: value
                for header, value in zip(headers, normalized)
                if header and value
            }
            if row:
                row["_kind"] = "item"
                rows.append(row)
        return rows

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

    async def delete_record(self, domain: str, payload: dict[str, Any]) -> SheetsActionResult:
        rows = self._memory_db.get(domain, [])
        if not rows:
            return SheetsActionResult(success=False, message="Không có bản ghi nào để xoá.")
        target = self._resolve_target_row(rows, payload)
        if not target:
            return SheetsActionResult(success=False, message="Không tìm thấy bản ghi phù hợp để xoá.")
        self._memory_db[domain] = [r for r in rows if r is not target]
        return SheetsActionResult(success=True, message="Đã xoá bản ghi.", rows=[target])

    def _resolve_target_row(
        self, rows: list[dict[str, Any]], payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        if not rows:
            return None
        entity_reference = str(payload.get("entity_reference") or "").lower()
        entity_name = str(payload.get("entity_name") or "").lower()
        # Contextual pronouns always refer to the most recent row
        if entity_reference in {
            "cái hôm qua", "hôm qua", "cái trên", "task kia", "task này",
            "bill này", "khoản đó",
        }:
            return rows[-1]
        # Name-based lookup: search newest-first
        if entity_name:
            for row in reversed(rows):
                if entity_name in str(row.get("entity_name", "")).lower():
                    return row
            # No match found — return None so the caller can handle the miss
            # instead of silently modifying the last unrelated row
            return None
        # No reference and no name — default to most recent row
        return rows[-1]
