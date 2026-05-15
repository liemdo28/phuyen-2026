from __future__ import annotations

# Canonical emotional vocabulary — single source of truth.
# All modules that detect emotional signals import from here.

# ── Travel-context stress (shallow, fast detection) ──────────────────────────
TRAVEL_STRESS_TOKENS = [
    "mệt", "roi", "rối", "không biết", "ko biết",
    "nhiều quá", "khó chọn", "khó quá", "kẹt xe", "mưa quá",
]

# ── Journey-level emotional signals (deeper, trip-phase detection) ────────────
JOURNEY_STRESS_TOKENS = [
    "mệt", "chán", "ức", "stress", "bực", "lo", "sợ",
    "không ổn", "quá nhiều", "overwhelm",
]
JOURNEY_EXCITEMENT_TOKENS = [
    "vui", "thích", "tuyệt", "hay quá", "đẹp", "wow",
    "ổn", "ok", "thú vị",
]
JOURNEY_BURNOUT_TOKENS = [
    "thôi nghỉ", "về thôi", "không muốn", "đủ rồi",
    "mệt lắm", "nghỉ thôi", "không nổi",
]
JOURNEY_COMFORT_TOKENS = [
    "dễ chịu", "thoải mái", "ổn áp", "bình thường", "được", "ok bạn",
]

# ── Fatigue signals (physical tiredness) ─────────────────────────────────────
FATIGUE_TOKENS = [
    "buồn ngủ", "đuối", "mệt", "kiệt sức", "ngủ thôi",
]

# ── Life-context signals (work/lifestyle/social) ─────────────────────────────
WORK_STRESS_TOKENS = [
    "công việc", "deadline", "họp", "sếp", "áp lực", "dự án", "overtime",
    "làm thêm", "căng thẳng", "mệt vì làm",
]
RECOVERY_TOKENS = [
    "nghỉ ngơi", "cần nghỉ", "kiệt sức", "muốn nghỉ", "burn out", "burnout",
    "không nổi nữa", "cần nạp năng lượng", "nạp pin", "recharge",
]
SOCIAL_HIGH_TOKENS = [
    "bạn bè", "hội bạn", "nhóm", "party", "tiệc", "cùng nhau", "đi chơi cùng",
    "gặp gỡ", "tụ tập",
]
SOCIAL_LOW_TOKENS = [
    "một mình", "solo", "yên tĩnh", "không muốn gặp ai", "cần không gian riêng",
    "tránh xa", "ẩn", "im lặng",
]
EMOTIONAL_LOW_TOKENS = [
    "buồn", "chán", "trống rỗng", "cô đơn", "không vui", "thất vọng",
    "không có hứng", "flat", "meh",
]
EMOTIONAL_HIGH_TOKENS = [
    "vui", "hào hứng", "năng lượng", "sẵn sàng", "tuyệt vời", "thích quá",
    "excited", "hạnh phúc", "phấn khởi",
]
LIFE_BURNOUT_TOKENS = [
    "quá tải", "overwhelm", "quá nhiều thứ", "không thở được", "bão não",
    "muốn biến mất", "cần thoát", "đủ rồi", "không muốn nghĩ",
]
LIFESTYLE_BUSY_TOKENS = [
    "bận", "không có thời gian", "lịch kín", "không rảnh", "tight schedule",
    "ít thời gian", "tranh thủ",
]
LIFESTYLE_FREE_TOKENS = [
    "rảnh", "thoải mái", "không vội", "có thời gian", "thư thả",
    "không có gì đặc biệt", "tự do",
]

# ── Excitement / Relaxation (travel companion quick detection) ────────────────
COMPANION_EXCITEMENT_TOKENS = [
    "wow", "đẹp", "chill", "sunset", "hoàng hôn", "check-in",
    "sống ảo", "hào hứng", "thích quá",
]
RELAXED_TOKENS = [
    "cafe", "cà phê", "chụp ảnh", "chụp hình", "ngắm", "thảnh thơi",
]
