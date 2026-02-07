# ClawdBot Supervisor — Current State








**Last Updated:** February 6, 2026 (Remote Supervisor Station)
**Supervisor:** Claude (Opus)
**Principal:** Rick (Chaplain)








---








## Quick Orientation








ClawdBot is Rick's self-hosted AI assistant running on a Linux laptop (System76, Ubuntu). It bridges multiple messaging platforms through a WebSocket-based Gateway. Claude (Opus) serves as supervisor for system changes after two self-inflicted outages in January 2026.








**Public URL:** https://ai.btctx.us (via Cloudflare tunnel)
**Gateway Port:** 18789 (HTTPS, self-signed cert)
**Canvas Port:** 18793








---








## Current Phase Status








| Track | Phase | Status | Notes |
|-------|-------|--------|-------|
| **LOS (Life Operating System)** | PRD v2.1 | ✅ Complete | Closed January 30, 2026 |
| **LOS** | Phase 1: Foundation | ✅ Complete | Voice profile, USER.md, arnoldos skill, morning brief |
| **LOS** | Phase 2: Ministry Skills | ✅ Complete | sermon-writer, bible-brainstorm, voice-card.md |
| **LOS** | Phase 3: Remaining Skills | ❌ Closed | Redistributed to Future Integrations Roadmap |
| **LOS** | Phase 4: Optimization | 🔄 Ongoing | Continuous improvement, not a milestone |
| **ArnoldOS** | Phase 2: Supervised Writes | ✅ Active | Calendar, Tasks, Drive — Rick confirms each write |
| **Web Scout** | All Phases | ✅ Complete | CNN F&G, ITC, Logos, Gospel Truth — all operational |
| **Git Backup** | All Phases | ✅ Complete | Private repo, gitleaks, RECOVERY.md |
| **Dashboard Command Center** | Phases 1-7 + 5.5 | ✅ Complete (8 phases) | Full task CRUD + calendar + Today's Focus. Phase 8 (sermon prep) next |
| **Finney Modernization** | All deliverables | ✅ Complete | 12 sermons modernized, 12 summaries, 74 illustrations |
| **API Migration** | Multi-Provider | ✅ Complete | OpenRouter gateway, Opus primary, cc-wrapper, spend alerts |








**Proving Period:** ArnoldOS started Jan 29, tracking reliability through ~Feb 12








---
















## Model Architecture (Multi-Provider)








**Three-provider strategy:** Primary → Backup → Flexible Pool








| Alias | Model | Provider | Cost (in/out /M) | Use |
|-------|-------|----------|-------------------|-----|
| opus | Claude Opus 4.5 | Anthropic (direct) | $5/$25 | Primary — interactive chat, writing, Morning Brief |
| flash | Gemini 2.5 Flash | Google (direct, free) | $0/$0 | Lightweight cron jobs |
| qwen3 | Qwen3 235B A22B | OpenRouter | $0.07/$0.46 | Agentic tasks, cheap cron jobs |
| grok | Grok 4.1 Fast | OpenRouter | $0.20/$0.50 | On-demand only, 2M context |
| grok-think | Grok 4 | OpenRouter | $3/$15 | On-demand only, deep reasoning |
| gemini-pro | Gemini 3 Pro | OpenRouter | $2/$12 | On-demand only, 1M context multimodal |
| nano-banana | Gemini 3 Pro Image | OpenRouter | $2/$12 | On-demand only, image generation |








**Rules:**
- Claude NEVER via OpenRouter — always Anthropic direct
- Grok, Gemini Pro, Nano Banana = on-demand only (Rick's explicit command)
- OpenRouter spend cap set in dashboard
- Models allowlist in `agents.defaults.models` in clawdbot.json — must add new models there + restart gateway








**Config locations:**
- Anthropic API key: `~/.clawdbot/clawdbot.json` → `env.vars.ANTHROPIC_API_KEY` (primary)
- Anthropic auth profile: `~/.clawdbot/agents/main/agent/auth-profiles.json` (mode: token)
- Google OAuth tokens: `~/.config/clawd/google-tokens.json` (ArnoldOS)
- Google API key: `~/.clawdbot/clawdbot.json` → `env.vars.GEMINI_API_KEY`
- OpenRouter API key: `~/.clawdbot/clawdbot.json` → `env.vars.OPENROUTER_API_KEY`
- Models allowlist: `~/.clawdbot/clawdbot.json` → `agents.defaults.models`








**Auth architecture (as of 2026-02-03):**
- Anthropic: API key auth only (OAuth removed)
- Google: OAuth for ArnoldOS (Calendar, Tasks, Drive)
- OpenRouter: API key
- Gemini: API key








## Active Constraints








### Hard Rules (No Exceptions Without Supervisor Review)








1. **Never execute trades** — Analysis only, no buy/sell/transfer
2. **Calendar/Tasks/Drive/Gmail writes require confirmation** — Unless in approved exceptions table
3. **Never modify gateway.auth settings** — Caused 10-hour outage
4. **Category C changes require supervisor review** — TLS, auth, networking, services, anything affecting connectivity
5. **Claude Code CC-C tasks require supervisor + Rick** — Full governance in effect








### Approved Autonomous Exceptions








| Operation | Scope | Schedule | Approved By | Date |
|-----------|-------|----------|-------------|------|
| Weekly Market Report | .docx to Drive Trading folder + Telegram | Fridays 4:00 AM CST | Rick | 2026-01-29 |
| Bible Brainstorm Output | .docx to Drive Ministry/Brainstorm/ + local | On-demand | Rick | 2026-01-30 |
| Sermon Images | .png to Drive Images/Ministry/ | On-demand via nano-banana | Rick | 2026-02-01 |








| Sermon Pipeline Bookkeeping | Task create/update, calendar desc update | During brainstorm/sermon sessions | Rick | 2026-01-31 |
| Liturgy Handout Output | .docx to local outputs/liturgy/ | On-demand | Rick | 2026-02-07 |








*Pattern for future exceptions: Rick authorizes → spec file created → AGENTS.md updated → logged*








---








## What's Working








| System | Status | Notes |
|--------|--------|-------|
| Gateway | ✅ Running | TLS enabled, self-signed cert |
| Cloudflare Tunnel | ✅ Running | ai.btctx.us → localhost:18789 |
| Web UI | ✅ Working | Device pairing functional |
| Telegram | ✅ Working | Primary notification channel |
| Morning Brief Cron | ✅ Running | 4:30 AM CST daily, ArnoldOS data integrated |
| Ara Check-in Cron | ✅ Running | 11 AM + 4 PM CST daily |
| Weekly Market Report | ✅ Running | Fridays 4:00 AM CST |
| arnoldos.py script | ✅ Working | All 7 calendars, tasks, Drive, supervised writes, quick capture |
| arnoldos skill | ✅ Tested | 10/10 detection prompts passed |
| sermon-writer skill | ✅ Tested | 10/10 detection, 3.5/5 voice rating |
| bible-brainstorm skill | ✅ Tested | All 5 phases working, .docx output |
| Claude Code governance | ✅ Active | CC-A/B/C categories enforced |
| **Web Scout skill** | ✅ Complete | CNN F&G, ITC, Logos, Gospel Truth — 4 targets |
| **Git Backup** | ✅ Complete | Private repo, gitleaks pre-commit, RECOVERY.md, Drive sync |
| **liturgy skill** | ✅ Complete | RCL lookup + .docx generator for St. Peter's Stone Church |
| **OpenRouter** | ✅ Live | Multi-model access — Qwen3, Grok, Gemini Pro, Nano Banana |
| **Spend Monitor** | ✅ Running | `openrouter-spend-monitor.py` every 5 min, Telegram alerts |
| **CC Wrapper** | ✅ Active | `cc-wrapper.sh` — 30-min timeout, cost logging, >$5 alerts |
| **X/Twitter (bird)** | ✅ Connected | @FaithFreedmBTC via cookie auth (~/.clawdbot/bird-env) |
| **Proton Keep-Alive Crons** | ✅ Running | 3 annual reminders (Jan 18/25/31) + calendar event |
| **Clawdbot Update Checker** | ✅ Running | Weekly Monday, Gemini Flash |
| **Doc Update Manifest** | ✅ Active | Deterministic doc update routing via `memory/context/doc-update-manifest.md` |
| **Encrypted Config Backup** | ✅ Running | Daily 2 AM, GPG AES256 → Drive `02_ClawdBot/Backups/`, 5-version retention |
| **Crontab Self-Backup** | ✅ Running | Daily midnight → `system/crontab.bak` in git |
| **Recovery Templates** | ✅ In git | `system/` dir: service files, cloudflared config, requirements.txt, redacted config template |
| **Clawdbot Update Check** | ✅ Running | Weekly Monday 10 AM, checks npm + MoltBot migration |
| **Weekend Weather Digest** | ✅ Running | Saturdays 8 AM, OpenRouter/Qwen3 test job |
| **Dashboard (Vercel)** | ✅ Running | https://clawd-dashboard-nine.vercel.app — task CRUD, calendar, Today's Focus |
| Cache: tasks cron | ✅ Running | Every 60s — cache-tasks.sh → memory/cache/tasks.json |
| Cache: calendar today | ✅ Running | Every 60s (staggered +30s) — cache-today.sh → memory/cache/today.json |
| Cache: calendar week | ✅ Running | Every 5 min — cache-week.sh → memory/cache/week.json |
| Google Tasks OAuth (dashboard) | ✅ Working | Separate scoped client, tasks-only, Vercel env vars |
| File Server | ✅ Running | Port 18790, Cloudflare path routing /files/* |
| CNN F\&G in Morning Brief | ✅ Running | Integrated into 4:30 AM cron |
| Sermon Prep Reminder | ✅ Running | Mondays 8 AM, Gemini Flash |
| Public Mirror Auto-Sync | ✅ Running | Every 6 hours → github.com/PlebRick/ClawdBot_Public |
| Dashboard Calendar Write | ✅ Working | OAuth scope expanded, Phase 9 complete |
| **code-server (Remote Supervisor)** | ✅ Running | `https://code.btctx.us` — VS Code + Claude Code via browser, port 18794 |








---








## Key Decisions Log








| Date | Decision | Authorized By |
|------|----------|---------------|
| 2026-01-27 | Safe Change Protocol established | Rick + Claude |
| 2026-01-28 | Supervision model: ClawdBot proposes → Claude reviews → Rick executes | Rick + Claude |
| 2026-01-29 | LOS Phase 1 complete | Claude (verified) |
| 2026-01-29 | ArnoldOS Phase 2 activated (supervised writes) | Claude (approved) |
| 2026-01-29 | Weekly Market Report autonomous exception | Rick |
| 2026-01-29 | USER.md enriched and approved | Rick |
| 2026-01-29 | Claude Code Governance Protocol approved | Claude + Rick |
| 2026-01-29 | Redundancy strategy confirmed (Claude.ai projects remain primary) | Rick |
| 2026-01-30 | LOS Phase 2 complete (sermon-writer, bible-brainstorm) | Claude (verified) |
| 2026-01-30 | Bible Brainstorm Output autonomous exception | Rick |
| 2026-01-30 | LOS Phase 3 closed — redistributed to Future Integrations | Rick + Claude |
| 2026-01-30 | LOS PRD v2.1 marked complete | Rick + Claude |
| 2026-01-30 | Web Scout skill approved (Category B) | Claude |
| 2026-01-30 | Web Scout Phases 1-5 complete | Claude (verified) |
| 2026-01-30 | Gospel Truth (Finney) added to Web Scout | Claude (approved) |
| 2026-01-30 | Supervisor docs ownership model established | Rick + Claude |
| 2026-01-31 | Git backup completed — private repo, security audit, gitleaks, RECOVERY.md | Rick |
| 2026-01-31 | Supervisor-project → Google Drive auto-sync established | Rick |
| 2026-01-31 | Finney project complete — 12 sermons, summaries, 74 illustrations | Rick |
| 2026-01-31 | Dashboard Phases 3-7 + 5.5 complete (CC-B governance throughout) | Rick + Claude |
| 2026-01-31 | Cron-cached memory_get pattern for dashboard data (architectural discovery) | Claude |
| 2026-01-31 | Provider tools vs native tools — exec unavailable via Gateway HTTP invoke | Claude (discovered) |
| 2026-01-31 | Separate tasks-only OAuth client for dashboard writes (blast radius isolation) | Rick + Claude |
| 2026-01-31 | Today's Focus scope: only overdue + due-today tasks, not future/undated | Rick |
| 2026-02-01 | API Migration complete — OpenRouter multi-provider, OAuth kept as backup | Rick + Claude |
| 2026-02-01 | CC Guardrails active — cc-wrapper.sh with 30-min timeout, cost logging | Rick + Claude |
| 2026-02-01 | Spend monitoring cron — every 5 min, Telegram alerts at thresholds | Rick + Claude |
| 2026-02-08 | File server architecture (port 18790, CF path routing) | Rick + Claude |
| 2026-02-08 | Quick capture arnoldos.py command (70+ keywords) | Rick + Claude |
| 2026-02-08 | Dashboard Phase 9 (calendar write) complete | Rick + Claude |
| 2026-02-08 | Public mirror auto-sync every 6 hours | Rick + Claude |
| 2026-02-06 | Remote Supervisor Station deployed — code-server + Cloudflare Access + CLAUDE.md governance | Rick + Claude |








---








## AI Stack Architecture








ClawdBot operates with multiple AI components:








```
ClawdBot (orchestrator on host machine)
├── Claude API (primary LLM brain)
├── Claude Code (autonomous coding agent, spawned via exec)
├── Gemini (backup LLM)
├── Shell access (exec tool, full sudo)
├── Browser relay (Chrome automation) — being replaced by Web Scout
├── Web Scout (Playwright headless browser)
└── All other tools (memory, process, etc.)
```








**Key insight:** Claude Code runs as a separate native process with NO knowledge of ClawdBot's governance (AGENTS.md, SOUL.md, etc.). It has full filesystem access and requires separate governance.








---








## Skill Locations








| Skill | Platform | Location | Status |
|-------|----------|----------|--------|
| `bible-brainstorming` | Claude.ai | Project skill | ✅ Active (supervisor use) |
| `arnoldos` | ClawdBot | `~/clawd/skills/` | ✅ Complete |
| `sermon-writer` | ClawdBot | `~/clawd/skills/` | ✅ Complete |
| `bible-brainstorm` | ClawdBot | `~/clawd/skills/` | ✅ Complete |
| `web-scout` | ClawdBot | `~/clawd/skills/` | ✅ Complete |








**Note:** The `bible-brainstorming` skill visible to the supervisor is a Claude.ai project skill. ClawdBot has its own `bible-brainstorm` skill. Both platforms now have ministry skills as redundant capability.








---








## Web Scout Skill — Details








**Purpose:** General-purpose authenticated headless browser skill replacing unreliable Chrome relay extension.








**Location:** `~/clawd/skills/web-scout/`








**Targets:**








| Target | URL | Auth Method | Capabilities |
|--------|-----|-------------|--------------|
| CNN Fear & Greed | money.cnn.com | None | Index + 7 components |
| IntoTheCryptoverse | app.intothecryptoverse.com | Firebase (IndexedDB injection) | 118+ charts, macro/crypto/tradfi |
| Logos | app.logos.com | Cookie (v11 AES-128-CBC) | 7,500-book library search with citations |
| Gospel Truth | gospeltruth.net | None | 851 Finney sermons, subject/scripture indexes |








**Technical Architecture:**
- Playwright (Node.js) with headless Chromium
- Hybrid auth: cookies for Logos, Firebase tokens for ITC
- Cookie extraction via Chrome v11 AES-128-CBC decryption (GNOME Keyring)
- Rate limiting: 2s minimum between requests, exponential backoff on errors
- Session expiry detection with notification to Rick








**Remaining Integration Work (non-blocking):**
- Integrate CNN F&G into morning brief cron
- Integrate ITC into weekly market report cron
- Register in formal skill registry








---








## Dashboard Command Center








**Repo:** github.com/PlebRick/clawd-dashboard (private)
**Live:** https://clawd-dashboard-nine.vercel.app (Vercel, auto-deploy from main)
**PRD:** memory/context/dashboard-command-center-prd.md
**Governance:** CC-B (plan → code review → push)








### Phase Status








| Phase | What | Status |
|-------|------|--------|
| 1 | arnoldos.py --json output | ✅ |
| 2 | Domain navigation + layout | ✅ |
| 3 | Google Tasks read (cron cache pattern) | ✅ |
| 4 | Task completion (direct Google Tasks API) | ✅ |
| 5 | Task creation (inline, auto-tagging) | ✅ |
| 5.5 | Task editing (inline, title + due date) | ✅ |
| 6 | Calendar read per domain | ✅ |
| 7 | Today's Focus (cross-domain aggregation) | ✅ |
| 8 | Sermon pipeline card | ✅ |
| 9 | Calendar event creation | ✅ |
| 10 | Polish & performance | ⬜ |
| 11 | File browser | ✅ |








### Key Architecture








- **Data flow:** arnoldos.py → cron scripts (every 60s/5min) → memory/cache/*.json → Gateway memory_get → Dashboard SWR hooks
- **Write flow:** Dashboard → Next.js API route → Google Tasks API directly (bypasses Gateway)
- **Why not exec?** Provider tools (exec, read, write) are injected by the LLM provider during agent turns only — not registered for Gateway HTTP invoke. Only native ClawdBot tools (memory, sessions, web, cron) are available via /tools/invoke.
- **OAuth:** Separate tasks-only client (blast radius isolation). Credentials in Vercel env vars, not on host.








### Cron Jobs (3 new)








| Schedule | Script | Output |
|----------|--------|--------|
| `* * * * *` | cache-tasks.sh | memory/cache/tasks.json |
| `* * * * *` | cache-today.sh (staggered +30s) | memory/cache/today.json |
| `*/5 * * * *` | cache-week.sh | memory/cache/week.json |








---








## Redundancy Strategy








Rick maintains parallel systems intentionally:








| Platform | Role | Status |
|----------|------|--------|
| Claude.ai Projects | Primary for ministry work | Stable, Anthropic-hosted |
| ClawdBot/MoltBot | Operations + redundant capability | Active, self-hosted, ministry skills complete |
| Gemini | Backup LLM | Available |








**Principles:**
- Claude.ai projects are NOT being retired
- ClawdBot skills provide redundant capability
- Neither replaces the other until ClawdBot proves long-term stability
- MoltBot is a young open-source project — hedging appropriately








**Benefits:**
- If ClawdBot has issues → Claude.ai projects still work
- If Anthropic has outage → ClawdBot runs with Gemini
- Skills developed for ClawdBot validate methodology








---








## Incident Lessons (Summary)








Two self-inflicted outages occurred January 27-28, 2026. Full details archived; key lessons:








### TLS Incident (Jan 27) — 45 min outage
- **Cause:** Wrong order (gateway TLS before tunnel config) + wrong config file + IPv4-only trustedProxies
- **Lesson:** Client first, server second for protocol changes. Verify which config file services actually use. Include IPv6.








### Auth Incident (Jan 28) — 10 hour outage
- **Cause:** Escalating "fixes" without diagnosis. Set `gateway.auth.mode` to invalid value `"none"`.
- **Lesson:** Diagnosis before intervention. Failed fix = wrong diagnosis → STOP. Login issues are almost never auth config problems (usually device pairing).








### Patterns to Watch For
1. ClawdBot acting before diagnosing
2. Escalating fixes when initial attempt fails
3. Changes to connectivity path without review
4. Editing config files without verifying which file the service uses
5. Claude Code spawned without proper category assignment








### Safe Login Troubleshooting








```bash
clawdbot devices list    # Check for pending pairing requests
clawdbot devices approve <id>  # Approve the request
```








**NOT** by changing gateway.auth configuration.








---








## Architecture Quick Reference








### Services








| Component | Service Name | Config File |
|-----------|--------------|-------------|
| Gateway | `clawdbot.service` | `~/.clawdbot/clawdbot.json` |
| Tunnel | `cloudflared.service` | `/etc/cloudflared/config.yml` |
| code-server | `code-server@ubuntu76` | `~/.config/code-server/config.yaml` |
| Dashboard | Vercel (external) | Vercel env vars + GitHub auto-deploy |








**Warning:** `~/.cloudflared/config.yml` exists but is NOT used by systemd. Always verify with `sudo systemctl cat cloudflared`.








### Traffic Flow
```
Browser → HTTPS → Cloudflare → Tunnel → HTTPS localhost:18789 → Gateway
```








### Key Config Values
```json
"trustedProxies": ["127.0.0.1", "::1"]  // Both IPv4 and IPv6 required
"gateway.auth.mode": "password"          // Only valid values: "token" or "password"
```








### Essential Commands
```bash
# Status
systemctl status clawdbot
sudo systemctl status cloudflared








# Logs
journalctl -u clawdbot -n 50 --no-pager
sudo journalctl -u cloudflared -n 50 --no-pager








# Recovery
sudo systemctl stop clawdbot && pkill -9 -f clawdbot && sudo systemctl start clawdbot








# Device pairing
clawdbot devices list
clawdbot devices approve <REQUEST_ID>








# Test connectivity
curl -k https://localhost:18789
curl -I https://ai.btctx.us
```








---








## Change Review Categories








### System Changes (Safe Change Protocol)








| Category | Risk | Process |
|----------|------|---------|
| **A** | Low | No review needed (reading files, status checks, workspace edits) |
| **B** | Medium | Document before executing (app configs, packages, new skills) |
| **C** | High | **REQUIRES SUPERVISOR REVIEW** |








### Claude Code Invocations (Claude Code Governance)








| Category | Risk | Process |
|----------|------|---------|
| **CC-A** | Low | Task description only, contained workspace |
| **CC-B** | Medium | Task description + code review before deployment |
| **CC-C** | High | Task description + code review + Rick present |








**Flag restrictions:**
- `--full-auto`: CC-A only
- `--yolo`: Never without supervisor + Rick approval








---








## ClawdBot Memory Hierarchy








| Location | Purpose | Auto-Loaded |
|----------|---------|-------------|
| `USER.md` | Rick's identity (lean, 2.7K) | ✅ Every session |
| `SOUL.md` | Agent persona | ✅ Every session |
| `AGENTS.md` | Operating rules, hard constraints | ✅ Every session |
| `MEMORY.md` | Long-term curated knowledge | Searchable |
| `memory/context/` | Depth files (voice profile, theology, bio) | On-demand via search |
| `memory/context/supervisor-docs/` | Supervisor reference docs (ClawdBot-owned) | On-demand |
| `memory/training/` | Training-optimized content | On-demand |
| `skills/` | Custom workspace skills (4 built) | On trigger |








**Total searchable depth:** 155K+ chars behind 2.7K bootstrap








---








## Supervisor Docs Ownership








**Model established January 30, 2026:**








| Location | Owner | Purpose |
|----------|-------|---------|
| `~/clawd/supervisor-project/` | ClawdBot | Living documents, updated in real-time |
| Claude.ai project files | Rick (periodic sync) | Snapshots for session context |








**Sync process:**
1. ClawdBot updates docs as work happens
2. `backup-to-github.sh` pushes to GitHub and auto-syncs changed supervisor-project files to Google Drive (`02_ClawdBot/supervisor-project/`)
3. Before new supervisor chat, Rick copies from Drive to Claude Desktop project
4. Manual sync also available: `bash scripts/sync-supervisor-to-drive.sh`








**Files in supervisor-project/:**
- `Clawdbot supervisor current state.md` — What's true right now
- `Clawdbot technical reference.md` — How ClawdBot works
- `safe-change-protocol.md` — Category A/B/C procedures
- `future-integrations-roadmap.md` — What's planned
- `los-prd-v2.1.md` — Historical reference (closed)
- `workspace-tree.md` — Full file structure








---








## Related Documents








| Document | Purpose | Location |
|----------|---------|----------|
| Safe Change Protocol | Category A/B/C procedures | `supervisor-project/` |
| Technical Reference | Deep architecture | `supervisor-project/` |
| LOS PRD v2.1 | Full roadmap (COMPLETE) | `supervisor-project/` |
| Claude Code Governance | CC-A/B/C procedures | `memory/context/claude-code-governance.md` |
| Future Integrations Roadmap | Planned expansions | `supervisor-project/` |
| RECOVERY.md | Disaster recovery runbook | workspace root |








---








*This document should be updated when major milestones are reached or key decisions are made.*








---








## Key Decisions Log








### 2026-02-03: Gateway Outage (Kimi Registration Incident)








**What happened:**
- Kimi K2.5 was set as default model (replacing Opus) on Feb 2 ~21:25 CST
- Kimi session attempted to register itself in `models.providers.openrouter`
- Omitted required `baseUrl` field
- Gateway crashed on restart, entered loop
- Could not self-recover








**Root cause:** Kimi was operating as primary model without full awareness of Safe Change Protocol constraints. It made a Category C config change autonomously.








**Resolution:**
1. Rick + supervisor manually added `baseUrl` field
2. Default model reset to `anthropic/claude-opus-4.5`
3. New rule added to AGENTS.md: `Gateway Config Protection` explicitly lists `models.providers.*` as Category C








**Lesson:** Non-Opus models should not be set as primary for interactive sessions — they lack the full governance context. Use Opus as brain, cheaper models as subagents.
### 2026-02-03: Anthropic Direct API + OAuth Cleanup








**Changes:**
- Added `ANTHROPIC_API_KEY` env var to clawdbot.json
- Created auth profile with `mode: "token"` (API key, not OAuth)
- Switched primary model to `anthropic/claude-opus-4.5` (direct)
- Removed all Anthropic OAuth configuration
- Google OAuth retained for ArnoldOS








**Benefits:**
- ~20% cost savings vs OpenRouter markup
- Simpler auth architecture
- No more OAuth token refresh complexity for Anthropic








**AGENTS.md hardening (post-Kimi incident):**
- `Gateway Config Protection` rule added
- `models.providers.*` explicitly marked Category C
- Missing/malformed provider fields crash gateway (unrecoverable)
- Non-Opus models should not be primary (lack governance context)