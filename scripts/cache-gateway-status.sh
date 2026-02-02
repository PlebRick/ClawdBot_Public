#!/bin/bash
# Cache gateway status JSON for dashboard consumption
# Runs every minute via crontab
CACHE_DIR="$HOME/clawd/memory/cache"
mkdir -p "$CACHE_DIR"
python3 "$HOME/clawd/scripts/cache-gateway-status.py" > "$CACHE_DIR/gateway-status.json.tmp" 2>/dev/null && \
  mv "$CACHE_DIR/gateway-status.json.tmp" "$CACHE_DIR/gateway-status.json"
