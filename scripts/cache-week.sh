#!/bin/bash
# Cache arnoldos week (calendar) JSON for dashboard consumption
# Runs every 5 minutes via crontab
CACHE_DIR="$HOME/clawd/memory/cache"
mkdir -p "$CACHE_DIR"
python3 "$HOME/clawd/scripts/arnoldos.py" week --json > "$CACHE_DIR/week.json.tmp" 2>/dev/null && \
  mv "$CACHE_DIR/week.json.tmp" "$CACHE_DIR/week.json"
