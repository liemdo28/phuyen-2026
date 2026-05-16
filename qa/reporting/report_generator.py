"""
QA Report Generator — Produces structured audit reports in multiple formats.
Generates dev fix queues and replayable violation records.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import asdict, dataclass

from ..audit.audit_engine import AuditReport, AuditResult, AuditSeverity, AuditViolation
from ..scoring.scoring_engine import QAScore, SessionAggregator


@dataclass
class DevFixItem:
    priority: int
    session_id: str
    rule: str
    severity: str
    user_message: str
    ai_response: str
    reason: str
    fix_suggestion: str
    dimension: str
    replayable: bool = True
    status: str = "open"  # open, in_progress, fixed, verified


@dataclass
class QARunReport:
    run_id: str
    timestamp: str
    total_sessions: int
    pass_count: int
    fail_count: int
    pass_rate: float
    overall_score: float
    grade: str
    zero_audit_achieved: bool
    dimension_averages: Dict[str, float]
    worst_dimensions: List[str]
    critical_violations: list
    dev_fix_queue: List[DevFixItem]
    improvement_targets: List[str]
    regression_status: str


class ReportGenerator:
    """Generates QA reports and developer fix queues."""

    def __init__(self, output_dir: str = "qa/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_run_report(self, aggregator: SessionAggregator, run_id: str = None) -> QARunReport:
        """Generate a full run report from an aggregator."""
        if not run_id:
            run_id = f"qa_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        summary = aggregator.get_summary()
        critical = aggregator.get_critical_violations()
        fix_queue = self._build_fix_queue(aggregator)
        targets = self._build_improvement_targets(summary, critical)

        report = QARunReport(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            total_sessions=summary.get("total_sessions", 0),
            pass_count=summary.get("pass_count", 0),
            fail_count=summary.get("fail_count", 0),
            pass_rate=summary.get("pass_rate", 0.0),
            overall_score=summary.get("overall_score", 0.0),
            grade=summary.get("grade", "F"),
            zero_audit_achieved=aggregator.zero_audit_achieved(),
            dimension_averages=summary.get("dimension_averages", {}),
            worst_dimensions=summary.get("worst_dimensions", []),
            critical_violations=critical,
            dev_fix_queue=fix_queue,
            improvement_targets=targets,
            regression_status="STABLE" if not critical else "REGRESSION_RISK",
        )

        return report

    def _build_fix_queue(self, aggregator: SessionAggregator) -> List[DevFixItem]:
        """Build prioritized dev fix queue from violations."""
        all_violations = []

        severity_priority = {
            AuditSeverity.CRITICAL: 1,
            AuditSeverity.HIGH: 2,
            AuditSeverity.MEDIUM: 3,
            AuditSeverity.LOW: 4,
        }

        for report in aggregator.reports:
            for v in report.violations:
                all_violations.append(DevFixItem(
                    priority=severity_priority.get(v.severity, 4),
                    session_id=report.session_id,
                    rule=v.rule,
                    severity=v.severity.value,
                    user_message=report.user_message[:200],
                    ai_response=report.actual_response[:200],
                    reason=v.reason,
                    fix_suggestion=v.fix_suggestion,
                    dimension=v.dimension,
                    replayable=report.replayable,
                ))

        # Sort by priority then deduplicate by rule
        all_violations.sort(key=lambda x: x.priority)
        seen_rules = set()
        deduplicated = []
        for item in all_violations:
            if item.rule not in seen_rules:
                deduplicated.append(item)
                seen_rules.add(item.rule)

        return deduplicated

    def _build_improvement_targets(self, summary: dict, critical: list) -> List[str]:
        """Build specific improvement targets for dev team."""
        targets = []

        dim_avgs = summary.get("dimension_averages", {})
        for dim, score in sorted(dim_avgs.items(), key=lambda x: x[1]):
            if score < 8.0:
                percentage_improvement = round((8.0 - score) / 10 * 100)
                targets.append(
                    f"🔴 {dim.replace('_', ' ').title()}: {score:.1f}/10 "
                    f"— needs +{percentage_improvement}% improvement"
                )

        if critical:
            targets.insert(0, f"🚨 CRITICAL: {len(critical)} critical violations must be fixed first")

        if not targets:
            targets.append("✅ All dimensions above threshold — focus on edge cases")

        return targets

    def save_json_report(self, report: QARunReport) -> str:
        """Save report as JSON file."""
        path = os.path.join(self.output_dir, f"{report.run_id}.json")

        report_dict = {
            "run_id": report.run_id,
            "timestamp": report.timestamp,
            "summary": {
                "total_sessions": report.total_sessions,
                "pass_count": report.pass_count,
                "fail_count": report.fail_count,
                "pass_rate": report.pass_rate,
                "overall_score": report.overall_score,
                "grade": report.grade,
                "zero_audit_achieved": report.zero_audit_achieved,
            },
            "dimension_averages": report.dimension_averages,
            "worst_dimensions": report.worst_dimensions,
            "improvement_targets": report.improvement_targets,
            "regression_status": report.regression_status,
            "critical_violations": report.critical_violations,
            "dev_fix_queue": [
                {
                    "priority": item.priority,
                    "session_id": item.session_id,
                    "rule": item.rule,
                    "severity": item.severity,
                    "user_message": item.user_message,
                    "reason": item.reason,
                    "fix_suggestion": item.fix_suggestion,
                    "dimension": item.dimension,
                    "replayable": item.replayable,
                    "status": item.status,
                }
                for item in report.dev_fix_queue
            ],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)

        return path

    def save_markdown_report(self, report: QARunReport) -> str:
        """Save report as human-readable markdown."""
        path = os.path.join(self.output_dir, f"{report.run_id}.md")

        lines = [
            f"# QA Run Report: {report.run_id}",
            f"**Generated:** {report.timestamp}",
            "",
            "---",
            "",
            "## 📊 Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Sessions | {report.total_sessions} |",
            f"| Pass | {report.pass_count} ({report.pass_rate:.1f}%) |",
            f"| Fail | {report.fail_count} |",
            f"| Overall Score | **{report.overall_score:.1f}/10** |",
            f"| Grade | **{report.grade}** |",
            f"| Zero Audit | {'✅ ACHIEVED' if report.zero_audit_achieved else '❌ NOT YET'} |",
            f"| Regression Status | {report.regression_status} |",
            "",
            "---",
            "",
            "## 🎯 Dimension Scores",
            "",
        ]

        dim_avgs = report.dimension_averages
        for dim, score in sorted(dim_avgs.items(), key=lambda x: x[1]):
            bar = "█" * int(score / 10 * 20) + "░" * (20 - int(score / 10 * 20))
            status = "✅" if score >= 8.0 else "⚠️" if score >= 7.0 else "🔴"
            lines.append(f"- {status} **{dim.replace('_', ' ').title()}**: {score:.1f}/10 `{bar}`")

        lines += [
            "",
            "---",
            "",
            "## 🚨 Improvement Targets",
            "",
        ]
        for target in report.improvement_targets:
            lines.append(f"- {target}")

        lines += [
            "",
            "---",
            "",
            "## 🛠️ Dev Fix Queue",
            "",
            f"**{len(report.dev_fix_queue)} unique violations** — sorted by priority",
            "",
        ]

        for i, item in enumerate(report.dev_fix_queue[:20], 1):  # top 20
            severity_emoji = {
                "CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"
            }.get(item.severity, "⚪")

            lines += [
                f"### {i}. {severity_emoji} `{item.rule}` [{item.severity}]",
                f"**Dimension:** {item.dimension}",
                f"**User Said:** `{item.user_message[:100]}`",
                f"**Reason:** {item.reason}",
                f"**Fix:** {item.fix_suggestion}",
                f"**Replayable:** {'Yes' if item.replayable else 'No'}",
                "",
            ]

        if report.critical_violations:
            lines += [
                "",
                "---",
                "",
                "## 🚨 Critical Violations (Immediate Action Required)",
                "",
            ]
            for cv in report.critical_violations[:10]:
                lines += [
                    f"- **{cv['rule']}** in session `{cv['session_id']}`",
                    f"  - Message: `{cv['message'][:80]}`",
                    f"  - Fix: {cv['reason']}",
                    "",
                ]

        lines += [
            "",
            "---",
            "",
            "## 🔄 Next Steps",
            "",
            "1. Fix all CRITICAL violations immediately",
            "2. Address HIGH severity issues in fix queue",
            "3. Run regression tests via `qa/regression/regression_engine.py`",
            "4. Re-run QA batch to verify fixes",
            "5. Loop until Zero Audit achieved",
            "",
        ]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return path

    def print_live_report(self, score: QAScore, report: AuditReport):
        """Print a real-time QA result to console."""
        status_icon = "✅" if score.pass_fail == "PASS" else "❌"
        severity_colors = {
            "CRITICAL": "\033[91m",  # red
            "HIGH": "\033[93m",      # yellow
            "MEDIUM": "\033[94m",    # blue
            "LOW": "\033[92m",       # green
        }
        reset = "\033[0m"

        print(f"\n{status_icon} [{report.session_id}] Score: {score.overall_score:.1f}/10 (Grade: {score.grade})")
        print(f"   Msg: {report.user_message[:60]}...")

        if report.violations:
            for v in report.violations:
                color = severity_colors.get(v.severity.value, "")
                print(f"   {color}⚠ {v.severity.value}: {v.rule}{reset}")
                print(f"     → {v.fix_suggestion[:80]}")

    def generate_zero_audit_certificate(self, run_id: str) -> str:
        """Generate a Zero Audit Achievement certificate."""
        cert = f"""
╔══════════════════════════════════════════════════════════════╗
║          🏆 ZERO AUDIT CERTIFICATE 🏆                        ║
║                                                               ║
║  QA Run: {run_id:<50} ║
║  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<52} ║
║                                                               ║
║  ✅ All sessions PASSED                                        ║
║  ✅ Zero audit violations detected                            ║
║  ✅ AI survived human civilization stress test                ║
║                                                               ║
║  The AI demonstrates:                                         ║
║  • Natural human-like conversation                            ║
║  • Emotional intelligence                                     ║
║  • Vietnamese culture & slang understanding                   ║
║  • Travel chaos management                                    ║
║  • Fatigue & emotional awareness                              ║
║  • Zero hallucinations                                        ║
║                                                               ║
║              CIVILIZATION LAYER: ACTIVE                       ║
╚══════════════════════════════════════════════════════════════╝
"""
        path = os.path.join(self.output_dir, f"{run_id}_ZERO_AUDIT.txt")
        with open(path, "w") as f:
            f.write(cert)
        return path
