"""
Fix queue persistence for autonomous QA.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from ..audit.audit_engine import AuditReport


@dataclass(slots=True)
class FixQueueItem:
    item_id: str
    status: str
    severity: str
    rule: str
    dimension: str
    user_message: str
    reason: str
    fix_suggestion: str
    source_session_id: str
    replayable: bool
    regression_risk: str
    created_at: str


class FixQueueManager:
    """Writes unresolved QA findings into a durable queue."""

    def __init__(self, root_dir: str | Path = "qa/fix_queue"):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def build_items(self, reports: list[AuditReport]) -> list[FixQueueItem]:
        items: list[FixQueueItem] = []
        seen: set[tuple[str, str, str]] = set()
        for report in reports:
            for index, violation in enumerate(report.violations, start=1):
                key = (violation.rule, report.user_message.casefold(), violation.dimension)
                if key in seen:
                    continue
                seen.add(key)
                item_id = f"{report.session_id}:{index}"
                items.append(
                    FixQueueItem(
                        item_id=item_id,
                        status="open",
                        severity=violation.severity.value,
                        rule=violation.rule,
                        dimension=violation.dimension,
                        user_message=report.user_message,
                        reason=violation.reason,
                        fix_suggestion=violation.fix_suggestion,
                        source_session_id=report.session_id,
                        replayable=report.replayable,
                        regression_risk="HIGH" if violation.severity.value in {"CRITICAL", "HIGH"} else "MEDIUM",
                        created_at=datetime.now().isoformat(),
                    )
                )
        return items

    def save(self, run_id: str, items: list[FixQueueItem]) -> tuple[str, str]:
        json_path = self.root_dir / f"{run_id}.json"
        md_path = self.root_dir / f"{run_id}.md"

        json_payload = {
            "run_id": run_id,
            "generated_at": datetime.now().isoformat(),
            "open_items": [asdict(item) for item in items],
            "open_count": len(items),
        }
        json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = [
            f"# Fix Queue — {run_id}",
            "",
            f"Open items: **{len(items)}**",
            "",
        ]
        for item in items:
            lines.extend(
                [
                    f"## [{item.severity}] `{item.rule}`",
                    f"- Status: `{item.status}`",
                    f"- Dimension: `{item.dimension}`",
                    f"- Replayable: {'Yes' if item.replayable else 'No'}",
                    f"- User: `{item.user_message}`",
                    f"- Reason: {item.reason}",
                    f"- Fix: {item.fix_suggestion}",
                    "",
                ]
            )
        md_path.write_text("\n".join(lines), encoding="utf-8")
        return str(json_path), str(md_path)
