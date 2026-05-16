"""
MovementResistanceRouter — nearby-first, low-friction routing.

When the user signals movement resistance:
  "gần thôi", "lười đi", "ngại chạy", "không muốn xa", "ngại di xa"

The AI should NOT suggest anything far. It should:
1. Filter all recommendations to a tight radius
2. Chain nearby places (eat → rest → activity → eat — all walkable)
3. Minimize transfers and decision points
4. Make travel feel effortless

This module also handles "social energy routing":
  - Solo mood → quiet single spots
  - Family → places with child facilities
  - Group → places with space for 8 people
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── Movement resistance signals ───────────────────────────────────────────────

RESISTANCE_SIGNALS = [
    "gần thôi", "gần đây thôi", "gần đây", "gần nhất",
    "lười đi", "lười di chuyển", "ngại đi xa", "ngại chạy",
    "không muốn đi xa", "không muốn đi đâu", "ở đây thôi",
    "quanh đây", "đi bộ thôi", "không muốn xe",
    # No-accent variants
    "gan thoi", "gan day thoi", "luoi di", "ngai di xa",
    "khong muon di xa", "o day thoi",
]

SOCIAL_SOLO_SIGNALS = [
    "một mình", "solo", "đi một mình", "chỉ mình", "mình thôi",
]

SOCIAL_GROUP_SIGNALS = [
    "cả nhóm", "cả hội", "mọi người", "đi nhóm", "8 người", "bạn bè",
]


@dataclass
class RoutingConstraints:
    """Constraints derived from movement resistance + social context."""
    max_distance_km: float = 20.0
    prefer_walkable: bool = False       # < 1km
    require_child_safe: bool = False
    require_group_capacity: bool = False  # seats for 8+
    avoid_crowds: bool = False
    prefer_parking: bool = True         # Kia Carnival needs parking
    social_mode: str = "family"

    # Prompt hint for LLM
    routing_hint: str = ""

    @property
    def is_restricted(self) -> bool:
        return self.max_distance_km < 10 or self.prefer_walkable


@dataclass
class MovementProfile:
    """Current movement state of the user."""
    tolerance: str        # "high"|"medium"|"low"|"resistance"
    avg_score: float      # 0.0 – 1.0 from history
    resistance_signals_in_text: list[str] = field(default_factory=list)
    social_mode: str = "family"
    has_child: bool = True


class MovementResistanceRouter:
    """
    Interprets movement resistance signals and builds routing constraints
    that keep all recommendations within the user's comfort radius.
    """

    def analyze(self, text: str, profile_movement_tolerance: str = "medium") -> MovementProfile:
        """Detect movement resistance from current message text."""
        t = text.lower()
        found_signals = [s for s in RESISTANCE_SIGNALS if s in t]

        is_solo = any(s in t for s in SOCIAL_SOLO_SIGNALS)
        is_group = any(s in t for s in SOCIAL_GROUP_SIGNALS)
        social = "solo" if is_solo else "group" if is_group else "family"

        # Tolerance derived from signals in text + history
        if found_signals or profile_movement_tolerance == "resistance":
            tolerance = "resistance"
            avg = 0.1
        elif profile_movement_tolerance == "low":
            tolerance = "low"
            avg = 0.3
        elif profile_movement_tolerance == "medium":
            tolerance = "medium"
            avg = 0.5
        else:
            tolerance = "high"
            avg = 0.8

        return MovementProfile(
            tolerance=tolerance,
            avg_score=avg,
            resistance_signals_in_text=found_signals,
            social_mode=social,
            has_child=True,  # Always true for this trip (Bé is always in the group)
        )

    def build_constraints(self, profile: MovementProfile, fatigue: float = 0.0) -> RoutingConstraints:
        """Build routing constraints from movement profile + fatigue."""
        # Distance limits
        if profile.tolerance == "resistance" or fatigue >= 0.75:
            max_km = 1.5
            prefer_walkable = True
        elif profile.tolerance == "low" or fatigue >= 0.5:
            max_km = 5.0
            prefer_walkable = False
        elif profile.tolerance == "medium":
            max_km = 15.0
            prefer_walkable = False
        else:
            max_km = 50.0
            prefer_walkable = False

        hint = self._build_routing_hint(profile, max_km, fatigue)

        return RoutingConstraints(
            max_distance_km=max_km,
            prefer_walkable=prefer_walkable,
            require_child_safe=profile.has_child,
            require_group_capacity=profile.social_mode == "group",
            avoid_crowds=fatigue >= 0.5,
            social_mode=profile.social_mode,
            routing_hint=hint,
        )

    def _build_routing_hint(self, profile: MovementProfile, max_km: float, fatigue: float) -> str:
        parts: list[str] = []

        if profile.tolerance == "resistance":
            parts.append(f"Chỉ gợi ý trong bán kính {max_km:.0f}km — user đang ngại di chuyển.")
            parts.append("Ưu tiên đi bộ hoặc xe dưới 5 phút.")
        elif max_km <= 5:
            parts.append(f"Giới hạn {max_km:.0f}km — năng lượng di chuyển thấp.")
        elif max_km <= 15:
            parts.append(f"Ưu tiên điểm trong {max_km:.0f}km.")

        if profile.has_child:
            parts.append("Điểm đến phải an toàn cho trẻ 4 tuổi.")

        if profile.social_mode == "group":
            parts.append("Cần chỗ ngồi cho 8 người — gọi trước hoặc chọn quán rộng.")
        elif profile.social_mode == "solo":
            parts.append("Solo trip — ưu tiên chỗ yên tĩnh, không nhất thiết phải đông.")

        if fatigue >= 0.5:
            parts.append("Giảm thiểu điểm dừng và thay đổi địa điểm.")

        if profile.resistance_signals_in_text:
            parts.append(f"User nói: '{profile.resistance_signals_in_text[0]}' — đừng gợi ý xa.")

        return " ".join(parts)

    def format_for_prompt(self, constraints: RoutingConstraints) -> str:
        """Compact injection for LLM."""
        if not constraints.is_restricted:
            return ""
        lines = [f"## Routing Constraints"]
        lines.append(f"- Bán kính tối đa: {constraints.max_distance_km:.0f}km")
        if constraints.prefer_walkable:
            lines.append("- Ưu tiên đi bộ hoặc di chuyển rất ngắn")
        if constraints.avoid_crowds:
            lines.append("- Tránh chỗ đông")
        if constraints.routing_hint:
            lines.append(f"- {constraints.routing_hint}")
        return "\n".join(lines)
