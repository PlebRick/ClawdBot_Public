#!/bin/bash
# Sync ministry projects from ~/Projects/ to Google Drive "ricks-projects" folder
# Only syncs whitelisted project folders (not dev projects like clawd-dashboard)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1

# Whitelist: only these project folders sync to Drive
PROJECTS="Finney amillennialism"
DRIVE_FOLDER="1mLsMxY5rsTeE8J85VjQu2AIhVx-YqDYG"

for proj in $PROJECTS; do
  if [ -d "/home/ubuntu76/Projects/$proj" ]; then
    python3 -u scripts/sync-projects-drive.py "/home/ubuntu76/Projects/$proj" "$DRIVE_FOLDER" --name "$proj"
  fi
done
