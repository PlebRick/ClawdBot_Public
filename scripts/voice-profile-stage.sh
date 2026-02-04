#!/bin/bash
# Stage voice profile files for Drive sync
# Copies from scattered ClawdBot locations → unified staging structure

set -e

STAGE_DIR="$HOME/clawd/sync/voice-profile"

echo "Staging voice profile files..."

# Core files (with renames where needed)
cp "$HOME/clawd/memory/context/ricks-voice-profile.md" "$STAGE_DIR/core/"
cp "$HOME/clawd/memory/training/voice-profile.md" "$STAGE_DIR/core/voice-profile-training.md"
cp "$HOME/clawd/memory/context/ricks-theological-framework.md" "$STAGE_DIR/core/"
cp "$HOME/clawd/memory/context/ricks-bio.md" "$STAGE_DIR/core/"
cp "$HOME/clawd/memory/training/ai-voice-calibration.md" "$STAGE_DIR/core/"
cp "$HOME/clawd/memory/context/user.md" "$STAGE_DIR/core/user-profile.md"

# Reference files
cp "$HOME/clawd/skills/sermon-writer/references/voice-card.md" "$STAGE_DIR/reference/"
cp "$HOME/clawd/skills/sermon-writer/references/voice-phrases.md" "$STAGE_DIR/reference/"
cp "$HOME/clawd/memory/context/theological-positions.md" "$STAGE_DIR/reference/"
cp "$HOME/clawd/memory/context/recurring-themes.md" "$STAGE_DIR/reference/"

# Sermon archive (directory)
rsync -a --delete "$HOME/clawd/memory/training/sermon-archive/" "$STAGE_DIR/sermon-archive/"

# Calibration sessions (glob pattern)
cp "$HOME/clawd/memory/training/voice-calibration-session-"*.md "$STAGE_DIR/calibration-sessions/" 2>/dev/null || true

echo "Staging complete."
