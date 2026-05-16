#!/bin/bash
# QA cron runner — called every 3 minutes by launchd / crontab
# Logs to qa/qa_loop.log, writes reports to qa/reports/

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO_ROOT/qa/qa_loop.log"
PYTHON=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3

echo "$(date '+%Y-%m-%d %H:%M:%S') [cron] QA batch start" >> "$LOG"

cd "$REPO_ROOT"
$PYTHON qa/run_qa.py --mock --sessions 20 >> "$LOG" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') [cron] QA batch done" >> "$LOG"
