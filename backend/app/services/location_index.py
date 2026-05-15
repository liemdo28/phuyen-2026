"""
Location Intelligence Service — Phase: Google Sheet Location Intelligence

Centralized location index that:
- Scans ALL Google Sheet tabs for location data
- Builds a searchable, geocoded index
- Provides natural language search
- Generates Google Maps deeplinks
- Ranks by distance, trip context, weather, and user preferences
"""

from __future__ import annotations

import json
import math
import os
import unicodedata
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.adapters.sheets_api_client import SheetsApiClient, SheetsApiError
from app.services.geocoding import GeocodingEngine, get_geocoding_engine

# ── Cache path ────────────────────────────────────────────────────────────────
_CACHE_DIR = Path(os.environ.get("STATE_DIR", "/data"))
_LOCATION_INDEX_FILE = _CACHE_DIR / "location_index.json"
_LOCATION_INDEX_VERSION = 1

# ── Location type categories ───────────────────────────────────────────────────
LOCATION_TYPE_SYNONYMS: dict[str, list[str]] = {
    "restaurant": ["quán", "nhà hàng", "ăn", "hải sản", "bún", "bánh", "phở", "mì", "cơm", "lẩu", "nướng", " Seafood ", "seafood", "food", "restaurant", "cafe", "cà phê", "café", "coffee", "drink"],
    "hotel": ["khách sạn", "hotel", "resort", "homestay", "nhà nghỉ", "lưu trú", "phòng", "nghỉ", "stay"],
    "beach": ["bãi", "biển", "beach", "tắm biển", "sông", "đầm", "hòn"],
    "attraction": ["tháp", "đền", "chùa", "điểm du lịch", "attraction", "view", "cảnh đẹp", "thắng cảnh"],
    "cafe": ["cafe", "cà phê", "café", "coffee", "trà", "nước", "đồ uống", "giải khát"],
    "market": ["chợ", "market", "búa", "súp", "đặc sản"],
    "parking": ["đỗ xe", "parking", "bãi xe", "garage"],
    "gas_station": ["xăng", "petrol", "gas station", "đổ xăng", "dầu"],
    "airport": ["sân bay", "airport", "vé máy bay"],
    "meetup": ["điểm hẹn", "tập trung", "đón", "meetup", "gặp"],
    "hidden": ["bí mật", "ẩn", "hidden", "ít người", "bình thường", "yên tĩnh"],
}

# ── Column detection patterns ──────────────────────────────────────────────────
LOCATION_COLUMN_PATTERNS: dict[str, list[str]] = {
    "name": ["tên", "quán", "khách sạn", "tên quán", "tên khách sạn", "name", "place", "địa điểm", "điểm đến", "điểm tham quan", "spot", "location", "nơi", "chỗ", "địa điểm"],
    "address": ["địa chỉ", "address", "đường", "số nhà", "nơi", "chỗ ở", "location address"],
    "note": ["ghi chú", "note", "notes", "mô tả", "ghi chú thêm", "chi tiết", "bình luận", "review", "đánh giá"],
    "type": ["loại", "type", "danh mục", "category", "kiểu", "hạng"],
    "area": ["khu vực", "area", "vùng", "zone", "tỉnh", "thành phố", "city"],
    "price": ["giá", "price", "chi phí", "ngân sách", "budget"],
    "hours": ["giờ", "hours", "mở cửa", "thời gian", "khung giờ", "time"],
    "on_route": ["đường về", "on route", "về", "trên đường", "về nhà", "dọc đường"],
    "child_safe": ["an toàn", "child safe", "trẻ em", "bé", "family"],
}

# ── Priority columns per sheet ─────────────────────────────────────────────────
SHEET_LOCATION_COLUMNS: dict[str, dict[str, str]] = {
    "Quán Ăn": {
        "name": "Tên Quán",
        "address": "Địa chỉ",
        "note": "Ghi chú",
        "type": "Loại",
        "area": "Khu vực",
        "price": "Giá",
        "hours": "Giờ mở cửa",
    },
    "Gợi Ý Lịch Trình": {
        "name": "Địa điểm",
        "address": "Địa chỉ",
        "note": "Ghi chú",
        "type": "Loại",
        "area": "Khu vực",
        "hours": "Thời gian tốt",
    },
}


@dataclass
class IndexedLocation:
    """A single location in the central index."""
    place_name: str
    sheet_name: str
    row: int
    address: str
    lat: Optional[float]
    lon: Optional[float]
    category: str
    note: str = ""
    area: str = ""
    price_k: int = 0
    hours: str = ""
    on_route: bool = False
    child_safe: bool = False
    maps_url: str = ""
    directions_url: str = ""
    geocode_source: str = ""  # "override", "nominatim", "unresolved"
    geocode_confidence: float = 0.0
    last_updated: str = ""  # ISO timestamp
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "IndexedLocation":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class LocationIndex:
    """
    Centralized location index built from Google Sheets.
    
    Usage:
        index = LocationIndex()
        await index.refresh()  # Scan all sheets
        results = await index.search("quán hải sản", user_lat=13.0955, user_lon=109.3028)
        best = results[0]
        print(best.maps_url)  # Google Maps deeplink
    """

    def __init__(
        self,
        sheets_client: Optional[SheetsApiClient] = None,
        geocoder: Optional[GeocodingEngine] = None,
    ) -> None:
        self.sheets = sheets_client or SheetsApiClient()
        self.geocoder = geocoder or get_geocoding_engine()
        self._index: list[IndexedLocation] = []
        self._name_lookup: dict[str, list[int]] = {}  # normalized name → index positions
        self._type_lookup: dict[str, list[int]] = {}  # category → index positions
        self._loaded = False
        self._load_from_disk()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_from_disk(self) -> None:
        """Load index from disk cache."""
        if _LOCATION_INDEX_FILE.exists():
            try:
                data = json.loads(_LOCATION_INDEX_FILE.read_text())
                if data.get("version") == _LOCATION_INDEX_VERSION:
                    self._index = [IndexedLocation.from_dict(loc) for loc in data.get("locations", [])]
                    self._rebuild_lookups()
                    self._loaded = True
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    def _save_to_disk(self) -> None:
        """Save index to disk cache."""
        try:
            _LOCATION_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": _LOCATION_INDEX_VERSION,
                "locations": [loc.to_dict() for loc in self._index],
                "updated_at": datetime.now().isoformat(),
            }
            _LOCATION_INDEX_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2)
            )
        except OSError:
            pass  # Non-fatal on read-only systems

    def _rebuild_lookups(self) -> None:
        """Rebuild fast-lookup dictionaries after index changes."""
        self._name_lookup.clear()
        self._type_lookup.clear()
        for i, loc in enumerate(self._index):
            # Name lookup
            names = [_normalize(loc.place_name)]
            names.extend(_normalize(a) for a in loc.aliases if a)
            for name in names:
                if name not in self._name_lookup:
                    self._name_lookup[name] = []
                self._name_lookup[name].append(i)
            # Type lookup
            cat = loc.category.lower()
            if cat not in self._type_lookup:
                self._type_lookup[cat] = []
            self._type_lookup[cat].append(i)

    # ── Refresh: scan all sheets ─────────────────────────────────────────────

    async def refresh(self, force: bool = False) -> int:
        """
        Scan all Google Sheets and rebuild the location index.
        Returns number of locations found.
        """
        if self._loaded and not force:
            return len(self._index)

        locations: list[IndexedLocation] = []

        # 1. Scan Quán Ăn sheet
        try:
            data = await self.sheets.restaurants()
            if data.get("ok"):
                for item in data.get("data", []):
                    loc = self._parse_restaurant_row(item)
                    if loc:
                        locations.append(loc)
        except SheetsApiError:
            pass

        # 2. Scan Gợi Ý Lịch Trình sheet
        try:
            itinerary_data = await self.sheets._call("itinerary_locations")
            if itinerary_data.get("ok"):
                for item in itinerary_data.get("data", []):
                    loc = self._parse_itinerary_row(item)
                    if loc:
                        locations.append(loc)
        except (SheetsApiError, AttributeError):
            pass

        # 3. Merge with hardcoded PLACES that aren't in sheets yet
        locations = self._merge_with_hardcoded_places(locations)

        # 4. Geocode any unresolved locations
        await self._geocode_batch(locations)

        # 5. Update index
        self._index = locations
        self._rebuild_lookups()
        self._loaded = True
        self._save_to_disk()

        return len(self._index)

    def _parse_restaurant_row(self, item: dict) -> Optional[IndexedLocation]:
        """Parse a row from Quán Ăn sheet."""
        name = item.get("Tên Quán") or item.get("name", "") or item.get("ten", "")
        if not name:
            return None
        return IndexedLocation(
            place_name=name,
            sheet_name="Quán Ăn",
            row=int(item.get("row", 0)),
            address=item.get("Địa chỉ") or item.get("address", "") or "",
            lat=None,
            lon=None,
            category=self._detect_category(item.get("Loại") or item.get("type", ""), name),
            note=item.get("Ghi chú") or item.get("note", "") or "",
            area=item.get("Khu vực") or item.get("area", "") or "Tuy Hòa",
            price_k=int(item.get("Giá", 0) or 0),
            hours=item.get("Giờ mở cửa") or item.get("hours", "") or "",
            on_route=bool(item.get("Đường về") or item.get("on_route", "")),
            child_safe=bool(item.get("An toàn") or item.get("child_safe", "")),
            last_updated=datetime.now().isoformat(),
            aliases=self._generate_aliases(name),
        )

    def _parse_itinerary_row(self, item: dict) -> Optional[IndexedLocation]:
        """Parse a row from Gợi Ý Lịch Trình sheet."""
        name = item.get("Địa điểm") or item.get("name", "") or ""
        if not name:
            return None
        return IndexedLocation(
            place_name=name,
            sheet_name="Gợi Ý Lịch Trình",
            row=int(item.get("row", 0)),
            address=item.get("Địa chỉ") or "",
            lat=None,
            lon=None,
            category=self._detect_category(item.get("Loại") or "", name),
            note=item.get("Ghi chú") or "",
            area=item.get("Khu vực") or "",
            hours=item.get("Thời gian tốt") or "",
            child_safe=bool(item.get("An toàn") or item.get("family", "")),
            last_updated=datetime.now().isoformat(),
            aliases=self._generate_aliases(name),
        )

    def _merge_with_hardcoded_places(
        self, locations: list[IndexedLocation]
    ) -> list[IndexedLocation]:
        """Add hardcoded places not yet in the index."""
        existing_names = {_normalize(loc.place_name) for loc in locations}
        hardcoded_names = {
            "sun village resort": "hotel",
            "quán bún cá ngừ bà hai": "restaurant",
            "bánh cán ngọc lan": "restaurant",
            "bún sứa đặc sản": "restaurant",
            "bánh hỏi lòng heo": "restaurant",
            "mì quảng bà mua": "restaurant",
            "hải sản sông biển": "restaurant",
            "sò huyết ô loan": "restaurant",
            "tôm hùm sông cầu": "restaurant",
            "quán hải sản gành đá đĩa": "restaurant",
            "cafe biển bãi xép": "cafe",
            "quán cá ngừ đại dương": "restaurant",
            "bánh tráng nướng đường phố": "restaurant",
            "gành đá đĩa": "attraction",
            "mũi điện": "attraction",
            "bãi xép": "beach",
            "đầm ô loan": "attraction",
            "tháp nhạn": "attraction",
            "bãi biển tuy hòa": "beach",
            "chợ tuy hòa": "market",
            "hòn yến": "beach",
        }
        for name, cat in hardcoded_names.items():
            if name not in existing_names:
                from app.services.maps_service import PLACES
                for p in PLACES:
                    if _normalize(p["name"]) == name:
                        locations.append(IndexedLocation(
                            place_name=p["name"],
                            sheet_name="maps_service",
                            row=0,
                            address="Phú Yên",
                            lat=p["lat"],
                            lon=p["lon"],
                            category=cat,
                            note=p.get("note", ""),
                            area=p.get("area", ""),
                            price_k=p.get("price_k", 0),
                            hours=p.get("hours", ""),
                            child_safe=p.get("child_safe", False),
                            geocode_source="override",
                            geocode_confidence=0.99,
                            last_updated=datetime.now().isoformat(),
                            maps_url=_maps_search_url(p["name"], p["lat"], p["lon"]),
                            directions_url=_directions_url(p["lat"], p["lon"]),
                        ))
                        break
        return locations

    async def _geocode_batch(self, locations: list[IndexedLocation]) -> None:
        """Geocode all locations that don't have coordinates yet."""
        for loc in locations:
            if loc.lat is not None and loc.lon is not None:
                continue
            if not loc.address:
                continue
            result = await self.geocoder.geocode(loc.address)
            if result:
                loc.lat = result.lat
                loc.lon = result.lon
                loc.geocode_source = result.source
                loc.geocode_confidence = result.confidence
                if not loc.area:
                    loc.area = self._extract_area_from_display(result.display_name)
                loc.maps_url = _maps_search_url(loc.place_name, result.lat, result.lon)
                loc.directions_url = _directions_url(result.lat, result.lon)
            else:
                loc.geocode_source = "unresolved"
                loc.geocode_confidence = 0.0

    # ── Search ───────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        category: Optional[str] = None,
        on_route: Optional[bool] = None,
        limit: int = 5,
        child_safe: bool = False,
    ) -> list[IndexedLocation]:
        """
        Search the location index with natural language query.
        
        Rankings by:
        1. Name/alias fuzzy match score
        2. Distance (if user coords provided)
        3. Category match
        4. On-route filter
        5. Child-safe filter
        """
        if not self._loaded:
            await self.refresh()

        q_norm = _normalize(query)
        scored: list[tuple[float, IndexedLocation]] = []

        for loc in self._index:
            # Filter: category
            if category and _normalize(category) not in _normalize(loc.category):
                continue
            # Filter: on_route
            if on_route is not None and loc.on_route != on_route:
                continue
            # Filter: child_safe
            if child_safe and not loc.child_safe:
                continue

            # Score: name match
            name_score = self._name_match_score(q_norm, loc)

            # Score: type/keyword match
            type_score = self._keyword_match_score(q_norm, loc)

            # Score: distance (closer = higher)
            dist_score = 0.0
            if user_lat is not None and user_lon is not None and loc.lat and loc.lon:
                dist_km = _haversine(user_lat, user_lon, loc.lat, loc.lon)
                dist_score = max(0, 1.0 - dist_km / 50.0)  # 50km = 0, 0km = 1

            # Combined score
            total_score = name_score * 0.5 + type_score * 0.3 + dist_score * 0.2
            scored.append((total_score, loc))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [loc for _, loc in scored[:limit]]

    async def search_by_name(
        self,
        name: str,
        limit: int = 3,
    ) -> list[IndexedLocation]:
        """Find locations by exact or fuzzy name match."""
        if not self._loaded:
            await self.refresh()
        q_norm = _normalize(name)
        results: list[tuple[float, IndexedLocation]] = []
        for loc in self._index:
            score = self._name_match_score(q_norm, loc)
            if score > 0.3:
                results.append((score, loc))
        results.sort(key=lambda x: x[0], reverse=True)
        return [loc for _, loc in results[:limit]]

    def _name_match_score(self, query_norm: str, loc: IndexedLocation) -> float:
        """Compute 0-1 score for name/alias match."""
        name_norm = _normalize(loc.place_name)
        # Exact contains
        if query_norm == name_norm:
            return 1.0
        if query_norm in name_norm or name_norm in query_norm:
            return 0.9
        # Alias match
        for alias in loc.aliases:
            a_norm = _normalize(alias)
            if query_norm == a_norm:
                return 0.95
            if query_norm in a_norm or a_norm in query_norm:
                return 0.85
        # Token overlap
        query_tokens = set(query_norm.split())
        name_tokens = set(name_norm.split())
        overlap = len(query_tokens & name_tokens)
        if overlap > 0:
            return overlap / max(len(query_tokens), len(name_tokens)) * 0.8
        return 0.0

    def _keyword_match_score(self, query_norm: str, loc: IndexedLocation) -> float:
        """Compute 0-1 score for keyword/type match."""
        score = 0.0
        cat_norm = _normalize(loc.category)
        # Category keywords
        for cat_key, synonyms in LOCATION_TYPE_SYNONYMS.items():
            if any(syn in query_norm for syn in synonyms):
                if cat_norm == cat_key or cat_key in cat_norm:
                    score = max(score, 0.8)
            if cat_key in query_norm and cat_key in cat_norm:
                score = max(score, 0.9)
        # Note search
        note_norm = _normalize(loc.note)
        if note_norm and query_norm in note_norm:
            score = max(score, 0.4)
        return score

    def _detect_category(self, type_str: str, name: str) -> str:
        """Detect category from type string and name."""
        combined = _normalize(f"{type_str} {name}")
        for cat, keywords in LOCATION_TYPE_SYNONYMS.items():
            if any(kw in combined for kw in keywords):
                return cat
        return "attraction"

    def _generate_aliases(self, name: str) -> list[str]:
        """Generate common aliases for a place name."""
        aliases = []
        name_lower = name.lower()
        # Remove common prefixes
        for prefix in ["quán ", "nhà hàng ", "khách sạn ", "bãi "]:
            if name_lower.startswith(prefix):
                aliases.append(name_lower[len(prefix):].strip())
        return aliases

    def _extract_area_from_display(self, display_name: str) -> str:
        """Extract area/town from Nominatim display_name."""
        parts = display_name.split(", ")
        if len(parts) >= 3:
            return parts[-3].strip()
        return ""

    def get_all_categories(self) -> list[str]:
        """Return all unique categories in the index."""
        if not self._loaded:
            return []
        cats = set(loc.category for loc in self._index if loc.category)
        return sorted(cats)

    def get_all_areas(self) -> list[str]:
        """Return all unique areas in the index."""
        if not self._loaded:
            return []
        areas = set(loc.area for loc in self._index if loc.area)
        return sorted(areas)

    def stats(self) -> dict:
        """Return index statistics."""
        return {
            "total_locations": len(self._index),
            "geocoded": sum(1 for loc in self._index if loc.lat is not None),
            "categories": self.get_all_categories(),
            "areas": self.get_all_areas(),
            "loaded": self._loaded,
        }


# ── Map URL builders ──────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Vietnamese-aware text normalization for matching."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace("đ", "d")


def _maps_search_url(name: str, lat: float, lon: float) -> str:
    from urllib.parse import quote
    q = quote(f"{name}, Phú Yên, Vietnam")
    return f"https://www.google.com/maps/search/?api=1&query={q}&query_place_id={lat},{lon}"


def _directions_url(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ── Singleton ─────────────────────────────────────────────────────────────────
_location_index: LocationIndex | None = None


def get_location_index() -> LocationIndex:
    global _location_index
    if _location_index is None:
        _location_index = LocationIndex()
    return _location_index