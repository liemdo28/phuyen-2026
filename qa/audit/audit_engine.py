"""
Minimal autonomous QA audit engine.
"""

from __future__ import annotations

import re
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


# ── Audit helpers ─────────────────────────────────────────────────────────────

# Expense patterns: "ăn hết 150k", "tiêu 80k", "đổ xăng 100k"
_EXPENSE_RE = re.compile(
    r"(ăn\s*hết|an\s*het|tiêu|tieu|đổ xăng|do xang|mua|chi)\s*\d",
    re.IGNORECASE,
)

# Negated "đâu" — idiomatic "don't want to go anywhere" (NOT a location query)
_NEGATED_DAU_RE = re.compile(
    r"(không|khong|chẳng|chang|chả|cha)\s+\w*\s*(đâu|dau)\b",
    re.IGNORECASE,
)


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
        msg = user_message.casefold()
        violations: list[Violation] = []

        # ── Empty response ────────────────────────────────────────────────────
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

        # ── Robotic / corporate tone ──────────────────────────────────────────
        # English markers (from LLM raw output leak) + Vietnamese markers
        robotic_markers = [
            # English (LLM sometimes slips into English)
            "as an ai",
            "i hope this helps",
            "furthermore,",
            "please feel free",
            "contact support",
            "best regards",
            "kind regards",
            # Vietnamese corporate / templated phrases
            "xin chào quý khách",
            "chúng tôi rất tiếc",
            "vui lòng liên hệ",
            "đội ngũ hỗ trợ",
            "tôi hy vọng điều này giúp ích",
            "như một trợ lý ai",
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

        # ── Choice overload ───────────────────────────────────────────────────
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

        # ── Missed food need ──────────────────────────────────────────────────
        # Skip if message is clearly an expense record (e.g. "ăn hết 150k")
        is_expense = bool(_EXPENSE_RE.search(user_message))
        hunger_markers = ("doi", "đói", "ăn gì", "an gi", "ăn ở đâu", "quán", "quan",
                          "chè", "che", "bé đói", "be doi", "chưa ăn")
        if not is_expense and any(marker in msg for marker in hunger_markers):
            food_markers = ("ăn", "quán", "món", "chè", "bia", "cafe", "hải sản",
                            "bun", "bún", "gần", "khu nào", "cho biết")
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

        # ── Missed location guidance ──────────────────────────────────────────
        # Only trigger when user is genuinely asking WHERE, not idioms like
        # "không muốn đi đâu cả" (= "don't want to go anywhere")
        location_markers = ("ở đâu", "o dau", "đi đâu", "di dau", "chỗ nào", "cho nao",
                            "gần đây", "gan day", "maps", "trạm", "tram")
        has_location_intent = any(marker in msg for marker in location_markers)
        # Suppress if it's a negation ("không muốn đi đâu")
        is_negated_location = bool(_NEGATED_DAU_RE.search(user_message))
        # Suppress if the message is about movement resistance ("gần thôi" = "nearby only")
        is_resistance = any(w in msg for w in ["gần thôi", "gan thoi", "không xa", "khong xa",
                                                "ngại đi xa", "ngai di xa", "lười đi", "luoi di"])

        if has_location_intent and not is_negated_location and not is_resistance:
            geo_markers = ("location", "maps", "vị trí", "share", "địa điểm", "dia diem",
                           "gần", "khu nào", "đang ở", "cho biết", "chỉ đường")
            if not any(marker in text for marker in geo_markers):
                violations.append(
                    Violation(
                        rule="missed_location_guidance",
                        dimension="routing_quality",
                        reason="User hỏi địa điểm nhưng response không điều hướng theo vị trí.",
                        fix_suggestion="Hỏi khu vực đang ở hoặc cung cấp gợi ý địa điểm cụ thể.",
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
