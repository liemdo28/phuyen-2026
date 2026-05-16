"""
Vietnamese Emotional Intelligence Database

Maps real human emotional expressions to structured emotional states.
Covers sarcasm, exaggeration, indirect emotional signaling, fatigue language,
recovery language, and social decompression patterns.
"""
from __future__ import annotations

# ── Fatigue & Exhaustion ──────────────────────────────────────────────────────
# Both direct and indirect fatigue expressions
FATIGUE_PATTERNS: list[tuple[str, float]] = [
    # Direct high-signal
    ("mệt xỉu", 0.9),
    ("mệt quá trời", 0.9),
    ("mệt muốn chết", 0.95),
    ("kiệt sức", 0.9),
    ("hết pin", 0.85),
    ("hết năng lượng", 0.85),
    ("không còn sức", 0.85),
    ("đuối quá", 0.85),
    ("đuối lắm", 0.8),
    ("rã rời", 0.8),
    ("bã người", 0.75),
    ("bở người", 0.75),
    ("die rồi", 0.8),
    ("chết rồi", 0.7),
    ("sắp ngất", 0.75),
    # Medium signal
    ("mệt lắm", 0.7),
    ("mệt rồi", 0.65),
    ("mệt quá", 0.7),
    ("mệt", 0.5),
    ("buồn ngủ", 0.6),
    ("buồn ngủ quá", 0.75),
    ("ngủ gật", 0.7),
    ("ngủ không được", 0.5),
    ("đuối", 0.6),
    ("không muốn làm gì", 0.6),
    ("lười quá", 0.55),
    ("ngại quá", 0.5),
    # Indirect / recovery language
    ("cần nghỉ", 0.7),
    ("muốn nghỉ", 0.65),
    ("nghỉ tí", 0.55),
    ("nghỉ chút", 0.55),
    ("nằm chút", 0.6),
    ("nằm nghỉ", 0.65),
    ("nằm xỉu", 0.7),
    ("nằm lăn", 0.6),
    ("ngồi thở", 0.5),
    ("cần nạp năng lượng", 0.6),
    ("recharge", 0.55),
    ("muốn reset", 0.6),
    ("hết xăng", 0.7),
    ("không còn xăng", 0.75),
    ("chạy hết xăng rồi", 0.8),
    # Gen Z fatigue
    ("não cá vàng", 0.45),
    ("não đông đặc", 0.5),
    ("não offline", 0.55),
    ("não không hoạt động", 0.5),
    ("đơ người", 0.6),
    ("đơ hết rồi", 0.65),
    ("lag não", 0.55),
    ("não lag", 0.55),
    ("buffering", 0.45),
]

# ── Stress & Overwhelm ────────────────────────────────────────────────────────
STRESS_PATTERNS: list[tuple[str, float]] = [
    # High signal
    ("stress vãi", 0.9),
    ("stress quá trời", 0.9),
    ("nổ đầu", 0.85),
    ("loạn não", 0.8),
    ("rối tung rồi", 0.8),
    ("rối cả lên", 0.8),
    ("không biết phải làm sao", 0.75),
    ("điên rồi", 0.75),
    ("bực quá", 0.7),
    ("bực mình ghê", 0.7),
    ("ức chế quá", 0.75),
    ("căng thẳng quá", 0.8),
    ("áp lực quá", 0.75),
    # Medium signal
    ("stress", 0.6),
    ("rối", 0.5),
    ("lo lắng", 0.55),
    ("lo quá", 0.6),
    ("không biết", 0.3),
    ("không chắc", 0.3),
    ("khó quyết định", 0.55),
    ("khó chọn", 0.5),
    ("nhiều quá", 0.45),
    ("quá nhiều thứ", 0.5),
    ("choáng ngợp", 0.65),
    ("ngộp", 0.6),
    # Indirect stress
    ("đau đầu quá", 0.65),
    ("nhức đầu", 0.55),
    ("nhức đầu quá", 0.65),
    ("thở không nổi", 0.7),
    ("tức quá", 0.6),
    ("khó chịu", 0.45),
]

# ── Hunger & Food Need ────────────────────────────────────────────────────────
HUNGER_PATTERNS: list[tuple[str, float]] = [
    # Direct high signal
    ("đói xỉu", 0.95),
    ("đói muốn chết", 0.95),
    ("đói bẹp", 0.9),
    ("đói cồn cào", 0.85),
    ("bụng kêu", 0.85),
    ("bụng trống", 0.8),
    ("đói quá trời", 0.9),
    ("đói cực kỳ", 0.85),
    # Medium signal
    ("đói lắm", 0.75),
    ("đói rồi", 0.7),
    ("đói quá", 0.75),
    ("đói", 0.55),
    ("bụng đói", 0.6),
    ("chưa ăn gì", 0.7),
    ("chưa ăn sáng", 0.65),
    ("chưa ăn trưa", 0.65),
    ("chưa ăn tối", 0.65),
    # Indirect
    ("ăn gì đây", 0.5),
    ("kiếm gì ăn", 0.6),
    ("ăn gì bây giờ", 0.6),
    ("muốn ăn", 0.5),
    ("thèm ăn", 0.55),
    ("thèm", 0.4),
    ("nạp năng lượng", 0.5),
    ("ăn bù", 0.55),
    # Thirsty
    ("khát", 0.5),
    ("khát nước", 0.6),
    ("uống gì đây", 0.45),
    ("muốn uống", 0.4),
]

# ── Excitement & Positive Energy ──────────────────────────────────────────────
EXCITEMENT_PATTERNS: list[tuple[str, float]] = [
    ("hào hứng quá", 0.9),
    ("hype quá", 0.85),
    ("hype lên", 0.8),
    ("phấn khích", 0.8),
    ("thích quá", 0.75),
    ("thích phết", 0.65),
    ("mê quá", 0.75),
    ("đỉnh quá", 0.8),
    ("đỉnh lắm", 0.75),
    ("ngầu quá", 0.75),
    ("ngầu lắm", 0.7),
    ("xịn quá", 0.7),
    ("xịn lắm", 0.65),
    ("đẹp quá", 0.7),
    ("đẹp lắm", 0.65),
    ("tuyệt quá", 0.75),
    ("wow", 0.65),
    ("wao", 0.65),
    ("ố la la", 0.6),
    ("ồ", 0.3),
    ("oo", 0.3),
    ("trời ơi đẹp", 0.8),
    ("muốn sống ở đây luôn", 0.8),
    ("sống ảo quá", 0.65),
    ("chill quá", 0.7),
    ("vui quá", 0.7),
    ("vui lắm", 0.65),
    ("sướng quá", 0.7),
    ("thư giãn quá", 0.65),
    ("thoải mái quá", 0.65),
    ("tan chảy", 0.7),
    ("mlem mlem", 0.7),
    ("ngon quá", 0.65),
    ("ngon lắm", 0.65),
]

# ── Sarcasm & Exaggeration Database ──────────────────────────────────────────
# Vietnamese internet culture uses exaggeration constantly
# Pattern → (literal_meaning, actual_intensity_multiplier, emotion)
SARCASM_PATTERNS: list[tuple[str, str, float, str]] = [
    # Hunger exaggeration
    ("đói xỉu", "very hungry", 0.95, "hungry"),
    ("đói muốn chết", "extremely hungry", 1.0, "hungry"),
    ("đói bẹp", "very hungry", 0.9, "hungry"),
    # Fatigue exaggeration
    ("mệt muốn chết", "extremely tired", 1.0, "fatigue"),
    ("mệt xỉu", "very tired", 0.9, "fatigue"),
    ("chết rồi", "very exhausted/overwhelmed", 0.85, "fatigue"),
    ("die rồi", "very exhausted/overwhelmed", 0.85, "fatigue"),
    # Heat exaggeration
    ("nóng muốn chết", "extremely hot", 0.95, "discomfort"),
    ("nóng chảy mỡ", "extremely hot", 1.0, "discomfort"),
    ("nóng như thiêu như đốt", "very hot", 0.9, "discomfort"),
    ("nóng vãi", "extremely hot", 0.9, "discomfort"),
    # Crowd exaggeration
    ("đông như trẩy hội", "very crowded", 0.9, "crowded"),
    ("đông nghịt", "very crowded", 0.85, "crowded"),
    ("đông nghẹt", "very crowded", 0.85, "crowded"),
    ("đông kinh khủng", "extremely crowded", 0.9, "crowded"),
    ("đông muốn ngộp", "overwhelmingly crowded", 0.95, "crowded"),
    ("nhét không vô", "completely full", 0.9, "crowded"),
    # Beauty exaggeration
    ("đẹp muốn khóc", "breathtakingly beautiful", 0.95, "excitement"),
    ("đẹp vãi luôn", "extremely beautiful", 0.9, "excitement"),
    ("đẹp tuyệt vời", "very beautiful", 0.85, "excitement"),
    ("đẹp thần sầu", "stunningly beautiful", 0.9, "excitement"),
    # Deliciousness exaggeration
    ("ngon vãi", "extremely delicious", 0.9, "food_positive"),
    ("ngon quá trời", "extremely delicious", 0.9, "food_positive"),
    ("ngon kinh khủng", "incredibly delicious", 0.95, "food_positive"),
    ("ngon phát khóc", "so delicious it's overwhelming", 1.0, "food_positive"),
    ("ngon tuyệt cú mèo", "extremely delicious", 0.85, "food_positive"),
    # Sarcasm / irony markers (actual sentiment is negative)
    ("vui phết", "somewhat positive but may be sarcastic", 0.4, "mild_positive"),
    ("hay thật", "may be sarcastic", 0.4, "mild_positive"),
    ("thích thật", "may be sarcastic", 0.4, "mild_positive"),
    ("tốt thật", "may be sarcastic", 0.4, "mild_positive"),
    ("ổn thôi", "okay but not great", 0.3, "neutral_low"),
    ("cũng được", "acceptable but not enthusiastic", 0.25, "neutral_low"),
    ("bình thường", "mediocre", 0.2, "neutral_low"),
    ("tạm", "barely okay", 0.15, "neutral_low"),
    ("tạm ổn", "barely okay", 0.2, "neutral_low"),
]

# ── Confusion & Indecision ────────────────────────────────────────────────────
CONFUSION_PATTERNS: list[tuple[str, float]] = [
    ("không biết phải đi đâu", 0.8),
    ("không biết ăn gì", 0.75),
    ("không biết làm gì", 0.7),
    ("không biết chọn", 0.65),
    ("không biết", 0.4),
    ("biết đâu mà chọn", 0.65),
    ("khó quá không chọn được", 0.7),
    ("khó chọn", 0.6),
    ("rối quá", 0.7),
    ("nhiều lựa chọn quá", 0.55),
    ("sao bây giờ", 0.5),
    ("bây giờ sao đây", 0.55),
    ("phải làm sao", 0.5),
    ("làm sao bây giờ", 0.55),
    ("đi đâu bây giờ", 0.5),
    ("ăn gì bây giờ", 0.5),
    ("uống gì bây giờ", 0.45),
    ("nên làm gì", 0.5),
    ("nên đi đâu", 0.5),
    ("nên ăn gì", 0.5),
]

# ── Recovery & Rest Seeking ───────────────────────────────────────────────────
RECOVERY_PATTERNS: list[tuple[str, float]] = [
    # High-signal recovery intent
    ("cần được nghỉ", 0.9),
    ("muốn được nghỉ ngơi", 0.85),
    ("cần nghỉ ngơi", 0.85),
    ("muốn nằm", 0.8),
    ("muốn nghỉ", 0.75),
    ("đi healing", 0.8),
    ("healing trip", 0.75),
    ("muốn reset", 0.75),
    ("cần reset", 0.8),
    ("recovery", 0.7),
    # Medium signal
    ("kiếm chỗ chill", 0.65),
    ("muốn yên tĩnh", 0.7),
    ("chỗ yên tĩnh", 0.6),
    ("ít người thôi", 0.65),
    ("không muốn đi xa", 0.6),
    ("gần thôi", 0.5),
    ("chỗ mát mẻ", 0.55),
    ("chỗ thoáng", 0.5),
    ("không muốn đông", 0.65),
    ("tránh đông", 0.6),
    # Indirect recovery
    ("ngồi thở tí", 0.55),
    ("dừng chân", 0.5),
    ("nghỉ chân", 0.55),
    ("ngồi nghỉ", 0.6),
    ("vào trong thôi", 0.45),
    ("vào quán nghỉ", 0.55),
    ("uống nước nghỉ", 0.5),
    ("me time", 0.65),
    ("một mình thôi", 0.55),
]

# ── Social Drinking / Nightlife Emotional Context ─────────────────────────────
SOCIAL_DRINKING_EMOTIONS: list[tuple[str, str]] = [
    # Drinking invitations
    ("làm vài lon", "social_drinking"),
    ("quất vài chai", "social_drinking"),
    ("làm vài ly", "social_drinking"),
    ("uống vài lon", "social_drinking"),
    ("nhậu không", "social_drinking"),
    ("nhậu thôi", "social_drinking"),
    ("nhậu nhẹt", "social_drinking"),
    ("nhậu một chút", "social_drinking"),
    ("bia không", "social_drinking"),
    ("bia thôi", "social_drinking"),
    ("đi làm tí", "social_drinking"),
    ("làm tí đi", "social_drinking"),
    # Decompression after day
    ("giải tỏa stress", "social_decompression"),
    ("thư giãn tí", "social_decompression"),
    ("xả stress", "social_decompression"),
    ("giải nhiệt", "social_decompression"),
    ("giải sầu", "social_decompression"),
    ("quên hết mọi thứ", "social_decompression"),
    ("hết ngày rồi", "social_decompression"),
    ("cuối ngày rồi", "social_decompression"),
    ("đã xong việc", "social_decompression"),
    # Late night social
    ("đêm nay đi đâu", "nightlife"),
    ("tối nay làm gì", "nightlife"),
    ("đêm nay chill đâu", "nightlife"),
    ("pub nào chill", "nightlife"),
    ("quán bar nào", "nightlife"),
    ("đi club không", "nightlife"),
]

# ── Complete Emotional Signal → Weights ──────────────────────────────────────
def score_fatigue(text: str) -> float:
    """Score fatigue level 0.0–1.0 from text."""
    score = 0.0
    for pattern, weight in FATIGUE_PATTERNS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_stress(text: str) -> float:
    """Score stress level 0.0–1.0 from text."""
    score = 0.0
    for pattern, weight in STRESS_PATTERNS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_hunger(text: str) -> float:
    """Score hunger level 0.0–1.0 from text."""
    score = 0.0
    for pattern, weight in HUNGER_PATTERNS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_excitement(text: str) -> float:
    """Score excitement level 0.0–1.0 from text."""
    score = 0.0
    for pattern, weight in EXCITEMENT_PATTERNS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_confusion(text: str) -> float:
    """Score confusion level 0.0–1.0 from text."""
    score = 0.0
    for pattern, weight in CONFUSION_PATTERNS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def score_recovery_need(text: str) -> float:
    """Score recovery need 0.0–1.0 from text."""
    score = 0.0
    for pattern, weight in RECOVERY_PATTERNS:
        if pattern in text:
            score = max(score, weight)
    return min(score, 1.0)


def detect_sarcasm(text: str) -> tuple[bool, float]:
    """
    Returns (is_sarcastic, confidence).
    Confidence 0.0–1.0.
    """
    for pattern, _, intensity, _ in SARCASM_PATTERNS:
        if pattern in text:
            # Sarcasm confidence based on context markers
            sarcasm_markers = ["thật", "phết", "thật sự", "mà thôi", "đấy"]
            sarcasm_boost = sum(0.1 for m in sarcasm_markers if m in text)
            # Positive exaggerations are not sarcasm, they're enthusiasm
            enthusiasm_markers = ["muốn chết", "xỉu", "vãi", "kinh khủng", "phát khóc"]
            if any(m in pattern for m in enthusiasm_markers):
                return False, 0.0
            if sarcasm_boost > 0:
                return True, min(0.5 + sarcasm_boost, 0.9)
    return False, 0.0


def detect_social_context(text: str) -> str:
    """Detect social drinking / nightlife context."""
    for pattern, context_type in SOCIAL_DRINKING_EMOTIONS:
        if pattern in text:
            return context_type
    return ""
