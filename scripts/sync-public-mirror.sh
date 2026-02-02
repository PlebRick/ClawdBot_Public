#!/bin/bash
# Sync operational files to public mirror repo
# Excludes: personal bio, voice profile, sermons, daily logs

set -e

MIRROR_DIR=~/clawd-public-mirror
SOURCE_DIR=~/clawd

# Ensure mirror exists
if [ ! -d "$MIRROR_DIR/.git" ]; then
    echo "ERROR: Mirror repo not initialized at $MIRROR_DIR"
    echo "Run: git clone https://github.com/PlebRick/ClawdBot_Public.git $MIRROR_DIR"
    exit 1
fi

# Selective sync - whitelist approach
rsync -av --delete \
    --include='skills/***' \
    --include='scripts/***' \
    --include='memory/context/***' \
    --include='supervisor-project/***' \
    --include='system/***' \
    --include='AGENTS.md' \
    --include='TOOLS.md' \
    --include='RECOVERY.md' \
    --include='TODO.md' \
    --exclude='*' \
    "$SOURCE_DIR/" "$MIRROR_DIR/"

# Commit and push if changes exist
cd "$MIRROR_DIR"
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "sync $(date +%Y-%m-%d-%H%M)"
    git push origin main
    echo "Mirror updated and pushed."
else
    echo "No changes to sync."
fi
