"""
Location Geocoding Engine — Phase: Google Sheet Location Intelligence

Uses Nominatim (OpenStreetMap) for free geocoding.
Falls back to hardcoded Phú Yên place database.
Caches all geocoding results to avoid rate limiting.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import httpx

# ── Cache path ────────────────────────────────────────────────────────────────
_CACHE_DIR = Path(os.environ.get("STATE_DIR", "/data"))
_GEOCODE_CACHE = _CACHE_DIR / "geocode_cache.json"

# ── Nominatim config ──────────────────────────────────────────────────────────
_NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
_SEARCH_BASE = "https://nominatim.openstreetmap.org/search"
_REVERSE_BASE = "https://nominatim.openstreetmap.org/reverse"
_USER_AGENT = "PhuYen2026Bot/1.0 (LiemDo - Travel AI)"
_RATE_LIMIT_SECONDS = 1.1  # Nominatim requires max 1 req/sec

# ── Known Phú Yên place overrides ─────────────────────────────────────────────
# Pre-geocoded places to avoid API calls and ensure accuracy
_PHUYEN_PLACE_CACHE: dict[str, dict] = {
    "sun village resort": {"lat": 13.0955, "lon": 109.3028, "display": "Sun Village Resort, Phú Yên"},
    "quán bún cá ngừ bà hai": {"lat": 13.0982, "lon": 109.2970, "display": "Bún Cá Ngừ Bà Hai, Tuy Hòa"},
    "bánh cán ngọc lan": {"lat": 13.0962, "lon": 109.2958, "display": "Bánh Căn Ngọc Lan, Tuy Hòa"},
    "bún sứa đặc sản": {"lat": 13.0935, "lon": 109.2962, "display": "Bún Sứa Đặc Sản, Tuy Hòa"},
    "bánh hỏi lòng heo": {"lat": 13.0948, "lon": 109.2975, "display": "Bánh Hỏi Lòng Heo, Tuy Hòa"},
    "mì quảng bà mua": {"lat": 13.0965, "lon": 109.2980, "display": "Mì Quảng Bà Mua, Tuy Hòa"},
    "hải sản sông biển": {"lat": 13.0945, "lon": 109.3150, "display": "Hải Sản Sông Biển, Tuy Hòa"},
    "sò huyết ô loan": {"lat": 13.4200, "lon": 109.2500, "display": "Sò Huyết Ô Loan, Sông Cầu"},
    "tôm hùm sông cầu": {"lat": 13.4050, "lon": 109.2420, "display": "Tôm Hùm Sông Cầu, Sông Cầu"},
    "quán hải sản gành đá đĩa": {"lat": 14.3880, "lon": 109.2160, "display": "Quán Hải Sản Gành Đá Đĩa, Sông Cầu"},
    "cafe biển bãi xép": {"lat": 13.0150, "lon": 109.3280, "display": "Cafe Biển Bãi Xép, Bãi Xép"},
    "quán cá ngừ đại dương": {"lat": 13.0950, "lon": 109.2985, "display": "Quán Cá Ngừ Đại Dương, Tuy Hòa"},
    "bánh tráng nướng đường phố": {"lat": 13.0968, "lon": 109.3010, "display": "Bánh Tráng Nướng, Tuy Hòa"},
    "gành đá đĩa": {"lat": 14.3912, "lon": 109.2144, "display": "Gành Đá Đĩa, Sông Cầu"},
    "mũi điện": {"lat": 12.8667, "lon": 109.4500, "display": "Mũi Điện, Phú Yên"},
    "bãi xép": {"lat": 13.0150, "lon": 109.3280, "display": "Bãi Xép, Phú Yên"},
    "đầm ô loan": {"lat": 13.4200, "lon": 109.2500, "display": "Đầm Ô Loan, Sông Cầu"},
    "tháp nhạn": {"lat": 13.1010, "lon": 109.2880, "display": "Tháp Nhạn, Tuy Hòa"},
    "bãi biển tuy hòa": {"lat": 13.0955, "lon": 109.3200, "display": "Bãi Biển Tuy Hòa, Tuy Hòa"},
    "chợ tuy hòa": {"lat": 13.0940, "lon": 109.2960, "display": "Chợ Tuy Hòa, Tuy Hòa"},
    "hòn yến": {"lat": 13.2500, "lon": 109.3000, "display": "Hòn Yến, Sông Cầu"},
    "tuy hòa": {"lat": 13.0955, "lon": 109.3028, "display": "Tuy Hòa, Phú Yên"},
    "sông cầu": {"lat": 13.4000, "lon": 109.2400, "display": "Sông Cầu, Phú Yên"},
}


@dataclass
class GeoResult:
    """Result of geocoding an address or place name."""
    lat: float
    lon: float
    display_name: str
    source: str  # "cache", "override", "nominatim", "default"
    confidence: float = 0.5  # 0.0-1.0


class GeocodingCache:
    """Persistent JSON cache for geocoding results."""

    def __init__(self, cache_path: Path = _GEOCODE_CACHE) -> None:
        self.cache_path = cache_path
        self._cache: dict[str, GeoResult] = {}
        self._load()

    def _load(self) -> None:
        if self.cache_path.exists():
            try:
                raw = json.loads(self.cache_path.read_text())
                for key, val in raw.items():
                    self._cache[key] = GeoResult(**val)
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    def _save(self) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            data = {k: asdict(v) for k, v in self._cache.items()}
            self.cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except OSError:
            pass  # Non-fatal on read-only systems

    def get(self, query: str) -> GeoResult | None:
        return self._cache.get(query.strip().lower())

    def set(self, query: str, result: GeoResult) -> None:
        self._cache[query.strip().lower()] = result
        self._save()

    def has(self, query: str) -> bool:
        return query.strip().lower() in self._cache


class GeocodingEngine:
    """
    Geocoding engine using Nominatim (OSM) with persistent cache.
    
    Usage:
        engine = GeocodingEngine()
        result = await engine.geocode("123 Nguyễn Huệ, Tuy Hòa, Phú Yên")
    """

    def __init__(self) -> None:
        self.cache = GeocodingCache()
        self._semaphore = asyncio.Semaphore(1)  # Rate limit: 1 concurrent request

    async def geocode(self, address: str) -> GeoResult | None:
        """
        Geocode an address or place name.
        
        Priority:
        1. In-memory / persistent cache
        2. Phú Yên known place overrides
        3. Nominatim API (rate-limited)
        4. Fallback: Tuy Hòa center
        """
        if not address or not address.strip():
            return None

        query = address.strip()
        q_lower = query.lower()

        # 1. Check cache
        cached = self.cache.get(query)
        if cached:
            return cached

        # 2. Check known place overrides
        override = self._check_override(q_lower, query)
        if override:
            self.cache.set(query, override)
            return override

        # 3. Nominatim API (rate limited)
        result = await self._nominatim_geocode(query)
        if result:
            self.cache.set(query, result)
            return result

        # 4. Fallback
        return self._default_result(query)

    async def geocode_batch(self, addresses: list[str]) -> dict[str, GeoResult | None]:
        """Geocode multiple addresses concurrently (rate-limited)."""
        results: dict[str, GeoResult | None] = {}
        for addr in addresses:
            results[addr] = await self.geocode(addr)
        return results

    def _check_override(self, q_lower: str, original: str) -> GeoResult | None:
        """Check against known Phú Yên places."""
        # Exact match
        if q_lower in _PHUYEN_PLACE_CACHE:
            data = _PHUYEN_PLACE_CACHE[q_lower]
            return GeoResult(
                lat=data["lat"],
                lon=data["lon"],
                display_name=data["display"],
                source="override",
                confidence=0.99,
            )
        # Partial match
        for key, data in _PHUYEN_PLACE_CACHE.items():
            if key in q_lower or q_lower in key:
                return GeoResult(
                    lat=data["lat"],
                    lon=data["lon"],
                    display_name=data["display"],
                    source="override",
                    confidence=0.9,
                )
        return None

    async def _nominatim_geocode(self, query: str) -> GeoResult | None:
        """Call Nominatim API with rate limiting."""
        await asyncio.sleep(_RATE_LIMIT_SECONDS)  # Nominatim requires 1 req/sec

        params = {
            "q": f"{query}, Phú Yên, Vietnam",
            "format": "json",
            "limit": "1",
            "addressdetails": "1",
        }
        headers = {"User-Agent": _USER_AGENT}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(_SEARCH_BASE, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        if not data:
            # Try without Vietnam suffix
            try:
                params["q"] = query
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(_SEARCH_BASE, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()
            except (httpx.HTTPError, ValueError):
                return None

        if not data:
            return None

        first = data[0]
        return GeoResult(
            lat=float(first["lat"]),
            lon=float(first["lon"]),
            display_name=first.get("display_name", query),
            source="nominatim",
            confidence=0.7 if float(first.get("importance", 0)) > 0.5 else 0.5,
        )

    def _default_result(self, query: str) -> GeoResult:
        """Fallback: Tuy Hòa city center."""
        return GeoResult(
            lat=13.0955,
            lon=109.3028,
            display_name=f"{query} (khu vực Tuy Hòa)",
            source="default",
            confidence=0.1,
        )

    def geocode_sync(self, address: str) -> GeoResult | None:
        """Synchronous geocode for non-async contexts."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.geocode(address))


# ── Singleton ─────────────────────────────────────────────────────────────────
_geocoding_engine: GeocodingEngine | None = None


def get_geocoding_engine() -> GeocodingEngine:
    global _geocoding_engine
    if _geocoding_engine is None:
        _geocoding_engine = GeocodingEngine()
    return _geocoding_engine