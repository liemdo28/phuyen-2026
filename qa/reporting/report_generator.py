"""
Run report generator for autonomous QA.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FixItem:
    """Single item in the dev fix queue — attribute-accessible."""
    rule: str
    severity: str
    user_message: str
    reason: str
    fix_suggestion: str
    replayable: bool = True


@dataclass
class RunReport:
    """Return object from generate_run_report — attribute-accessible."""
    run_id: str
    generated_at: str
    summary: dict
    dev_fix_queue: list[FixItem] = field(default_factory=list)


class ReportGenerator:
    def __init__(self, root_dir: str | Path = "qa/reports"):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def generate_run_report(self, aggregator, *, run_id: str) -> RunReport:
        summary = aggregator.get_summary()
        fix_queue = [
            FixItem(
                rule=violation.rule,
                severity=violation.severity.value,
                user_message=report.user_message,
                reason=violation.reason,
                fix_suggestion=violation.fix_suggestion,
                replayable=report.replayable,
            )
            for report in aggregator.reports
            for violation in report.violations
        ]
        return RunReport(
            run_id=run_id,
            generated_at=summary["generated_at"],
            summary=summary,
            dev_fix_queue=fix_queue,
        )

    def save_json_report(self, run_report: RunReport) -> str:
        payload = {
            "run_id": run_report.run_id,
            "generated_at": run_report.generated_at,
            "summary": run_report.summary,
            "dev_fix_queue": [
                {
                    "rule": item.rule,
                    "severity": item.severity,
                    "user_message": item.user_message,
                    "reason": item.reason,
                    "fix_suggestion": item.fix_suggestion,
                    "replayable": item.replayable,
                }
                for item in run_report.dev_fix_queue
            ],
        }
        path = self.root_dir / f"{run_report.run_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def save_markdown_report(self, run_report: RunReport) -> str:
        summary = run_report.summary
        lines = [
            f"# QA Report — {run_report.run_id}",
            "",
            f"- Sessions: **{summary.get('total_sessions', summary.get('session_count', 0))}**",
            f"- Pass rate: **{summary.get('pass_rate', 0):.1f}%**",
            f"- Score: **{summary.get('overall_score', 0):.1f}/10** (Grade: {summary.get('grade', '?')})",
            f"- Violations: **{summary.get('total_violations', summary.get('violation_count', 0))}**",
            f"- Zero audit: **{'✅ Yes' if summary.get('zero_audit_achieved') else '❌ No'}**",
            "",
            "## Fix Queue",
            "",
        ]
        for item in run_report.dev_fix_queue:
            emoji = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "⚪"}.get(item.severity, "⚪")
            lines.extend([
                f"- {emoji} [{item.severity}] `{item.rule}` — `{item.user_message}`",
                f"  Fix: {item.fix_suggestion}",
            ])
        path = self.root_dir / f"{run_report.run_id}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    def generate_zero_audit_certificate(self, run_id: str) -> str:
        """Write and return path of zero-audit certificate."""
        cert = {
            "certificate": "ZERO_AUDIT",
            "run_id": run_id,
            "message": "All QA sessions passed with zero violations.",
        }
        path = self.root_dir / f"{run_id}_ZERO_AUDIT.json"
        path.write_text(json.dumps(cert, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)
