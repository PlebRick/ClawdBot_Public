#!/bin/bash
# Supervisor Project Sync — Python wrapper (v2)
# Replaces rclone-based sync with native Drive API + format conversion
# See supervisor-sync-v2.py for implementation

exec python3 ~/clawd/scripts/supervisor-sync-v2.py "$@"
