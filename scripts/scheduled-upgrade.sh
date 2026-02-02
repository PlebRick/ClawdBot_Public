#!/bin/bash
# Scheduled system upgrade
LOG="/home/ubuntu76/clawd/logs/upgrade-$(date +%Y%m%d-%H%M%S).log"

echo "[$(date)] Starting scheduled upgrade..." | tee -a "$LOG"

export DEBIAN_FRONTEND=noninteractive

sudo apt-get update >> "$LOG" 2>&1
sudo apt-get upgrade -y >> "$LOG" 2>&1
sudo apt-get dist-upgrade -y >> "$LOG" 2>&1
sudo apt-get autoremove -y >> "$LOG" 2>&1
sudo apt-get autoclean >> "$LOG" 2>&1

echo "[$(date)] Upgrade complete. Check if reboot needed:" | tee -a "$LOG"
[ -f /var/run/reboot-required ] && echo "REBOOT REQUIRED" | tee -a "$LOG" || echo "No reboot needed" | tee -a "$LOG"

echo "[$(date)] Done." | tee -a "$LOG"
