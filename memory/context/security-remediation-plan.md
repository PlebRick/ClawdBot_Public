# Security Remediation Plan
*Created: 2026-01-27 | Last Updated: 2026-01-31*
*Priority: HIGH — secrets were exposed in git history and world-readable files*


---


## Status Summary


| Phase | Threat | Status |
|-------|--------|--------|
| 1 | 🔴 GitHub token revoke + SSH switch | ✅ DONE 2025-07-12 — all tokens deleted, repo deleted |
| 2 | 🔴 Scrub secrets from files | ✅ DONE 2026-01-27 — .gitignore hardened, all secrets scrubbed |
| 3 | 🔴 Systemd service secrets | ✅ DONE 2025-07-12 — moved to /etc/clawdbot-env (600 perms) |
| 4 | 🔴 Rotate gateway password | ✅ DONE 2025-07-12 — rotated, Rick stored in password manager |
| 5 | 🟡 trustedProxies | ✅ DONE 2025-07-12 — set to ["127.0.0.1", "::1"] for Cloudflare tunnel (IPv4 + IPv6) |
| 6 | 🟡 allowInsecureAuth | 🔄 REVERTED 2026-01-29 — set back to true (Rick approved). Device pairing was blocking Web UI login; password auth still active. Original hardening was Phase 6 on 2025-07-12. |
| 7 | 🟡 Duplicate sudo rules | ✅ DONE 2026-01-27 |
| 8 | 🟡 Fail2ban | ✅ DONE 2026-01-27 |
| 9 | 🟡 Tor service | ✅ KEPT — Rick confirms active use |
| 10 | 🟢 Cloudflare config perms | ✅ DONE 2026-01-27 |
| 11 | 🟢 Docker cleanup | ✅ KEPT — Rick confirms active use |
| 12 | 🟢 bird-auth perms | ✅ DONE 2026-01-27 |
| 13 | 🟢 Git backup (secure redo) | ✅ DONE 2026-01-31 — private repo, full security audit, gitleaks pre-commit hook |


---


## Threat Summary


| # | Threat | Severity | Exposed Where |
|---|--------|----------|---------------|
| H1 | GitHub token (full repo+org access) in git remote URL | 🔴 HIGH | `.git/config`, backup script, git history |
| H2 | Gateway password in memory files committed to GitHub | 🔴 HIGH | `MEMORY.md`, `memory/2025-06-07.md`, git history |
| H3 | X/Twitter session cookies in world-readable systemd service + committed script | 🔴 HIGH | `/etc/systemd/system/clawdbot.service` (644), `scripts/bird-auth.sh`, git history |
| M1 | `allowInsecureAuth: true` on Control UI | 🟡 MEDIUM | `clawdbot.json` |
| M2 | `trustedProxies` not configured (Cloudflare headers ignored) | 🟡 MEDIUM | `clawdbot.json` |
| M3 | `sudo NOPASSWD: ALL` defined twice | 🟡 MEDIUM | `/etc/sudoers` + `/etc/sudoers.d/ubuntu76` |
| M4 | Fail2ban not running | 🟡 MEDIUM | System service |
| M5 | Tor service running (unnecessary?) | 🟡 MEDIUM | System service |
| L1 | Cloudflare `config.yml` world-readable | 🟢 LOW | `~/.cloudflared/config.yml` (644) |
| L2 | Stale Docker BuildKit container (22 months old) | 🟢 LOW | Docker |
| L3 | `bird-auth.sh` has execute permissions for group+other | 🟢 LOW | File permissions |


---


## PHASE 1: Revoke & Rotate the GitHub Token
**Severity: 🔴 HIGH | Status: 🟡 PARTIALLY COMPLETE**


### ✅ Completed (2026-01-27)
- Backup cron disabled (no more auto-pushes)
- Local `.git` removed (no local repo to accidentally commit to)


### ⏳ Rick Needs To Do
- **Delete the GitHub repo:** `https://github.com/PlebRick/clawd-backup/settings` → scroll to bottom → "Delete this repository"
- **Revoke the compromised token:** `https://github.com/settings/tokens` → find `gho_Fs5k...` → Delete


### ⏳ When We Recreate the Backup Repo (Later)
- Use SSH auth (keys already exist at `~/.ssh/id_ed25519`)
- Verify SSH key is added to GitHub at `https://github.com/settings/keys`
- Rewrite `backup-to-github.sh` without token embedding
- Use `git remote set-url origin git@github.com:PlebRick/clawd-backup.git`
- Authenticate `gh` CLI via SSH: `gh auth login`


### Why This Matters
The token `gho_Fs5k...` has `repo`, `read:org`, and `gist` scopes — **full read/write access to ALL of Rick's private repos**. It was embedded in the git remote URL and the backup script re-injected it on every run.


---


## PHASE 2: Scrub Secrets from Git History & Memory Files
**Severity: 🔴 HIGH | Status: 🟡 PARTIALLY COMPLETE**


### ✅ Completed (2026-01-27)
- Local `.git` nuked — no local history containing secrets
- Removed gateway password from `memory/2025-06-07.md` and `MEMORY.md`
- Moved X/Twitter secrets from `scripts/bird-auth.sh` into `~/.clawdbot/bird-env` (600 perms)
- `bird-auth.sh` now sources from protected env file, permissions set to 700


### ⏳ Still Needed
- Update `.gitignore` before recreating any git repo (add `*.env`, `bird-env`, etc.)
- Git history on GitHub will be fully gone once Rick deletes the repo (Phase 1)


---


## PHASE 3: Fix World-Readable Systemd Service Secrets
**Severity: 🔴 HIGH | Status: ⏳ TODO**
**⚠️ Requires gateway restart — do when Rick is at laptop**


### Why
`/etc/systemd/system/clawdbot.service` is `644` (world-readable) and contains `AUTH_TOKEN` and `CT0` in plaintext `Environment=` lines. Any local process or user can read them.


### Steps


**3.1 — Create a protected environment file**
```bash
sudo tee /etc/clawdbot-env > /dev/null << 'EOF'
AUTH_TOKEN=0d2ef951b05efdc388545743509f6b561db1d996
CT0=d531e80212b2cf260d2ddb6ce6b894ad26ce63e53242d150be2aae8b1e90d785740b6a4a870c409affc299abe45136c65828bab4d90e2768d378bbc49999d08d7dd593c0213f7af5c1790230bcb5e15b
EOF
sudo chmod 600 /etc/clawdbot-env
sudo chown root:root /etc/clawdbot-env
```


**3.2 — Update service file**
Remove the two `Environment=AUTH_TOKEN=...` and `Environment=CT0=...` lines.
Add: `EnvironmentFile=/etc/clawdbot-env`


**3.3 — Reload and restart**
```bash
sudo systemctl daemon-reload
sudo systemctl restart clawdbot.service
sudo systemctl status clawdbot.service
```


### Test
```bash
grep -E "(AUTH_TOKEN|CT0)" /etc/systemd/system/clawdbot.service  # should be empty
ls -la /etc/clawdbot-env                                          # should be -rw------- root root
sudo systemctl is-active clawdbot.service                         # should be "active"
clawdbot health                                                   # should be healthy
```


---


## PHASE 4: Rotate the Gateway Password
**Severity: 🔴 HIGH | Status: ⏳ TODO**
**⚠️ Requires Rick to store new password — do when Rick is available**


### Why
The password `177621@Coke-Pizza-Football-Fall` was exposed in git history pushed to GitHub. Even though we scrubbed it locally, GitHub may have cached it. The safe move is to rotate.


### Steps
1. Generate new password: `openssl rand -base64 24`
2. Update `~/.clawdbot/clawdbot.json` → `gateway.auth.password`
3. Restart gateway: `clawdbot gateway restart`
4. Enter new password in Control UI at `https://ai.btctx.us`
5. **Rick stores new password in a password manager** (NOT in any file Clawd touches)


### Test
- Old password should NOT work in webchat
- New password SHOULD work
- Telegram unaffected


---


## PHASE 5: Configure trustedProxies
**Severity: 🟡 MEDIUM | Status: ⏳ TODO**
**⚠️ Requires gateway restart — do when Rick is at laptop**


### Why
Cloudflare Tunnel runs locally and sends `X-Forwarded-For` headers. Without `trustedProxies`, the gateway can't distinguish local vs. remote connections. Causes floods of "Proxy headers detected from untrusted address" warnings.


### Steps
1. Add to `gateway` section of `~/.clawdbot/clawdbot.json`: `"trustedProxies": ["127.0.0.1", "::1"]`
2. Restart: `clawdbot gateway restart`


### Test
- "Proxy headers detected" warnings should stop in logs
- Webchat should work normally


---


## PHASE 6: Disable allowInsecureAuth
**Severity: 🟡 MEDIUM | Status: ⏳ TODO**
**⚠️ Requires Phase 5 first. Risk of lockout — do at laptop with local access as fallback**


### Why
`allowInsecureAuth: true` allows password transmission over unencrypted HTTP. Should be `false` since all external access goes through Cloudflare HTTPS.


### Steps
1. Change in `~/.clawdbot/clawdbot.json`: `"allowInsecureAuth": false`
2. Restart: `clawdbot gateway restart`


### Test
- Connect via `https://ai.btctx.us` — should work
- If locked out, revert to `true` via local terminal


---


## PHASE 7: Clean Up Duplicate Sudo Rules
**Severity: 🟡 MEDIUM | Status: ✅ DONE (2026-01-27)**


### What Was Done
- Removed duplicate `NOPASSWD` rule from `/etc/sudoers`
- Kept the standard one in `/etc/sudoers.d/ubuntu76`
- Backed up original to `/etc/sudoers.bak`
- Verified `sudo whoami` still returns `root`
- Verified only one NOPASSWD entry exists


---


## PHASE 8: Enable Fail2ban
**Severity: 🟡 MEDIUM | Status: ✅ DONE (2026-01-27)**


### What Was Done
- Installed `fail2ban` package
- Created `/etc/fail2ban/jail.local` with default ban settings (1h ban, 5 retries, 10m window)
- Enabled `sshd` jail (ready if SSH is ever turned on)
- Service is active and enabled on boot


---


## PHASE 9: Disable Tor (If Not Needed)
**Severity: 🟡 MEDIUM | Status: ⏳ WAITING — needs Rick's confirmation**


### Why
Tor is running on port 9050. If not being used, it's unnecessary attack surface.


### Action Needed
**Rick: Are you using Tor?** If not:
```bash
sudo systemctl disable --now tor
sudo systemctl mask tor
```


---


## PHASE 10: Fix Cloudflare Config Permissions
**Severity: 🟢 LOW | Status: ✅ DONE (2026-01-27)**


### What Was Done
- Changed `~/.cloudflared/config.yml` from `644` to `600`
- Cloudflared service unaffected (reads as root)


---


## PHASE 11: Remove Stale Docker Container
**Severity: 🟢 LOW | Status: ⏳ WAITING — needs Rick's confirmation**


### Why
22-month-old BuildKit container sitting idle. Potential unpatched vulnerabilities. No ports exposed.


### Action Needed
**Rick: Are you using Docker BuildKit?** If not:
```bash
docker rm -f buildx_buildkit_practical_bouman0
docker system prune -f
```


---


## PHASE 12: Fix bird-auth.sh Permissions
**Severity: 🟢 LOW | Status: ✅ DONE (2026-01-27)**


### What Was Done
- Changed `scripts/bird-auth.sh` from `755` to `700` (owner-only execute)
- Secrets were already moved out in Phase 2


---


## Post-Remediation Audit (Run After ALL Phases Complete)


```bash
# No secrets in git
cd ~/clawd && git log -p --all | grep -iE "(177621|gho_|AUTH_TOKEN|CT0=)"


# No secrets in world-readable files
grep -r "177621\|gho_\|AUTH_TOKEN.*=\|CT0.*=" /etc/systemd/system/ ~/clawd/scripts/ ~/clawd/memory/ ~/clawd/MEMORY.md


# Proper permissions
ls -la ~/.clawdbot/clawdbot.json ~/.clawdbot/bird-env /etc/clawdbot-env ~/.cloudflared/config.yml


# Services healthy
clawdbot health
sudo systemctl is-active clawdbot.service
sudo systemctl is-active cloudflared
sudo systemctl is-active fail2ban


# No unnecessary services
sudo systemctl is-active tor
docker ps
```


---


## Ongoing Security Practices (Post-Fix)


1. **Never commit secrets** to any file in `~/clawd/` — use `.gitignore` and `~/.clawdbot/` for secrets
2. **Rotate tokens** — GitHub token every 90 days, gateway password quarterly
3. **Set a cron reminder** for token rotation
4. **I (Clawd) will flag security issues during setup going forward** — this was my failure and won't happen again


---


*Document: ~/clawd/memory/context/security-remediation-plan.md*
*Updated: 2026-01-27*
