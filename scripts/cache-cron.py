#!/usr/bin/env python3
"""Cache clawdbot cron jobs + system crontab for dashboard."""
import json, os, subprocess, sys, time
from datetime import datetime, timezone

CRON_JOBS_PATH = os.path.expanduser("~/.clawdbot/cron/jobs.json")

def get_system_crontab():
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            lines = [l.strip() for l in r.stdout.strip().split("\n") if l.strip() and not l.startswith("#")]
            return lines
        return []
    except Exception:
        return []

# Clawdbot cron jobs
clawdbot_jobs = []
try:
    with open(CRON_JOBS_PATH) as f:
        data = json.load(f)
    for job in data.get("jobs", []):
        state = job.get("state", {})
        clawdbot_jobs.append({
            "id": job.get("id"),
            "name": job.get("name"),
            "enabled": job.get("enabled", False),
            "agentId": job.get("agentId", job.get("payload", {}).get("agentId", "main")),
            "schedule": job.get("schedule", {}),
            "sessionTarget": job.get("sessionTarget"),
            "payloadKind": job.get("payload", {}).get("kind"),
            "nextRunAtMs": state.get("nextRunAtMs"),
            "lastRunAtMs": state.get("lastRunAtMs"),
            "lastStatus": state.get("lastStatus"),
            "lastDurationMs": state.get("lastDurationMs"),
        })
except Exception:
    pass

# System crontab entries
system_cron = get_system_crontab()

output = {
    "cachedAt": datetime.now(timezone.utc).isoformat(),
    "cachedAtMs": int(time.time() * 1000),
    "clawdbot": {
        "count": len(clawdbot_jobs),
        "jobs": clawdbot_jobs,
    },
    "system": {
        "count": len(system_cron),
        "entries": system_cron,
    },
}

json.dump(output, sys.stdout, indent=2)
