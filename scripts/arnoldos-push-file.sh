#!/bin/bash
# Push a single file or folder to Drive (non-destructive)
# Usage: arnoldos-push-file.sh <local-path>
# Example: arnoldos-push-file.sh ~/clawd/arnoldos/Ministry/Sermons/my-sermon.docx

LOCAL_BASE="$HOME/clawd/arnoldos"
REMOTE_BASE="gdrive:01_ArnoldOS_Gemini"

if [ -z "$1" ]; then
    echo "Usage: arnoldos-push-file.sh <local-path>"
    exit 1
fi

FULL_PATH="$(realpath "$1")"

# Make sure it's under arnoldos/
if [[ ! "$FULL_PATH" == "$LOCAL_BASE"* ]]; then
    echo "Error: File must be under $LOCAL_BASE"
    exit 1
fi

# Get relative path
REL_PATH="${FULL_PATH#$LOCAL_BASE/}"
REMOTE_DIR="$REMOTE_BASE/$(dirname "$REL_PATH")"

echo "Pushing: $FULL_PATH"
echo "     To: $REMOTE_DIR/"

rclone copy "$FULL_PATH" "$REMOTE_DIR/" --progress

echo "Done."
