#!/bin/bash
# Supervisor Project Sync — Bidirectional sync with gdrive:02_ClawdBot/supervisor-project
# Usage: supervisor-sync.sh [pull|push|push-file <path>|dry|status]

REMOTE="gdrive:02_ClawdBot/supervisor-project"
LOCAL="$HOME/clawd/supervisor-project"
LOG="$HOME/clawd/memory/logs/supervisor-sync.log"

EXCLUDES=(
    "--exclude" ".DS_Store"
    "--exclude" "*.tmp"
)

timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

log() {
    echo "[$(timestamp)] $1" | tee -a "$LOG"
}

case "$1" in
    pull)
        log "Starting PULL from Drive → Local"
        rclone copy "$REMOTE" "$LOCAL" "${EXCLUDES[@]}" --log-file="$LOG" --log-level INFO
        log "Pull complete"
        ;;
    push)
        log "Starting PUSH from Local → Drive"
        rclone copy "$LOCAL" "$REMOTE" "${EXCLUDES[@]}" --progress --log-file="$LOG" --log-level INFO
        log "Push complete"
        ;;
    push-file)
        if [ -z "$2" ]; then
            echo "Usage: supervisor-sync.sh push-file <local-path>"
            exit 1
        fi
        FULL_PATH="$(realpath "$2")"
        if [[ ! "$FULL_PATH" == "$LOCAL"* ]]; then
            echo "Error: File must be under $LOCAL"
            exit 1
        fi
        REL_PATH="${FULL_PATH#$LOCAL/}"
        REMOTE_DIR="$REMOTE/$(dirname "$REL_PATH")"
        echo "Pushing: $FULL_PATH → $REMOTE_DIR/"
        rclone copy "$FULL_PATH" "$REMOTE_DIR/" --progress
        ;;
    dry)
        log "Dry run: showing what PULL would do"
        rclone copy "$REMOTE" "$LOCAL" "${EXCLUDES[@]}" --dry-run 2>&1 | grep -v "^$"
        ;;
    status)
        echo "Remote: $REMOTE"
        echo "Local:  $LOCAL"
        echo "Cron:   $(crontab -l 2>/dev/null | grep supervisor-sync || echo 'not set')"
        echo ""
        echo "Last sync:"
        tail -3 "$LOG" 2>/dev/null || echo "(no log yet)"
        echo ""
        echo "Local file count: $(find "$LOCAL" -type f 2>/dev/null | wc -l)"
        ;;
    *)
        echo "Usage: supervisor-sync.sh [pull|push|push-file <path>|dry|status]"
        echo ""
        echo "  pull            - Download from Drive → Local"
        echo "  push            - Upload Local → Drive"
        echo "  push-file PATH  - Upload single file"
        echo "  dry             - Show what pull would do"
        echo "  status          - Show sync info"
        exit 1
        ;;
esac
