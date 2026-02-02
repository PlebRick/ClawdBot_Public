#!/bin/bash
# Cache preaching schedule JSON for dashboard consumption
# Runs every 5 minutes via crontab
CACHE_DIR="$HOME/clawd/memory/cache"
mkdir -p "$CACHE_DIR"
python3 "$HOME/clawd/scripts/arnoldos.py" preaching-schedule --json > "$CACHE_DIR/preaching.json.tmp" 2>/dev/null && \
  mv "$CACHE_DIR/preaching.json.tmp" "$CACHE_DIR/preaching.json"
