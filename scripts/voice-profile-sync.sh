#!/bin/bash
# Voice Profile Sync — Python wrapper (v2)
# Replaces rclone-based sync with native Drive API + format conversion
# See voice-profile-sync-v2.py for implementation

exec python3 ~/clawd/scripts/voice-profile-sync-v2.py "$@"
