"""
Conversation Generator — Produces realistic multi-turn conversations
based on persona profiles and scenario types.
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

from .persona_engine import Persona, PersonaType, get_weighted_persona
from ..slang.vietnamese_chaos import VietnameseChaosEngine
from ..typo.typo_engine import TypoEngine
from ..no_accent.no_accent_engine import NoAccentEngine
from ..fragmented.fragment_engine import FragmentEngine
from ..emotional.emotion_engine import EmotionEngine
from ..travel.travel_chaos import TravelChaosEngine


class ScenarioType(Enum):
    FOOD_SEARCH = "food_search"
    LOCATION_QUERY = "location_query"
    ITINERARY_REQUEST = "itinerary_request"
    WEATHER_CHECK = "weather_check"
    BUDGET_INQUIRY = "budget_inquiry"
    EMERGENCY = "emergency"
    NIGHTLIFE = "nightlife"
    TRANSPORT = "transport"
    LOCAL_TIPS = "local_tips"
    COMPLAINT = "complaint"
    MULTI_INTENT = "multi_intent"
    FRAGMENTED_ORDER = "fragmented_order"
    EMOTIONAL_VENTING = "emotional_venting"
    RECOVERY_NEEDED = "recovery_needed"


@dataclass
class ConversationTurn:
    role: str  # "user" or "assistant"
    message: str
    persona_type: Optional[str] = None
    scenario: Optional[str] = None
    emotional_state: Optional[str] = None
    intent_tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ConversationSession:
    session_id: str
    persona: Persona
    scenario: ScenarioType
    turns: List[ConversationTurn] = field(default_factory=list)
    emotional_arc: List[float] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


# ── Scenario Templates ─────────────────────────────────────

SCENARIO_TEMPLATES = {
    ScenarioType.FOOD_SEARCH: [
        # Single message intents
        ["{food_query}"],
        # Fragmented multi-turn
        ["{budget}", "{food_type}", "{meal_time}"],
        # Contextual continuation
        ["{food_query}", "gần {location} thôi nha", "có chỗ đậu xe không"],
        # Emotional food search
        ["{exhaustion_prefix} {food_query}", "nhanh nhanh thôi"],
    ],

    ScenarioType.LOCATION_QUERY: [
        ["{location_query}"],
        ["{location_query}", "đi bằng xe hơi dc không", "mất bao lâu"],
        ["cách {current_location} bao xa", "{location_name}", "có đáng đi không"],
    ],

    ScenarioType.FRAGMENTED_ORDER: [
        # Classic fragmented: budget → food type → time
        ["{budget}", "{food_type}", "{meal_time}"],
        # Location fragments
        ["{location_name}", "gần đây", "ngon ngon"],
        # Chaos order
        ["{random_fragment_1}", "{random_fragment_2}", "{random_fragment_3}"],
    ],

    ScenarioType.EMOTIONAL_VENTING: [
        ["{emotional_opener}", "{request_buried}"],
        ["{frustration}", "thôi gợi ý đi", "{clarification}"],
        ["{complaint}", "{actual_question}"],
    ],

    ScenarioType.RECOVERY_NEEDED: [
        ["{fatigue_signal}", "chỗ nào yên tĩnh", "không đi xa được"],
        ["{exhaustion}", "cafe nào không ồn", "có wifi không"],
    ],

    ScenarioType.NIGHTLIFE: [
        ["{nightlife_query}"],
        ["mấy giờ rồi", "{nightlife_query}", "còn mở không"],
        ["{drunk_prefix} {nightlife_query}"],
    ],

    ScenarioType.MULTI_INTENT: [
        ["{food_and_location}", "à còn {transport_question}"],
        ["{location_query}", "đó có {food_type} không", "giá cả thế nào"],
        ["{itinerary_start}", "{budget}", "{constraint}"],
    ],
}


FILL_TEMPLATES = {
    "food_query": [
        "ăn gì bây giờ",
        "quán hải sản ngon đâu",
        "bún cá ngừ ở đâu",
        "cơm trưa gần đây",
        "đói quá gợi ý cái gì đi",
        "quán nào ngon mà không đông",
        "hải sản tươi đâu",
        "seafood ngon nhất vùng này",
        "ăn sáng ở đâu",
        "bún sứa ở đâu ngon",
        "bánh căn ở đâu",
        "ăn tối family-friendly",
    ],
    "budget": [
        "500k",
        "300k",
        "1 triệu",
        "hai trăm",
        "rẻ thôi",
        "200-300k",
        "tầm 500",
        "khoảng 1tr",
        "budget ổn ổn",
        "không quá 500",
    ],
    "food_type": [
        "hải sản",
        "cơm",
        "bún",
        "phở",
        "buffet",
        "quán nhậu",
        "đồ ăn nhẹ",
        "cafe",
        "nước",
        "tráng miệng",
    ],
    "meal_time": [
        "trưa",
        "tối",
        "sáng",
        "chiều",
        "giờ này",
        "bây giờ",
        "khoảng 12h",
        "6h tối",
    ],
    "location_name": [
        "Gành Đá Đĩa",
        "Hòn Yến",
        "Bãi Xép",
        "Mũi Điện",
        "Đầm Ô Loan",
        "Sông Cầu",
        "Tuy Hòa",
        "Long Thủy",
        "Đại Lãnh",
    ],
    "current_location": [
        "khách sạn",
        "trung tâm Tuy Hòa",
        "Gành Đá Đĩa",
        "bãi biển",
        "resort",
    ],
    "location_query": [
        "Gành Đá Đĩa cách đây bao xa",
        "Hòn Yến đi như thế nào",
        "Mũi Điện có gì hay không",
        "Bãi Xép an toàn không cho bé",
        "Đầm Ô Loan mùa này có gì",
        "Sông Cầu tôm hùm giá bao nhiêu",
    ],
    "exhaustion_prefix": [
        "mệt vl",
        "chân đau quá",
        "đi cả ngày rồi",
        "kiệt sức rồi",
        "không còn sức đâu",
    ],
    "emotional_opener": [
        "trời ơi hôm nay mệt quá",
        "tức ghê mà thôi kệ",
        "không hiểu sao lại thế này",
        "ừ thôi tôi chấp nhận rồi",
        "oke fine whatever",
    ],
    "frustration": [
        "hỏi mãi không ai trả lời",
        "AI này cứ gợi ý lung tung",
        "lần trước gợi ý sai rồi",
        "không hiểu ý tôi à",
    ],
    "fatigue_signal": [
        "mệt lắm rồi",
        "không muốn đi xa",
        "chỉ muốn ngồi nghỉ",
        "đứng không vững",
        "bé cũng mệt rồi",
    ],
    "nightlife_query": [
        "bar nào vui",
        "chỗ nào uống bia ngon",
        "quán nhậu đêm khuya",
        "còn chỗ nào mở không",
        "nightlife ở đây thế nào",
        "làm vài lon ko",
    ],
    "drunk_prefix": [
        "oi oi",
        "hehe",
        "thich roi",
        "di di di",
        "chill vl",
    ],
    "transport_question": [
        "xe ôm hay taxi",
        "grab có không",
        "đường có tốt không",
        "bao lâu đến",
        "có kẹt xe không",
    ],
    "constraint": [
        "có bé nhỏ",
        "xe 7 chỗ",
        "không đi xa quá",
        "trời nóng",
        "sắp mưa",
    ],
    "request_buried": [
        "gợi ý chỗ ăn đi",
        "cho tôi biết chỗ nào tốt",
        "nên đi đâu",
        "recommend cái gì đi",
    ],
    "complaint": [
        "chỗ trước bị chặt chém",
        "quán đó đông quá đi không được",
        "bãi biển hôm nay có sóng lớn",
        "thời tiết xấu thật",
    ],
    "actual_question": [
        "vậy giờ đi đâu",
        "còn lựa chọn nào không",
        "plan B là gì",
        "backup option có không",
    ],
}


class ConversationGenerator:
    def __init__(self):
        self.chaos_engine = VietnameseChaosEngine()
        self.typo_engine = TypoEngine()
        self.no_accent_engine = NoAccentEngine()
        self.fragment_engine = FragmentEngine()
        self.emotion_engine = EmotionEngine()
        self.travel_chaos = TravelChaosEngine()

    def generate_session(
        self,
        persona: Optional[Persona] = None,
        scenario: Optional[ScenarioType] = None,
        num_turns: int = 3,
    ) -> ConversationSession:
        """Generate a full conversation session."""
        import uuid

        if persona is None:
            persona = get_weighted_persona()
        if scenario is None:
            scenario = random.choice(list(ScenarioType))

        session = ConversationSession(
            session_id=str(uuid.uuid4())[:8],
            persona=persona,
            scenario=scenario,
        )

        messages = self._build_messages(persona, scenario, num_turns)

        for i, msg in enumerate(messages):
            turn = ConversationTurn(
                role="user",
                message=msg,
                persona_type=persona.type.value,
                scenario=scenario.value,
                emotional_state=self.emotion_engine.get_state_label(
                    persona.emotional_baseline
                ),
                intent_tags=self._extract_intent_hints(msg),
                metadata={"turn_index": i},
            )
            session.turns.append(turn)
            session.emotional_arc.append(persona.emotional_baseline)

        return session

    def _build_messages(
        self, persona: Persona, scenario: ScenarioType, num_turns: int
    ) -> List[str]:
        """Build raw messages for the scenario."""
        template_sets = SCENARIO_TEMPLATES.get(scenario, [["{food_query}"]])
        template = random.choice(template_sets)

        messages = []
        for slot in template[:num_turns]:
            filled = self._fill_slot(slot)
            styled = self._apply_persona_style(filled, persona)
            messages.append(styled)

        # Maybe add follow-up chaos
        if random.random() < persona.fragmentation and len(messages) < num_turns:
            messages.append(self._generate_followup(persona))

        return messages

    def _fill_slot(self, template: str) -> str:
        """Fill a slot template with random content."""
        import re
        result = template
        placeholders = re.findall(r'\{(\w+)\}', template)
        for ph in placeholders:
            if ph in FILL_TEMPLATES:
                replacement = random.choice(FILL_TEMPLATES[ph])
                result = result.replace(f"{{{ph}}}", replacement, 1)
            else:
                result = result.replace(f"{{{ph}}}", ph, 1)
        return result

    def _apply_persona_style(self, text: str, persona: Persona) -> str:
        """Apply persona-specific language transformations."""
        # Apply typos
        if random.random() < persona.typo_rate:
            text = self.typo_engine.apply(text, intensity=persona.typo_rate)

        # Strip accents if no-accent persona
        if persona.accent_probability < 0.1:
            text = self.no_accent_engine.strip_accents(text)
        elif persona.accent_probability < 0.5 and random.random() > persona.accent_probability:
            text = self.no_accent_engine.partial_strip(text)

        # Apply slang
        if random.random() < persona.slang_level * 0.7:
            text = self.chaos_engine.inject_slang(text, persona.type)

        # Apply emotional coloring
        text = self.emotion_engine.colorize(text, persona.emotional_baseline, persona.type)

        return text.strip()

    def _generate_followup(self, persona: Persona) -> str:
        """Generate a contextually appropriate follow-up message."""
        followups = {
            PersonaType.GEN_Z: ["ez ez", "còn gì nữa không", "ngon chưa", "oke bro"],
            PersonaType.ANGRY_CUSTOMER: ["Còn gì không?", "Nhanh lên", "???"],
            PersonaType.EXHAUSTED_TRAVELER: ["gần thôi nha", "..."],
            PersonaType.DRUNK_USER: ["hehe", "dau di tiep", "ok ok"],
            PersonaType.LOCAL_USER: ["thôi dc rồi", "biết rồi cảm ơn"],
        }
        options = followups.get(persona.type, ["cảm ơn", "còn gì nữa không", "oke"])
        return random.choice(options)

    def _extract_intent_hints(self, message: str) -> List[str]:
        """Extract basic intent signals from message text."""
        hints = []
        text = message.lower()
        if any(w in text for w in ["ăn", "quán", "hải sản", "cơm", "bún", "đói"]):
            hints.append("food")
        if any(w in text for w in ["đi", "cách", "bao xa", "đường", "xe", "grab"]):
            hints.append("transport")
        if any(w in text for w in ["thời tiết", "mưa", "nắng", "trời"]):
            hints.append("weather")
        if any(w in text for w in ["mệt", "nghỉ", "cafe", "yên tĩnh"]):
            hints.append("recovery")
        if any(w in text for w in ["bar", "nhậu", "bia", "lon", "uống"]):
            hints.append("nightlife")
        if any(w in text for w in ["k", "tr", "triệu", "tiền", "giá", "rẻ"]):
            hints.append("budget")
        return hints

    def generate_chaos_batch(
        self, count: int = 50
    ) -> List[ConversationSession]:
        """Generate a large batch of chaotic conversation sessions."""
        sessions = []
        for _ in range(count):
            persona = get_weighted_persona()
            scenario = random.choice(list(ScenarioType))
            num_turns = random.randint(1, 4)
            session = self.generate_session(persona, scenario, num_turns)
            sessions.append(session)
        return sessions
