#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

LIMIT="${CODEX_AUTOFIX_LIMIT:-3}"
MIN_SEVERITY="${CODEX_AUTOFIX_MIN_SEVERITY:-HIGH}"
PROMPT_OUT="${CODEX_AUTOFIX_PROMPT_OUT:-$REPO_ROOT/qa/fix_queue/latest_codex_prompt.md}"
LAST_MESSAGE_OUT="${CODEX_AUTOFIX_LAST_MESSAGE_OUT:-$REPO_ROOT/qa/fix_queue/latest_codex_reply.txt}"

cd "$REPO_ROOT"

python3 qa/codex_fix_bridge.py \
  --limit "$LIMIT" \
  --min-severity "$MIN_SEVERITY" \
  --write-prompt "$PROMPT_OUT" \
  --run-codex \
  --output-last-message "$LAST_MESSAGE_OUT"
