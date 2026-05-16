"""
Fragment Engine — Generates fragmented, multi-message conversation patterns.
Real humans often send ideas in separate messages instead of one coherent message.
"""

import random
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class FragmentedConversation:
    fragments: List[str]
    merged_intent: str
    delay_pattern: List[float]  # seconds between messages (simulated)
    intent_type: str


# Fragmented conversation templates: each tuple is (fragments, merged_intent, intent_type)
FRAGMENT_TEMPLATES = [
    # Budget → food → time
    (
        ["500k", "hai người", "trưa nay"],
        "Tìm quán ăn trưa cho 2 người trong tầm 500k",
        "food_budget",
    ),
    (
        ["300k", "hải sản", "tối"],
        "Gợi ý quán hải sản tối với ngân sách 300k",
        "food_budget",
    ),
    (
        ["1 triệu", "cả nhà", "ăn sáng"],
        "Quán ăn sáng cho cả nhà, budget 1 triệu",
        "food_budget",
    ),

    # Location → activity → constraint
    (
        ["Gành Đá Đĩa", "đi như thế nào", "có bé nhỏ"],
        "Hướng dẫn đi Gành Đá Đĩa có bé nhỏ",
        "navigation_family",
    ),
    (
        ["Hòn Yến", "mùa này có san hô không", "nước trong không"],
        "Hỏi về điều kiện Hòn Yến hiện tại",
        "location_query",
    ),
    (
        ["Bãi Xép", "an toàn không", "bé 4 tuổi"],
        "Hỏi độ an toàn của Bãi Xép cho bé 4 tuổi",
        "safety_family",
    ),

    # Emotional → need → clarification
    (
        ["mệt vl", "cần nghỉ", "gần đây thôi"],
        "Tìm chỗ nghỉ ngơi gần đây vì mệt",
        "recovery",
    ),
    (
        ["đói quá", "nhanh lên", "cơm thôi"],
        "Tìm quán cơm gần đây nhanh",
        "food_urgent",
    ),
    (
        ["mưa rồi", "đi đâu bây giờ", "có bé"],
        "Tìm chỗ đi khi trời mưa với bé nhỏ",
        "weather_alternative",
    ),

    # Nightlife fragmented
    (
        ["tối nay", "làm vài lon", "chỗ nào vui"],
        "Tìm quán nhậu vui tối nay",
        "nightlife",
    ),
    (
        ["bar nào", "gần biển", "không quá đắt"],
        "Tìm bar gần biển với giá bình dân",
        "nightlife_budget",
    ),

    # Topic switching
    (
        ["Mũi Điện xem bình minh", "à còn ăn gì sau đó", "và quay về bằng gì"],
        "Lịch trình Mũi Điện: xem bình minh, ăn sáng, về",
        "mini_itinerary",
    ),

    # Random chaotic (drunk / confused)
    (
        ["dau day", "ngon ko", "bao nhieu tien"],
        "Hỏi về địa điểm gần đây, chất lượng và giá",
        "chaos_query",
    ),
    (
        ["đi đâu đây", "oke oke", "mấy giờ rồi"],
        "Hỏi nên đi đâu",
        "confused",
    ),

    # Price checking fragments
    (
        ["tôm hùm Sông Cầu", "giá bao nhiêu", "cho 7 người"],
        "Hỏi giá tôm hùm Sông Cầu cho nhóm 7",
        "price_inquiry",
    ),
    (
        ["bánh căn", "ở đâu ngon nhất", "mấy giờ mở"],
        "Tìm quán bánh căn ngon và giờ mở cửa",
        "food_specific",
    ),

    # Late continuation (user sends partial then continues later)
    (
        ["cho tôi hỏi"],
        "Người dùng bắt đầu câu hỏi chưa hoàn chỉnh",
        "incomplete_start",
    ),
    (
        ["à quên"],
        "Người dùng có điều gì muốn nói thêm",
        "afterthought",
    ),
]


class FragmentEngine:
    """Generates and manages fragmented conversation patterns."""

    def generate_fragments(self, intent: str, num_fragments: int = None) -> FragmentedConversation:
        """Generate a fragmented version of an intent."""
        template = random.choice(FRAGMENT_TEMPLATES)
        fragments, merged_intent, intent_type = template

        # Optionally limit fragment count
        if num_fragments:
            fragments = fragments[:num_fragments]

        # Generate delay pattern (simulating typing delays)
        delays = self._generate_delays(len(fragments))

        return FragmentedConversation(
            fragments=fragments,
            merged_intent=merged_intent,
            delay_pattern=delays,
            intent_type=intent_type,
        )

    def fragment_message(self, message: str) -> List[str]:
        """Break a coherent message into realistic fragments."""
        words = message.split()
        if len(words) <= 2:
            return [message]

        # Determine split points
        num_fragments = random.randint(2, min(4, len(words)))
        splits = sorted(random.sample(range(1, len(words)), num_fragments - 1))

        fragments = []
        prev = 0
        for split in splits:
            chunk = " ".join(words[prev:split])
            if chunk:
                fragments.append(chunk)
            prev = split
        if prev < len(words):
            fragments.append(" ".join(words[prev:]))

        return [f for f in fragments if f.strip()]

    def generate_chaos_sequence(self) -> List[str]:
        """Generate a completely chaotic, multi-turn sequence."""
        sequences = [
            # Money then food type then time
            ["500k", "hải sản", "trưa"],
            # Reversed logic
            ["tối nay", "7 người", "hải sản tươi", "không quá 1tr"],
            # Emotional then practical
            ["mệt quá", "ăn gì đơn giản thôi", "gần đây"],
            # Random words
            ["quán", "ngon", "local", "chill"],
            # Location hops
            ["Gành Đá Đĩa xong", "ăn trưa đâu", "rồi ra biển"],
            # Nightlife chaos
            ["lon bia", "chỗ view đẹp", "tối nay", "chill"],
            # Budget split
            ["200k", "hải sản", "à thêm 100k nữa dc ko"],
        ]
        return random.choice(sequences)

    def should_fragment(self, persona_fragmentation: float) -> bool:
        """Decide whether to fragment messages based on persona."""
        return random.random() < persona_fragmentation

    def _generate_delays(self, num_messages: int) -> List[float]:
        """Generate realistic delay patterns between messages."""
        delays = []
        for i in range(num_messages):
            if i == 0:
                delays.append(0.0)
            else:
                # Real humans: 0.5s to 5s between fragments
                delay = random.uniform(0.3, 4.0)
                # Tired users type slower
                delays.append(delay)
        return delays

    def build_context_test(self) -> Tuple[List[str], str, str]:
        """Build a test where AI must merge multiple messages into one intent."""
        templates = [
            (["500k", "hai san", "trua"], "Find seafood lunch for 500k", "food_budget"),
            (["muon an", "hai san tuoi", "gan day thoi"], "Find nearby fresh seafood", "food_nearby"),
            (["toi muon", "di Ganh Da Dia", "co phai di xa khong"], "Ask about Ganh Da Dia distance", "navigation"),
            (["toi bi", "ket xe", "gan Tuy Hoa", "phai lam gi"], "Stuck in traffic near Tuy Hoa", "emergency"),
        ]
        return random.choice(templates)
