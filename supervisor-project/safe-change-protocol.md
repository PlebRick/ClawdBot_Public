# ClawdBot Safe Change Protocol


## Overview


This document establishes a protocol for making system changes safely, with Claude (Opus) acting as a reviewer/supervisor for changes that could affect ClawdBot's connectivity or system stability.


---


## The Core Problem


ClawdBot runs on infrastructure that it can modify. This creates a risk where ClawdBot can "saw off the branch it's sitting on" - making a change that breaks its own connectivity before it can complete or rollback the change.


---


## Change Categories


### Category A: Low Risk (No Review Required)
- Reading files or logs
- Querying system status
- Non-persistent operations
- Changes that don't affect networking, authentication, or services


### Category B: Medium Risk (Document Before Executing)
- Modifying application configs (not networking/auth)
- Installing packages
- Creating new files/scripts
- Creating new skills
- Changes that can be easily rolled back


### Category C: High Risk (REQUIRES SUPERVISOR REVIEW)
- **Any change to TLS/HTTPS settings**
- **Any change to authentication/authorization**
- **Any change to proxy/tunnel configuration**
- **Any change to systemd services**
- **Any change that affects ClawdBot's own connectivity**
- Service restarts for critical components


---


## The Review Process


### Step 1: ClawdBot Proposes


For Category C changes, ClawdBot must provide:


```
## Proposed Change


**What**: [One-line description]
**File(s)**: [Full path to each file being modified]
**Current value**: [What it is now]
**New value**: [What it will become]


**Command sequence**:
1. [First command]
2. [Second command]
...


**Why this order**: [Explain why steps are in this sequence]
**How to test**: [Command to verify success]


**Rollback procedure**:
1. [First rollback step]
2. [Second rollback step]


**What could break**: [Honest assessment of risks]
**Does this affect my own connectivity?**: [Yes/No + explanation]
```


### Step 2: Claude Reviews


Claude (Opus) will check:
1. **File paths** - Is this the correct file? (Check what the service actually uses)
2. **Order of operations** - Is the sequence safe? (Client before server for protocol changes)
3. **Network assumptions** - IPv4 AND IPv6 considered?
4. **Rollback validity** - Can this actually be rolled back if connectivity is lost?
5. **Missing steps** - Are there any steps that should be added?


Claude responds with:
- **APPROVED** - Proceed as planned
- **APPROVED WITH CHANGES** - Specific modifications required
- **REJECTED** - Explain why, suggest alternative approach


### Step 3: Human Executes


Chaplain executes the approved change while monitoring for issues.


### Step 4: Verify


Run the test command(s) to confirm success before proceeding.


---


## Safe Ordering Rules


### Protocol Changes (HTTP ↔ HTTPS)


**ALWAYS update in this order:**
1. Update the CLIENT config to accept the new protocol
2. Restart the CLIENT
3. Verify CLIENT is working with current setup
4. Update the SERVER config to use new protocol
5. Restart the SERVER
6. Verify end-to-end


**Why**: If you change the server first, the client can't connect to complete further changes.


### Authentication Changes


**ALWAYS:**
1. Ensure you have a LOCAL access method that won't be affected
2. Make the change
3. Test remote access
4. If remote fails, use local access to rollback


### Service Changes


**Before restarting any service:**
1. Verify the config file is valid (syntax check if possible)
2. Know the exact rollback command
3. Have logs ready to monitor: `journalctl -u <service> -f`


---


## Pre-Change Checklist


Before ANY Category C change:
- [ ] Verified correct config file path (check systemd service definition)
- [ ] Documented current state
- [ ] Rollback procedure written and ready
- [ ] Rollback doesn't depend on the thing being changed
- [ ] IPv4 AND IPv6 considered for network changes
- [ ] Change order is safe (client before server)
- [ ] Human is available to intervene if needed
- [ ] Submitted for supervisor review (if Category C)


---


## Emergency Rollback Commands


Keep these ready:


```bash
# Gateway - disable TLS (if enabled)
# Edit ~/.clawdbot/clawdbot.json, set gateway.tls.enabled: false
sudo systemctl restart clawdbot


# Gateway - reset allowInsecureAuth
sed -i 's/"allowInsecureAuth": false/"allowInsecureAuth": true/' ~/.clawdbot/clawdbot.json
sudo systemctl restart clawdbot


# Cloudflared - revert to HTTP
# Edit /etc/cloudflared/config.yml, change https:// back to http://
sudo systemctl restart cloudflared


# Kill stuck processes
sudo systemctl stop clawdbot
pkill -9 -f clawdbot
sudo systemctl start clawdbot


# Full tunnel reset
sudo systemctl restart cloudflared
```


---


## Communication Template


### ClawdBot → Claude (Proposing Change)


```
I need to make a Category C change. Here's my proposal:


**What**: [description]
**File**: [path]
**Change**: [before → after]
**Commands**: [sequence]
**Test**: [verification]
**Rollback**: [procedure]
**Connectivity risk**: [assessment]


Please review.
```


### Claude → ClawdBot (Review Response)


```
**REVIEW: [APPROVED / APPROVED WITH CHANGES / REJECTED]**


[If approved with changes or rejected, explain why and what needs to change]


[Any additional safety notes]
```


---


## Lessons from the TLS Incident


1. **Verify before modifying** - `sudo systemctl cat <service>` shows which config is actually used
2. **Client first, server second** - For protocol changes
3. **IPv6 exists** - trustedProxies needs `["127.0.0.1", "::1"]`
4. **Don't cut your own connection** - If you're changing how you connect, have an alternative path
5. **Review catches mistakes** - A second set of eyes would have caught the wrong config file


---


## Category Examples


| Change | Category | Reason |
|--------|----------|--------|
| Read a log file | A | No persistence, no risk |
| Create a new skill | B | Additive, easy rollback |
| Install an npm package | B | Reversible, no connectivity impact |
| Modify gateway TLS settings | C | Affects connectivity |
| Change cloudflared config | C | Affects connectivity |
| Restart clawdbot.service | C | Could break connectivity |
| Modify gateway.auth.mode | C | Could lock out access |


---


*This document should be reviewed and updated after any incident involving system changes.*
## Lessons from Proton Email Loss (2026-02-01)


**Incident:** Two Proton Mail accounts deleted due to 12-month inactivity on free tier. X/Twitter account was using one of these as its email.


**Impact:** Could not receive X/Twitter security emails. Required email change to chaplaincen@gmail.com.


**Mitigation:**
- 3 annual cron reminders to log into Proton (Jan 18/25/31, Gemini Flash)
- Calendar event for annual Proton login
- Operational rule: critical accounts should not depend on free-tier services with inactivity policies


## Recovery Hardening (2026-02-01)


**Context:** Audit revealed clawdbot.json (all API keys, agent configs, cron jobs) had no backup. Single point of failure.


**Changes implemented:**
- Encrypted config backup to Drive (daily 2 AM, GPG AES256, 5-version retention)
- Recovery templates in git (`system/` directory)
- Crontab self-backup (daily midnight)
- Raw config in password manager as fallback


**Operational rule:** When adding new API keys, channels, or services to clawdbot.json, the next daily backup will capture it automatically. For critical changes, run `bash scripts/backup-config-encrypted.sh` manually to create an immediate backup.
