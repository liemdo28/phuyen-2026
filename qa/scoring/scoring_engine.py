"""
Minimal scoring and aggregation for autonomous QA runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..audit.audit_engine import AuditReport


@dataclass(slots=True)
class SessionAggregator:
    reports: list[AuditReport] = field(default_factory=list)

    def add_result(self, report: AuditReport) -> None:
        self.reports.append(report)

    def zero_audit_achieved(self) -> bool:
        return all(not report.violations for report in self.reports)

    def get_summary(self) -> dict[str, object]:
        total = len(self.reports)
        violation_count = sum(len(report.violations) for report in self.reports)
        pass_count = sum(1 for report in self.reports if not report.violations)
        pass_rate = (pass_count / total * 100) if total else 0.0

        # Score: start at 10, deduct 0.5 per violation (floor 0)
        raw_score = max(0.0, 10.0 - violation_count * 0.5)
        overall_score = round(raw_score, 1)

        if overall_score >= 9:
            grade = "S"
        elif overall_score >= 8:
            grade = "A"
        elif overall_score >= 7:
            grade = "B"
        elif overall_score >= 6:
            grade = "C"
        else:
            grade = "F"

        return {
            "generated_at": datetime.now().isoformat(),
            # Legacy keys (used by autonomous_qa_system)
            "session_count": total,
            "violation_count": violation_count,
            "pass_count": pass_count,
            "fail_count": total - pass_count,
            "zero_audit_achieved": self.zero_audit_achieved(),
            # Keys expected by run_qa.py default batch mode
            "total_sessions": total,
            "total_violations": violation_count,
            "pass_rate": round(pass_rate, 1),
            "overall_score": overall_score,
            "grade": grade,
        }
