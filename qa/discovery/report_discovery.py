"""
Autonomous QA report discovery.

Scans the repository for replayable QA artifacts such as run reports,
replay logs, markdown audits, csv exports, and conversation logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


DEFAULT_SCAN_DIRS = [
    "qa",
    "reports",
    "audit",
    "stress",
    "logs",
    "tests",
    "history",
    "replays",
    "failures",
]

SUPPORTED_EXTENSIONS = {
    ".json": "json",
    ".md": "markdown",
    ".markdown": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".csv": "csv",
    ".txt": "text",
    ".log": "log",
}


@dataclass(slots=True)
class ReportArtifact:
    path: Path
    relative_path: str
    file_type: str
    report_type: str
    source_area: str
    size_bytes: int
    metadata: dict[str, object] = field(default_factory=dict)


class ReportDiscoveryEngine:
    """Discovers QA artifacts under repo-managed scan roots."""

    def __init__(self, repo_root: str | Path, scan_dirs: Iterable[str] | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.scan_dirs = list(scan_dirs or DEFAULT_SCAN_DIRS)

    def discover(self) -> list[ReportArtifact]:
        artifacts: list[ReportArtifact] = []
        seen: set[Path] = set()

        for rel_dir in self.scan_dirs:
            root = self.repo_root / rel_dir
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path in seen:
                    continue
                if path.name.startswith("."):
                    continue
                artifact = self._classify(path)
                if artifact is None:
                    continue
                artifacts.append(artifact)
                seen.add(path)

        artifacts.sort(key=lambda item: item.relative_path)
        return artifacts

    def _classify(self, path: Path) -> ReportArtifact | None:
        ext = path.suffix.lower()
        file_type = SUPPORTED_EXTENSIONS.get(ext)
        if file_type is None:
            return None

        rel_path = path.relative_to(self.repo_root).as_posix()
        rel_lower = rel_path.lower()
        name_lower = path.name.lower()

        report_type = "generic"
        source_area = rel_path.split("/", 1)[0] if "/" in rel_path else rel_path

        if "/replays/" in rel_lower or "replay" in name_lower:
            report_type = "replay_record"
        elif "/reports/" in rel_lower or "report" in name_lower:
            report_type = "run_report"
        elif "/regression/" in rel_lower:
            report_type = "regression_report"
        elif "/audit/" in rel_lower:
            report_type = "audit_report"
        elif "/logs/" in rel_lower or ext == ".log":
            report_type = "log_capture"
        elif "/history/" in rel_lower:
            report_type = "history_record"
        elif "/failures/" in rel_lower:
            report_type = "failure_record"
        elif "/tests/" in rel_lower:
            report_type = "test_fixture"

        metadata = {
            "stem": path.stem,
            "extension": ext,
        }

        return ReportArtifact(
            path=path,
            relative_path=rel_path,
            file_type=file_type,
            report_type=report_type,
            source_area=source_area,
            size_bytes=path.stat().st_size,
            metadata=metadata,
        )
