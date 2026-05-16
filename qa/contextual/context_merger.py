"""
Context Merger — Handles multi-turn conversation context merging.
Detects fragmented intents and builds a coherent understanding.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class MergeStrategy(Enum):
    SEQUENTIAL = "sequential"      # Messages build on each other
    ADDITIVE = "additive"          # Each message adds new info
    CORRECTIVE = "corrective"      # Later message corrects earlier
    PARALLEL = "parallel"          # Messages describe same thing differently
    TOPIC_SWITCH = "topic_switch"  # User changed topic


@dataclass
class MergedContext:
    merged_intent: str
    components: Dict[str, str]  # intent component → value
    strategy: MergeStrategy
    confidence: float
    raw_messages: List[str]
    resolved_budget: Optional[str] = None
    resolved_food_type: Optional[str] = None
    resolved_location: Optional[str] = None
    resolved_time: Optional[str] = None
    resolved_group: Optional[str] = None
    resolved_constraint: Optional[str] = None


class ContextMerger:
    """Merges fragmented conversation turns into coherent intent."""

    def merge(self, messages: List[str]) -> MergedContext:
        """Merge multiple messages into unified intent context."""
        components = {}
        strategy = MergeStrategy.ADDITIVE

        budget = self._extract_budget(messages)
        food_type = self._extract_food_type(messages)
        location = self._extract_location(messages)
        time_ref = self._extract_time(messages)
        group = self._extract_group(messages)
        constraint = self._extract_constraint(messages)

        if budget:
            components["budget"] = budget
        if food_type:
            components["food_type"] = food_type
        if location:
            components["location"] = location
        if time_ref:
            components["time"] = time_ref
        if group:
            components["group"] = group
        if constraint:
            components["constraint"] = constraint

        merged_intent = self._build_intent_string(components)
        confidence = min(1.0, len(components) / 3)

        # Detect strategy
        if any("thay đổi" in m.lower() or "không phải" in m.lower() for m in messages):
            strategy = MergeStrategy.CORRECTIVE
        elif any("à" in m.lower() or "còn" in m.lower() for m in messages):
            strategy = MergeStrategy.ADDITIVE
        elif len(set(self._detect_domains(messages))) > 1:
            strategy = MergeStrategy.TOPIC_SWITCH

        return MergedContext(
            merged_intent=merged_intent,
            components=components,
            strategy=strategy,
            confidence=confidence,
            raw_messages=messages,
            resolved_budget=budget,
            resolved_food_type=food_type,
            resolved_location=location,
            resolved_time=time_ref,
            resolved_group=group,
            resolved_constraint=constraint,
        )

    def _extract_budget(self, messages: List[str]) -> Optional[str]:
        import re
        for msg in messages:
            # Match money patterns
            m = re.search(
                r'(\d+)\s*(k|nghìn|ngàn|tr|triệu|đ|đồng|usd|\$)',
                msg.lower()
            )
            if m:
                amount = m.group(1)
                unit = m.group(2)
                unit_map = {
                    "k": "000đ", "nghìn": "000đ", "ngàn": "000đ",
                    "tr": "triệu", "triệu": "triệu",
                    "đ": "đ", "đồng": "đ",
                }
                normalized_unit = unit_map.get(unit, unit)
                return f"{amount}{normalized_unit}"

            # Match plain patterns like "500k", "rẻ thôi", "bình dân"
            if any(w in msg.lower() for w in ["rẻ thôi", "bình dân", "không cần đắt"]):
                return "budget-friendly"
            if any(w in msg.lower() for w in ["ok ok", "tầm trung"]):
                return "mid-range"

        return None

    def _extract_food_type(self, messages: List[str]) -> Optional[str]:
        food_types = {
            "hải sản": "seafood",
            "seafood": "seafood",
            "cơm": "rice dish",
            "bún": "noodle soup",
            "phở": "pho",
            "buffet": "buffet",
            "nhậu": "drinking food",
            "cafe": "cafe",
            "ăn nhẹ": "light snack",
            "đồ ăn nhẹ": "light snack",
            "tôm hùm": "lobster",
            "cá": "fish",
            "bánh": "pastry",
            "mì": "noodles",
        }

        for msg in messages:
            msg_lower = msg.lower()
            for food, normalized in food_types.items():
                if food in msg_lower:
                    return normalized

        return None

    def _extract_location(self, messages: List[str]) -> Optional[str]:
        locations = [
            "gành đá đĩa", "hòn yến", "bãi xép", "mũi điện",
            "đầm ô loan", "sông cầu", "tuy hòa", "long thủy",
            "đại lãnh", "phú yên", "vũng rô",
            "gần đây", "gần khách sạn", "trung tâm",
        ]

        for msg in messages:
            msg_lower = msg.lower()
            for loc in locations:
                if loc in msg_lower:
                    return loc

        return None

    def _extract_time(self, messages: List[str]) -> Optional[str]:
        time_words = {
            "sáng": "morning",
            "trưa": "lunch",
            "chiều": "afternoon",
            "tối": "evening",
            "đêm": "night",
            "khuya": "late night",
            "bây giờ": "now",
            "giờ này": "now",
        }

        for msg in messages:
            msg_lower = msg.lower()
            for word, normalized in time_words.items():
                if word in msg_lower:
                    return normalized

        return None

    def _extract_group(self, messages: List[str]) -> Optional[str]:
        import re
        for msg in messages:
            # Number of people
            m = re.search(r'(\d+)\s*người', msg.lower())
            if m:
                return f"{m.group(1)} people"

            group_words = {
                "cả nhà": "family",
                "cả nhóm": "group",
                "hai người": "2 people",
                "một mình": "solo",
                "bé": "with child",
                "gia đình": "family",
            }
            msg_lower = msg.lower()
            for word, normalized in group_words.items():
                if word in msg_lower:
                    return normalized

        return None

    def _extract_constraint(self, messages: List[str]) -> Optional[str]:
        constraints = {
            "có bé": "child-friendly",
            "bé nhỏ": "child-friendly",
            "gần đây": "nearby only",
            "không đi xa": "nearby only",
            "có đậu xe": "needs parking",
            "mở cửa": "must be open",
            "không ồn": "quiet",
            "yên tĩnh": "quiet",
            "có wifi": "needs wifi",
            "view biển": "beach view",
            "điều hòa": "needs AC",
        }

        for msg in messages:
            msg_lower = msg.lower()
            for signal, normalized in constraints.items():
                if signal in msg_lower:
                    return normalized

        return None

    def _build_intent_string(self, components: Dict[str, str]) -> str:
        """Build a human-readable merged intent string."""
        parts = []

        if "food_type" in components:
            parts.append(f"Find {components['food_type']}")
        else:
            parts.append("Find food/place")

        if "budget" in components:
            parts.append(f"budget: {components['budget']}")
        if "time" in components:
            parts.append(f"time: {components['time']}")
        if "location" in components:
            parts.append(f"near: {components['location']}")
        if "group" in components:
            parts.append(f"for: {components['group']}")
        if "constraint" in components:
            parts.append(f"constraint: {components['constraint']}")

        return " | ".join(parts) if parts else "General inquiry"

    def _detect_domains(self, messages: List[str]) -> List[str]:
        """Detect domain for each message."""
        domains = []
        for msg in messages:
            msg_lower = msg.lower()
            if any(w in msg_lower for w in ["ăn", "quán", "hải sản", "cơm"]):
                domains.append("food")
            elif any(w in msg_lower for w in ["đường", "cách", "đi đến"]):
                domains.append("navigation")
            elif any(w in msg_lower for w in ["thời tiết", "mưa", "nắng"]):
                domains.append("weather")
            elif any(w in msg_lower for w in ["bar", "nhậu", "uống"]):
                domains.append("nightlife")
            else:
                domains.append("general")
        return domains

    def audit_context_merge(self, messages: List[str], ai_response: str) -> dict:
        """Audit if AI correctly merged fragmented messages."""
        merged = self.merge(messages)
        violations = []
        passed = []

        response_lower = ai_response.lower()

        # Check budget awareness
        if merged.resolved_budget and merged.resolved_budget != "budget-friendly":
            amount = "".join(filter(str.isdigit, merged.resolved_budget))
            if amount and amount not in response_lower:
                if not any(w in response_lower for w in ["giá", "chi phí", "tầm", "khoảng"]):
                    violations.append({
                        "rule": "missed_budget_context",
                        "severity": "HIGH",
                        "detail": f"User specified budget {merged.resolved_budget} but AI ignored it",
                    })
            else:
                passed.append("budget_acknowledged")

        # Check food type awareness
        if merged.resolved_food_type:
            if merged.resolved_food_type.split()[0] not in response_lower:
                violations.append({
                    "rule": "missed_food_type_context",
                    "severity": "MEDIUM",
                    "detail": f"User wanted {merged.resolved_food_type} but AI suggested different food",
                })
            else:
                passed.append("food_type_matched")

        return {
            "merged_intent": merged.merged_intent,
            "components_detected": len(merged.components),
            "strategy": merged.strategy.value,
            "confidence": merged.confidence,
            "violations": violations,
            "passed": passed,
            "context_score": max(0.0, 1.0 - len(violations) * 0.3),
        }
