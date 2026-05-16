from __future__ import annotations

import json
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from qa.discovery.report_discovery import ReportDiscoveryEngine
from qa.discovery.scenario_extractor import ScenarioExtractor
from qa.orchestration.autonomous_qa_system import AutonomousQAOrchestrationSystem


def test_report_discovery_finds_replays_and_reports(tmp_path: Path) -> None:
    qa_dir = tmp_path / "qa"
    (qa_dir / "replays").mkdir(parents=True)
    (qa_dir / "reports").mkdir(parents=True)
    (qa_dir / "replays" / "abc.json").write_text(
        json.dumps(
            {
                "session_id": "abc",
                "user_message": "doi chet roi",
                "detected_intent": "food",
                "audit_result": "FAIL",
                "severity": "HIGH",
                "violations": [{"rule": "missed_hunger_signal", "fix_suggestion": "Suggest food"}],
                "replayable": True,
            }
        ),
        encoding="utf-8",
    )
    (qa_dir / "reports" / "run.json").write_text(
        json.dumps(
            {
                "run_id": "run1",
                "dev_fix_queue": [
                    {
                        "rule": "robotic_corporate_tone",
                        "severity": "HIGH",
                        "user_message": "met vl ko muon di xa",
                        "fix_suggestion": "Shorten and calm down",
                        "replayable": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    engine = ReportDiscoveryEngine(tmp_path)
    artifacts = engine.discover()

    assert len(artifacts) == 2
    assert {artifact.report_type for artifact in artifacts} == {"replay_record", "run_report"}


def test_scenario_extractor_handles_replay_and_fix_queue(tmp_path: Path) -> None:
    qa_dir = tmp_path / "qa"
    (qa_dir / "replays").mkdir(parents=True)
    (qa_dir / "reports").mkdir(parents=True)
    replay = qa_dir / "replays" / "abc.json"
    replay.write_text(
        json.dumps(
            {
                "session_id": "abc",
                "user_message": "kiem quan local chill chill",
                "detected_intent": "slang_casual",
                "audit_result": "FAIL",
                "severity": "HIGH",
                "violations": [{"rule": "formal_response_to_slang_user", "fix_suggestion": "Sound more casual"}],
                "replayable": True,
            }
        ),
        encoding="utf-8",
    )
    report = qa_dir / "reports" / "run.json"
    report.write_text(
        json.dumps(
            {
                "run_id": "run1",
                "dev_fix_queue": [
                    {
                        "rule": "choice_overload",
                        "severity": "MEDIUM",
                        "user_message": "doi qua goi y nhanh di",
                        "fix_suggestion": "Max 3 options",
                        "replayable": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    artifacts = ReportDiscoveryEngine(tmp_path).discover()
    scenarios = ScenarioExtractor().extract_many(artifacts)

    assert len(scenarios) == 2
    assert {scenario.user_message for scenario in scenarios} == {
        "kiem quan local chill chill",
        "doi qua goi y nhanh di",
    }


def test_autonomous_qa_system_generates_reports_and_fix_queue(tmp_path: Path) -> None:
    qa_dir = tmp_path / "qa"
    for dirname in ["replays", "reports", "history", "fix_queue", "regression/results"]:
        (qa_dir / dirname).mkdir(parents=True, exist_ok=True)

    (qa_dir / "replays" / "abc.json").write_text(
        json.dumps(
            {
                "session_id": "abc",
                "user_message": "doi chet roi",
                "detected_intent": "food",
                "audit_result": "FAIL",
                "severity": "HIGH",
                "violations": [{"rule": "missed_hunger_signal", "fix_suggestion": "Suggest food quickly"}],
                "replayable": True,
            }
        ),
        encoding="utf-8",
    )

    system = AutonomousQAOrchestrationSystem(tmp_path)

    def ai_handler(message: str) -> str:
        return "I am an AI assistant and I hope this helps."

    result = system.run(ai_handler, max_scenarios=10)

    assert result.artifact_count >= 1
    assert result.scenario_count >= 1
    assert result.unresolved_audit_count >= 1
    assert Path(result.report_json_path).exists()
    assert Path(result.fix_queue_json_path).exists()
