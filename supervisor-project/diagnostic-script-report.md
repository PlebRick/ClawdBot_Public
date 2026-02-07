# Diagnostic Script Report — 2026-02-06


## What Was Done


Created `~/clawd/scripts/supervisor/clawdbot-diagnostic.sh` — a comprehensive 10-section health check covering services, connectivity, config, skills, memory, cron, cache, git, disk, and the model registry. The script uses color-coded pass/fail/warn markers and ends with a summary tally.


### Bug fixes during development


1. **`set -euo pipefail` → `set -uo pipefail`**: The `-e` flag caused the script to abort on the first non-zero exit code, which is wrong for a diagnostic tool that intentionally probes for failures. Removed `-e` so all 10 sections run to completion.


2. **trustedProxies path**: The script checked for `trustedProxies` at the top level of `clawdbot.json`. The actual path is `gateway.trustedProxies`. Fixed the Python JSON query. No config change was needed — the values `127.0.0.1` and `::1` were already present.


3. **401 handling**: Unauthenticated curl to auth-gated endpoints (file server) returns 401. Changed from fail to warning with "(reachable, auth required)" since the service is clearly running.


4. **Cache time display**: Fixed seconds display showing raw total instead of remainder (e.g., "3m 202s" → "3m 22s").


5. **Model registry parsing**: Updated to match the actual config structure where model keys are full IDs (e.g., `anthropic/claude-opus-4.5`) with an `alias` field, and the default model uses a `primary`/`fallbacks` object.


## Current Results


```
Passed:   45
Failed:    2
Warnings:  5
```


## Failures That Need Investigation


### 1. clawd-files not active as user systemd unit


The diagnostic checks `systemctl --user is-active clawd-files` and it fails. However, port 18790 is responding (HTTP 401), so something is serving files. Likely the file server is running as a standalone process (python3) rather than a user systemd unit.


**Options:**
- A) Create a user systemd unit for clawd-files so it auto-restarts and is managed like other services
- B) Change the diagnostic to check for a listening process on 18790 instead of a systemd unit
- C) If the CLAUDE.md service inventory is the source of truth (it lists "file-server" as a "standalone process"), then option B is correct and the script expectation is wrong


### 2. Memory DB not found


The script looks for `~/.clawdbot/state/memory/main.sqlite` but the file doesn't exist. This could mean:
- Memory indexing hasn't been run yet (`clawdbot memory sync`)
- The DB path has changed in a newer ClawdBot version
- Memory search may not be functional


**Action:** Run `clawdbot memory sync --force` and check if the DB gets created, or locate the actual DB path.


## Warnings (Low Priority)


| Warning | Notes |
|---------|-------|
| localhost:18790 returns 401 | Expected — auth required. Not a real problem. |
| ai.btctx.us/files/ returns 401 | Same as above, tunneled through cloudflared. |
| sermon-writer missing frontmatter | SKILL.md exists but lacks `name:` and `description:` in frontmatter. |
| web-scout missing frontmatter | Same issue. Skills may still work but won't be discoverable by ClawdBot's skill loader. |
| 5 uncommitted git changes | 3 are cache file churn (normal). 2 are new files: this script and `tech-ref-cheatsheet.md`. Should be committed. |