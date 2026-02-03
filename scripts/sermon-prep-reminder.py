#!/usr/bin/env python3
"""
Sermon Prep Reminder — Weekly check for upcoming preaching gaps

Checks preaching pipeline for dates within 14 days that have:
- TBD passage
- Missing brainstorm
- Missing draft (if <7 days out)

Sends Telegram alert only if gaps found.

Usage: python3 sermon-prep-reminder.py [--dry-run]
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=-6))
CACHE_FILE = os.path.expanduser("~/clawd/memory/cache/preaching.json")
LOOKAHEAD_DAYS = 14
DRAFT_URGENCY_DAYS = 7  # Flag missing draft if within 7 days


def load_preaching_schedule():
    """Load preaching schedule from cache."""
    if not os.path.exists(CACHE_FILE):
        # Try to refresh cache
        subprocess.run(
            ["python3", os.path.expanduser("~/clawd/scripts/arnoldos.py"), 
             "preaching-schedule", "--json"],
            capture_output=True
        )
    
    if not os.path.exists(CACHE_FILE):
        return None
    
    with open(CACHE_FILE) as f:
        return json.load(f)


def check_gaps(schedule):
    """Check for prep gaps in upcoming sermons."""
    today = datetime.now(CST).date()
    cutoff = today + timedelta(days=LOOKAHEAD_DAYS)
    draft_cutoff = today + timedelta(days=DRAFT_URGENCY_DAYS)
    
    gaps = []
    
    for sermon in schedule.get("schedule", []):
        sermon_date = datetime.strptime(sermon["date"], "%Y-%m-%d").date()
        
        # Skip if outside lookahead window
        if sermon_date > cutoff or sermon_date < today:
            continue
        
        days_until = (sermon_date - today).days
        missing = []
        
        # Check passage
        if sermon.get("passage") in (None, "TBD", ""):
            missing.append("passage")
        
        # Check brainstorm
        files = sermon.get("files", {})
        if not files.get("brainstorm"):
            missing.append("brainstorm")
        
        # Check draft (only urgent if within 7 days)
        if sermon_date <= draft_cutoff and not files.get("draft"):
            missing.append("draft")
        
        if missing:
            gaps.append({
                "date": sermon["date"],
                "days_until": days_until,
                "summary": sermon.get("summary", ""),
                "passage": sermon.get("passage", "TBD"),
                "status": sermon.get("status", "unknown"),
                "missing": missing
            })
    
    return gaps


def format_message(gaps):
    """Format Telegram message for gaps."""
    if not gaps:
        return None
    
    lines = ["📋 **Sermon Prep Reminder**\n"]
    
    for gap in sorted(gaps, key=lambda x: x["date"]):
        days = gap["days_until"]
        urgency = "🔴" if days <= 7 else "🟡"
        
        lines.append(f"{urgency} **{gap['date']}** ({days} days) — {gap['summary']}")
        lines.append(f"   Passage: {gap['passage']}")
        lines.append(f"   Missing: {', '.join(gap['missing'])}")
        lines.append("")
    
    return "\n".join(lines)


def send_telegram(message):
    """Send message via Telegram."""
    try:
        result = subprocess.run(
            ["clawdbot", "send", "--channel", "telegram", message],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)
        return False


def main():
    dry_run = "--dry-run" in sys.argv
    
    # Load schedule
    schedule = load_preaching_schedule()
    if not schedule:
        print("Could not load preaching schedule", file=sys.stderr)
        sys.exit(1)
    
    # Check for gaps
    gaps = check_gaps(schedule)
    
    if not gaps:
        print("No sermon prep gaps found. All good!")
        sys.exit(0)
    
    # Format message
    message = format_message(gaps)
    print(message)
    
    if dry_run:
        print("\n[DRY RUN — message not sent]")
    else:
        if send_telegram(message):
            print("\n[Sent to Telegram]")
        else:
            print("\n[Telegram send failed]", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
