#!/bin/bash
# Unstage voice profile files after Drive sync
# Copies from staging → scattered ClawdBot locations (with renames)

set -e

STAGE_DIR="$HOME/clawd/sync/voice-profile"

echo "Unstaging voice profile files..."

# Core files (reverse renames)
cp "$STAGE_DIR/core/ricks-voice-profile.md" "$HOME/clawd/memory/context/"
cp "$STAGE_DIR/core/voice-profile-training.md" "$HOME/clawd/memory/training/voice-profile.md"
cp "$STAGE_DIR/core/ricks-theological-framework.md" "$HOME/clawd/memory/context/"
cp "$STAGE_DIR/core/ricks-bio.md" "$HOME/clawd/memory/context/"
cp "$STAGE_DIR/core/ai-voice-calibration.md" "$HOME/clawd/memory/training/"
cp "$STAGE_DIR/core/user-profile.md" "$HOME/clawd/memory/context/user.md"

# Reference files
cp "$STAGE_DIR/reference/voice-card.md" "$HOME/clawd/skills/sermon-writer/references/"
cp "$STAGE_DIR/reference/voice-phrases.md" "$HOME/clawd/skills/sermon-writer/references/"
cp "$STAGE_DIR/reference/theological-positions.md" "$HOME/clawd/memory/context/"
cp "$STAGE_DIR/reference/recurring-themes.md" "$HOME/clawd/memory/context/"

# Sermon archive
rsync -a "$STAGE_DIR/sermon-archive/" "$HOME/clawd/memory/training/sermon-archive/"

# Calibration sessions - copy ALL from staging (may include new ones from Drive)
cp "$STAGE_DIR/calibration-sessions/"*.md "$HOME/clawd/memory/training/" 2>/dev/null || true

echo "Unstaging complete."
