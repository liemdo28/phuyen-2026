"""
Scenario extraction from discovered QA artifacts.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .report_discovery import ReportArtifact

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


@dataclass(slots=True)
class ExtractedScenario:
    scenario_id: str
    source_path: str
    source_type: str
    user_message: str
    expected_behavior: str
    failure_type: str
    severity: str = "MEDIUM"
    replayable: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


class ScenarioExtractor:
    """Extracts replayable QA scenarios from repository artifacts."""

    def extract_many(self, artifacts: list[ReportArtifact]) -> list[ExtractedScenario]:
        scenarios: list[ExtractedScenario] = []
        for artifact in artifacts:
            scenarios.extend(self.extract(artifact))
        return self._dedupe(scenarios)

    def extract(self, artifact: ReportArtifact) -> list[ExtractedScenario]:
        if artifact.file_type == "json":
            return self._extract_json(artifact)
        if artifact.file_type == "markdown":
            return self._extract_markdown(artifact)
        if artifact.file_type == "csv":
            return self._extract_csv(artifact)
        if artifact.file_type == "yaml":
            return self._extract_yaml(artifact)
        if artifact.file_type in {"text", "log"}:
            return self._extract_textual(artifact)
        return []

    def _extract_json(self, artifact: ReportArtifact) -> list[ExtractedScenario]:
        try:
            payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        except Exception:
            return []

        scenarios: list[ExtractedScenario] = []
        if isinstance(payload, dict) and {"session_id", "user_message", "violations"}.issubset(payload.keys()):
            scenarios.append(
                ExtractedScenario(
                    scenario_id=str(payload.get("session_id")),
                    source_path=artifact.relative_path,
                    source_type=artifact.report_type,
                    user_message=str(payload.get("user_message", "")).strip(),
                    expected_behavior=self._join_fix_suggestions(payload.get("violations", [])),
                    failure_type=str(payload.get("detected_intent") or artifact.report_type),
                    severity=str(payload.get("severity", "MEDIUM")),
                    replayable=bool(payload.get("replayable", True)),
                    metadata={"raw": payload},
                )
            )
            return scenarios

        if isinstance(payload, dict) and "dev_fix_queue" in payload:
            for index, item in enumerate(payload.get("dev_fix_queue", []), start=1):
                user_message = str(item.get("user_message", "")).strip()
                if not user_message:
                    continue
                scenarios.append(
                    ExtractedScenario(
                        scenario_id=f"{payload.get('run_id', artifact.path.stem)}:fix:{index}",
                        source_path=artifact.relative_path,
                        source_type=artifact.report_type,
                        user_message=user_message,
                        expected_behavior=str(item.get("fix_suggestion", "")).strip(),
                        failure_type=str(item.get("rule") or "audit_failure"),
                        severity=str(item.get("severity", "MEDIUM")),
                        replayable=bool(item.get("replayable", True)),
                        metadata={"run_id": payload.get("run_id"), "queue_item": item},
                    )
                )
            return scenarios

        if isinstance(payload, list):
            for index, item in enumerate(payload, start=1):
                if not isinstance(item, dict):
                    continue
                user_message = str(
                    item.get("user_message")
                    or item.get("text")
                    or item.get("message")
                    or ""
                ).strip()
                if not user_message:
                    continue
                scenarios.append(
                    ExtractedScenario(
                        scenario_id=f"{artifact.path.stem}:{index}",
                        source_path=artifact.relative_path,
                        source_type=artifact.report_type,
                        user_message=user_message,
                        expected_behavior=str(item.get("expected_behavior", "")).strip(),
                        failure_type=str(item.get("failure_type") or item.get("rule") or artifact.report_type),
                        severity=str(item.get("severity", "MEDIUM")),
                        replayable=bool(item.get("replayable", True)),
                        metadata={"row": item},
                    )
                )
        return scenarios

    def _extract_csv(self, artifact: ReportArtifact) -> list[ExtractedScenario]:
        scenarios: list[ExtractedScenario] = []
        try:
            with artifact.path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for index, row in enumerate(reader, start=1):
                    keys = {k.lower(): v for k, v in row.items() if k}
                    user_message = str(
                        keys.get("user_message")
                        or keys.get("message")
                        or keys.get("text")
                        or keys.get("query")
                        or ""
                    ).strip()
                    if not user_message:
                        continue
                    scenarios.append(
                        ExtractedScenario(
                            scenario_id=f"{artifact.path.stem}:{index}",
                            source_path=artifact.relative_path,
                            source_type=artifact.report_type,
                            user_message=user_message,
                            expected_behavior=str(keys.get("expected_behavior", "")).strip(),
                            failure_type=str(keys.get("failure_type") or keys.get("rule") or artifact.report_type),
                            severity=str(keys.get("severity", "MEDIUM")),
                            metadata={"row": row},
                        )
                    )
        except Exception:
            return []
        return scenarios

    def _extract_yaml(self, artifact: ReportArtifact) -> list[ExtractedScenario]:
        if yaml is None:
            return self._extract_textual(artifact)
        try:
            payload = yaml.safe_load(artifact.path.read_text(encoding="utf-8"))
        except Exception:
            return []
        fake_artifact = ReportArtifact(
            path=artifact.path,
            relative_path=artifact.relative_path,
            file_type="json",
            report_type=artifact.report_type,
            source_area=artifact.source_area,
            size_bytes=artifact.size_bytes,
            metadata=artifact.metadata,
        )
        temp_path = artifact.path.with_suffix(".json")
        return self._extract_json_from_payload(fake_artifact, payload, temp_path.stem)

    def _extract_json_from_payload(
        self,
        artifact: ReportArtifact,
        payload: object,
        stem: str,
    ) -> list[ExtractedScenario]:
        temp_file = artifact.path
        original_path = artifact.path
        artifact = ReportArtifact(
            path=temp_file,
            relative_path=artifact.relative_path,
            file_type="json",
            report_type=artifact.report_type,
            source_area=artifact.source_area,
            size_bytes=artifact.size_bytes,
            metadata=artifact.metadata,
        )
        if isinstance(payload, dict):
            text = json.dumps(payload, ensure_ascii=False)
        else:
            text = json.dumps(payload, ensure_ascii=False)
        temp_holder = original_path.parent / f".{stem}.tmp"
        temp_holder.write_text(text, encoding="utf-8")
        try:
            artifact = ReportArtifact(
                path=temp_holder,
                relative_path=artifact.relative_path,
                file_type="json",
                report_type=artifact.report_type,
                source_area=artifact.source_area,
                size_bytes=temp_holder.stat().st_size,
                metadata=artifact.metadata,
            )
            return self._extract_json(artifact)
        finally:
            temp_holder.unlink(missing_ok=True)

    def _extract_markdown(self, artifact: ReportArtifact) -> list[ExtractedScenario]:
        text = artifact.path.read_text(encoding="utf-8", errors="ignore")
        scenarios: list[ExtractedScenario] = []

        user_said_matches = re.findall(r"\*\*User Said:\*\*\s*`([^`]+)`", text)
        for index, user_message in enumerate(user_said_matches, start=1):
            scenarios.append(
                ExtractedScenario(
                    scenario_id=f"{artifact.path.stem}:md:{index}",
                    source_path=artifact.relative_path,
                    source_type=artifact.report_type,
                    user_message=user_message.strip(),
                    expected_behavior="",
                    failure_type="markdown_report",
                )
            )
        if scenarios:
            return scenarios

        code_blocks = re.findall(r"```(?:text|json)?\n(.*?)```", text, flags=re.DOTALL)
        for index, block in enumerate(code_blocks, start=1):
            cleaned = " ".join(line.strip() for line in block.splitlines() if line.strip())
            if not cleaned:
                continue
            scenarios.append(
                ExtractedScenario(
                    scenario_id=f"{artifact.path.stem}:code:{index}",
                    source_path=artifact.relative_path,
                    source_type=artifact.report_type,
                    user_message=cleaned[:300],
                    expected_behavior="",
                    failure_type="markdown_code_block",
                )
            )
        return scenarios

    def _extract_textual(self, artifact: ReportArtifact) -> list[ExtractedScenario]:
        text = artifact.path.read_text(encoding="utf-8", errors="ignore")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        scenarios: list[ExtractedScenario] = []
        for index, line in enumerate(lines[:50], start=1):
            if len(line.split()) < 2:
                continue
            scenarios.append(
                ExtractedScenario(
                    scenario_id=f"{artifact.path.stem}:line:{index}",
                    source_path=artifact.relative_path,
                    source_type=artifact.report_type,
                    user_message=line[:300],
                    expected_behavior="",
                    failure_type="text_log_line",
                    replayable=False,
                )
            )
        return scenarios

    def _join_fix_suggestions(self, violations: list[dict]) -> str:
        suggestions = [str(v.get("fix_suggestion", "")).strip() for v in violations if isinstance(v, dict)]
        suggestions = [s for s in suggestions if s]
        return " | ".join(suggestions[:3])

    def _dedupe(self, scenarios: list[ExtractedScenario]) -> list[ExtractedScenario]:
        deduped: list[ExtractedScenario] = []
        seen: set[tuple[str, str]] = set()
        for scenario in scenarios:
            key = (scenario.user_message.casefold(), scenario.failure_type.casefold())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(scenario)
        return deduped
