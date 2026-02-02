#!/bin/bash
# Cache workspace tree JSON for dashboard consumption
# Runs every minute via crontab
CACHE_DIR="$HOME/clawd/memory/cache"
mkdir -p "$CACHE_DIR"
python3 "$HOME/clawd/scripts/cache-tree.py" > "$CACHE_DIR/tree.json.tmp" 2>/dev/null && \
  mv "$CACHE_DIR/tree.json.tmp" "$CACHE_DIR/tree.json"
