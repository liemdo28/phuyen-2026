#!/bin/sh
set -eu

DEFAULT_APP_ROOT="/app"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
FALLBACK_APP_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
APP_ROOT="${APP_ROOT:-$DEFAULT_APP_ROOT}"
if [ ! -d "$APP_ROOT" ]; then
  APP_ROOT="$FALLBACK_APP_ROOT"
fi
QA_ROOT="${QA_ROOT:-$APP_ROOT/qa}"
STATE_ROOT="${STATE_DIR:-/tmp}"
ARTIFACT_ROOT="${QA_ARTIFACT_ROOT:-$STATE_ROOT/qa-artifacts}"
LOG_ROOT="$ARTIFACT_ROOT/logs"
RUN_LOG="$LOG_ROOT/autonomous-qa-$(date +%Y%m%d-%H%M%S).log"
BACKEND_URL="${QA_BACKEND_URL:-https://phuyen-2026-telegram.onrender.com}"
MAX_SCENARIOS="${QA_MAX_SCENARIOS:-80}"
MOCK_MODE="${QA_MOCK_MODE:-false}"

mkdir -p \
  "$ARTIFACT_ROOT/reports" \
  "$ARTIFACT_ROOT/fix_queue" \
  "$ARTIFACT_ROOT/history" \
  "$ARTIFACT_ROOT/regression-results" \
  "$LOG_ROOT"

echo "[qa] app_root=$APP_ROOT"
echo "[qa] qa_root=$QA_ROOT"
echo "[qa] backend_url=$BACKEND_URL"
echo "[qa] artifact_root=$ARTIFACT_ROOT"
echo "[qa] max_scenarios=$MAX_SCENARIOS"
echo "[qa] mock_mode=$MOCK_MODE"

cd "$APP_ROOT"

CMD="python3 $QA_ROOT/run_qa.py --audit-reports --max-scenarios $MAX_SCENARIOS"
if [ "$MOCK_MODE" = "true" ]; then
  CMD="$CMD --mock"
fi

set +e
QA_BACKEND_URL="$BACKEND_URL" sh -c "$CMD" >"$RUN_LOG" 2>&1
STATUS=$?
set -e

cat "$RUN_LOG"

copy_if_dir() {
  SRC="$1"
  DEST="$2"
  if [ -d "$SRC" ]; then
    find "$SRC" -maxdepth 1 -type f -exec cp {} "$DEST"/ \;
  fi
}

copy_if_dir "$QA_ROOT/reports" "$ARTIFACT_ROOT/reports"
copy_if_dir "$QA_ROOT/fix_queue" "$ARTIFACT_ROOT/fix_queue"
copy_if_dir "$QA_ROOT/history" "$ARTIFACT_ROOT/history"
copy_if_dir "$QA_ROOT/regression/results" "$ARTIFACT_ROOT/regression-results"

exit "$STATUS"
