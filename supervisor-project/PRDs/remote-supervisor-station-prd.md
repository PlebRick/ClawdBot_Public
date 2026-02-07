# Remote Supervisor Station PRD
## Claude Code on System76 via code-server + Cloudflare Access

**Created:** February 5, 2026  
**Status:** Draft — Pending Rick + Supervisor approval  
**Author:** Claude (Opus) as ClawdBot Supervisor  
**Principal:** Rick (Chaplain)

---

## Executive Summary

Install code-server (VS Code in a browser) on the System76 and expose it through the existing Cloudflare tunnel with Zero Trust authentication. This gives Claude Code direct filesystem access to `~/clawd/` from any browser on any device — enabling real-time diagnosis and repair of ClawdBot without the current relay bottleneck.

**The problem we're solving:** When ClawdBot breaks itself (TLS incident: 45 min, auth incident: 10 hours), the current supervisor model requires Rick to relay error messages, run commands, and report results between Claude and the terminal. This telephone game is the bottleneck.

**The solution:** SSH into the System76, run `claude` in the terminal, and Claude Code reads logs, edits configs, and restarts services directly. No relay. Diagnosis-to-fix drops from hours to minutes.

**Access method:** Browser-based. Open `code.btctx.us` from any device (work Windows, home Mac, phone). No client installs required.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Any Device (Mac, Windows, Phone)                            │
│  Browser → code.btctx.us                                     │
└──────────────┬───────────────────────────────────────────────┘
               │ HTTPS
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Cloudflare Edge                                             │
│  ┌────────────────────────────┐                              │
│  │ Cloudflare Access          │                              │
│  │ • Google OAuth (Rick only) │                              │
│  │ • Session: 24h             │                              │
│  └────────────┬───────────────┘                              │
│               │ Authenticated                                │
│  ┌────────────▼───────────────┐                              │
│  │ Cloudflare Tunnel          │                              │
│  │ • Encrypted transport      │                              │
│  │ • No ports exposed         │                              │
│  └────────────┬───────────────┘                              │
└───────────────┼──────────────────────────────────────────────┘
                │ Outbound connection from System76
                ▼
┌──────────────────────────────────────────────────────────────┐
│  System76 (localhost only)                                   │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ code-server    │  │ ClawdBot       │  │ File Server   │  │
│  │ :18791         │  │ Gateway :18789 │  │ :18790        │  │
│  │                │  │                │  │               │  │
│  │ VS Code in     │  │ AI assistant   │  │ Dashboard     │  │
│  │ browser +      │  │ + all skills   │  │ file access   │  │
│  │ terminal +     │  │                │  │               │  │
│  │ Claude Code    │  │                │  │               │  │
│  └────────────────┘  └────────────────┘  └───────────────┘  │
│                                                              │
│  ~/clawd/ ← shared workspace, full read/write access         │
└──────────────────────────────────────────────────────────────┘
```

**Port allocation:**

| Port | Service | Existing? |
|------|---------|-----------|
| 18789 | ClawdBot Gateway | ✅ Existing |
| 18790 | File Server | ✅ Existing |
| 18791 | code-server | 🆕 New |
| 18793 | Canvas Host | ✅ Existing |

**Subdomain allocation:**

| Subdomain | Routes to | Auth |
|-----------|-----------|------|
| `ai.btctx.us` | Gateway :18789 | ClawdBot password |
| `code.btctx.us` | code-server :18791 | Cloudflare Access (Google OAuth) + code-server password |
| `files.btctx.us` (or path-based) | File Server :18790 | Existing |

---

## Security Model (4 Layers)

### Layer 1: Cloudflare Access (Zero Trust)

- Identity provider: Google OAuth (Rick's Google account)
- Policy: Allow only Rick's email address
- Session duration: 24 hours (re-auth daily)
- MFA: Inherited from Google account (should be enabled)
- Blocks all unauthenticated traffic before it reaches the tunnel

### Layer 2: Cloudflare Tunnel (Transport)

- End-to-end encryption
- No ports open on System76
- `cloudflared` makes outbound-only connections to Cloudflare
- System76 is invisible on the public internet

### Layer 3: code-server (Application)

- Built-in password authentication
- Password stored in `~/.config/code-server/config.yaml`
- Binds to `127.0.0.1:18791` only (localhost)
- Cannot be reached except through the tunnel

### Layer 4: Claude Code (Governance)

- `CLAUDE.md` at `~/clawd/` defines operational boundaries
- `cc-wrapper.sh` enforces 30-minute timeout and cost logging
- Safe Change Protocol applies for all Category C operations
- No autonomous execution — requires human to start session

**What an attacker needs to breach all layers:**
1. Compromise Rick's Google account (past MFA)
2. Know the code-server password
3. Understand ClawdBot's architecture to do anything meaningful

**Comparison to current setup:**

| Surface | Current | After |
|---------|---------|-------|
| ClawdBot Web UI | Cloudflare tunnel + gateway password | Same (unchanged) |
| Dashboard | Cloudflare tunnel + Vercel (public) | Same (unchanged) |
| code-server | N/A | Cloudflare Access + tunnel + code-server password |
| SSH | Not exposed | Not exposed (code-server terminal instead) |

No new ports opened. No SSH exposed. Attack surface addition is minimal — one new localhost service behind the same tunnel with an extra auth layer.

---

## Prerequisites

**Already in place:**

- [x] System76 running Ubuntu 24/7
- [x] `cloudflared` service active and stable
- [x] Cloudflare tunnel routing `ai.btctx.us`
- [x] `btctx.us` domain managed in Cloudflare
- [x] Claude Code CLI installed (`claude`)
- [x] `cc-wrapper.sh` with cost logging and timeout
- [x] Node.js runtime
- [x] Git + GitHub CLI
- [x] Full `~/clawd/` workspace

**Need to verify before starting:**

- [ ] Cloudflare account tier supports Access (free tier includes 50 users — sufficient)
- [ ] Rick's Google account has MFA enabled
- [ ] Available port 18791 not in use: `ss -tlnp | grep 18791`
- [ ] DNS for `btctx.us` allows adding `code` subdomain (CNAME)

---

## Implementation Phases

### Phase 1: Install code-server (Category B)

**What:** Install code-server as a systemd service binding to localhost.

**Risk:** Low. New service, no interaction with existing services, no networking changes.

**Commands for ClawdBot to execute:**

```bash
# Step 1: Install code-server
curl -fsSL https://code-server.dev/install.sh | sh

# Step 2: Verify installation
code-server --version

# Step 3: Configure code-server
mkdir -p ~/.config/code-server
cat > ~/.config/code-server/config.yaml << 'EOF'
bind-addr: 127.0.0.1:18791
auth: password
password: GENERATE_SECURE_PASSWORD_HERE
cert: false
EOF

# Step 4: Set permissions
chmod 600 ~/.config/code-server/config.yaml

# Step 5: Enable and start systemd service
sudo systemctl enable --now code-server@ubuntu76

# Step 6: Verify running
systemctl status code-server@ubuntu76
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18791
# Expected: 302 (redirect to login)
```

**Password generation:**
```bash
# Generate a strong random password
openssl rand -base64 24
# Store in password manager immediately
```

**Rollback:**
```bash
sudo systemctl stop code-server@ubuntu76
sudo systemctl disable code-server@ubuntu76
# code-server remains installed but inactive — no impact
```

**Verification:**
- `systemctl status code-server@ubuntu76` shows active
- `curl http://127.0.0.1:18791` returns response
- No impact on ClawdBot: `systemctl status clawdbot` still active
- No impact on tunnel: `curl -I https://ai.btctx.us` still works

---

### Phase 2: Configure Cloudflare Access (Category B)

**What:** Set up Zero Trust authentication policy for `code.btctx.us` in Cloudflare dashboard.

**Risk:** Low. This is Cloudflare dashboard configuration, not touching the System76 at all. Does not affect existing `ai.btctx.us` routing.

**Who executes:** Rick (Cloudflare dashboard, manual steps)

**Steps:**

#### 2a: Enable Cloudflare Zero Trust (if not already)

1. Go to `dash.cloudflare.com` → Zero Trust (left sidebar)
2. If first time: choose free plan (up to 50 users)
3. Set team name (e.g., `btctx`)

#### 2b: Add Google as Identity Provider

1. Zero Trust → Settings → Authentication → Add new → Google
2. Enter Google OAuth client ID and secret
   - Create at `console.cloud.google.com` → APIs & Services → Credentials → OAuth 2.0 Client
   - Authorized redirect URI: `https://<team-name>.cloudflareaccess.com/cdn-cgi/access/callback`
3. Test the connection

**Alternative (simpler):** Use "One-time PIN" method instead of Google OAuth:
1. Zero Trust → Settings → Authentication → Add new → One-time PIN
2. Cloudflare emails a code to your verified email each login
3. No Google OAuth client setup needed
4. Slightly less convenient but zero external dependencies

#### 2c: Create Access Application

1. Zero Trust → Access → Applications → Add an application
2. Type: **Self-hosted**
3. Application name: `Code Server`
4. Session duration: `24 hours`
5. Application domain: `code.btctx.us`
6. Add policy:
   - Policy name: `Rick Only`
   - Action: **Allow**
   - Include rule: Emails — `rickarnold777@gmail.com` (or whichever email)
7. Save

**Verification:**
- Navigate to `code.btctx.us` in browser
- Should see Cloudflare Access login page (not code-server, not 404)
- After authenticating, should see... nothing yet (tunnel route not added — that's Phase 3)

**Rollback:**
- Delete the Access application from Cloudflare dashboard
- No System76 changes to revert

---

### Phase 3: Add Tunnel Route (Category C — REQUIRES SUPERVISOR REVIEW)

**What:** Add `code.btctx.us` route to the Cloudflare tunnel config, routing to code-server on port 18791.

**Risk:** HIGH. Modifies `/etc/cloudflared/config.yml` which controls ALL tunnel routing. A mistake here could break `ai.btctx.us` (ClawdBot web UI) access.

**File:** `/etc/cloudflared/config.yml`

**Current value:**
```yaml
tunnel: clawd
credentials-file: /home/ubuntu76/.cloudflared/ebafbb8f-dc1f-44df-95ca-5bd1583715a6.json

ingress:
  - hostname: ai.btctx.us
    service: https://localhost:18789
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```

**New value:**
```yaml
tunnel: clawd
credentials-file: /home/ubuntu76/.cloudflared/ebafbb8f-dc1f-44df-95ca-5bd1583715a6.json

ingress:
  - hostname: ai.btctx.us
    service: https://localhost:18789
    originRequest:
      noTLSVerify: true
  - hostname: code.btctx.us
    service: http://localhost:18791
    originRequest:
      noTLSVerify: false
  - service: http_status:404
```

**Key details:**
- code-server uses HTTP (not HTTPS) — `cert: false` in config
- New route goes BEFORE the catch-all `http_status:404`
- Existing `ai.btctx.us` route is unchanged
- `noTLSVerify: false` is correct because code-server doesn't use TLS

**DNS requirement:**
- Add CNAME record: `code.btctx.us` → `<tunnel-id>.cfargotunnel.com`
- OR if using Cloudflare-managed tunnel, this may auto-create

**Command sequence:**

```bash
# Step 1: Backup current config
sudo cp /etc/cloudflared/config.yml /etc/cloudflared/config.yml.backup-$(date +%Y%m%d)

# Step 2: Verify current config works
curl -I https://ai.btctx.us
# Expected: 200 or 301

# Step 3: Edit config (add new route)
# [Use exact content above — supervisor should verify before execution]

# Step 4: Validate config syntax
sudo cloudflared tunnel ingress validate --config /etc/cloudflared/config.yml
# Expected: "OK"

# Step 5: Restart cloudflared
sudo systemctl restart cloudflared

# Step 6: Verify existing route still works
curl -I https://ai.btctx.us
# Expected: 200 or 301 (same as Step 2)

# Step 7: Verify new route works
curl -I https://code.btctx.us
# Expected: 302 or 200 (Cloudflare Access page or code-server)
```

**Rollback procedure:**
```bash
# If ai.btctx.us breaks after restart:
sudo cp /etc/cloudflared/config.yml.backup-YYYYMMDD /etc/cloudflared/config.yml
sudo systemctl restart cloudflared
# Verify: curl -I https://ai.btctx.us
```

**What could break:**
- If the new ingress entry has a YAML syntax error → all routes fail
- If the catch-all is not last → new route may not match
- If DNS CNAME not set → Cloudflare can't route to tunnel

**Does this affect ClawdBot's connectivity?** Only if the config edit introduces a syntax error that breaks the entire tunnel. The backup-and-validate approach mitigates this.

**Pre-change checklist:**
- [ ] Verified correct config file: `sudo systemctl cat cloudflared` shows `/etc/cloudflared/config.yml`
- [ ] Current state documented (backup created)
- [ ] Rollback procedure ready and doesn't depend on tunnel
- [ ] Config validated before restart
- [ ] Human available to intervene
- [ ] Submitted for supervisor review ← **THIS DOCUMENT SERVES AS THE PROPOSAL**

---

### Phase 4: DNS Configuration (Category B)

**What:** Add CNAME record for `code.btctx.us` pointing to the tunnel.

**Who executes:** Rick (Cloudflare DNS dashboard)

**Steps:**

1. Go to `dash.cloudflare.com` → `btctx.us` → DNS → Records
2. Add record:
   - Type: `CNAME`
   - Name: `code`
   - Target: `<tunnel-id>.cfargotunnel.com` (same as `ai` subdomain)
   - Proxy status: **Proxied** (orange cloud — required for Access to work)
3. Save

**Note:** If the tunnel is managed via Cloudflare dashboard (not just CLI), adding the hostname in the tunnel config may auto-create the DNS record. Check before manually adding.

**Verification:**
- `dig code.btctx.us` resolves
- `curl -I https://code.btctx.us` returns Cloudflare Access page

---

### Phase 5: Create CLAUDE.md Governance (Category B)

**What:** Create `~/clawd/CLAUDE.md` — the governance file Claude Code reads automatically when started in a directory.

**Risk:** Low. New file, additive. Does not affect ClawdBot behavior.

**File:** `~/clawd/CLAUDE.md`

```markdown
# Claude Code Governance — ClawdBot Supervisor Station

## Identity
You are operating as a supervisor/maintenance agent for ClawdBot,
a self-hosted AI assistant running on this machine. Your role is
diagnosis, repair, and maintenance — not autonomous operation.

## Read First
Before any action, read these files for current system state:
- `supervisor-project/Clawdbot supervisor current state.md`
- `supervisor-project/safe-change-protocol.md`
- `RECOVERY.md` (if doing disaster recovery)

## Hard Rules

### NEVER (no exceptions)
- Modify `~/.clawdbot/clawdbot.json` without explicit human approval
- Change gateway.auth settings (caused 10-hour outage)
- Delete or overwrite bootstrap files (AGENTS.md, SOUL.md, USER.md, etc.)
- Execute trades or financial transactions
- Publish content to external platforms
- Access, read, or modify files in `~/.clawdbot/` without explicit request
- Run with `--yolo` flag

### ALWAYS
- Follow Safe Change Protocol categories (A/B/C)
- Create backups before modifying any config file
- Verify ClawdBot is still running after any system change
- Log actions to `memory/context/supervisor-audit-log.md`
- Ask before any Category C change — do not auto-approve

## Category Quick Reference

### Category A (Just Do It)
- Read logs: `journalctl -u clawdbot`, `journalctl -u cloudflared`
- Check status: `systemctl status clawdbot`, `systemctl status cloudflared`
- Read any file in `~/clawd/`
- Search memory files
- Run diagnostic commands

### Category B (Document, Then Do)
- Edit files in `~/clawd/memory/`, `~/clawd/scripts/`, `~/clawd/skills/`
- Install packages
- Create new files
- Update documentation
- Run `backup-to-github.sh`

### Category C (STOP — Requires Human Approval)
- Any change to `/etc/cloudflared/config.yml`
- Any change to `~/.clawdbot/clawdbot.json`
- Any `sudo systemctl restart` for clawdbot or cloudflared
- Any change to systemd service files
- Any change affecting network/tunnel/auth

For Category C: state what you want to do, why, the exact commands,
and the rollback procedure. Wait for explicit "approved" or "go ahead."

## Common Repair Scenarios

### ClawdBot Unresponsive
```bash
# Diagnose
systemctl status clawdbot
journalctl -u clawdbot -n 100 --no-pager

# If service crashed (Category C — ask first)
sudo systemctl restart clawdbot

# If stuck
sudo systemctl stop clawdbot
pkill -9 -f clawdbot
sudo systemctl start clawdbot

# Verify
systemctl status clawdbot
curl -k https://localhost:18789
```

### Tunnel Down
```bash
# Diagnose
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -n 100 --no-pager

# Check config
sudo cat /etc/cloudflared/config.yml

# Restart (Category C — ask first)
sudo systemctl restart cloudflared

# Verify
curl -I https://ai.btctx.us
```

### Login Issues
```bash
# Almost ALWAYS device pairing, NOT auth config
clawdbot devices list
clawdbot devices approve <REQUEST_ID>
# NEVER modify gateway.auth settings
```

### After Any Fix
```bash
# Always verify full stack
systemctl status clawdbot
systemctl status cloudflared
curl -k https://localhost:18789
curl -I https://ai.btctx.us
```

## Audit Tasks (If Asked)

- Compare crontab against HEARTBEAT.md for drift
- Check disk space: `df -h`
- Check memory: `free -h`
- Review recent logs for errors
- Verify backup scripts ran: `ls -la ~/clawd/system/crontab.bak`
- Check Drive sync status: `cat ~/clawd/logs/memory-sync.log | tail -20`

## File Locations
- Gateway config: `~/.clawdbot/clawdbot.json`
- Tunnel config: `/etc/cloudflared/config.yml`
- Workspace: `~/clawd/`
- Recovery runbook: `~/clawd/RECOVERY.md`
- Safe Change Protocol: `~/clawd/supervisor-project/safe-change-protocol.md`

## Cost Awareness
- You run on Anthropic API tokens. Be efficient.
- Don't read entire large files when `head` or `tail` suffices.
- Don't search broadly when you know the file path.
- Prefer `grep` over reading full files for specific information.
```

**Rollback:** Delete the file. Claude Code without `CLAUDE.md` simply has no governance guidance — it defaults to interactive mode where it asks before changes.

---

### Phase 6: Install VS Code Extensions (Category B)

**What:** Pre-install useful extensions in code-server for the supervisor workflow.

**Commands:**
```bash
# Install extensions via CLI
code-server --install-extension ms-python.python
code-server --install-extension esbenp.prettier-vscode
code-server --install-extension redhat.vscode-yaml

# Restart code-server to pick up extensions
sudo systemctl restart code-server@ubuntu76
```

**Note:** Claude Code extension is NOT available for code-server (it's VS Code marketplace only). Claude Code runs in the terminal instead — `claude` CLI. This is fine; the terminal is where the real work happens anyway.

---

### Phase 7: Set Default Workspace (Category A)

**What:** Configure code-server to open `~/clawd/` by default.

**Edit** `~/.config/code-server/config.yaml`:
```yaml
bind-addr: 127.0.0.1:18791
auth: password
password: <password>
cert: false
app-name: ClawdBot Supervisor
```

**Then create workspace file** `~/clawd/clawd.code-workspace`:
```json
{
  "folders": [
    { "path": "." }
  ],
  "settings": {
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.cwd": "/home/ubuntu76/clawd",
    "files.autoSave": "afterDelay",
    "files.exclude": {
      "**/.git": true,
      "**/node_modules": true,
      "**/__pycache__": true
    }
  }
}
```

**Bookmark URL:** `https://code.btctx.us/?folder=/home/ubuntu76/clawd`

---

### Phase 8: Verification & Smoke Test

**Full stack verification after all phases complete:**

```bash
# 1. Existing services unaffected
systemctl status clawdbot          # Active
systemctl status cloudflared        # Active
curl -I https://ai.btctx.us        # 200/301

# 2. New service running
systemctl status code-server@ubuntu76   # Active
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18791  # 302

# 3. Tunnel routing both services
curl -I https://code.btctx.us      # Cloudflare Access page

# 4. No port exposure
ss -tlnp | grep -E '18789|18790|18791'
# All should show 127.0.0.1 only
```

**Browser smoke test (Rick executes):**

1. Open `https://code.btctx.us` in browser
2. Cloudflare Access login appears → authenticate with Google
3. code-server password prompt appears → enter password
4. VS Code loads in browser with `~/clawd/` file tree
5. Open terminal (Ctrl+`)
6. Run: `claude "What is the current status of ClawdBot? Check systemctl and report."`
7. Claude Code should read service status and report back
8. Verify: `systemctl status clawdbot` still active after Claude Code session

**Cross-device test:**
- [ ] Works from Mac (home)
- [ ] Works from Windows (work)
- [ ] Works from phone browser (optional)

---

## Execution Plan

**ClawdBot executes Phases 1, 5, 6, 7** (all Category B — shell commands)

**Rick executes Phases 2, 4** (Cloudflare dashboard — manual)

**Phase 3 requires supervisor review** (Category C — tunnel config change)

**Suggested command sequence for ClawdBot:**

```
Step 1: "Execute Phase 1 of the remote supervisor station PRD — install code-server"
Step 2: "Execute Phase 5 — create CLAUDE.md governance file"
Step 3: "Execute Phase 6 — install VS Code extensions"  
Step 4: "Execute Phase 7 — configure default workspace"
```

Rick handles Phases 2 and 4 in the Cloudflare dashboard between Steps 1 and the tunnel config.

Phase 3 (tunnel config) should be executed last, after everything else is verified working locally.

---

## Post-Setup: Automated Audit Jobs (Optional, Category B)

Once the station is operational, consider adding these lightweight cron jobs:

### Daily System Health Check
```bash
# Runs Claude Code for a quick audit, writes to cache file
# Schedule: Daily 6:00 AM CST
bash ~/clawd/scripts/cc-wrapper.sh "Run a quick system health check: verify clawdbot and cloudflared services are active, check disk space, check if any cron jobs failed in the last 24 hours. Write a brief JSON report to ~/clawd/memory/cache/supervisor-health.json with keys: timestamp, services_ok, disk_free_gb, cron_failures. Be concise."
```

### Weekly Doc Freshness Audit
```bash
# Checks if supervisor docs match reality
# Schedule: Mondays 7:00 AM CST
bash ~/clawd/scripts/cc-wrapper.sh "Compare supervisor-project/Clawdbot supervisor current state.md against actual system state. Check: are all services listed still running? Are all cron jobs listed still active? Are any new cron jobs missing from docs? Write findings to memory/context/supervisor-audit-log.md (append, with date header)."
```

**These are suggestions for after the station is proven stable.** Not part of initial setup.

---

## Rollback Plan (Full Uninstall)

If the entire setup needs to be reversed:

```bash
# 1. Remove tunnel route (Category C)
sudo cp /etc/cloudflared/config.yml.backup-YYYYMMDD /etc/cloudflared/config.yml
sudo systemctl restart cloudflared

# 2. Stop and disable code-server
sudo systemctl stop code-server@ubuntu76
sudo systemctl disable code-server@ubuntu76

# 3. Remove Cloudflare Access application (dashboard)
# Zero Trust → Access → Applications → Delete "Code Server"

# 4. Remove DNS record (dashboard)  
# DNS → Records → Delete CNAME for "code"

# 5. Optionally remove code-server package
sudo apt remove code-server  # or equivalent

# 6. CLAUDE.md can stay or be removed — no impact either way

# 7. Verify everything back to original
systemctl status clawdbot
curl -I https://ai.btctx.us
```

---

## Cost Impact

| Item | One-time | Ongoing |
|------|----------|---------|
| code-server | Free (open source) | 0 |
| Cloudflare Access | Free (up to 50 users) | 0 |
| Cloudflare Tunnel | Already running | 0 |
| System76 resources | ~100MB RAM for code-server | Minimal |
| Claude Code usage | Per-session API cost | $2-5/session (controlled by cc-wrapper) |

**Total additional monthly cost:** $0 infrastructure + variable Claude Code usage (only when actively supervising).

---

## Success Criteria

**Phase 1 complete when:**
- [ ] code-server running on localhost:18791
- [ ] No impact on existing services

**Phase 2 complete when:**
- [ ] Cloudflare Access configured with Google OAuth or One-time PIN
- [ ] Access policy restricts to Rick's email only

**Phase 3 complete when:**
- [ ] `code.btctx.us` routes to code-server through tunnel
- [ ] `ai.btctx.us` still works (regression test)

**Full setup complete when:**
- [ ] Can open `code.btctx.us` from any browser
- [ ] Authenticate through Cloudflare Access
- [ ] See VS Code with `~/clawd/` workspace
- [ ] Run `claude` in terminal
- [ ] Claude Code can diagnose ClawdBot status
- [ ] ClawdBot unaffected by entire setup

**Supervisor capability proven when:**
- [ ] Can diagnose a simulated issue via Claude Code
- [ ] Can restart ClawdBot service via Claude Code (with approval)
- [ ] Response time from "something's broken" to "diagnosed" < 5 minutes

---

## Open Questions

1. **Google OAuth vs One-time PIN for Cloudflare Access?** One-time PIN is simpler (no Google OAuth client setup) but slightly less convenient (email code each login). Recommendation: Start with One-time PIN, upgrade to Google OAuth later if the daily code entry gets annoying.

2. **code-server vs Cloudflare browser-rendered SSH?** Cloudflare Access can also expose SSH sessions through the browser. This would be lighter weight (no code-server install) but loses the VS Code file browser and editor. Could add as an alternative access path later.

3. **Should automated audit cron jobs run from the start?** Recommendation: No. Prove the manual workflow first. Add automation after 2 weeks of stable operation.

4. **Password storage for code-server.** Should go in Rick's password manager alongside the GPG passphrase and other credentials. Add to RECOVERY.md credential inventory.

5. **Session timeout for code-server.** Default is no timeout. Consider adding `--idle-timeout 3600` (1 hour) to reduce resource usage when forgotten.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `safe-change-protocol.md` | Category A/B/C procedures — Phase 3 follows this |
| `Clawdbot technical reference.md` | Full architecture reference |
| `Clawdbot supervisor current state.md` | Current system state |
| `gateway-architecture-learnings.md` | Provider vs native tools, cron-cache pattern |
| `RECOVERY.md` | Disaster recovery — add code-server to credential inventory |
| `memory/context/claude-code-governance.md` | Existing CC governance — CLAUDE.md extends this |

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-05 | 1.0 | Initial PRD — code-server + Cloudflare Access + CLAUDE.md |

---

*This PRD is pending approval. No implementation should begin until Rick reviews and approves. Phase 3 (tunnel config) additionally requires formal supervisor review per Safe Change Protocol.*
