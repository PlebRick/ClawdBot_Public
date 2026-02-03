#!/bin/bash
# ArnoldOS Drive Sync — Bidirectional sync with gdrive:01_ArnoldOS_Gemini
# Usage: arnoldos-sync.sh [pull|push|sync|push-file <path>|dry|status]

REMOTE="gdrive:01_ArnoldOS_Gemini"
LOCAL="$HOME/clawd/arnoldos"
LOG="$HOME/clawd/memory/logs/arnoldos-sync.log"

EXCLUDES=(
    "--exclude" "*.mp4"
    "--exclude" "*.mov"
    "--exclude" "*.zip"
    "--exclude" "*.tar.gz"
    "--exclude" ".DS_Store"
    "--exclude" "*.tmp"
    "--exclude" "README.md"
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
        rclone copy "$LOCAL" "$REMOTE" "${EXCLUDES[@]}" --log-file="$LOG" --log-level INFO
        log "Push complete"
        ;;
    sync)
        # Bidirectional: pull then push
        log "Starting BIDIRECTIONAL SYNC"
        log "Step 1: Pull from Drive → Local"
        rclone copy "$REMOTE" "$LOCAL" "${EXCLUDES[@]}" --log-file="$LOG" --log-level INFO
        log "Step 2: Push from Local → Drive"
        rclone copy "$LOCAL" "$REMOTE" "${EXCLUDES[@]}" --log-file="$LOG" --log-level INFO
        log "Bidirectional sync complete"
        ;;
    push-file)
        if [ -z "$2" ]; then
            echo "Usage: arnoldos-sync.sh push-file <local-path>"
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
        echo "=== What PULL would do (Drive → Local) ==="
        rclone copy "$REMOTE" "$LOCAL" "${EXCLUDES[@]}" --dry-run 2>&1 | grep -v "^$"
        echo ""
        echo "=== What PUSH would do (Local → Drive) ==="
        rclone copy "$LOCAL" "$REMOTE" "${EXCLUDES[@]}" --dry-run 2>&1 | grep -v "^$"
        ;;
    status)
        echo "Remote: $REMOTE"
        echo "Local:  $LOCAL"
        echo "Cron:   $(crontab -l 2>/dev/null | grep arnoldos || echo 'not set')"
        echo ""
        echo "Last sync:"
        tail -5 "$LOG" 2>/dev/null || echo "(no log yet)"
        echo ""
        echo "Local file count: $(find "$LOCAL" -type f 2>/dev/null | wc -l)"
        ;;
    *)
        echo "Usage: arnoldos-sync.sh [pull|push|sync|push-file <path>|dry|status]"
        echo ""
        echo "  pull            - Download from Drive → Local (non-destructive)"
        echo "  push            - Upload Local → Drive (non-destructive)"
        echo "  sync            - Bidirectional: pull then push"
        echo "  push-file PATH  - Upload single file"
        echo "  dry             - Show what sync would do"
        echo "  status          - Show sync info"
        exit 1
        ;;
esac
