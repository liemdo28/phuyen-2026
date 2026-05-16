"""
Mi Location Database — Phú Yên emotional place intelligence.

Every location has emotional metadata so Mi can match place → user mood.
Not a list of tourist spots — a living map of human experiences.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlaceProfile:
    id: str
    name: str
    name_vi: str
    lat: float
    lon: float
    area: str                       # tuy_hoa | song_cau | ganh_da_dia | mui_dien | bai_xep

    # Emotional fit
    vibe: list[str]                 # chill | active | romantic | local | touristy | healing
    recovery_score: float           # 0-1: how good for recovery/rest
    fatigue_fit: float              # 0-1: suitable when tired (1=great when tired)
    social_energy_needed: float     # 0-1: 0=works solo, 1=needs social energy
    crowd_timing: dict[str, str]    # {"morning":"low","midday":"high","afternoon":"medium"}

    # Practical
    type: str                       # beach|cafe|food|market|viewpoint|activity|nightlife
    child_safe: bool = True
    parking: bool = True
    indoor: bool = False
    price_range: str = "mid"        # budget|mid|premium

    # Ratings
    sunset_score: float = 0.0       # 0-1
    chill_score: float = 0.0        # 0-1
    local_score: float = 1.0        # 0-1: 1=pure local, 0=tourist trap
    nightlife_score: float = 0.0    # 0-1

    # Timing
    best_times: list[str] = field(default_factory=list)    # ["06:00-09:00", "15:00-18:00"]
    avoid_times: list[str] = field(default_factory=list)   # ["10:00-14:00"]

    # Mi's local tip
    mi_tip: str = ""

    def maps_url(self) -> str:
        return f"https://maps.google.com/?q={self.lat},{self.lon}"

    def matches_mood(self, fatigue_level: str, vibe_want: str | None = None) -> bool:
        if fatigue_level in ("high", "critical") and self.fatigue_fit < 0.5:
            return False
        if vibe_want and vibe_want not in self.vibe:
            return False
        return True


# ── Phú Yên Location Database ─────────────────────────────────────────────────

PHU_YEN_PLACES: list[PlaceProfile] = [

    # ── Beaches ───────────────────────────────────────────────────────────────
    PlaceProfile(
        id="bai_xep",
        name="Bãi Xép", name_vi="Bãi Xép",
        lat=13.0819, lon=109.3312,
        area="tuy_hoa",
        vibe=["chill", "healing", "romantic", "local"],
        recovery_score=0.9, fatigue_fit=0.9, social_energy_needed=0.2,
        crowd_timing={"morning": "low", "midday": "medium", "afternoon": "low", "evening": "low"},
        type="beach", child_safe=True, parking=True, indoor=False, price_range="budget",
        sunset_score=0.8, chill_score=0.95, local_score=0.85, nightlife_score=0.1,
        best_times=["06:00-09:00", "14:30-17:30"],
        avoid_times=["10:00-14:00"],
        mi_tip="Sóng nhỏ nhất Phú Yên — an toàn cho bé. Cafe nhỏ view biển, chiều mát ngồi chill đỉnh lắm.",
    ),

    PlaceProfile(
        id="ganh_da_dia",
        name="Gành Đá Đĩa", name_vi="Gành Đá Đĩa",
        lat=14.3725, lon=109.2156,
        area="ganh_da_dia",
        vibe=["active", "touristy", "local"],
        recovery_score=0.2, fatigue_fit=0.2, social_energy_needed=0.6,
        crowd_timing={"morning": "low", "midday": "high", "afternoon": "high", "evening": "low"},
        type="viewpoint", child_safe=True, parking=True, indoor=False, price_range="budget",
        sunset_score=0.3, chill_score=0.3, local_score=0.7, nightlife_score=0.0,
        best_times=["06:30-09:00"],
        avoid_times=["10:00-15:00"],
        mi_tip="Đi sớm trước 9h — ít người, ánh sáng đẹp, đá còn ẩm sáng. Giày đế cao su bắt buộc cho bé, đá trơn.",
    ),

    PlaceProfile(
        id="mui_dien",
        name="Mũi Điện", name_vi="Mũi Điện — Bình minh cực Đông",
        lat=13.6519, lon=109.4614,
        area="mui_dien",
        vibe=["active", "romantic", "healing"],
        recovery_score=0.4, fatigue_fit=0.1, social_energy_needed=0.5,
        crowd_timing={"morning": "low", "midday": "low", "afternoon": "low", "evening": "low"},
        type="viewpoint", child_safe=True, parking=True, indoor=False, price_range="budget",
        sunset_score=0.1, chill_score=0.5, local_score=0.9, nightlife_score=0.0,
        best_times=["04:30-07:00"],
        avoid_times=[],
        mi_tip="Xuất phát 4h30 từ Tuy Hòa. Đường vào nhỏ, Carnival đi được nhưng chạy chậm. Đáng xem nhất là bình minh cực Đông.",
    ),

    PlaceProfile(
        id="dam_o_loan",
        name="Đầm Ô Loan", name_vi="Đầm Ô Loan",
        lat=13.2900, lon=109.2800,
        area="song_cau",
        vibe=["chill", "local", "healing", "romantic"],
        recovery_score=0.8, fatigue_fit=0.7, social_energy_needed=0.3,
        crowd_timing={"morning": "low", "midday": "low", "afternoon": "low", "evening": "low"},
        type="activity", child_safe=True, parking=True, indoor=False, price_range="mid",
        sunset_score=0.9, chill_score=0.85, local_score=0.95, nightlife_score=0.0,
        best_times=["06:00-09:00", "14:00-17:30"],
        avoid_times=[],
        mi_tip="Kayak buổi sáng hoặc chiều mát — sò huyết Ô Loan ăn tại đây tươi hơn đặt ở thành phố nhiều.",
    ),

    # ── Cafes ─────────────────────────────────────────────────────────────────
    PlaceProfile(
        id="cafe_bai_xep",
        name="Cafe Bãi Xép", name_vi="Cafe view biển Bãi Xép",
        lat=13.0822, lon=109.3308,
        area="tuy_hoa",
        vibe=["chill", "healing", "romantic"],
        recovery_score=0.95, fatigue_fit=1.0, social_energy_needed=0.1,
        crowd_timing={"morning": "low", "midday": "medium", "afternoon": "low", "evening": "low"},
        type="cafe", child_safe=True, parking=True, indoor=False, price_range="budget",
        sunset_score=0.85, chill_score=1.0, local_score=0.8, nightlife_score=0.0,
        best_times=["07:00-10:00", "14:00-18:00"],
        avoid_times=[],
        mi_tip="Ngồi nhìn biển, gió mát, không đông. Uống đồ từ từ không ai đuổi. Tốt nhất khi cần reset đầu óc.",
    ),

    PlaceProfile(
        id="cafe_pho_tuy_hoa",
        name="Phố Cafe Tuy Hòa", name_vi="Khu phố cà phê Tuy Hòa",
        lat=13.0966, lon=109.3026,
        area="tuy_hoa",
        vibe=["chill", "local", "active"],
        recovery_score=0.7, fatigue_fit=0.8, social_energy_needed=0.3,
        crowd_timing={"morning": "medium", "midday": "low", "afternoon": "medium", "evening": "high"},
        type="cafe", child_safe=True, parking=True, indoor=True, price_range="budget",
        sunset_score=0.0, chill_score=0.8, local_score=0.85, nightlife_score=0.2,
        best_times=["07:00-09:00", "15:00-18:00"],
        avoid_times=[],
        mi_tip="Nhiều quán view biển, máy lạnh, wifi tốt. Tránh 10h-14h nắng gắt thì ngồi trong thoải mái.",
    ),

    # ── Food ──────────────────────────────────────────────────────────────────
    PlaceProfile(
        id="bun_ca_ngu",
        name="Bún Cá Ngừ Đại Dương", name_vi="Bún cá ngừ đại dương Tuy Hòa",
        lat=13.0950, lon=109.3005,
        area="tuy_hoa",
        vibe=["local"],
        recovery_score=0.6, fatigue_fit=0.8, social_energy_needed=0.2,
        crowd_timing={"morning": "high", "midday": "low", "afternoon": "low", "evening": "low"},
        type="food", child_safe=True, parking=True, indoor=True, price_range="budget",
        sunset_score=0.0, chill_score=0.5, local_score=1.0, nightlife_score=0.0,
        best_times=["06:00-09:00"],
        avoid_times=["10:00-17:00"],
        mi_tip="Đặc sản số 1 Phú Yên, ăn sáng. ~40k/phần. Phải ăn 1 lần không hối hận.",
    ),

    PlaceProfile(
        id="banh_can",
        name="Bánh Căn Phú Yên", name_vi="Bánh căn Ngọc Lan",
        lat=13.0940, lon=109.2998,
        area="tuy_hoa",
        vibe=["local"],
        recovery_score=0.6, fatigue_fit=0.9, social_energy_needed=0.1,
        crowd_timing={"morning": "high", "midday": "low", "afternoon": "low", "evening": "low"},
        type="food", child_safe=True, parking=True, indoor=False, price_range="budget",
        sunset_score=0.0, chill_score=0.4, local_score=1.0, nightlife_score=0.0,
        best_times=["06:00-09:00"],
        avoid_times=["10:00-17:00"],
        mi_tip="~30k/phần, bé ăn được. Địa phương nhất, không có ở nơi khác đâu.",
    ),

    PlaceProfile(
        id="hai_san_song_cau",
        name="Hải Sản Sông Cầu", name_vi="Khu hải sản tươi sống Sông Cầu",
        lat=14.1833, lon=109.2167,
        area="song_cau",
        vibe=["local", "active"],
        recovery_score=0.3, fatigue_fit=0.4, social_energy_needed=0.7,
        crowd_timing={"morning": "low", "midday": "medium", "afternoon": "medium", "evening": "high"},
        type="food", child_safe=True, parking=True, indoor=False, price_range="mid",
        sunset_score=0.0, chill_score=0.4, local_score=0.95, nightlife_score=0.3,
        best_times=["17:00-21:00"],
        avoid_times=[],
        mi_tip="Tôm hùm, cá ngừ, mực ống đều tươi sống. Giá thương lượng được. Buổi tối đông vui hơn nhưng vẫn mang không khí địa phương.",
    ),

    # ── Market / Street ────────────────────────────────────────────────────────
    PlaceProfile(
        id="cho_tuy_hoa",
        name="Chợ Tuy Hòa", name_vi="Chợ trung tâm Tuy Hòa",
        lat=13.0961, lon=109.2952,
        area="tuy_hoa",
        vibe=["local", "active"],
        recovery_score=0.2, fatigue_fit=0.3, social_energy_needed=0.5,
        crowd_timing={"morning": "high", "midday": "medium", "afternoon": "low", "evening": "low"},
        type="market", child_safe=True, parking=True, indoor=True, price_range="budget",
        sunset_score=0.0, chill_score=0.2, local_score=1.0, nightlife_score=0.0,
        best_times=["06:00-11:00"],
        avoid_times=["11:00-17:00"],
        mi_tip="Mua đặc sản về: khô cá ngừ, nước mắm Phú Yên, bánh tráng. Sáng sớm đông vui nhất.",
    ),

    # ── Nightlife ─────────────────────────────────────────────────────────────
    PlaceProfile(
        id="pho_dem_tuy_hoa",
        name="Phố Đêm Tuy Hòa", name_vi="Khu phố đêm Tuy Hòa",
        lat=13.0955, lon=109.2975,
        area="tuy_hoa",
        vibe=["active", "local"],
        recovery_score=0.1, fatigue_fit=0.1, social_energy_needed=0.8,
        crowd_timing={"morning": "low", "midday": "low", "afternoon": "low", "evening": "high"},
        type="nightlife", child_safe=False, parking=True, indoor=False, price_range="budget",
        sunset_score=0.0, chill_score=0.2, local_score=0.8, nightlife_score=0.8,
        best_times=["19:00-23:00"],
        avoid_times=["00:00-18:00"],
        mi_tip="Bia hơi, hải sản nướng vỉa hè, nhạc sống. Không cần đặt trước, cứ đi là có chỗ.",
    ),

    PlaceProfile(
        id="quan_nhau_bien",
        name="Quán Nhậu Biển", name_vi="Quán nhậu hải sản biển Tuy Hòa",
        lat=13.0900, lon=109.3100,
        area="tuy_hoa",
        vibe=["active", "local"],
        recovery_score=0.1, fatigue_fit=0.1, social_energy_needed=0.9,
        crowd_timing={"morning": "low", "midday": "low", "afternoon": "low", "evening": "high"},
        type="nightlife", child_safe=False, parking=True, indoor=False, price_range="mid",
        sunset_score=0.3, chill_score=0.3, local_score=0.85, nightlife_score=0.9,
        best_times=["18:00-23:00"],
        avoid_times=[],
        mi_tip="Mồi tươi, nhậu với gió biển. Khu này view cảng đẹp ban đêm.",
    ),
]

# ── Index helpers ──────────────────────────────────────────────────────────────

_BY_ID: dict[str, PlaceProfile] = {p.id: p for p in PHU_YEN_PLACES}
_BY_TYPE: dict[str, list[PlaceProfile]] = {}
for _p in PHU_YEN_PLACES:
    _BY_TYPE.setdefault(_p.type, []).append(_p)


def get_place(place_id: str) -> PlaceProfile | None:
    return _BY_ID.get(place_id)


def find_places(
    type: str | None = None,
    vibe: str | None = None,
    fatigue_level: str = "none",    # none|low|medium|high|critical
    child_safe: bool | None = None,
    indoor: bool | None = None,
    max_results: int = 3,
) -> list[PlaceProfile]:
    """
    Find places matching emotional + practical criteria.
    Returns sorted by best fit for current user state.
    """
    candidates = list(PHU_YEN_PLACES)

    if type:
        candidates = [p for p in candidates if p.type == type]
    if child_safe is not None:
        candidates = [p for p in candidates if p.child_safe == child_safe]
    if indoor is not None:
        candidates = [p for p in candidates if p.indoor == indoor]
    if vibe:
        candidates = [p for p in candidates if vibe in p.vibe]

    # Sort by fatigue fit when tired
    fatigue_weight = {"none": 0, "low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
    fw = fatigue_weight.get(fatigue_level, 0)

    def score(p: PlaceProfile) -> float:
        s = p.chill_score * 0.3 + p.local_score * 0.2
        if fw > 0:
            s += p.fatigue_fit * fw * 0.5
        return s

    candidates.sort(key=score, reverse=True)
    return candidates[:max_results]


def best_for_mood(
    healing: bool = False,
    tired: bool = False,
    hungry: bool = False,
    nightlife: bool = False,
    child_safe: bool = True,
) -> list[PlaceProfile]:
    """Quick emotional routing."""
    if nightlife:
        return find_places(type="nightlife", child_safe=False, max_results=2)
    if hungry:
        return find_places(type="food", child_safe=child_safe, max_results=2)
    if tired or healing:
        return find_places(fatigue_level="high", vibe="chill", max_results=3)
    return find_places(vibe="local", max_results=3)
