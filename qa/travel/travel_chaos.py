"""
Travel Chaos Engine — Simulates real-world travel disruptions and
unexpected scenarios that stress-test the AI's situational awareness.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class ChaosType(Enum):
    WEATHER = "weather"
    TRAFFIC = "traffic"
    BEACH_CONDITIONS = "beach_conditions"
    CROWD_SPIKE = "crowd_spike"
    EXHAUSTION = "exhaustion"
    LOW_BATTERY = "low_battery"
    WEAK_INTERNET = "weak_internet"
    GPS_FAILURE = "gps_failure"
    PLAN_CHANGE = "plan_change"
    CHILD_EMERGENCY = "child_emergency"
    VEHICLE_ISSUE = "vehicle_issue"
    RESTAURANT_CLOSED = "restaurant_closed"
    OVER_BUDGET = "over_budget"
    SUNSET_TIMING = "sunset_timing"
    SEA_DANGER = "sea_danger"


@dataclass
class ChaosScenario:
    chaos_type: ChaosType
    description: str
    user_messages: List[str]
    expected_ai_behavior: str
    fail_conditions: List[str]
    location_context: Optional[str] = None
    time_context: Optional[str] = None
    urgency: str = "medium"  # low, medium, high, critical


CHAOS_SCENARIOS = [
    ChaosScenario(
        chaos_type=ChaosType.WEATHER,
        description="Sudden rain ruins outdoor plans",
        user_messages=[
            "mưa rồi ơi trời",
            "kế hoạch hủy hết rồi",
            "giờ đi đâu với bé",
        ],
        expected_ai_behavior="Suggest indoor alternatives immediately, acknowledge rain disruption, child-friendly options",
        fail_conditions=[
            "AI suggests outdoor activities",
            "AI ignores the rain",
            "AI doesn't mention child",
            "AI gives too many options (overwhelm)",
        ],
        time_context="afternoon",
        urgency="high",
    ),

    ChaosScenario(
        chaos_type=ChaosType.TRAFFIC,
        description="Stuck in traffic, need help",
        user_messages=[
            "kẹt xe kinh khủng",
            "mất bao lâu nữa tới Gành Đá Đĩa",
            "có đường nào khác không",
        ],
        expected_ai_behavior="Provide alternative routes, realistic time estimate, suggest stopping point if needed",
        fail_conditions=[
            "AI gives generic traffic advice",
            "AI ignores urgency",
            "AI doesn't suggest alternatives",
        ],
        location_context="Phú Yên highway",
        urgency="high",
    ),

    ChaosScenario(
        chaos_type=ChaosType.BEACH_CONDITIONS,
        description="Dangerous sea conditions",
        user_messages=[
            "sóng to quá",
            "bé có xuống biển được không",
            "lá cờ đỏ có nghĩa gì",
        ],
        expected_ai_behavior="Immediately explain red flag danger, do NOT allow child near water, suggest safe alternatives",
        fail_conditions=[
            "AI says it's probably fine",
            "AI doesn't explain red flag",
            "AI doesn't prioritize child safety",
            "AI suggests swimming anyway",
        ],
        location_context="beach",
        urgency="critical",
    ),

    ChaosScenario(
        chaos_type=ChaosType.CROWD_SPIKE,
        description="Location way too crowded",
        user_messages=[
            "đông quá trời luôn",
            "chen không vào được",
            "chỗ nào ít người hơn",
        ],
        expected_ai_behavior="Suggest less crowded alternatives nearby, explain why it's crowded, timing advice",
        fail_conditions=[
            "AI recommends same crowded spot",
            "AI doesn't acknowledge the crowd",
            "AI gives tourist-trap alternative",
        ],
        urgency="medium",
    ),

    ChaosScenario(
        chaos_type=ChaosType.EXHAUSTION,
        description="Entire group exhausted mid-trip",
        user_messages=[
            "mệt lắm rồi cả nhà",
            "bé ngủ gật",
            "chỉ muốn nằm nghỉ",
        ],
        expected_ai_behavior="Suggest immediate rest spot, no ambitious activities, recovery-focused options, child nap considerations",
        fail_conditions=[
            "AI suggests more sightseeing",
            "AI gives long itinerary",
            "AI ignores child exhaustion",
            "AI recommends far locations",
        ],
        urgency="high",
    ),

    ChaosScenario(
        chaos_type=ChaosType.LOW_BATTERY,
        description="Phone about to die while traveling",
        user_messages=[
            "pin 3% rồi",
            "cần sạc gấp",
            "gần đây có chỗ sạc không",
        ],
        expected_ai_behavior="Give immediate nearby charging location, be ultra-brief (user will lose phone soon), maybe mention power bank shops",
        fail_conditions=[
            "AI gives long response when phone dying",
            "AI doesn't provide immediate answer",
            "AI asks clarifying questions when urgent",
        ],
        urgency="critical",
    ),

    ChaosScenario(
        chaos_type=ChaosType.VEHICLE_ISSUE,
        description="Car broke down or running low on fuel",
        user_messages=[
            "xe sắp hết xăng",
            "trạm xăng gần nhất đâu",
            "xe diesel nha",
        ],
        expected_ai_behavior="Immediate nearest diesel station, address and distance, safety first",
        fail_conditions=[
            "AI gives petrol station for diesel car",
            "AI doesn't know location context",
            "AI response too slow/long",
        ],
        location_context="rural Phú Yên road",
        urgency="critical",
    ),

    ChaosScenario(
        chaos_type=ChaosType.RESTAURANT_CLOSED,
        description="Target restaurant closed unexpectedly",
        user_messages=[
            "quán đó đóng cửa rồi",
            "đặt bàn rồi mà",
            "giờ ăn đâu 7 người",
        ],
        expected_ai_behavior="Immediately suggest 2-3 nearby alternatives for large group, acknowledge frustration",
        fail_conditions=[
            "AI ignores frustration",
            "AI suggests closed restaurant again",
            "AI doesn't account for 7-person group size",
            "AI not empathetic",
        ],
        urgency="high",
    ),

    ChaosScenario(
        chaos_type=ChaosType.SUNSET_TIMING,
        description="User wants to see sunset but running late",
        user_messages=[
            "mấy giờ mặt trời lặn hôm nay",
            "đang ở Tuy Hòa",
            "kịp ra Bãi Xép không",
        ],
        expected_ai_behavior="Give exact sunset time for the date, calculate travel time, tell if feasible, suggest backup if not",
        fail_conditions=[
            "AI doesn't know sunset time",
            "AI gives wrong calculation",
            "AI doesn't suggest backup",
            "AI is vague",
        ],
        time_context="late afternoon",
        urgency="high",
    ),

    ChaosScenario(
        chaos_type=ChaosType.PLAN_CHANGE,
        description="Mid-trip plan reversal",
        user_messages=[
            "thay đổi kế hoạch rồi",
            "không đi Gành Đá Đĩa nữa",
            "giờ muốn đi đâu mát mẻ hơn",
        ],
        expected_ai_behavior="Seamlessly adapt, suggest cool alternatives, don't ask too many clarifying questions",
        fail_conditions=[
            "AI references old plan insistently",
            "AI asks too many questions",
            "AI doesn't suggest specific alternatives",
        ],
        urgency="medium",
    ),

    ChaosScenario(
        chaos_type=ChaosType.OVER_BUDGET,
        description="Group ran over budget",
        user_messages=[
            "hết tiền rồi gần gần",
            "chỉ còn 500k cho 7 người",
            "ăn gì bây giờ",
        ],
        expected_ai_behavior="Suggest genuinely budget-friendly local options, don't recommend tourist traps, specific practical help",
        fail_conditions=[
            "AI recommends expensive restaurants",
            "AI gives tourist-trap recommendations",
            "AI doesn't acknowledge budget constraint",
            "AI suggests fine dining",
        ],
        urgency="medium",
    ),

    ChaosScenario(
        chaos_type=ChaosType.SEA_DANGER,
        description="Jellyfish or sea danger warning",
        user_messages=[
            "có sứa không",
            "hôm qua nghe nói biển có sứa nhiều",
            "bé có tắm được không",
        ],
        expected_ai_behavior="Give honest safety assessment, prioritize child safety, suggest alternatives if dangerous",
        fail_conditions=[
            "AI dismisses jellyfish concern",
            "AI says it's probably fine without data",
            "AI ignores child safety",
        ],
        urgency="high",
    ),
]


class TravelChaosEngine:
    """Generates travel disruption scenarios for QA testing."""

    def get_random_scenario(self) -> ChaosScenario:
        return random.choice(CHAOS_SCENARIOS)

    def get_scenario_by_type(self, chaos_type: ChaosType) -> Optional[ChaosScenario]:
        for scenario in CHAOS_SCENARIOS:
            if scenario.chaos_type == chaos_type:
                return scenario
        return None

    def get_critical_scenarios(self) -> List[ChaosScenario]:
        return [s for s in CHAOS_SCENARIOS if s.urgency == "critical"]

    def get_child_safety_scenarios(self) -> List[ChaosScenario]:
        """Get scenarios involving child safety — highest priority."""
        return [
            s for s in CHAOS_SCENARIOS
            if any("child" in fc.lower() or "bé" in fc.lower() or "child" in s.description.lower()
                   for fc in s.fail_conditions)
        ]

    def build_travel_day_chaos(self) -> List[Dict]:
        """Build a full day of chaotic travel events."""
        day = []

        morning = {
            "time": "07:00",
            "event": "morning_start",
            "messages": [
                "sáng nay đi đâu trước",
                "thời tiết hôm nay thế nào",
                "bé dậy rồi đói rồi",
            ],
        }

        midday_chaos = random.choice(CHAOS_SCENARIOS)
        afternoon_chaos = random.choice(CHAOS_SCENARIOS)
        evening = {
            "time": "18:00",
            "event": "evening_plans",
            "messages": [
                "tối nay ăn đâu",
                "cả nhà mệt rồi",
                "gần khách sạn thôi",
            ],
        }

        day.append(morning)
        day.append({"time": "12:00", "event": midday_chaos.chaos_type.value,
                    "messages": midday_chaos.user_messages})
        day.append({"time": "15:00", "event": afternoon_chaos.chaos_type.value,
                    "messages": afternoon_chaos.user_messages})
        day.append(evening)

        return day

    def generate_weather_messages(self, condition: str) -> List[str]:
        """Generate weather-specific messages."""
        conditions = {
            "rain": [
                "mưa rồi",
                "mưa to quá",
                "không đi ra ngoài được",
                "trời xấu quá",
            ],
            "hot": [
                "nóng vl",
                "không chịu nổi",
                "35 độ mà đi biển à",
                "cần chỗ có điều hòa",
                "bé sắp sốc nhiệt",
            ],
            "windy": [
                "gió to quá",
                "sóng cao",
                "biển động",
                "đi biển được không",
            ],
            "perfect": [
                "trời đẹp quá",
                "đi đâu tận dụng thời tiết này",
                "nắng nhẹ mát mẻ",
            ],
        }
        return conditions.get(condition, conditions["perfect"])
