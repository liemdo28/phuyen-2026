"""
Location Intelligence Service — Phase: Google Sheet Location Intelligence

Wraps LocationIndex with Telegram-friendly UX:
- Natural language search
- Maps deeplink generation
- Multi-button Telegram keyboards
- Route suggestions
- Auto-detection of location intent in messages
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from app.services.geocoding import get_geocoding_engine
from app.services.location_index import (
    IndexedLocation,
    LocationIndex,
    get_location_index,
)

# ── Intent patterns ──────────────────────────────────────────────────────────

LOCATION_INTENT_PATTERNS = [
    # Open / find place
    r"\b(mở|tìm|tới|đến|chỉ|chỉ đường|chỉ đườg)\b.*\b(quán|địa điểm|nơi|chỗ|chổ|spot|place)\b",
    r"\b(mở|tìm)\s+(hải sản|quán|khách sạn|bãi|biển|cafe|điểm)\b",
    r"\b(tìm|kiếm)\s+(quán|chỗ|nơi|địa điểm)\b",
    # Maps / route
    r"\b(maps|map|máp)\b",
    r"\b(route|routing|đường|đi tới|đến|đi đến|chỉ đường|dẫn đường)\b.*\b(quán|bãi|biển|điểm|chỗ)\b",
    r"\bđường\s+(tới|đến|đi)\b",
    r"\b(tới|đến|đi|ở)\s+\w+\s+(được không|mình|thôi)\b",
    # Specific actions
    r"\b(ăn|sáng|trưa|tối)\s+(ở đâu|quán nào|đâu)\b",
    r"\b(quán|chỗ)\s+(nào|đâu|gần|near)\b",
    r"\b(gần|gần đây|đây)\b",
    r"\b(bãi|biển)\s+(nào|đẹp|gần)\b",
    r"\b(cafe|cà phê|café)\s+(nào|đâu|gần)\b",
    # Direction / nearby
    r"\b(gần|nearby|xa|ở đâu|đâu)\b",
    r"\b(địa chỉ|address|ở đâu)\b",
    # Place names mentioned
    r"\b(gành đá|gành da|mũi điện|bãi xép|bai xep|ô loan|mùi điện)\b",
    r"\b(tuy hòa|sông cầu|song cau)\b",
    # On route
    r"\b(đường về|dọc đường|trên đường|về nhà)\b.*\b(quán|cafe|bãi)\b",
]

# Vietnamese category emoji
CATEGORY_EMOJI = {
    "restaurant": "🍽️",
    "cafe": "☕",
    "beach": "🏖️",
    "hotel": "🏨",
    "attraction": "📍",
    "market": "🛒",
    "gas_station": "⛽",
    "parking": "🅿️",
    "airport": "✈️",
    "meetup": "🤝",
    "hidden": "🌿",
}


@dataclass
class LocationSearchResult:
    """A search result ready for Telegram display."""
    location: IndexedLocation
    distance_km: float = 0.0
    drive_minutes: int = 0
    match_score: float = 0.0


@dataclass
class LocationIntentResult:
    """Result of location intent detection."""
    is_location_intent: bool
    query: str = ""
    category: str = ""
    user_lat: float | None = None
    user_lon: float | None = None
    on_route: bool = False
    child_safe: bool = False


class LocationIntelligence:
    """
    Location Intelligence service — natural language location search powered by Google Sheets.
    
    Usage:
        li = LocationIntelligence()
        result = await li.detect_intent("mở quán hải sản gần đây")
        if result.is_location_intent:
            places = await li.search(result.query, user_lat=13.0955, user_lon=109.3028)
            for p in places:
                print(p.location.place_name, p.location.maps_url)
    """

    def __init__(self, index: LocationIndex | None = None) -> None:
        self._index = index or get_location_index()
        self._intent_re = [re.compile(p, re.IGNORECASE) for p in LOCATION_INTENT_PATTERNS]

    async def detect_intent(
        self,
        text: str,
        user_lat: float | None = None,
        user_lon: float | None = None,
    ) -> LocationIntentResult:
        """
        Detect if a message is a location intent.
        
        Returns LocationIntentResult with is_location_intent=True if detected.
        """
        text_lower = text.lower().strip()

        # Check intent patterns
        is_location = any(pat.search(text) for pat in self._intent_re)

        if not is_location:
            return LocationIntentResult(is_location_intent=False)

        # Extract query - remove intent words, keep the place/entity
        query = self._extract_location_query(text_lower)

        # Detect category
        category = self._detect_category_from_text(text_lower)

        # Check on_route flag
        on_route = any(
            kw in text_lower
            for kw in ["đường về", "dọc đường", "trên đường", "về nhà"]
        )

        # Check child_safe
        child_safe = any(kw in text_lower for kw in ["bé", "trẻ", "child", "family"])

        return LocationIntentResult(
            is_location_intent=True,
            query=query,
            category=category,
            user_lat=user_lat,
            user_lon=user_lon,
            on_route=on_route,
            child_safe=child_safe,
        )

    async def search(
        self,
        query: str,
        user_lat: float | None = None,
        user_lon: float | None = None,
        category: str | None = None,
        on_route: bool | None = None,
        child_safe: bool = False,
        limit: int = 5,
    ) -> list[LocationSearchResult]:
        """
        Search indexed locations and return scored + enriched results.
        """
        locations = await self._index.search(
            query=query,
            user_lat=user_lat,
            user_lon=user_lon,
            category=category,
            on_route=on_route,
            child_safe=child_safe,
            limit=limit,
        )

        results = []
        for loc in locations:
            dist_km = 0.0
            drive_min = 0
            if user_lat and user_lon and loc.lat and loc.lon:
                dist_km = _haversine(user_lat, user_lon, loc.lat, loc.lon)
                drive_min = _drive_minutes(dist_km)

            results.append(LocationSearchResult(
                location=loc,
                distance_km=dist_km,
                drive_minutes=drive_min,
                match_score=0.8,  # Already scored in index.search
            ))

        return results

    async def search_by_name(
        self,
        name: str,
        limit: int = 3,
    ) -> list[LocationSearchResult]:
        """Find a place by name."""
        locations = await self._index.search_by_name(name, limit=limit)
        return [
            LocationSearchResult(location=loc, match_score=0.9)
            for loc in locations
        ]

    async def get_nearby(
        self,
        user_lat: float,
        user_lon: float,
        category: str | None = None,
        limit: int = 5,
        child_safe: bool = False,
    ) -> list[LocationSearchResult]:
        """Find places near user location."""
        return await self.search(
            query="",
            user_lat=user_lat,
            user_lon=user_lon,
            category=category,
            child_safe=child_safe,
            limit=limit,
        )

    async def get_on_route_places(
        self,
        user_lat: float,
        user_lon: float,
        limit: int = 5,
    ) -> list[LocationSearchResult]:
        """Find places that are on the route back."""
        return await self.search(
            query="",
            user_lat=user_lat,
            user_lon=user_lon,
            on_route=True,
            limit=limit,
        )

    def build_telegram_buttons(
        self,
        result: LocationSearchResult,
        include_nearby: bool = True,
    ) -> dict:
        """
        Build Telegram InlineKeyboardMarkup for a location result.
        
        Buttons:
        📍 Mở Maps | 🚗 Chỉ đường
        ☕ Nearby   | 🌅 Next Spot
        """
        loc = result.location
        buttons = [
            [
                {"text": "📍 Mở Maps", "url": loc.maps_url},
                {"text": "🚗 Chỉ đường", "url": loc.directions_url},
            ]
        ]

        if include_nearby and loc.lat and loc.lon:
            nearby_url = (
                f"https://www.google.com/maps/search/?api=1"
                f"&query={loc.lat},{loc.lon}"
            )
            buttons.append([
                {"text": "☕ Nearby", "url": nearby_url},
            ])

        return {"inline_keyboard": buttons}

    def format_result_text(
        self,
        result: LocationSearchResult,
        include_maps_button: bool = True,
    ) -> str:
        """
        Format a search result as readable Telegram text.
        
        Example:
        🍽️ Quán Bún Cá Ngừ Bà Hai
        📍 Tuy Hòa · 0.8km · ~2 phút
        💰 ~40k/người · 06:00-14:00
        💬 Cá ngừ đại dương tươi, locals hay ăn sáng
        """
        loc = result.location
        emoji = CATEGORY_EMOJI.get(loc.category, "📍")

        lines = [f"{emoji} *{loc.place_name}*"]

        # Location + distance
        meta = []
        if loc.area:
            meta.append(loc.area)
        if result.distance_km > 0:
            meta.append(f"{result.distance_km:.1f}km")
        if result.drive_minutes > 0:
            meta.append(f"~{result.drive_minutes} phút")
        if meta:
            lines.append("📍 " + " · ".join(meta))

        # Price + hours
        details = []
        if loc.price_k > 0:
            details.append(f"~{loc.price_k}k/người")
        if loc.hours:
            details.append(loc.hours)
        if details:
            lines.append("💰 " + " · ".join(details))

        # Note
        if loc.note:
            lines.append(f"💬 {loc.note}")

        return "\n".join(lines)

    def format_multi_result_text(
        self,
        results: list[LocationSearchResult],
        header: str = "Kết quả tìm kiếm:",
    ) -> str:
        """Format multiple results as a numbered list."""
        if not results:
            return "Không tìm thấy địa điểm nào phù hợp. Thử tìm tên khác?"

        parts = [f"{header}\n"]
        for i, r in enumerate(results, 1):
            loc = r.location
            emoji = CATEGORY_EMOJI.get(loc.category, "📍")

            # Distance line
            dist = f" · {r.distance_km:.1f}km" if r.distance_km > 0 else ""
            drive = f" · ~{r.drive_minutes}p" if r.drive_minutes > 0 else ""

            # Price line
            price = f" · {loc.price_k}k" if loc.price_k > 0 else ""

            parts.append(
                f"{i}. {emoji} *{loc.place_name}*{dist}{drive}\n"
            )
            if price:
                parts.append(f"   💰 {price} · {loc.area or loc.hours or 'Phú Yên'}\n")
            if loc.note:
                parts.append(f"   💬 {loc.note}\n")
            parts.append(f"   📍 {loc.maps_url}\n")
            parts.append("\n")

        parts.append(
            f"📊 Tổng: {len(results)} địa điểm · /maps để mở tất cả"
        )
        return "".join(parts).strip()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _extract_location_query(self, text: str) -> str:
        """Extract the location/entity name from the query text."""
        # Remove intent words
        intent_words = [
            "mở", "tìm", "tới", "đến", "ở", "maps", "map", "chỉ đường",
            "dẫn đường", "đường", "ở đâu", "ở đâu", "quán nào",
            "chỗ nào", "nơi nào", "đâu", "gần", "gần đây",
            "có quán", "có chỗ", "đi tới", "đi đến",
        ]
        query = text
        for word in intent_words:
            query = query.replace(word, " ")
        # Clean up
        query = re.sub(r"\s+", " ", query).strip(" .,!?-")
        return query or text

    def _detect_category_from_text(self, text: str) -> str:
        """Detect location category from text keywords."""
        cat_keywords = {
            "restaurant": ["quán", "nhà hàng", "hải sản", "bún", "phở", "mì", "ăn", "bữa", "tối", "sáng", "trưa"],
            "cafe": ["cafe", "cà phê", "café", "coffee", "trà", "nước", "đồ uống"],
            "beach": ["bãi", "biển", "tắm", "bơi", "sông", "hòn"],
            "hotel": ["khách sạn", "resort", "homestay", "nghỉ", "ở", "phòng", "lưu trú"],
            "attraction": ["điểm", "tháp", "đền", "chùa", "view", "cảnh", "thắng", "du lịch"],
            "market": ["chợ", "market", "búa"],
            "gas_station": ["xăng", "đổ xăng", "dầu"],
        }
        for cat, keywords in cat_keywords.items():
            if any(kw in text for kw in keywords):
                return cat
        return ""

    def parse_location_from_text(self, text: str) -> str | None:
        """
        Extract a place name from raw text.
        
        E.g., "mở quán hải sản" → "hải sản"
        E.g., "đường tới bãi xép" → "bãi xép"
        """
        # Try to find known place names in text
        normalized = _normalize(text)
        results = []

        # Use the index
        for loc in self._index._index:
            loc_norm = _normalize(loc.place_name)
            # Check if place name appears in text
            if loc_norm in normalized or normalized in loc_norm:
                results.append((len(loc_norm), loc.place_name))
            # Check aliases
            for alias in loc.aliases:
                alias_norm = _normalize(alias)
                if alias_norm in normalized:
                    results.append((len(alias_norm), loc.place_name))

        if results:
            # Return the longest match (most specific)
            results.sort(key=lambda x: x[0], reverse=True)
            return results[0][1]

        return None


# ── Utilities ────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace("đ", "d")


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _drive_minutes(dist_km: float) -> int:
    speed = 25.0 if dist_km < 5 else 40.0
    return max(1, round(dist_km / speed * 60))


# ── Singleton ─────────────────────────────────────────────────────────────────

_location_intelligence: LocationIntelligence | None = None


def get_location_intelligence() -> LocationIntelligence:
    global _location_intelligence
    if _location_intelligence is None:
        _location_intelligence = LocationIntelligence()
    return _location_intelligence