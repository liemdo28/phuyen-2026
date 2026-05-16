"""Entity Index — structured travel location storage + natural language search.

Provides:
- TravelEntity CRUD with persistent JSON cache
- Multi-signal search (name, vibe, energy, weather, traveler type)
- Fuzzy matching with Vietnamese-aware normalization
- Geocoding integration
- Sheets ingestion pipeline
"""
from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.adapters.sheets_api_client import SheetsApiClient, SheetsApiError
from app.services.geocoding import GeocodingEngine, get_geocoding_engine
from app.schemas.travel_entity import (
    TravelEntity, OpeningHours, ParkingInfo,
    TransportAccess, CrowdInfo,
    VIBE_TAGS, TRAVELER_TYPES, ENERGY_FIT_TAGS,
    WEATHER_FIT_TAGS, TRIP_FIT_TAGS, LOCAL_VS_TOURIST,
    EMOTIONAL_VIBE, LEVEL1_CATEGORIES,
)

# ── Cache ─────────────────────────────────────────────────────────────────────
_CACHE_DIR = Path(os.environ.get("STATE_DIR", "/data"))
_ENTITY_INDEX_FILE = _CACHE_DIR / "entity_index.json"
_ENTITY_INDEX_VERSION = 2

# ── Category synonyms ──────────────────────────────────────────────────────────
_L1_FROM_KEYWORD: dict[str, list[str]] = {
    "restaurant": ["quán", "nhà hàng", "ăn", "hải sản", "bún", "bánh",
                   "phở", "mì", "cơm", "lẩu", "nướng", "seafood", "food",
                   "restaurant", "cafe", "cà phê", "café", "coffee"],
    "hotel": ["khách sạn", "hotel", "resort", "homestay", "nhà nghỉ", "lưu trú"],
    "beach": ["bãi", "biển", "beach", "tắm biển", "sông", "đầm", "hòn"],
    "attraction": ["tháp", "đền", "chùa", "du lịch", "view", "cảnh đẹp",
                   "thắng cảnh", "điểm tham quan"],
    "cafe": ["cafe", "cà phê", "café", "coffee", "trà", "nước", "đồ uống"],
    "market": ["chợ", "market", "búa", "đặc sản"],
    "nightlife": ["bar", "nhậu", "beer", "rượu", "quán nhậu"],
    "shopping": ["mua", "siêu thị", "shop", "bán", "đồ"],
    "gas_station": ["xăng", "petrol", "gas station", "đổ xăng", "dầu"],
    "parking": ["đỗ xe", "parking", "bãi xe", "garage"],
    "viewpoint": ["view", "panorama", "ngắm", "phong cảnh"],
    "hidden_spot": ["bí mật", "ẩn", "ít người", "bình thường", "yên tĩnh"],
}

# ── Vibe keywords ──────────────────────────────────────────────────────────────
_VIBE_KEYWORDS: dict[str, list[str]] = {
    "chill": ["chill", "yên tĩnh", "nhẹ nhàng", "thư giãn", "bình yên"],
    "local": ["local", "địa phương", "người dân", "bản địa", "authentic"],
    "luxury": ["sang", "sang trọng", "luxury", "premium", "đắt tiền"],
    "quiet": ["yên", "quiet", "tĩnh lặng", "vắng"],
    "crowded": ["đông", "đông đúc", "crowded", "đầy", "đông khách"],
    "romantic": ["lãng mạn", "romantic", "tình nhân", " couple"],
    "sunset": ["hoàng hôn", "sunset", "dusk"],
    "instagrammable": ["sống ảo", "đẹp", "insta", "check-in", "photogenic"],
    "family": ["gia đình", "family", "trẻ em", "cả nhà"],
    "hidden": ["ẩn", "bí mật", "hidden", "ít người biết"],
    "authentic": ["authenic", "thật", "nguyên bản", "truyền thống"],
    "touristy": ["du lịch", "tourist", "khách", "nổi tiếng"],
    "night_vibe": ["đêm", "night", "quán nhậu", "bar"],
    "ocean_vibe": ["biển", "ocean", "sea", "sóng"],
}

# ── Energy keywords ─────────────────────────────────────────────────────────────
_ENERGY_KEYWORDS: dict[str, list[str]] = {
    "low_energy": ["nhẹ", "ít vận động", "ngồi", "nhanh", "quick"],
    "high_energy": ["năng động", "vui", "nhảy", "high energy"],
    "recovery_friendly": ["hồi phục", "recovery", "nghỉ ngơi", "nhẹ nhàng"],
    "walking_heavy": ["đi bộ", "walking", "leo", "đường dài", "trekking"],
    "crowded_exhausting": ["đông", "náo nhiệt", "náo loạn", "mệt"],
    "calming": ["bình yên", "calm", "thư giãn", "relaxing"],
    "social_heavy": ["giao lưu", "social", "nhiều người", "bạn bè"],
}

# ── Weather keywords ────────────────────────────────────────────────────────────
_WEATHER_KEYWORDS: dict[str, list[str]] = {
    "hot_weather": ["nắng", "nóng", "hot", "mùa hè", "summer"],
    "rainy_weather": ["mưa", "rainy", "trời mưa", "gió"],
    "indoor_safe": ["trong nhà", "indoor", "máy lạnh", "điều hòa"],
    "sunset_best": ["hoàng hôn", "sunset", "chiều tà", "dusk"],
    "windy_weather": ["gió", "windy", "lộng gió"],
}

# ── Traveler keywords ────────────────────────────────────────────────────────────
_TRAVELER_KEYWORDS: dict[str, list[str]] = {
    "family": ["gia đình", "family", "trẻ em", "cả nhà", "con nít"],
    "couple": ["cặp đôi", "couple", "tình nhân", "yêu"],
    "foodie": ["foodie", "sành ăn", "thích ăn", "美食"],
    "photographer": ["chụp ảnh", "photo", "sống ảo", "camera"],
    "backpacker": ["backpacker", "ba lô", "túi đeo", "bụi"],
    "digital_nomad": ["làm việc", "remote", "laptop", "wifi", "coworking"],
    "solo_traveler": ["một mình", "solo", "đi một mình"],
    "luxury_traveler": ["sang", "luxury", "premium", "đắt"],
}


def _normalize(text: str) -> str:
    """Vietnamese-aware text normalization."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace("đ", "d")


class EntityIndex:
    """Central index of TravelEntity objects with multi-signal search."""

    def __init__(
        self,
        sheets_client: Optional[SheetsApiClient] = None,
        geocoder: Optional[GeocodingEngine] = None,
    ) -> None:
        self.sheets = sheets_client or SheetsApiClient()
        self.geocoder = geocoder or get_geocoding_engine()
        self._entities: list[TravelEntity] = []
        self._name_lookup: dict[str, list[int]] = {}
        self._category_lookup: dict[str, list[int]] = {}
        self._vibe_lookup: dict[str, list[int]] = {}
        self._traveler_lookup: dict[str, list[int]] = {}
        self._loaded = False
        self._load_from_disk()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load_from_disk(self) -> None:
        if _ENTITY_INDEX_FILE.exists():
            try:
                data = json.loads(_ENTITY_INDEX_FILE.read_text())
                if data.get("version") == _ENTITY_INDEX_VERSION:
                    self._entities = [
                        TravelEntity.from_dict(e) for e in data.get("entities", [])
                    ]
                    self._rebuild_lookups()
                    self._loaded = True
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    def _save_to_disk(self) -> None:
        try:
            _ENTITY_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": _ENTITY_INDEX_VERSION,
                "entities": [e.to_dict() for e in self._entities],
                "updated_at": datetime.now().isoformat(),
            }
            _ENTITY_INDEX_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2)
            )
        except OSError:
            pass

    def _rebuild_lookups(self) -> None:
        self._name_lookup.clear()
        self._category_lookup.clear()
        self._vibe_lookup.clear()
        self._traveler_lookup.clear()
        for i, e in enumerate(self._entities):
            # Name
            name = _normalize(e.name)
            for token in name.split():
                if token not in self._name_lookup:
                    self._name_lookup[token] = []
                self._name_lookup[token].append(i)
            # Category
            cat = e.category.lower()
            if cat:
                self._category_lookup.setdefault(cat, []).append(i)
            # Vibe
            for v in e.vibe_tags:
                self._vibe_lookup.setdefault(v.lower(), []).append(i)
            # Traveler type
            for t in e.traveler_types:
                self._traveler_lookup.setdefault(t.lower(), []).append(i)

    # ── Refresh from Google Sheets ────────────────────────────────────────────

    async def refresh(self, force: bool = False) -> int:
        if self._loaded and not force:
            return len(self._entities)

        entities: list[TravelEntity] = []

        # Quán Ăn sheet
        try:
            data = await self.sheets.restaurants()
            if data.get("ok"):
                for item in data.get("data", []):
                    e = self._parse_restaurant(item)
                    if e:
                        entities.append(e)
        except SheetsApiError:
            pass

        # Gợi Ý Lịch Trình sheet
        try:
            itinerary_data = await self.sheets._call("itinerary_locations")
            if itinerary_data.get("ok"):
                for item in itinerary_data.get("data", []):
                    e = self._parse_itinerary(item)
                    if e:
                        entities.append(e)
        except (SheetsApiError, AttributeError):
            pass

        entities = self._merge_hardcoded(entities)

        # Geocode unresolved
        await self._geocode_batch(entities)

        self._entities = entities
        self._rebuild_lookups()
        self._loaded = True
        self._save_to_disk()
        return len(self._entities)

    def _parse_restaurant(self, item: dict) -> Optional[TravelEntity]:
        name = item.get("Tên Quán") or item.get("name", "") or ""
        if not name:
            return None
        return TravelEntity(
            id=_make_id(name),
            name=name,
            slug=_normalize(name).replace(" ", "-"),
            category=self._detect_category(item.get("Loại") or "", name),
            subcategory=self._detect_subcategory(name),
            address=item.get("Địa chỉ") or item.get("address", ""),
            district=item.get("Khu vực") or "Tuy Hòa",
            province="Phú Yên",
            note=item.get("Ghi chú") or "",
            avg_price_vnd=int(item.get("Giá", 0) or 0),
            opening_hours=OpeningHours.from_str(item.get("Giờ mở cửa", "")),
            on_route=bool(item.get("Đường về", "")),
            child_safe=bool(item.get("An toàn") or item.get("family", "")),
            source_sheet="Quán Ăn",
            source_row=int(item.get("row", 0) or 0),
            last_updated=datetime.now().isoformat(),
            aliases=self._generate_aliases(name),
        )

    def _parse_itinerary(self, item: dict) -> Optional[TravelEntity]:
        name = item.get("Địa điểm") or item.get("name", "") or ""
        if not name:
            return None
        return TravelEntity(
            id=_make_id(name),
            name=name,
            slug=_normalize(name).replace(" ", "-"),
            category=self._detect_category(item.get("Loại") or "", name),
            address=item.get("Địa chỉ") or "",
            district=item.get("Khu vực") or "",
            province="Phú Yên",
            note=item.get("Ghi chú") or "",
            opening_hours=OpeningHours.from_str(item.get("Thời gian tốt") or ""),
            child_safe=bool(item.get("An toàn") or item.get("family", "")),
            source_sheet="Gợi Ý Lịch Trình",
            source_row=int(item.get("row", 0) or 0),
            last_updated=datetime.now().isoformat(),
            aliases=self._generate_aliases(name),
        )

    def _merge_hardcoded(self, entities: list[TravelEntity]) -> list[TravelEntity]:
        existing = {_normalize(e.name) for e in entities}
        hardcoded = [
            ("Quán Bún Cá Ngừ Bà Hai", "restaurant", 13.0899, 109.3095),
            ("Bánh Cán Ngọc Lan", "restaurant", 13.0860, 109.3080),
            ("Bún Sứa Đặc Sản", "restaurant", 13.0820, 109.3110),
            ("Mì Quảng Bà Mua", "restaurant", 13.0870, 109.3070),
            ("Gành Đá Đĩa", "attraction", 12.9533, 109.4233),
            ("Mũi Điện", "attraction", 12.8842, 109.4358),
            ("Bãi Xép", "beach", 12.9700, 109.3980),
            ("Đầm Ô Loan", "attraction", 12.9400, 109.3700),
            ("Tháp Nhạn", "attraction", 13.0689, 109.2847),
            ("Chợ Tuy Hòa", "local_market", 13.0833, 109.3000),
        ]
        from app.services.maps_service import PLACES
        for name, cat, lat, lon in hardcoded:
            if _normalize(name) not in existing:
                for p in PLACES:
                    if _normalize(p["name"]) == _normalize(name):
                        entities.append(TravelEntity(
                            id=_make_id(name),
                            name=p["name"],
                            slug=_normalize(name).replace(" ", "-"),
                            category=cat,
                            lat=p["lat"],
                            lng=p["lon"],
                            province="Phú Yên",
                            note=p.get("note", ""),
                            source_sheet="maps_service",
                            geocode_source="override",
                            geocode_confidence=0.99,
                            last_updated=datetime.now().isoformat(),
                            maps_url=_maps_search_url(p["name"], p["lat"], p["lon"]),
                            directions_url=_directions_url(p["lat"], p["lon"]),
                        ))
                        break
        return entities

    async def _geocode_batch(self, entities: list[TravelEntity]) -> None:
        for e in entities:
            if e.lat is not None or not e.address:
                continue
            result = await self.geocoder.geocode(e.address)
            if result:
                e.lat = result.lat
                e.lng = result.lon
                e.geocode_source = result.source
                e.geocode_confidence = result.confidence
                e.maps_url = _maps_search_url(e.name, result.lat, result.lon)
                e.directions_url = _directions_url(result.lat, result.lon)
                if not e.district:
                    e.district = _extract_area(result.display_name)

    # ── Search ────────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str = "",
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        category: Optional[str] = None,
        vibe: Optional[str] = None,
        traveler: Optional[str] = None,
        energy: Optional[str] = None,
        weather: Optional[str] = None,
        local_only: bool = False,
        on_route: Optional[bool] = None,
        child_safe: bool = False,
        limit: int = 5,
    ) -> list[TravelEntity]:
        if not self._loaded:
            await self.refresh()

        q_norm = _normalize(query)
        scored: list[tuple[float, TravelEntity]] = []

        for e in self._entities:
            # Filters
            if category and _normalize(category) not in _normalize(e.category):
                continue
            if on_route is not None and e.on_route != on_route:
                continue
            if child_safe and not e.child_safe:
                continue
            if local_only and e.local_vs_tourist not in ("local_hidden", "local_favorite"):
                continue
            if vibe and not e.matches_vibe(vibe):
                continue
            if traveler and not e.matches_traveler(traveler):
                continue
            if energy and not e.matches_energy(energy):
                continue
            if weather and not e.matches_weather(weather):
                continue

            # Score
            score = self._compute_score(q_norm, e, user_lat, user_lon)
            scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def _compute_score(
        self,
        q_norm: str,
        e: TravelEntity,
        user_lat: Optional[float],
        user_lon: Optional[float],
    ) -> float:
        score = 0.0

        # Name match (50%)
        name_norm = _normalize(e.name)
        if q_norm and q_norm in name_norm:
            score += 0.5
        elif q_norm:
            q_tokens = set(q_norm.split())
            n_tokens = set(name_norm.split())
            overlap = len(q_tokens & n_tokens)
            if overlap:
                score += overlap / max(len(q_tokens), len(n_tokens)) * 0.5

        # Vibe / keyword (30%)
        vibe_score = self._vibe_keyword_score(q_norm, e)
        score += vibe_score * 0.3

        # Distance (20%)
        dist_score = 0.0
        if user_lat is not None and user_lon is not None and e.lat and e.lng:
            dist_km = _haversine(user_lat, user_lon, e.lat, e.lng)
            dist_score = max(0, 1.0 - dist_km / 50.0)
        score += dist_score * 0.2

        return score

    def _vibe_keyword_score(self, q_norm: str, e: TravelEntity) -> float:
        score = 0.0
        # Check vibe tags
        for vibe, kws in _VIBE_KEYWORDS.items():
            if any(kw in q_norm for kw in kws) and vibe in e.vibe_tags:
                score = max(score, 0.8)
        # Check energy
        for en, kws in _ENERGY_KEYWORDS.items():
            if any(kw in q_norm for kw in kws) and en in e.energy_fit:
                score = max(score, 0.7)
        # Check weather
        for w, kws in _WEATHER_KEYWORDS.items():
            if any(kw in q_norm for kw in kws) and w in e.weather_fit:
                score = max(score, 0.6)
        # Check traveler
        for t, kws in _TRAVELER_KEYWORDS.items():
            if any(kw in q_norm for kw in kws) and t in e.traveler_types:
                score = max(score, 0.7)
        # Category keyword match
        for cat, kws in _L1_FROM_KEYWORD.items():
            if any(kw in q_norm for kw in kws) and cat == e.category:
                score = max(score, 0.9)
        return score

    def _detect_category(self, type_str: str, name: str) -> str:
        combined = _normalize(f"{type_str} {name}")
        for cat, kws in _L1_FROM_KEYWORD.items():
            if any(kw in combined for kw in kws):
                return cat
        return "attraction"

    def _detect_subcategory(self, name: str) -> str:
        n = _normalize(name)
        sub_map = {
            "seafood": ["hải sản", "seafood", "cá", "tôm", "cua", "sò"],
            "local_food": ["bún", "phở", "bánh", "mì", "cơm"],
            "street_food": ["bánh", "xôi", "bún bò", "bánh tráng"],
            "coffee": ["cà phê", "cafe", "café", "coffee"],
            "dessert": ["chè", "kem", "tráng miệng"],
        }
        for sub, kws in sub_map.items():
            if any(kw in n for kw in kws):
                return sub
        return ""

    def _generate_aliases(self, name: str) -> list[str]:
        aliases = []
        lower = name.lower()
        for prefix in ["quán ", "nhà hàng ", "khách sạn ", "bãi ", "bánh "]:
            if lower.startswith(prefix):
                aliases.append(lower[len(prefix):].strip())
        return aliases

    def get_all(self) -> list[TravelEntity]:
        return list(self._entities)

    def stats(self) -> dict:
        return {
            "total": len(self._entities),
            "categories": {e.category for e in self._entities if e.category},
            "vibes": {v for e in self._entities for v in e.vibe_tags},
            "geocoded": sum(1 for e in self._entities if e.lat),
        }


# ── Utilities ────────────────────────────────────────────────────────────────

def _make_id(name: str) -> str:
    return _normalize(name).replace(" ", "-")

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

def _maps_search_url(name: str, lat: float, lon: float) -> str:
    from urllib.parse import quote
    q = quote(f"{name}, Phú Yên, Vietnam")
    return f"https://www.google.com/maps/search/?api=1&query={q}&query_place_id={lat},{lon}"

def _directions_url(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"

def _extract_area(display_name: str) -> str:
    parts = display_name.split(", ")
    if len(parts) >= 3:
        return parts[-3].strip()
    return ""

# ── Singleton ────────────────────────────────────────────────────────────────
_entity_index: Optional[EntityIndex] = None

def get_entity_index() -> EntityIndex:
    global _entity_index
    if _entity_index is None:
        _entity_index = EntityIndex()
    return _entity_index