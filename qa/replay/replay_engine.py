"""
Replay persistence and regression comparison for autonomous QA.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from ..audit.audit_engine import AuditEngine, AuditReport


@dataclass(slots=True)
class ReplayResult:
    original_session_id: str
    replay_attempt: int
    original_audit: str
    replay_audit: str
    violations_before: int
    violations_after: int
    fixed: bool
    regressed: bool
    improvement: int


class ReplayEngine:
    def __init__(self, root_dir: str | Path = "qa/replays"):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.audit = AuditEngine()

    def save_for_replay(self, report: AuditReport) -> None:
        payload = {
            "session_id": report.session_id,
            "user_message": report.user_message,
            "ai_response": report.ai_response,
            "audit_result": report.audit_result,
            "violations": [
                {
                    "rule": item.rule,
                    "dimension": item.dimension,
                    "reason": item.reason,
                    "fix_suggestion": item.fix_suggestion,
                    "severity": item.severity.value,
                }
                for item in report.violations
            ],
            "replayable": report.replayable,
        }
        (self.root_dir / f"{report.session_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def run_replay_batch(
        self,
        ai_handler: Callable[[str], str],
        *,
        max_replays: int = 100,
    ) -> dict[str, object]:
        results: list[ReplayResult] = []
        files = sorted(self.root_dir.glob("*.json"))[:max_replays]
        for index, path in enumerate(files, start=1):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            user_message = str(payload.get("user_message", "")).strip()
            if not user_message:
                continue
            original_count = len(payload.get("violations", []))
            replay_response = ai_handler(user_message)
            replay_report = self.audit.audit(
                session_id=str(payload.get("session_id") or path.stem),
                user_message=user_message,
                ai_response=replay_response,
                scenario="replay",
            )
            replay_count = len(replay_report.violations)
            fixed = replay_count < original_count
            regressed = replay_count > original_count
            results.append(
                ReplayResult(
                    original_session_id=str(payload.get("session_id") or path.stem),
                    replay_attempt=index,
                    original_audit="FAIL" if original_count else "PASS",
                    replay_audit=replay_report.audit_result,
                    violations_before=original_count,
                    violations_after=replay_count,
                    fixed=fixed,
                    regressed=regressed,
                    improvement=original_count - replay_count,
                )
            )

        total = len(results)
        fixed_count = sum(1 for item in results if item.fixed)
        return {
            "total_replays": total,
            "fixed": fixed_count,
            "fix_rate": (fixed_count / total * 100.0) if total else 0.0,
            "results": results,
        }
