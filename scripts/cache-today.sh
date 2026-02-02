#!/bin/bash
# Cache arnoldos today (calendar) JSON for dashboard consumption
# Runs every minute via crontab
CACHE_DIR="$HOME/clawd/memory/cache"
mkdir -p "$CACHE_DIR"
python3 "$HOME/clawd/scripts/arnoldos.py" today --json > "$CACHE_DIR/today.json.tmp" 2>/dev/null && \
  mv "$CACHE_DIR/today.json.tmp" "$CACHE_DIR/today.json"
