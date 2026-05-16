"""
Autonomous QA orchestration system.

Discovers QA artifacts in the repo, extracts replayable scenarios, replays
them against an AI handler, audits the responses, generates fix queues, and
produces summary reports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from ..audit.audit_engine import AuditEngine
from ..discovery import ExtractedScenario, ReportArtifact, ReportDiscoveryEngine, ScenarioExtractor
from ..fix_queue import FixQueueManager
from ..regression.regression_engine import RegressionEngine
from ..reporting.report_generator import ReportGenerator
from ..replay.replay_engine import ReplayEngine
from ..scoring.scoring_engine import SessionAggregator


@dataclass(slots=True)
class AutonomousQASummary:
    run_id: str
    artifact_count: int
    scenario_count: int
    replayed_count: int
    unresolved_audit_count: int
    zero_unresolved: bool
    report_json_path: str
    report_md_path: str
    fix_queue_json_path: str
    fix_queue_md_path: str
    regression_free: bool
    replay_fix_rate: float


class AutonomousQAOrchestrationSystem:
    """End-to-end autonomous QA scanner, replayer, auditor, and fixer loop."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root).resolve()
        self.discovery = ReportDiscoveryEngine(self.repo_root)
        self.extractor = ScenarioExtractor()
        self.audit = AuditEngine()
        self.replays = ReplayEngine(str(self.repo_root / "qa" / "replays"))
        self.reporter = ReportGenerator(str(self.repo_root / "qa" / "reports"))
        self.fix_queue = FixQueueManager(self.repo_root / "qa" / "fix_queue")
        self.regression = RegressionEngine(str(self.repo_root / "qa" / "regression" / "results"))

    def discover_reports(self) -> list[ReportArtifact]:
        return self.discovery.discover()

    def extract_scenarios(self, artifacts: list[ReportArtifact]) -> list[ExtractedScenario]:
        return self.extractor.extract_many(artifacts)

    def run(
        self,
        ai_handler: Callable[[str], str],
        max_scenarios: int = 100,
    ) -> AutonomousQASummary:
        run_id = f"autonomous_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        artifacts = self.discover_reports()
        scenarios = self.extract_scenarios(artifacts)[:max_scenarios]
        aggregator = SessionAggregator()

        for scenario in scenarios:
            try:
                ai_response = ai_handler(scenario.user_message)
            except Exception as exc:
                ai_response = f"[ERROR: {exc}]"
            report = self.audit.audit(
                session_id=scenario.scenario_id,
                user_message=scenario.user_message,
                ai_response=ai_response,
                scenario=scenario.failure_type,
                context=scenario.metadata,
            )
            aggregator.add_result(report)
            if report.violations:
                self.replays.save_for_replay(report)

        run_report = self.reporter.generate_run_report(aggregator, run_id=run_id)
        report_json_path = self.reporter.save_json_report(run_report)
        report_md_path = self.reporter.save_markdown_report(run_report)

        fix_items = self.fix_queue.build_items(aggregator.reports)
        fix_json_path, fix_md_path = self.fix_queue.save(run_id, fix_items)

        replay_result = self.replays.run_replay_batch(ai_handler, max_replays=max_scenarios)
        regression_result = self.regression.run_all(ai_handler)

        unresolved_audit_count = len(fix_items)
        zero_unresolved = (
            unresolved_audit_count == 0
            and aggregator.zero_audit_achieved()
            and regression_result.get("regression_free", False)
        )

        self._write_history_summary(
            run_id=run_id,
            artifacts=artifacts,
            scenarios=scenarios,
            summary=aggregator.get_summary(),
            replay_result=replay_result,
            regression_result=regression_result,
            zero_unresolved=zero_unresolved,
            unresolved_audit_count=unresolved_audit_count,
            report_json_path=report_json_path,
            fix_json_path=fix_json_path,
        )

        return AutonomousQASummary(
            run_id=run_id,
            artifact_count=len(artifacts),
            scenario_count=len(scenarios),
            replayed_count=replay_result.get("total_replays", 0),
            unresolved_audit_count=unresolved_audit_count,
            zero_unresolved=zero_unresolved,
            report_json_path=report_json_path,
            report_md_path=report_md_path,
            fix_queue_json_path=fix_json_path,
            fix_queue_md_path=fix_md_path,
            regression_free=bool(regression_result.get("regression_free", False)),
            replay_fix_rate=float(replay_result.get("fix_rate", 0.0)),
        )

    def _write_history_summary(
        self,
        *,
        run_id: str,
        artifacts: list[ReportArtifact],
        scenarios: list[ExtractedScenario],
        summary: dict,
        replay_result: dict,
        regression_result: dict,
        zero_unresolved: bool,
        unresolved_audit_count: int,
        report_json_path: str,
        fix_json_path: str,
    ) -> None:
        history_dir = self.repo_root / "qa" / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "artifact_count": len(artifacts),
            "scenario_count": len(scenarios),
            "summary": summary,
            "replay": {
                **replay_result,
                "results": [
                    {
                        "original_session_id": item.original_session_id,
                        "replay_attempt": item.replay_attempt,
                        "original_audit": item.original_audit,
                        "replay_audit": item.replay_audit,
                        "violations_before": item.violations_before,
                        "violations_after": item.violations_after,
                        "fixed": item.fixed,
                        "regressed": item.regressed,
                        "improvement": item.improvement,
                    }
                    for item in replay_result.get("results", [])
                ],
            },
            "regression": regression_result,
            "zero_unresolved": zero_unresolved,
            "unresolved_audit_count": unresolved_audit_count,
            "report_json_path": report_json_path,
            "fix_queue_json_path": fix_json_path,
        }
        (history_dir / f"{run_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
