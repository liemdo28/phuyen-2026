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
        violation_count = sum(len(report.violations) for report in self.reports)
        return {
            "generated_at": datetime.now().isoformat(),
            "session_count": len(self.reports),
            "violation_count": violation_count,
            "pass_count": sum(1 for report in self.reports if not report.violations),
            "fail_count": sum(1 for report in self.reports if report.violations),
            "zero_audit_achieved": self.zero_audit_achieved(),
        }
