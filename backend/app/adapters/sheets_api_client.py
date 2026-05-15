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

    def _parse_json_response(self, response: httpx.Response, context: str) -> dict:
        try:
            data = response.json()
        except ValueError as exc:
            body_preview = (response.text or "")[:200]
            raise SheetsApiError(
                f"{context} trả về không phải JSON: {exc}. HTTP {response.status_code}. Body: {body_preview}"
            ) from exc

        if not data.get("ok"):
            raise SheetsApiError(f"Apps Script báo lỗi: {data.get('error', 'unknown')}")
        return data

    async def _call_post(self, action: str, data: dict) -> dict:
        if not self.configured:
            raise SheetsApiError("Chưa cấu hình SHEETS_WEBAPP_URL / SHEETS_API_SECRET trên môi trường deploy.")

        payload = {"token": self.secret, "action": action, "data": data}
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=False) as client:
                response = await client.post(self.base_url, json=payload)

                if response.status_code in {301, 302, 303, 307, 308} and response.headers.get("location"):
                    redirect_url = response.headers["location"]
                    response = await client.post(redirect_url, json=payload)

                if response.status_code == 405:
                    return await self._call_write_via_get(action, data)

                response.raise_for_status()
        except httpx.HTTPError as exc:
            if "405" in str(exc):
                return await self._call_write_via_get(action, data)
            raise SheetsApiError(f"Không gọi được Apps Script (POST): {exc}") from exc

        return self._parse_json_response(response, "Apps Script POST")

    async def _call_write_via_get(self, action: str, data: dict) -> dict:
        flat_params = {
            "action": action,
            "token": self.secret,
            **{key: "" if value is None else str(value) for key, value in data.items()},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(self.base_url, params=flat_params)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SheetsApiError(f"Không gọi được Apps Script (GET fallback): {exc}") from exc

        return self._parse_json_response(response, "Apps Script GET fallback")

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

    async def write_expense(self, item: dict) -> dict:
        return await self._call_post("write_expense", item)

    async def write_packing(self, item: dict) -> dict:
        return await self._call_post("write_packing", item)

    async def write_contribution(self, item: dict) -> dict:
        return await self._call_post("write_contribution", item)

    async def write_restaurant(self, item: dict) -> dict:
        return await self._call_post("write_restaurant", item)
