from __future__ import annotations

import math
from dataclasses import dataclass
from urllib.parse import quote
import unicodedata

# ── Local Phú Yên place database ─────────────────────────────────────────────
# When Google Maps API key is available: replace with live Place Search results.
# Format: name → {lat, lon, type, area, price_k, hours, note, child_safe}

PLACES: list[dict] = [
    {"name": "Sun Village Resort - Phú Yên", "lat": 13.0955, "lon": 109.3028, "type": "hotel", "area": "Tuy Hòa", "price_k": 0, "hours": "00:00-23:59", "note": "Điểm lưu trú của chuyến đi", "child_safe": True, "aliases": ["sun village", "sun village resort", "resort sun", "di resort", "khach san sun village", "hotel sun village", "resort"]},
    {"name": "Quán Bún Cá Ngừ Bà Hai", "lat": 13.0982, "lon": 109.2970, "type": "food", "area": "Tuy Hòa", "price_k": 40, "hours": "06:00-14:00", "note": "Cá ngừ đại dương tươi, locals hay ăn sáng", "child_safe": True},
    {"name": "Bánh Căn Ngọc Lan", "lat": 13.0962, "lon": 109.2958, "type": "food", "area": "Tuy Hòa", "price_k": 30, "hours": "06:00-09:00", "note": "Sáng sớm thôi, đông nhất 7h–8h", "child_safe": True},
    {"name": "Bún Sứa Đặc Sản", "lat": 13.0935, "lon": 109.2962, "type": "food", "area": "Tuy Hòa", "price_k": 35, "hours": "06:00-14:00", "note": "Phải thử ở Phú Yên", "child_safe": True},
    {"name": "Bánh Hỏi Lòng Heo", "lat": 13.0948, "lon": 109.2975, "type": "food", "area": "Tuy Hòa", "price_k": 45, "hours": "07:00-20:00", "note": "Đặc sản Phú Yên", "child_safe": True},
    {"name": "Mì Quảng Bà Mua", "lat": 13.0965, "lon": 109.2980, "type": "food", "area": "Tuy Hòa", "price_k": 35, "hours": "06:00-14:00", "note": "", "child_safe": True},
    {"name": "Hải Sản Sông Biển", "lat": 13.0945, "lon": 109.3150, "type": "seafood", "area": "Tuy Hòa", "price_k": 150, "hours": "10:00-22:00", "note": "Tôm hùm, mực nướng", "child_safe": True},
    {"name": "Sò Huyết Ô Loan", "lat": 13.4200, "lon": 109.2500, "type": "seafood", "area": "Sông Cầu", "price_k": 80, "hours": "08:00-20:00", "note": "Gần Đầm Ô Loan — đặc sản địa phương", "child_safe": True},
    {"name": "Tôm Hùm Sông Cầu", "lat": 13.4050, "lon": 109.2420, "type": "seafood", "area": "Sông Cầu", "price_k": 200, "hours": "09:00-21:00", "note": "Ngon nhất vùng", "child_safe": True},
    {"name": "Quán Hải Sản Gành Đá Đĩa", "lat": 14.3880, "lon": 109.2160, "type": "seafood", "area": "Sông Cầu", "price_k": 120, "hours": "08:00-20:00", "note": "Gần Gành Đá Đĩa", "child_safe": True},
    {"name": "Cafe Biển Bãi Xép", "lat": 13.0150, "lon": 109.3280, "type": "cafe", "area": "Bãi Xép", "price_k": 30, "hours": "06:00-22:00", "note": "View biển đẹp", "child_safe": True},
    {"name": "Quán Cá Ngừ Đại Dương", "lat": 13.0950, "lon": 109.2985, "type": "seafood", "area": "Tuy Hòa", "price_k": 100, "hours": "10:00-22:00", "note": "Cá ngừ câu tay — must try", "child_safe": True},
    {"name": "Bánh Tráng Nướng Đường Phố", "lat": 13.0968, "lon": 109.3010, "type": "street", "area": "Tuy Hòa", "price_k": 15, "hours": "18:00-23:00", "note": "Ăn đêm", "child_safe": False},
    {"name": "Gành Đá Đĩa", "lat": 14.3912, "lon": 109.2144, "type": "attraction", "area": "Sông Cầu", "price_k": 0, "hours": "06:00-17:00", "note": "Đi sáng sớm trước 9h, ít đông", "child_safe": False},
    {"name": "Mũi Điện", "lat": 12.8667, "lon": 109.4500, "type": "attraction", "area": "Tuy Hòa", "price_k": 0, "hours": "05:00-17:00", "note": "Bình minh cực Đông VN — xuất phát 4h30", "child_safe": False},
    {"name": "Bãi Xép", "lat": 13.0150, "lon": 109.3280, "type": "beach", "area": "Bãi Xép", "price_k": 0, "hours": "05:00-19:00", "note": "Sóng nhỏ, an toàn cho bé", "child_safe": True},
    {"name": "Đầm Ô Loan", "lat": 13.4200, "lon": 109.2500, "type": "attraction", "area": "Sông Cầu", "price_k": 100, "hours": "06:00-18:00", "note": "Kayak buổi sáng đẹp nhất", "child_safe": True},
    {"name": "Tháp Nhạn", "lat": 13.1010, "lon": 109.2880, "type": "attraction", "area": "Tuy Hòa", "price_k": 20, "hours": "07:00-17:00", "note": "Tháp Chăm, view đẹp", "child_safe": True},
    {"name": "Bãi biển Tuy Hòa", "lat": 13.0955, "lon": 109.3200, "type": "beach", "area": "Tuy Hòa", "price_k": 0, "hours": "05:00-19:00", "note": "Gần trung tâm", "child_safe": True},
    {"name": "Chợ Tuy Hòa", "lat": 13.0940, "lon": 109.2960, "type": "market", "area": "Tuy Hòa", "price_k": 0, "hours": "05:00-18:00", "note": "Đặc sản: cá bò khô, mực khô", "child_safe": True},
    {"name": "Hòn Yến", "lat": 13.2500, "lon": 109.3000, "type": "beach", "area": "Sông Cầu", "price_k": 0, "hours": "06:00-17:00", "note": "San hô đẹp tháng 5", "child_safe": False},
]

# Base location: Tuy Hòa city center (fallback when no user GPS)
TUY_HOA_CENTER = (13.0955, 109.3028)


@dataclass
class PlaceInfo:
    name: str
    lat: float
    lon: float
    type: str
    area: str
    price_k: int
    hours: str
    note: str
    child_safe: bool
    distance_km: float = 0.0
    drive_minutes: int = 0
    walk_minutes: int = 0
    maps_url: str = ""
    directions_url: str = ""
    open_now: bool = True
    closing_soon: bool = False


# ── Public API ────────────────────────────────────────────────────────────────

def find_place(name: str) -> PlaceInfo | None:
    """Look up a place by name (case-insensitive, partial match)."""
    name_lower = _normalize(name)
    for p in PLACES:
        place_name = _normalize(p["name"])
        aliases = [_normalize(alias) for alias in p.get("aliases", [])]
        if (
            name_lower in place_name
            or place_name in name_lower
            or any(name_lower in alias or alias in name_lower for alias in aliases)
        ):
            return _enrich(p, TUY_HOA_CENTER)
    return None


def find_nearby(
    user_lat: float,
    user_lon: float,
    place_type: str | None = None,
    limit: int = 5,
    child_safe_only: bool = False,
) -> list[PlaceInfo]:
    """Return closest places of a given type, sorted by distance."""
    results = []
    for p in PLACES:
        if place_type and p["type"] != place_type:
            continue
        if child_safe_only and not p["child_safe"]:
            continue
        results.append(_enrich(p, (user_lat, user_lon)))
    results.sort(key=lambda x: x.distance_km)
    return results[:limit]


def build_telegram_keyboard(place: PlaceInfo, extra_buttons: list[dict] | None = None) -> dict:
    """
    Build Telegram InlineKeyboardMarkup for a place.
    Returns dict compatible with Telegram Bot API reply_markup.
    """
    buttons = [
        [
            {"text": "📍 Mở Maps", "url": place.maps_url},
            {"text": "🚗 Chỉ đường", "url": place.directions_url},
        ]
    ]
    if extra_buttons:
        buttons.extend(extra_buttons)
    return {"inline_keyboard": buttons}


def format_place_line(place: PlaceInfo) -> str:
    """One-line place summary for AI response injection."""
    parts = [f"*{place.name}*"]
    if place.drive_minutes:
        parts.append(f"~{place.drive_minutes} phút chạy xe")
    if place.price_k:
        parts.append(f"~{place.price_k}k/người")
    if place.note:
        parts.append(place.note)
    status = _open_status_label(place)
    if status:
        parts.append(status)
    return " · ".join(parts)


# ── When Google Maps API key is available ─────────────────────────────────────
# Replace _enrich() with a live API call to get:
# - real-time opening hours
# - crowdedness
# - accurate driving time (Distance Matrix API)
# - place photos
# Plug-in point: check settings.google_maps_api_key before making live call.


# ── Internal helpers ──────────────────────────────────────────────────────────

def _enrich(p: dict, user_coords: tuple[float, float]) -> PlaceInfo:
    lat, lon = p["lat"], p["lon"]
    dist = _haversine(user_coords[0], user_coords[1], lat, lon)
    drive_min = _drive_minutes(dist)
    walk_min = _walk_minutes(dist)
    open_now, closing_soon = _check_hours(p["hours"])
    return PlaceInfo(
        name=p["name"],
        lat=lat,
        lon=lon,
        type=p["type"],
        area=p["area"],
        price_k=p["price_k"],
        hours=p["hours"],
        note=p["note"],
        child_safe=p["child_safe"],
        distance_km=round(dist, 1),
        drive_minutes=drive_min,
        walk_minutes=walk_min,
        maps_url=_maps_search_url(p["name"], lat, lon),
        directions_url=_directions_url(lat, lon),
        open_now=open_now,
        closing_soon=closing_soon,
    )


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _drive_minutes(dist_km: float) -> int:
    """Estimate driving time assuming ~25km/h in Phú Yên (city) or ~40km/h (highway)."""
    speed = 25.0 if dist_km < 5 else 40.0
    return max(1, round(dist_km / speed * 60))


def _walk_minutes(dist_km: float) -> int:
    return max(1, round(dist_km / 4.5 * 60))


def _maps_search_url(name: str, lat: float, lon: float) -> str:
    q = quote(f"{name}, Phú Yên, Việt Nam")
    return f"https://www.google.com/maps/search/?api=1&query={q}&query_place_id={lat},{lon}"


def _directions_url(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"


def _check_hours(hours_str: str) -> tuple[bool, bool]:
    """Returns (open_now, closing_soon) based on opening hours string."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    if not hours_str or hours_str == "":
        return True, False
    try:
        open_str, close_str = hours_str.split("-")
        now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        oh, om = map(int, open_str.strip().split(":"))
        ch, cm = map(int, close_str.strip().split(":"))
        open_time = now.replace(hour=oh, minute=om, second=0, microsecond=0)
        close_time = now.replace(hour=ch, minute=cm, second=0, microsecond=0)
        open_now = open_time <= now <= close_time
        closing_soon = open_now and (close_time - now).total_seconds() < 3600
        return open_now, closing_soon
    except Exception:
        return True, False


def _open_status_label(place: PlaceInfo) -> str:
    if not place.open_now:
        return "🔴 Đóng cửa"
    if place.closing_soon:
        return "🟡 Sắp đóng"
    return ""


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace("đ", "d")
