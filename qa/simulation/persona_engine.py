"""
Human Persona Engine — Simulates millions of real human communication styles.
Each persona has distinct language patterns, emotional baselines, and behavioral traits.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class PersonaType(Enum):
    GEN_Z = "gen_z"
    TOURIST_FOREIGN = "tourist_foreign"
    TOURIST_DOMESTIC = "tourist_domestic"
    ANGRY_CUSTOMER = "angry_customer"
    STRESSED_TRAVELER = "stressed_traveler"
    HUNGRY_TRAVELER = "hungry_traveler"
    EXHAUSTED_TRAVELER = "exhausted_traveler"
    LOCAL_USER = "local_user"
    DRUNK_USER = "drunk_user"
    TYPO_HEAVY = "typo_heavy"
    NO_ACCENT = "no_accent"
    MEME_USER = "meme_user"
    PASSIVE_AGGRESSIVE = "passive_aggressive"
    EMOTIONAL_USER = "emotional_user"
    SARCASTIC_USER = "sarcastic_user"
    OLDER_USER = "older_user"
    BUSINESS_USER = "business_user"
    CONFUSED_TOURIST = "confused_tourist"
    LATE_NIGHT_USER = "late_night_user"
    BUDGET_TRAVELER = "budget_traveler"


@dataclass
class Persona:
    type: PersonaType
    name: str
    age_range: tuple
    language_style: str
    emotional_baseline: float  # 0.0 = calm, 1.0 = extreme emotion
    typo_rate: float           # 0.0 = perfect, 1.0 = chaos
    slang_level: float         # 0.0 = formal, 1.0 = heavy slang
    accent_probability: float  # probability of using Vietnamese accents
    patience: float            # 0.0 = impatient, 1.0 = very patient
    message_length: str        # "short", "medium", "long"
    fragmentation: float       # tendency to send fragmented messages
    context_continuity: float  # tendency to maintain conversation context
    traits: List[str] = field(default_factory=list)
    sample_openers: List[str] = field(default_factory=list)


# ── Persona Definitions ────────────────────────────────────

PERSONAS = {
    PersonaType.GEN_Z: Persona(
        type=PersonaType.GEN_Z,
        name="Gen Z Traveler",
        age_range=(18, 26),
        language_style="gen_z_slang",
        emotional_baseline=0.5,
        typo_rate=0.3,
        slang_level=0.9,
        accent_probability=0.4,
        patience=0.5,
        message_length="short",
        fragmentation=0.8,
        context_continuity=0.4,
        traits=["uses 'vl' 'vcl' 'oke' 'ez'", "sends multiple short messages", "emoji heavy", "meme references"],
        sample_openers=[
            "đi đâu ngon ngon đi",
            "ăn gì giờ này bro",
            "quán nào chill nhất",
            "local local thôi mấy ông",
            "ez ez gợi ý đi",
            "mệt vl luôn",
            "chill spot nào đỉnh ko",
            "flex một tí dc ko 😂",
        ],
    ),

    PersonaType.TOURIST_FOREIGN: Persona(
        type=PersonaType.TOURIST_FOREIGN,
        name="Foreign Tourist",
        age_range=(25, 55),
        language_style="broken_vietnamese_or_english",
        emotional_baseline=0.3,
        typo_rate=0.2,
        slang_level=0.1,
        accent_probability=0.05,
        patience=0.6,
        message_length="medium",
        fragmentation=0.3,
        context_continuity=0.7,
        traits=["mixes English/Vietnamese", "confused about local customs", "asks basic questions", "over-explains context"],
        sample_openers=[
            "where can eat good food phu yen?",
            "how get from Tuy Hoa to Ganh Da Dia?",
            "is beach safe for swimming?",
            "recommend local restaurant not tourist",
            "tôi muốn ăn hải sản, chỗ nào ngon?",
            "beach đẹp where?",
        ],
    ),

    PersonaType.TOURIST_DOMESTIC: Persona(
        type=PersonaType.TOURIST_DOMESTIC,
        name="Domestic Tourist",
        age_range=(22, 45),
        language_style="standard_vietnamese",
        emotional_baseline=0.4,
        typo_rate=0.15,
        slang_level=0.4,
        accent_probability=0.85,
        patience=0.6,
        message_length="medium",
        fragmentation=0.4,
        context_continuity=0.6,
        traits=["compares to Đà Nẵng/Nha Trang", "asks about hidden gems", "budget conscious"],
        sample_openers=[
            "quán hải sản ngon mà không phải bẫy khách du lịch",
            "bãi biển nào đẹp không đông?",
            "lịch trình 3 ngày cho gia đình",
            "xe từ Đà Nẵng đến đây mất bao lâu?",
            "tiết kiệm hơn Đà Nẵng không?",
        ],
    ),

    PersonaType.ANGRY_CUSTOMER: Persona(
        type=PersonaType.ANGRY_CUSTOMER,
        name="Angry Customer",
        age_range=(25, 50),
        language_style="aggressive_vietnamese",
        emotional_baseline=0.9,
        typo_rate=0.25,
        slang_level=0.5,
        accent_probability=0.7,
        patience=0.1,
        message_length="medium",
        fragmentation=0.6,
        context_continuity=0.3,
        traits=["all caps sometimes", "demands answers", "threatens to leave", "repeats questions"],
        sample_openers=[
            "Sao AI lại gợi ý chỗ đó vậy???",
            "Tôi hỏi 3 lần rồi mà không ai trả lời",
            "Đây là lần cuối tôi hỏi nhé",
            "Dịch vụ gì mà tệ thế này",
            "Chỗ đó bị chặt chém rồi sao còn gợi ý???",
            "Trả lời đúng vào câu hỏi đi",
        ],
    ),

    PersonaType.STRESSED_TRAVELER: Persona(
        type=PersonaType.STRESSED_TRAVELER,
        name="Stressed Traveler",
        age_range=(28, 45),
        language_style="anxious_vietnamese",
        emotional_baseline=0.75,
        typo_rate=0.2,
        slang_level=0.3,
        accent_probability=0.75,
        patience=0.3,
        message_length="medium",
        fragmentation=0.5,
        context_continuity=0.5,
        traits=["worried", "second-guesses", "asks multiple questions at once", "mentions time pressure"],
        sample_openers=[
            "trời mưa rồi đi đâu bây giờ",
            "đặt chỗ rồi mà họ hủy, giờ phải làm gì",
            "xe bị hỏng giữa đường, gần đây có chỗ nào sửa không",
            "mấy giờ mặt trời lặn ở đây, bé muốn xem",
            "đi được không, hay là về trước?",
            "hết xăng rồi ơi trời",
        ],
    ),

    PersonaType.HUNGRY_TRAVELER: Persona(
        type=PersonaType.HUNGRY_TRAVELER,
        name="Hungry Traveler",
        age_range=(18, 50),
        language_style="food_focused_vietnamese",
        emotional_baseline=0.6,
        typo_rate=0.1,
        slang_level=0.4,
        accent_probability=0.8,
        patience=0.3,
        message_length="short",
        fragmentation=0.7,
        context_continuity=0.6,
        traits=["obsessed with food", "mentions hunger explicitly", "quick decisions needed"],
        sample_openers=[
            "đói quá",
            "ăn gì giờ này",
            "quán nào gần đây",
            "hải sản tươi đâu",
            "500k ăn gì đây",
            "bún cá ngừ đâu ngon nhất",
            "bé đói rồi nhanh lên",
        ],
    ),

    PersonaType.EXHAUSTED_TRAVELER: Persona(
        type=PersonaType.EXHAUSTED_TRAVELER,
        name="Exhausted Traveler",
        age_range=(25, 55),
        language_style="tired_vietnamese",
        emotional_baseline=0.6,
        typo_rate=0.35,
        slang_level=0.3,
        accent_probability=0.6,
        patience=0.2,
        message_length="short",
        fragmentation=0.85,
        context_continuity=0.3,
        traits=["short messages", "lots of '...'", "low energy language", "wants nearby options only"],
        sample_openers=[
            "mệt vl",
            "đi không nổi rồi",
            "gần đây thôi",
            "không muốn đi xa",
            "cafe yên tĩnh đâu",
            "nghỉ ngơi thôi",
            "mệt lắm rồi...",
            "có chỗ nào gần để dừng ko",
        ],
    ),

    PersonaType.LOCAL_USER: Persona(
        type=PersonaType.LOCAL_USER,
        name="Local User",
        age_range=(20, 60),
        language_style="local_dialect_south_central",
        emotional_baseline=0.3,
        typo_rate=0.1,
        slang_level=0.6,
        accent_probability=0.9,
        patience=0.7,
        message_length="short",
        fragmentation=0.5,
        context_continuity=0.7,
        traits=["knows local places", "uses local names", "skeptical of tourist recommendations", "direct"],
        sample_openers=[
            "quán cơm bình dân gần chợ Tuy Hòa đâu",
            "bãi Xép giờ này đông không",
            "đường ra Gành Đá Đĩa có kẹt xe không",
            "Hòn Yến mùa này nước có trong không",
            "quán nhậu vỉa hè nào ngon mà rẻ",
        ],
    ),

    PersonaType.DRUNK_USER: Persona(
        type=PersonaType.DRUNK_USER,
        name="Drunk User",
        age_range=(20, 40),
        language_style="drunk_vietnamese",
        emotional_baseline=0.8,
        typo_rate=0.7,
        slang_level=0.7,
        accent_probability=0.3,
        patience=0.1,
        message_length="short",
        fragmentation=0.95,
        context_continuity=0.1,
        traits=["random topic jumps", "repeats words", "emojis misused", "incoherent"],
        sample_openers=[
            "uong them ko may oi",
            "dau do co bao nhieu lon",
            "di dau di dau",
            "ngon vl luon luon",
            "tiep theo dau",
            "may la ai vay",
            "lon cuoi roi nhe",
        ],
    ),

    PersonaType.NO_ACCENT: Persona(
        type=PersonaType.NO_ACCENT,
        name="No Accent Typer",
        age_range=(15, 35),
        language_style="no_accent_vietnamese",
        emotional_baseline=0.4,
        typo_rate=0.1,
        slang_level=0.5,
        accent_probability=0.0,
        patience=0.5,
        message_length="short",
        fragmentation=0.6,
        context_continuity=0.5,
        traits=["no Vietnamese diacritics", "uses 'ko' for 'không'", "uses 'dc' for 'được'", "shorthand heavy"],
        sample_openers=[
            "quan nao ngon gan day",
            "an gi bay gio",
            "di dau dc",
            "biet quan hai san ko",
            "xe tu tuy hoa di ganh da dia mat bao lau",
            "500k an duoc gi",
        ],
    ),

    PersonaType.MEME_USER: Persona(
        type=PersonaType.MEME_USER,
        name="Internet Meme User",
        age_range=(16, 28),
        language_style="meme_heavy",
        emotional_baseline=0.6,
        typo_rate=0.2,
        slang_level=1.0,
        accent_probability=0.4,
        patience=0.4,
        message_length="short",
        fragmentation=0.7,
        context_continuity=0.4,
        traits=["uses memes", "references pop culture", "ironic tone", "unexpected pivots"],
        sample_openers=[
            "alo alo có ai không 📡",
            "đây có phải heaven không vậy",
            "skill issue nếu không biết chỗ này",
            "npc recommend gì cho main character đây",
            "hệ thống đang xử lý... 🔄",
            "unlocked new location",
            "side quest: tìm quán ăn ngon",
        ],
    ),

    PersonaType.PASSIVE_AGGRESSIVE: Persona(
        type=PersonaType.PASSIVE_AGGRESSIVE,
        name="Passive Aggressive User",
        age_range=(25, 45),
        language_style="passive_aggressive",
        emotional_baseline=0.7,
        typo_rate=0.1,
        slang_level=0.3,
        accent_probability=0.85,
        patience=0.2,
        message_length="medium",
        fragmentation=0.3,
        context_continuity=0.6,
        traits=["sarcastic politeness", "implied complaints", "backhanded compliments"],
        sample_openers=[
            "Cảm ơn lần trước, chỗ đó... thú vị lắm",
            "Không sao, tôi sẽ tự tìm vậy",
            "À đúng rồi, AI biết tất cả mà",
            "Thôi được, gợi ý đi, dù sao cũng không tệ hơn lần trước",
            "Nếu không có gì tốt hơn thì thôi",
        ],
    ),

    PersonaType.OLDER_USER: Persona(
        type=PersonaType.OLDER_USER,
        name="Older User",
        age_range=(50, 70),
        language_style="formal_polite_vietnamese",
        emotional_baseline=0.3,
        typo_rate=0.3,
        slang_level=0.05,
        accent_probability=0.95,
        patience=0.8,
        message_length="long",
        fragmentation=0.2,
        context_continuity=0.8,
        traits=["very polite", "formal language", "explains context at length", "not tech-savvy"],
        sample_openers=[
            "Chào bạn, tôi muốn hỏi về các địa điểm tham quan ở Phú Yên",
            "Gia đình tôi có một cháu nhỏ 4 tuổi, bạn có thể tư vấn giúp tôi không?",
            "Xin hỏi, đường đi từ Tuy Hòa đến Gành Đá Đĩa có khó không?",
            "Chúng tôi đi 7 người, nên ở khách sạn hay resort?",
        ],
    ),

    PersonaType.CONFUSED_TOURIST: Persona(
        type=PersonaType.CONFUSED_TOURIST,
        name="Confused Tourist",
        age_range=(20, 60),
        language_style="confused_mixed",
        emotional_baseline=0.5,
        typo_rate=0.2,
        slang_level=0.2,
        accent_probability=0.4,
        patience=0.5,
        message_length="medium",
        fragmentation=0.5,
        context_continuity=0.4,
        traits=["contradicts themselves", "changes plans mid-question", "asks unrelated follow-ups"],
        sample_openers=[
            "tôi muốn đi biển... à không, trước tiên ăn đã",
            "Gành Đá Đĩa hay Hòn Yến trước nhỉ? À mà giờ mấy giờ rồi",
            "đặt nhà hàng xong rồi nhưng... có chỗ nào gần hơn không",
            "nói tôi cần đi đâu",
            "hải sản hay cơm... ờ mà thôi hải sản đi",
        ],
    ),

    PersonaType.LATE_NIGHT_USER: Persona(
        type=PersonaType.LATE_NIGHT_USER,
        name="Late Night User",
        age_range=(20, 40),
        language_style="late_night_casual",
        emotional_baseline=0.5,
        typo_rate=0.3,
        slang_level=0.6,
        accent_probability=0.5,
        patience=0.4,
        message_length="short",
        fragmentation=0.75,
        context_continuity=0.4,
        traits=["mentions being tired", "asks about late spots", "nightlife focus"],
        sample_openers=[
            "giờ này còn chỗ nào mở không",
            "2am có gì ăn không",
            "bar nào còn mở",
            "đêm nay đi đâu vui",
            "quán nhậu late night",
            "mì gói thì tìm đâu",
        ],
    ),
}


def get_persona(persona_type: Optional[PersonaType] = None) -> Persona:
    """Get a persona by type, or random if not specified."""
    if persona_type:
        return PERSONAS.get(persona_type, random.choice(list(PERSONAS.values())))
    return random.choice(list(PERSONAS.values()))


def get_weighted_persona() -> Persona:
    """Get a persona with weights reflecting real-world distribution."""
    weights = {
        PersonaType.GEN_Z: 15,
        PersonaType.TOURIST_FOREIGN: 8,
        PersonaType.TOURIST_DOMESTIC: 12,
        PersonaType.ANGRY_CUSTOMER: 5,
        PersonaType.STRESSED_TRAVELER: 10,
        PersonaType.HUNGRY_TRAVELER: 12,
        PersonaType.EXHAUSTED_TRAVELER: 8,
        PersonaType.LOCAL_USER: 10,
        PersonaType.DRUNK_USER: 3,
        PersonaType.NO_ACCENT: 10,
        PersonaType.MEME_USER: 5,
        PersonaType.PASSIVE_AGGRESSIVE: 4,
        PersonaType.OLDER_USER: 6,
        PersonaType.CONFUSED_TOURIST: 7,
        PersonaType.LATE_NIGHT_USER: 5,
    }
    types = list(weights.keys())
    probs = [weights[t] for t in types]
    total = sum(probs)
    probs = [p / total for p in probs]
    chosen = random.choices(types, weights=probs, k=1)[0]
    return PERSONAS[chosen]


def mutate_persona(persona: Persona, stress_level: float = 0.0) -> Persona:
    """Apply stress/fatigue mutations to a persona at runtime."""
    import copy
    mutated = copy.copy(persona)
    mutated.typo_rate = min(1.0, persona.typo_rate + stress_level * 0.3)
    mutated.patience = max(0.0, persona.patience - stress_level * 0.4)
    mutated.emotional_baseline = min(1.0, persona.emotional_baseline + stress_level * 0.3)
    mutated.fragmentation = min(1.0, persona.fragmentation + stress_level * 0.2)
    return mutated
