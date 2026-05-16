"""
Vietnamese Social Context Intelligence Database

Detects:
- Group composition (solo, couple, family, group of friends)
- Social energy (high/medium/low)
- Movement resistance and mobility tolerance
- Crowd preference
- Romantic context
- Local vs tourist preference
- Nightlife vs daytime social patterns
"""
from __future__ import annotations

# ── Group Composition Detection ───────────────────────────────────────────────
SOLO_MARKERS: list[str] = [
    "đi một mình", "đi solo", "solo", "một mình thôi",
    "mình thôi", "chỉ có mình", "không có ai đi cùng",
    "đi một mình nha", "tự đi", "tự túc",
    "me time", "tự khám phá",
]

COUPLE_MARKERS: list[str] = [
    "đi với người yêu", "đi với ny", "với người yêu", "với ny",
    "2 người", "hai người",
    "đi date", "date night", "hẹn hò", "romantic",
    "cặp đôi", "đôi lứa", "mình và người thương",
    "đi với vợ", "đi với chồng", "đi với bạn gái", "đi với bạn trai",
    "với vợ", "với chồng", "với bạn gái", "với bạn trai",
    "chỉ 2 người", "2 đứa thôi",
]

FAMILY_MARKERS: list[str] = [
    "cả nhà", "gia đình", "có trẻ em", "có con nhỏ", "có bé",
    "đi gia đình", "mang theo con", "đưa con đi",
    "bé con theo", "cả gia đình", "gia đình đông",
    "bố mẹ và con", "anh chị em", "ba má đi cùng",
    "có em bé", "có baby", "baby theo",
    "nhiều thế hệ", "ông bà đi cùng",
    "xe lăn", "người già", "người cao tuổi",
]

GROUP_MARKERS: list[str] = [
    "bạn bè", "nhóm bạn", "cả nhóm", "anh em", "squad",
    "cả team", "hội bạn", "nhiều người", "đông người",
    "gang đi chơi", "crew", "hội tụ",
    "3 người", "4 người", "5 người", "6 người", "cả hội",
    "mấy anh em", "mấy đứa", "tụi mình", "tụi tao",
    "cả lớp", "cả phòng", "cả công ty",
]

# ── Social Energy Level ────────────────────────────────────────────────────────
HIGH_ENERGY_MARKERS: list[str] = [
    "muốn đông vui", "đông vui chút", "nhộn nhịp",
    "party", "liên hoan", "tiệc", "gặp mặt",
    "vui vẻ", "náo nhiệt", "sôi động",
    "karaoke", "bar", "club", "đi bar",
    "muốn vui", "cần vui lên", "tăng mood",
    "hype lên", "chill party", "social",
]

LOW_ENERGY_MARKERS: list[str] = [
    "muốn yên tĩnh", "yên tĩnh thôi", "không muốn đông",
    "tránh đông", "ít người", "ít người thôi",
    "chỗ vắng", "nơi vắng", "vắng người",
    "không muốn ồn", "ít ồn ào", "không muốn ồn ào",
    "chill nhẹ", "nhẹ nhàng thôi", "thoải mái thôi",
    "chỉ cần yên", "yên yên thôi",
    "không muốn gặp nhiều người", "introvert mode",
    "hướng nội", "muốn ở một mình",
]

# ── Movement Tolerance / Resistance ──────────────────────────────────────────
LOW_MOVEMENT_MARKERS: list[str] = [
    "gần thôi", "gần gần thôi", "gần đây thôi",
    "ngại đi xa", "không muốn đi xa", "đừng đi xa",
    "lười đi xa", "lười di chuyển", "lười quá",
    "không muốn di chuyển nhiều", "không muốn di chuyển xa",
    "đi bộ được không", "đi bộ thôi", "không muốn lái xe",
    "gần khách sạn", "gần chỗ đang ở", "gần đây",
    "trong tầm đi bộ", "5 phút thôi", "10 phút thôi",
    "không muốn tốn thời gian đường", "đường ngắn thôi",
    "không muốn mất công", "tiện đường",
    "trên đường về", "trên đường đi",
    "không muốn chạy xe xa", "không muốn đổ xăng",
    # Additional no-accent / indirect forms
    "không muốn đi đâu", "không muốn đi đâu cả", "không muốn đi",
    "ngại đi", "ngại di chuyển", "không đi xa đâu",
    "chỗ gần nhất", "gần nhất thôi", "tiện nhất thôi",
]

HIGH_MOVEMENT_MARKERS: list[str] = [
    "đi xa cũng được", "khám phá thôi", "đi loanh quanh",
    "muốn khám phá", "muốn đi nhiều chỗ", "road trip",
    "không ngại xa", "xa cũng được", "cứ đi thôi",
    "phiêu lưu", "adventure", "đi tới đâu hay tới đó",
    "tour tự túc", "tự lái xe khám phá",
]

# ── Crowd Tolerance ───────────────────────────────────────────────────────────
LOW_CROWD_TOLERANCE: list[str] = [
    "đông quá", "đông ghê", "đông kinh khủng",
    "đông như trẩy hội", "đông nghẹt", "đông nghịt",
    "full người", "hết chỗ", "không còn chỗ",
    "nhức đầu vì đông", "ngộp vì đông", "không chịu được đông",
    "tránh chỗ đông", "tránh đông", "chỗ ít người",
    "không thích đông", "ngại đông",
    "chỗ yên tĩnh", "nơi vắng", "ít khách",
]

HIGH_CROWD_TOLERANCE: list[str] = [
    "đông vui", "muốn đông", "sôi động",
    "chợ đêm", "phố đi bộ", "thị trường",
    "không ngại đông", "đông cũng được",
    "náo nhiệt", "nhộn nhịp", "vui vẻ đông người",
]

# ── Romantic Context ──────────────────────────────────────────────────────────
ROMANTIC_MARKERS: list[str] = [
    "sunset đẹp", "hoàng hôn đẹp", "ngắm hoàng hôn",
    "riêng tư", "2 người thôi", "chỉ 2 đứa",
    "view đẹp", "view lãng mạn", "không khí lãng mạn",
    "cafe view biển", "nhìn ra biển", "ngồi ngắm biển",
    "hẹn hò", "date night", "romantic dinner",
    "tặng quà", "bất ngờ", "ngạc nhiên",
    "đặc biệt", "đêm đặc biệt", "buổi tối đặc biệt",
    "kỷ niệm", "celebrate", "celebration",
    "bình minh đôi", "ngắm bình minh cùng",
]

# ── Local vs Tourist Preference ───────────────────────────────────────────────
LOCAL_PREFERENCE_MARKERS: list[str] = [
    "local local", "người địa phương ăn", "dân địa phương",
    "quán local", "đồ ăn local", "ẩm thực địa phương",
    "authentic", "authentics", "chính thống",
    "không tourist", "ít khách du lịch", "tránh tourist",
    "hidden gem", "chỗ ít người biết", "bí mật địa phương",
    "người ta hay ăn", "người bản địa ăn",
    "quán bình dân địa phương", "quán xóm",
    "ít được biết đến", "không nổi tiếng nhưng ngon",
    "underrated", "chỗ ngon ít người biết",
    "đừng chỗ fancy", "không cần fancy",
    "không cần fancy chỗ", "quán bình dân thôi",
]

TOURIST_OKAY_MARKERS: list[str] = [
    "nổi tiếng", "nhiều người biết", "check-in",
    "instagram", "sống ảo", "đẹp để chụp",
    "nổi tiếng nhất", "best of", "top quán",
    "review nhiều", "nhiều review",
]

# ── Family with Children ──────────────────────────────────────────────────────
CHILD_FRIENDLY_SIGNALS: list[str] = [
    "có con nhỏ", "có bé", "có trẻ em", "em bé",
    "bé con", "bé theo", "mang con theo",
    "chỗ cho bé vui chơi", "có chỗ cho bé",
    "an toàn cho bé", "bé an toàn",
    "không quá cay", "không cay", "đồ ăn không cay",
    "phần bé", "phần nhỏ", "đồ ăn bé được",
    "bể bơi trẻ em", "khu vui chơi",
    "có toilet", "toilet sạch",
    "chỗ đậu xe rộng", "đậu xe dễ",
    "không dốc", "bằng phẳng", "dễ đi",
    "ghế ngồi thoải mái", "phòng rộng",
]

# ── Parking & Logistics ───────────────────────────────────────────────────────
LOGISTICS_MARKERS: list[str] = [
    "đậu xe", "chỗ đậu xe", "parking",
    "đậu xe dễ", "có chỗ đậu", "bãi đậu xe",
    "xe máy", "ô tô", "xe hơi",
    "giao thông", "di chuyển thế nào",
    "grab được không", "có grab không",
    "đi được không", "dễ tìm không", "dễ đến không",
]


def detect_group_type(text: str) -> str:
    """Returns: solo | couple | family | group | unknown"""
    if any(m in text for m in FAMILY_MARKERS):
        return "family"
    if any(m in text for m in COUPLE_MARKERS):
        return "couple"
    if any(m in text for m in GROUP_MARKERS):
        return "group"
    if any(m in text for m in SOLO_MARKERS):
        return "solo"
    return "unknown"


def score_social_energy(text: str) -> str:
    """Returns: high | medium | low"""
    high = sum(1 for m in HIGH_ENERGY_MARKERS if m in text)
    low = sum(1 for m in LOW_ENERGY_MARKERS if m in text)
    if high > low:
        return "high"
    if low > high:
        return "low"
    return "medium"


def score_movement_tolerance(text: str) -> str:
    """Returns: low | medium | high"""
    low = sum(1 for m in LOW_MOVEMENT_MARKERS if m in text)
    high = sum(1 for m in HIGH_MOVEMENT_MARKERS if m in text)
    if low > 0:
        return "low"
    if high > 0:
        return "high"
    return "medium"


def score_crowd_tolerance(text: str) -> str:
    """Returns: low | medium | high"""
    low = sum(1 for m in LOW_CROWD_TOLERANCE if m in text)
    high = sum(1 for m in HIGH_CROWD_TOLERANCE if m in text)
    if low > 0 and low >= high:
        return "low"
    if high > low:
        return "high"
    return "medium"


def is_romantic_context(text: str) -> bool:
    return any(m in text for m in ROMANTIC_MARKERS)


def prefers_local(text: str) -> bool:
    return any(m in text for m in LOCAL_PREFERENCE_MARKERS)


def needs_child_friendly(text: str) -> bool:
    return any(m in text for m in CHILD_FRIENDLY_SIGNALS)
