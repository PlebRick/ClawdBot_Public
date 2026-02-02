#!/usr/bin/env python3
"""
OpenRouter Spend Monitor — Phase 3.5
Queries OR usage API, logs spend, sends Telegram alerts at thresholds.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

MONTHLY_BUDGET = 10.00
ALERT_THRESHOLDS = [(0.50, "⚠️"), (0.75, "🚨"), (0.90, "🔴"), (1.00, "🛑")]
TELEGRAM_BOT_TOKEN = "8068243519:AAGgdFraZyAM0SWtCLBkd4_GlxWbO8LGHE4"
TELEGRAM_CHAT_ID = "1458942775"
LOG_FILE = os.path.expanduser("~/clawd/memory/logs/openrouter-spend.log")
STATE_FILE = os.path.expanduser("~/clawd/memory/cache/or-spend-state.json")
KILL_FLAG = os.path.expanduser("~/clawd/memory/cache/or-budget-exhausted.flag")

def get_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        try:
            with open(os.path.expanduser("~/.clawdbot/clawdbot.json")) as f:
                cfg = json.load(f)
            key = cfg.get("env", {}).get("vars", {}).get("OPENROUTER_API_KEY", "")
        except Exception:
            pass
    return key

def get_usage(api_key):
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["data"]

def get_credits(api_key):
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["data"]

def send_telegram(message):
    payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"alerted_thresholds": [], "last_usage": 0}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def log_usage(monthly, daily, credits):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] monthly=${monthly:.4f} daily=${daily:.4f} credits=${credits:.2f}\n")

def main():
    api_key = get_api_key()
    if not api_key:
        print("No OPENROUTER_API_KEY found", file=sys.stderr)
        sys.exit(1)

    usage = get_usage(api_key)
    credits = get_credits(api_key)

    monthly_spend = usage.get("usage_monthly", usage.get("usage", 0))
    daily_spend = usage.get("usage_daily", 0)
    total_credits = credits.get("total_credits", MONTHLY_BUDGET)
    total_usage = credits.get("total_usage", 0)

    budget = float(total_credits) if total_credits else MONTHLY_BUDGET
    pct = total_usage / budget if budget > 0 else 0

    log_usage(monthly_spend, daily_spend, budget)

    state = load_state()

    for threshold, emoji in ALERT_THRESHOLDS:
        if pct >= threshold and threshold not in state["alerted_thresholds"]:
            remaining = budget - total_usage
            msg = (
                f"{emoji} <b>OpenRouter Budget Alert</b>\n\n"
                f"Total spend: ${total_usage:.2f} ({pct*100:.1f}% of ${budget:.2f} credits)\n"
                f"Remaining credits: ${remaining:.2f}\n"
                f"Today's spend: ${daily_spend:.2f}"
            )
            if threshold >= 1.0:
                msg += "\n\n🛑 <b>BUDGET EXHAUSTED — API calls may fail.</b>"
                Path(KILL_FLAG).touch()
            send_telegram(msg)
            state["alerted_thresholds"].append(threshold)

    if pct < 1.0 and os.path.exists(KILL_FLAG):
        os.remove(KILL_FLAG)

    state["last_usage"] = total_usage
    save_state(state)

    print(f"OK: ${total_usage:.4f} / ${budget:.2f} ({pct*100:.1f}%)")

if __name__ == "__main__":
    main()
