"""
Run report generator for autonomous QA.
"""

from __future__ import annotations

import json
from pathlib import Path


class ReportGenerator:
    def __init__(self, root_dir: str | Path = "qa/reports"):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def generate_run_report(self, aggregator, *, run_id: str) -> dict[str, object]:
        summary = aggregator.get_summary()
        return {
            "run_id": run_id,
            "generated_at": summary["generated_at"],
            "summary": summary,
            "dev_fix_queue": [
                {
                    "rule": violation.rule,
                    "severity": violation.severity.value,
                    "user_message": report.user_message,
                    "reason": violation.reason,
                    "fix_suggestion": violation.fix_suggestion,
                    "replayable": report.replayable,
                }
                for report in aggregator.reports
                for violation in report.violations
            ],
        }

    def save_json_report(self, payload: dict[str, object]) -> str:
        path = self.root_dir / f"{payload['run_id']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def save_markdown_report(self, payload: dict[str, object]) -> str:
        summary = payload["summary"]
        lines = [
            f"# Autonomous QA Report — {payload['run_id']}",
            "",
            f"- Sessions audited: **{summary['session_count']}**",
            f"- Violations: **{summary['violation_count']}**",
            f"- Zero audit achieved: **{'Yes' if summary['zero_audit_achieved'] else 'No'}**",
            "",
            "## Fix Queue",
            "",
        ]
        for item in payload["dev_fix_queue"]:
            lines.extend(
                [
                    f"- [{item['severity']}] `{item['rule']}` — `{item['user_message']}`",
                    f"  Fix: {item['fix_suggestion']}",
                ]
            )
        path = self.root_dir / f"{payload['run_id']}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)
