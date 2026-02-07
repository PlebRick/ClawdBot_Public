#!/bin/bash
cd ~/clawd
python3 scripts/skills-sync-v2.py "${1:-sync}"
