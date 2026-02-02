#!/bin/bash
# Sync supervisor-project/ files to Google Drive folder 02_ClawdBot/supervisor-project/
# Can be called standalone or after git push (see backup-to-github.sh)
#
# Drive folder ID: 1X1DQbFF_2eR_jpS3cyqlI1OcgeD3cglP

set -euo pipefail

CLAWD_DIR="$HOME/clawd"
SP_DIR="$CLAWD_DIR/supervisor-project"
SCRIPT_DIR="$CLAWD_DIR/scripts"
DRIVE_FOLDER_ID="1X1DQbFF_2eR_jpS3cyqlI1OcgeD3cglP"

python3 "$SCRIPT_DIR/sync-supervisor-drive.py" "$SP_DIR" "$DRIVE_FOLDER_ID"
