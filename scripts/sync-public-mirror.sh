#!/bin/bash
# Sync operational files to public mirror repo
# Excludes: personal bio, voice profile, sermons, daily logs, node_modules, secrets

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
# rsync include/exclude order is tricky; use explicit directory creation
mkdir -p "$MIRROR_DIR"/{skills,scripts,memory/context,supervisor-project,system}

# Sync each whitelisted path individually
rsync -av --delete \
    --exclude='node_modules/***' \
    --exclude='__pycache__/***' \
    --exclude='*.pyc' \
    --exclude='cookies/*.json' \
    --exclude='output/***' \
    --exclude='.env*' \
    "$SOURCE_DIR/skills/" "$MIRROR_DIR/skills/"

rsync -av --delete \
    --exclude='__pycache__/***' \
    --exclude='*.pyc' \
    "$SOURCE_DIR/scripts/" "$MIRROR_DIR/scripts/"

rsync -av --delete "$SOURCE_DIR/memory/context/" "$MIRROR_DIR/memory/context/"
rsync -av --delete "$SOURCE_DIR/supervisor-project/" "$MIRROR_DIR/supervisor-project/"
rsync -av --delete "$SOURCE_DIR/system/" "$MIRROR_DIR/system/"

# Individual files
cp -f "$SOURCE_DIR/AGENTS.md" "$MIRROR_DIR/" 2>/dev/null || true
cp -f "$SOURCE_DIR/TOOLS.md" "$MIRROR_DIR/" 2>/dev/null || true
cp -f "$SOURCE_DIR/RECOVERY.md" "$MIRROR_DIR/" 2>/dev/null || true
cp -f "$SOURCE_DIR/TODO.md" "$MIRROR_DIR/" 2>/dev/null || true

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
