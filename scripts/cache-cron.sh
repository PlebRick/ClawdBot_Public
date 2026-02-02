#!/bin/bash
# Cache cron jobs JSON for dashboard consumption
# Runs every minute via crontab
CACHE_DIR="$HOME/clawd/memory/cache"
mkdir -p "$CACHE_DIR"
python3 "$HOME/clawd/scripts/cache-cron.py" > "$CACHE_DIR/cron.json.tmp" 2>/dev/null && \
  mv "$CACHE_DIR/cron.json.tmp" "$CACHE_DIR/cron.json"
