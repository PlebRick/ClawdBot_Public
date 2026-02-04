#!/bin/bash
# Memory Sync — Python wrapper (v2)
# Syncs context/ and todos/ only (not daily logs, training, cache, logs)
# See memory-sync-v2.py for implementation

exec python3 ~/clawd/scripts/memory-sync-v2.py "$@"
