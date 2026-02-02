#!/usr/bin/env bash
# cc-wrapper.sh — Claude Code cost wrapper with timeout + Telegram alerts
# Phase 6: API Migration Project

set -euo pipefail

# === Config ===
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
TELEGRAM_BOT_TOKEN="8068243519:AAGgdFraZyAM0SWtCLBkd4_GlxWbO8LGHE4"
TELEGRAM_CHAT_ID="1458942775"
LOG_FILE="$HOME/clawd/memory/logs/claude-code-costs.log"
TIMEOUT_SECONDS=1800  # 30 minutes
COST_ALERT_THRESHOLD=5.00

# Save original args before parsing
ORIG_ARGS=("$@")

# === Helpers ===
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

get_usage() {
  curl -s https://openrouter.ai/api/v1/auth/key \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    | jq -r '.data.usage // 0'
}

send_telegram() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="$TELEGRAM_CHAT_ID" \
    -d text="$1" \
    -d parse_mode="Markdown" > /dev/null
}

# === Preflight ===
if [[ -z "$OPENROUTER_API_KEY" ]]; then
  echo "ERROR: OPENROUTER_API_KEY not set" >&2
  exit 1
fi

mkdir -p "$(dirname "$LOG_FILE")"

# Extract task description (first -p or --prompt value)
TASK_DESC="(no description)"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--prompt) TASK_DESC="${2:-}"; break ;;
    *) shift ;;
  esac
done

# === Main ===
BEFORE=$(get_usage)
START_TIME=$(date +%s)

echo "📸 Balance before: \$${BEFORE}"
echo "⏱️  Timeout: ${TIMEOUT_SECONDS}s (30 min)"
echo "🚀 Starting Claude Code..."

# Run CC with timeout using preserved args
set +e
timeout "$TIMEOUT_SECONDS" claude "${ORIG_ARGS[@]}"
EXIT_CODE=$?
set -e

END_TIME=$(date +%s)
AFTER=$(get_usage)

# Calculate cost and duration
COST=$(echo "$AFTER - $BEFORE" | bc -l)
COST_FMT=$(printf "%.2f" "$COST")
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

# Log it
log "Task: \"$TASK_DESC\" | Cost: \$${COST_FMT} | Duration: ${DURATION_MIN}m ${DURATION_SEC}s | Exit: $EXIT_CODE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Session Complete"
echo "   Cost:     \$${COST_FMT}"
echo "   Duration: ${DURATION_MIN}m ${DURATION_SEC}s"
echo "   Exit:     $EXIT_CODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Alert if over threshold
if (( $(echo "$COST > $COST_ALERT_THRESHOLD" | bc -l) )); then
  MSG="🚨 *Claude Code Cost Alert*
Session cost: \$${COST_FMT} (threshold: \$${COST_ALERT_THRESHOLD})
Task: ${TASK_DESC}
Duration: ${DURATION_MIN}m ${DURATION_SEC}s"
  send_telegram "$MSG"
  echo "⚠️  Alert sent to Telegram (cost exceeded \$${COST_ALERT_THRESHOLD})"
fi

# Warn if timed out
if [[ $EXIT_CODE -eq 124 ]]; then
  echo "⏰ WARNING: Claude Code was killed after 30-minute timeout"
  log "TIMEOUT: Task killed after ${TIMEOUT_SECONDS}s"
fi

exit $EXIT_CODE
