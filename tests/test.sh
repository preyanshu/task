#!/usr/bin/env bash
set -uo pipefail
TESTS_DIR="${TESTS_DIR:-/tests}"
VERIFIER_LOG_DIR="${VERIFIER_LOG_DIR:-/logs/verifier}"
mkdir -p "$VERIFIER_LOG_DIR"
python3 "$TESTS_DIR/test_outputs.py"
status=$?
if [ "$status" -eq 0 ]; then
  echo 1 > "$VERIFIER_LOG_DIR/reward.txt"
else
  echo 0 > "$VERIFIER_LOG_DIR/reward.txt"
fi
exit "$status"
