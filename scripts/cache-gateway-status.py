#!/usr/bin/env python3
"""Gather gateway status from clawdbot CLI + systemd and output JSON."""
import json, os, subprocess, sys, time
from datetime import datetime, timezone

CLAWDBOT = os.path.expanduser("~/.nvm/versions/node/v22.22.0/bin/clawdbot")

def run(cmd, env=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=env)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None

def run_json(cmd, env=None):
    out = run(cmd, env=env)
    if not out:
        return None
    try:
        return json.loads(out)
    except Exception:
        return None

# Ensure DBUS_SESSION_BUS_ADDRESS is set for systemctl --user
uid = os.getuid()
dbus_env = os.environ.copy()
if "DBUS_SESSION_BUS_ADDRESS" not in dbus_env:
    dbus_env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{uid}/bus"

# Ensure PATH includes nvm node
path = dbus_env.get("PATH", "")
nvm_bin = os.path.expanduser("~/.nvm/versions/node/v22.22.0/bin")
if nvm_bin not in path:
    dbus_env["PATH"] = f"{nvm_bin}:{path}"

# Gateway service uptime from systemd
active_since = run(
    ["systemctl", "--user", "show", "clawdbot-gateway.service",
     "--property=ActiveEnterTimestamp", "--value"],
    env=dbus_env
)
uptime_str = None
uptime_ms = None
if active_since:
    try:
        dt = datetime.strptime(active_since.strip(), "%a %Y-%m-%d %H:%M:%S %Z")
        dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        uptime_ms = int(delta.total_seconds() * 1000)
        secs = int(delta.total_seconds())
        days, rem = divmod(secs, 86400)
        hours, rem = divmod(rem, 3600)
        mins, _ = divmod(rem, 60)
        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        parts.append(f"{mins}m")
        uptime_str = " ".join(parts)
    except Exception:
        pass

# Service state
svc_state = run(
    ["systemctl", "--user", "is-active", "clawdbot-gateway.service"],
    env=dbus_env
)
is_running = svc_state == "active"

# Full status from clawdbot CLI
status = run_json([CLAWDBOT, "status", "--json"], env=dbus_env)

sessions_data = status.get("sessions", {}) if status else {}
agents_data = status.get("agents", {}) if status else {}
heartbeat_data = status.get("heartbeat", {}) if status else {}
gateway_data = status.get("gateway", {}) if status else {}
os_data = status.get("os", {}) if status else {}
update_data = status.get("update", {}) if status else {}
memory_data = status.get("memory", {}) if status else {}
channels = status.get("channelSummary", []) if status else []

# Determine active model from most recent session, falling back to default
recent_sessions = sessions_data.get("recent", [])
default_model = sessions_data.get("defaults", {}).get("model")
active_model = default_model

# Try to find the most recent 'main' agent session that isn't a cron job if possible,
# or just take the absolute most recent one.
if recent_sessions:
    # recent_sessions are typically sorted by recency (newest first).
    # We'll just grab the first one's model.
    # Note: 'recent' contains mixed agent sessions. 
    # If we want MAIN agent specifically, we might filter.
    # For now, "active model" across the bot usually means "what responded last".
    active_model = recent_sessions[0].get("model") or default_model

output = {
    "cachedAt": datetime.now(timezone.utc).isoformat(),
    "cachedAtMs": int(time.time() * 1000),
    "gateway": {
        "status": "online" if is_running else "offline",
        "serviceState": svc_state or "unknown",
        "uptime": uptime_str,
        "uptimeMs": uptime_ms,
        "mode": gateway_data.get("mode"),
        "url": gateway_data.get("url"),
    },
    "model": active_model,
    "defaultModel": default_model,
    "contextTokens": sessions_data.get("defaults", {}).get("contextTokens"),
    "sessions": {
        "count": sessions_data.get("count", 0),
        "recent": sessions_data.get("recent", []),
    },
    "agents": {
        "defaultId": agents_data.get("defaultId"),
        "agents": agents_data.get("agents", []),
        "totalSessions": agents_data.get("totalSessions", 0),
    },
    "heartbeat": heartbeat_data,
    "channels": channels,
    "os": os_data,
    "version": {
        "installed": update_data.get("registry", {}).get("latestVersion"),
        "installKind": update_data.get("installKind"),
    },
    "memory": {
        "files": memory_data.get("files"),
        "chunks": memory_data.get("chunks"),
        "provider": memory_data.get("provider"),
    },
}

json.dump(output, sys.stdout, indent=2)
