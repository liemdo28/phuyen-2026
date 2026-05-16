#!/usr/bin/env python3
"""
Bridge between autonomous QA fix queue and Codex CLI.

Reads qa/fix_queue/latest.json, selects top unresolved items, and either:
- prints a Codex-ready fix prompt
- writes the prompt to a file
- or invokes `codex exec` to let Codex fix the issues automatically
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
QA_ROOT = REPO_ROOT / "qa"
FIX_QUEUE_ROOT = QA_ROOT / "fix_queue"
DEFAULT_LATEST_FIX_QUEUE = FIX_QUEUE_ROOT / "latest.json"

SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}

NOISE_PREFIXES = (
    "🧪 running qa batch",
    "traceback",
    "file \"",
    "from qa.",
    "modulenotfounderror",
    "import ",
)


def _load_fix_queue(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Fix queue not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_fix_queue_candidates(primary_path: Path) -> list[Path]:
    candidates: list[Path] = []
    if primary_path.exists():
        candidates.append(primary_path)

    for path in sorted(FIX_QUEUE_ROOT.glob("autonomous_qa_*.json"), reverse=True):
        if path == primary_path:
            continue
        candidates.append(path)
    return candidates


def _is_noise_item(item: dict[str, object]) -> bool:
    user_message = str(item.get("user_message") or "").strip().casefold()
    if not user_message:
        return True
    return any(user_message.startswith(prefix) for prefix in NOISE_PREFIXES)


def _severity_rank(item: dict[str, object]) -> tuple[int, str]:
    severity = str(item.get("severity") or "MEDIUM").upper()
    return (SEVERITY_ORDER.get(severity, 99), severity)


def _filter_items(
    items: list[dict[str, object]],
    *,
    min_severity: str,
    limit: int,
    include_noise: bool,
) -> list[dict[str, object]]:
    threshold = SEVERITY_ORDER.get(min_severity.upper(), 99)
    selected: list[dict[str, object]] = []
    for item in sorted(items, key=lambda entry: (_severity_rank(entry), str(entry.get("rule") or ""))):
        severity = str(item.get("severity") or "MEDIUM").upper()
        if SEVERITY_ORDER.get(severity, 99) > threshold:
            continue
        if not include_noise and _is_noise_item(item):
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def _build_prompt(
    *,
    run_id: str,
    items: list[dict[str, object]],
    fix_queue_path: Path,
) -> str:
    issue_lines: list[str] = []
    for index, item in enumerate(items, start=1):
        issue_lines.extend(
            [
                f"{index}. [{item.get('severity')}] rule=`{item.get('rule')}`",
                f"   user_message: {item.get('user_message')}",
                f"   reason: {item.get('reason')}",
                f"   fix_recommendation: {item.get('fix_suggestion')}",
                f"   source_session_id: {item.get('source_session_id')}",
            ]
        )

    return (
        "Read the latest QA fix queue and fix the selected issues in the codebase.\n\n"
        f"Repository: {REPO_ROOT}\n"
        f"Latest fix queue: {fix_queue_path}\n"
        f"Run ID: {run_id}\n\n"
        "Requirements:\n"
        "- Fix the issues in code, not by muting tests or deleting scenarios.\n"
        "- Prefer the smallest safe patch that resolves the root cause.\n"
        "- Re-run the most relevant tests or QA commands after each fix.\n"
        "- Summarize what was fixed, what was verified, and any remaining risk.\n"
        "- Do not revert unrelated user changes.\n\n"
        "Selected QA items:\n"
        + "\n".join(issue_lines)
        + "\n\n"
        "Suggested verification flow:\n"
        "- python3 qa/run_qa.py --latest-fix-queue\n"
        "- python3 qa/run_qa.py --audit-reports --mock --max-scenarios 5\n"
        "- run any targeted backend tests needed for the touched files\n"
    )


def _write_prompt(path: Path, prompt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt, encoding="utf-8")


def _run_codex(
    *,
    codex_bin: str,
    prompt: str,
    model: str | None,
    output_file: Path | None,
) -> int:
    command = [
        codex_bin,
        "exec",
        "-C",
        str(REPO_ROOT),
        "--skip-git-repo-check",
        "-s",
        "danger-full-access",
        "-a",
        "never",
    ]
    if model:
        command.extend(["-m", model])
    if output_file is not None:
        command.extend(["-o", str(output_file)])
    command.append("-")

    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Send latest QA fix queue into Codex for autofix.")
    parser.add_argument("--fix-queue", default=str(DEFAULT_LATEST_FIX_QUEUE), help="Path to latest fix queue JSON")
    parser.add_argument("--limit", type=int, default=3, help="Max number of fix items to send to Codex")
    parser.add_argument("--min-severity", default="HIGH", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"], help="Minimum severity to include")
    parser.add_argument("--include-noise", action="store_true", help="Include obviously noisy/self-generated fix-queue entries")
    parser.add_argument("--print-prompt", action="store_true", help="Print generated Codex prompt to stdout")
    parser.add_argument("--write-prompt", help="Write generated prompt to a file")
    parser.add_argument("--run-codex", action="store_true", help="Invoke codex exec with the generated prompt")
    parser.add_argument("--codex-bin", default=shutil.which("codex") or "codex", help="Codex CLI path")
    parser.add_argument("--model", default=os.environ.get("CODEX_AUTOFIX_MODEL"), help="Optional model override for codex exec")
    parser.add_argument("--output-last-message", help="Write Codex last message to this file when using --run-codex")

    args = parser.parse_args()

    selected_path: Path | None = None
    payload: dict[str, object] | None = None
    items: list[dict[str, object]] = []
    for candidate in _iter_fix_queue_candidates(Path(args.fix_queue)):
        candidate_payload = _load_fix_queue(candidate)
        candidate_items = _filter_items(
            list(candidate_payload.get("open_items") or []),
            min_severity=args.min_severity,
            limit=args.limit,
            include_noise=args.include_noise,
        )
        if candidate_items:
            selected_path = candidate
            payload = candidate_payload
            items = candidate_items
            break

    if payload is None or selected_path is None or not items:
        print("No eligible fix-queue items found for Codex autofix.", file=sys.stderr)
        return 1

    prompt = _build_prompt(
        run_id=str(payload.get("run_id") or "unknown"),
        items=items,
        fix_queue_path=selected_path.resolve(),
    )

    if args.write_prompt:
        _write_prompt(Path(args.write_prompt), prompt)

    if args.print_prompt or not args.run_codex:
        print(prompt)

    if args.run_codex:
        return _run_codex(
            codex_bin=args.codex_bin,
            prompt=prompt,
            model=args.model,
            output_file=Path(args.output_last_message) if args.output_last_message else None,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
