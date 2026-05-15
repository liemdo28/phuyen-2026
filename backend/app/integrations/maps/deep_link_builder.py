"""Google Maps deep link generator for Phú Yên travel companion."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus, urlencode

# ---------------------------------------------------------------------------
# Hard-coded Phú Yên location intelligence
# ---------------------------------------------------------------------------

PHU_YEN_LOCATIONS: dict[str, dict] = {
    "ganh_da_dia": {
        "name": "Gành Đá Đĩa",
        "coords": "13.3894,109.2626",
        "type": "attraction",
        "best_time": "6-9h",
    },
    "bai_xep": {
        "name": "Bãi Xép",
        "coords": "13.0523,109.2967",
        "type": "beach",
        "best_time": "7-11h",
    },
    "mui_dien": {
        "name": "Mũi Điện",
        "coords": "12.8853,109.4601",
        "type": "attraction",
        "best_time": "4:30-7h",
    },
    "vinh_hoa": {
        "name": "Vịnh Hòa",
        "coords": "13.2087,109.2611",
        "type": "beach",
    },
    "dam_o_loan": {
        "name": "Đầm Ô Loan",
        "coords": "13.2583,109.2561",
        "type": "nature",
    },
    "thap_nhan": {
        "name": "Tháp Nhạn",
        "coords": "13.0939,109.3095",
        "type": "heritage",
    },
    "tuy_hoa_beach": {
        "name": "Bãi biển Tuy Hòa",
        "coords": "13.0878,109.3027",
        "type": "beach",
    },
    "song_cau": {
        "name": "Sông Cầu",
        "coords": "13.4387,109.2138",
        "type": "town",
    },
    "hon_yen": {
        "name": "Hòn Yến",
        "coords": "13.3456,109.2456",
        "type": "island",
    },
}

# Travel mode mapping to Google Maps travelmode param
TRAVEL_MODES = {
    "driving": "driving",
    "walking": "walking",
    "bicycling": "bicycling",
    "transit": "transit",
    # Vietnamese aliases
    "xe máy": "driving",
    "xe": "driving",
    "đi bộ": "walking",
    "xe đạp": "bicycling",
    "xe buýt": "transit",
}

# Vietnamese labels per link type
_LABEL_TEMPLATES = {
    "search": "Tìm: {query}",
    "directions": "Chỉ đường đến {destination}",
    "navigate": "Dẫn đường đến {destination}",
    "nearby": "Tìm {category} gần {location}",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class MapDeepLink:
    """A Google Maps deep link with metadata."""

    url: str
    display_label: str
    link_type: str  # search | directions | navigate | streetview


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class MapsDeepLinkBuilder:
    """Generate Google Maps deep links for Phú Yên travel guidance."""

    _BASE_SEARCH = "https://www.google.com/maps/search/?api=1"
    _BASE_DIR = "https://www.google.com/maps/dir/?api=1"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, query: str, near: str = "") -> MapDeepLink:
        """Build a Google Maps search link for *query*, optionally biased near *near*."""
        full_query = f"{query} {near}".strip() if near else query
        params = urlencode({"query": full_query}, quote_via=quote_plus)
        url = f"{self._BASE_SEARCH}&{params}"
        label = _LABEL_TEMPLATES["search"].format(query=full_query)
        return MapDeepLink(url=url, display_label=label, link_type="search")

    def directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
    ) -> MapDeepLink:
        """Build a Google Maps directions link from *origin* to *destination*."""
        travel_mode = TRAVEL_MODES.get(mode, mode)
        params = urlencode(
            {
                "origin": origin,
                "destination": destination,
                "travelmode": travel_mode,
            },
            quote_via=quote_plus,
        )
        url = f"{self._BASE_DIR}&{params}"
        label = _LABEL_TEMPLATES["directions"].format(destination=destination)
        return MapDeepLink(url=url, display_label=label, link_type="directions")

    def navigate_to(self, destination: str) -> MapDeepLink:
        """Build a one-tap navigation link (no origin specified – uses device GPS)."""
        params = urlencode({"destination": destination}, quote_via=quote_plus)
        url = f"{self._BASE_DIR}&{params}"
        label = _LABEL_TEMPLATES["navigate"].format(destination=destination)
        return MapDeepLink(url=url, display_label=label, link_type="navigate")

    def search_nearby(self, category: str, location: str) -> MapDeepLink:
        """Build a 'category near location' search link."""
        query = f"{category} near {location}"
        params = urlencode({"query": query}, quote_via=quote_plus)
        url = f"{self._BASE_SEARCH}&{params}"
        label = _LABEL_TEMPLATES["nearby"].format(category=category, location=location)
        return MapDeepLink(url=url, display_label=label, link_type="search")

    # ------------------------------------------------------------------
    # Telegram helpers
    # ------------------------------------------------------------------

    def build_telegram_button(self, link: MapDeepLink) -> dict:
        """Return an inline keyboard button dict ``{"text": ..., "url": ...}``."""
        return {"text": link.display_label, "url": link.url}

    # ------------------------------------------------------------------
    # Convenience: look up a known Phú Yên location by key
    # ------------------------------------------------------------------

    def link_for_location(self, location_key: str) -> MapDeepLink | None:
        """Return a navigate link for a known PHU_YEN_LOCATIONS key, or None."""
        loc = PHU_YEN_LOCATIONS.get(location_key)
        if loc is None:
            return None
        return self.navigate_to(loc["coords"])
