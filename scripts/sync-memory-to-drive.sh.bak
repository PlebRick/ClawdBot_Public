#!/bin/bash
# Sync local memory to Google Drive backup
# Run periodically via cron or manually

DRIVE_PATH="gdrive:02_ClawdBot/01_Memory"
LOCAL_MEMORY="/home/ubuntu76/clawd/memory"
LOCAL_MEMORY_MD="/home/ubuntu76/clawd/MEMORY.md"

echo "[$(date)] Starting memory sync to Drive..."

# Sync daily memory files
rclone sync "$LOCAL_MEMORY" "$DRIVE_PATH/daily" --progress

# Copy MEMORY.md
rclone copy "$LOCAL_MEMORY_MD" "$DRIVE_PATH" --progress

echo "[$(date)] Memory sync complete."
