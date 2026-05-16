"""
Minimal autonomous QA audit engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class Violation:
    rule: str
    dimension: str
    reason: str
    fix_suggestion: str
    severity: Severity = Severity.MEDIUM


@dataclass(slots=True)
class AuditReport:
    session_id: str
    user_message: str
    ai_response: str
    scenario: str
    violations: list[Violation] = field(default_factory=list)
    replayable: bool = True

    @property
    def audit_result(self) -> str:
        return "FAIL" if self.violations else "PASS"


class AuditEngine:
    """Heuristic QA auditor for replayed scenarios."""

    def audit(
        self,
        *,
        session_id: str,
        user_message: str,
        ai_response: str,
        scenario: str,
        context: dict[str, object] | None = None,
    ) -> AuditReport:
        response = (ai_response or "").strip()
        text = response.casefold()
        violations: list[Violation] = []

        if not response:
            violations.append(
                Violation(
                    rule="empty_response",
                    dimension="context_continuity",
                    reason="AI trả lời rỗng nên user không thể tiếp tục.",
                    fix_suggestion="Luôn có fallback ngắn gọn và hữu ích.",
                    severity=Severity.CRITICAL,
                )
            )

        robotic_markers = [
            "as an ai",
            "i hope this helps",
            "furthermore",
            "please feel free",
            "contact support",
        ]
        if any(marker in text for marker in robotic_markers):
            violations.append(
                Violation(
                    rule="robotic_response",
                    dimension="human_naturalness",
                    reason="Giọng điệu máy móc hoặc corporate.",
                    fix_suggestion="Rút ngắn, nói tự nhiên và Việt hóa hơn.",
                    severity=Severity.HIGH,
                )
            )

        if len(response) > 700:
            violations.append(
                Violation(
                    rule="choice_overload",
                    dimension="emotional_pacing",
                    reason="Phản hồi quá dài, dễ tăng cognitive load.",
                    fix_suggestion="Giữ tối đa 2-3 gợi ý và tóm tắt ngắn hơn.",
                    severity=Severity.MEDIUM,
                )
            )

        hunger_markers = ("doi", "đói", "ăn", "an", "quán", "quan", "chè", "che", "bia")
        if any(marker in user_message.casefold() for marker in hunger_markers):
            food_markers = ("ăn", "quán", "món", "chè", "bia", "cafe", "hải sản", "bun", "bún")
            if not any(marker in text for marker in food_markers):
                violations.append(
                    Violation(
                        rule="missed_food_need",
                        dimension="travel_suitability",
                        reason="User đang hỏi ăn/uống nhưng response không đưa hướng xử lý phù hợp.",
                        fix_suggestion="Ưu tiên gợi ý ăn/uống gần, ít lựa chọn, dễ đi.",
                        severity=Severity.HIGH,
                    )
                )

        location_markers = ("đâu", "o dau", "ở đâu", "gần", "gan", "maps", "trạm", "tram")
        if any(marker in user_message.casefold() for marker in location_markers):
            geo_markers = ("location", "maps", "vị trí", "share", "địa điểm", "dia diem", "gần")
            if not any(marker in text for marker in geo_markers):
                violations.append(
                    Violation(
                        rule="missed_location_guidance",
                        dimension="routing_quality",
                        reason="Query có yếu tố vị trí nhưng response không điều hướng theo địa điểm.",
                        fix_suggestion="Xin vị trí hoặc địa điểm cụ thể khi thiếu geolocation.",
                        severity=Severity.MEDIUM,
                    )
                )

        return AuditReport(
            session_id=session_id,
            user_message=user_message,
            ai_response=ai_response,
            scenario=scenario,
            violations=violations,
            replayable=True,
        )
