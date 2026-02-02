#!/bin/bash
# ArnoldOS Drive Sync — Local mirror of gdrive:01_ArnoldOS_Gemini
# Usage: arnoldos-sync.sh [pull|push|push-file <path>|dry|status]

REMOTE="gdrive:01_ArnoldOS_Gemini"
LOCAL="$HOME/clawd/arnoldos"
LOG="$HOME/clawd/memory/logs/arnoldos-sync.log"

# Exclude large files and system stuff
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
        rclone sync "$REMOTE" "$LOCAL" "${EXCLUDES[@]}" --log-file="$LOG" --log-level INFO
        log "Pull complete"
        ;;
    push)
        log "Starting PUSH from Local → Drive"
        echo "⚠️  WARNING: This will make Drive match Local. Files only on Drive will be DELETED."
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            rclone sync "$LOCAL" "$REMOTE" "${EXCLUDES[@]}" --progress --log-file="$LOG" --log-level INFO
            log "Push complete"
        else
            echo "Aborted."
        fi
        ;;
    push-file)
        if [ -z "$2" ]; then
            echo "Usage: arnoldos-sync.sh push-file <local-path>"
            exit 1
        fi
        ~/clawd/scripts/arnoldos-push-file.sh "$2"
        ;;
    dry)
        log "Dry run: showing what PULL would do"
        rclone sync "$REMOTE" "$LOCAL" "${EXCLUDES[@]}" --dry-run 2>&1 | grep -v "^$"
        ;;
    status)
        echo "Remote: $REMOTE"
        echo "Local:  $LOCAL"
        echo "Cron:   $(crontab -l 2>/dev/null | grep arnoldos || echo 'not set')"
        echo ""
        echo "Last sync:"
        tail -3 "$LOG" 2>/dev/null || echo "(no log yet)"
        echo ""
        echo "Local file count: $(find "$LOCAL" -type f 2>/dev/null | wc -l)"
        ;;
    *)
        echo "Usage: arnoldos-sync.sh [pull|push|push-file <path>|dry|status]"
        echo ""
        echo "  pull            - Download from Drive (Drive wins)"
        echo "  push            - Upload to Drive (Local wins) — DESTRUCTIVE"
        echo "  push-file PATH  - Upload single file (non-destructive)"
        echo "  dry             - Show what pull would do"
        echo "  status          - Show sync info"
        exit 1
        ;;
esac
