#!/bin/bash
# Proton account keep-alive reminder
# Usage: proton-reminder.sh <days_left>

DAYS_LEFT="$1"

MSG="🔒 Proton Account Keep-Alive Reminder

⏰ ${DAYS_LEFT} day(s) until your annual Proton login deadline (Feb 1)

Log into ALL your Proton email accounts to prevent deletion. Proton nukes free accounts after 12 months of inactivity.

👉 https://account.proton.me/login

Two accounts were already lost in 2026. Don't let it happen again."

# Send to Telegram
clawdbot message send --channel telegram --target 1458942775 --message "$MSG"

# Post to main session
clawdbot message send --channel webchat --target main --message "$MSG" 2>/dev/null || true
