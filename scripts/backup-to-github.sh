#!/bin/bash
# Auto-backup clawd workspace to GitHub
cd /home/ubuntu76/clawd || exit 1

# Ensure token auth
TOKEN=$(gh auth token 2>/dev/null)
if [ -n "$TOKEN" ]; then
  git remote set-url origin "https://PlebRick:${TOKEN}@github.com/PlebRick/ClawdBot_Backup.git"
fi

git add -A
if git diff --cached --quiet; then
  echo "No changes to backup"
  exit 0
fi

git commit -m "Auto-backup $(date '+%Y-%m-%d %H:%M')"
git push origin main

# Sync supervisor-project files to Google Drive
# Only runs if git push succeeded and supervisor-project files changed
if git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -q "^supervisor-project/"; then
  echo "Supervisor files changed — syncing to Drive..."
  bash "$(dirname "$0")/sync-supervisor-to-drive.sh" 2>&1 || echo "⚠️ Drive sync failed (non-fatal)"
fi

# Sync ~/Projects/ to Google Drive (ricks-projects)
echo "Syncing Projects to Drive..."
bash "$(dirname "$0")/sync-projects-to-drive.sh" 2>&1 || echo "⚠️ Projects Drive sync failed (non-fatal)"
