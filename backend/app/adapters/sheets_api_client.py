from __future__ import annotations

import httpx

from app.core.config import settings


class SheetsApiError(Exception):
    """Raised when the Apps Script sheet API cannot be reached or returns an error."""


class SheetsApiClient:
    def __init__(self) -> None:
        self.base_url = settings.sheets_webapp_url.strip()
        self.secret = settings.sheets_api_secret.strip()
        self._timeout = httpx.Timeout(15.0, connect=10.0)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.secret)

    async def _call(self, action: str, **params) -> dict:
        if not self.configured:
            raise SheetsApiError("Chưa cấu hình SHEETS_WEBAPP_URL / SHEETS_API_SECRET trên môi trường deploy.")

        query = {"action": action, "token": self.secret, **params}
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(self.base_url, params=query)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise SheetsApiError(f"Không gọi được Apps Script: {exc}") from exc
        except ValueError as exc:
            raise SheetsApiError(f"Apps Script trả về không phải JSON: {exc}") from exc

        if not data.get("ok"):
            raise SheetsApiError(f"Apps Script báo lỗi: {data.get('error', 'unknown')}")
        return data

    async def ping(self) -> bool:
        data = await self._call("ping")
        return bool(data.get("pong"))

    async def expenses_recent(self, limit: int = 5) -> dict:
        return await self._call("expenses_recent", limit=limit)

    async def expenses_total(self) -> dict:
        return await self._call("expenses_total")

    async def expenses_by_category(self) -> dict:
        return await self._call("expenses_by_category")

    async def expenses_by_day(self) -> dict:
        return await self._call("expenses_by_day")

    async def report_full(self) -> dict:
        return await self._call("report_full")

    async def debts(self) -> dict:
        return await self._call("debts")

    async def contributions(self) -> dict:
        return await self._call("contributions")

    async def packing_status(self, filter: str = "") -> dict:
        return await self._call("packing_status", filter=filter)

    async def restaurants(self, area: str = "") -> dict:
        return await self._call("restaurants", area=area)

    async def members(self) -> dict:
        return await self._call("members")
