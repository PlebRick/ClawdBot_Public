# TODO — Dev & Infrastructure Projects

## 1. 🔒 Security Remediation ✅ COMPLETE (2026-01-27)
**Full plan: `memory/context/security-remediation-plan.md`**
- [x] Phases 1-4 (🔴 HIGH): GitHub token revoked, repo deleted, secrets scrubbed, systemd fixed, gateway password rotated
- [x] Phases 5-6 (🟡 MEDIUM): trustedProxies configured, allowInsecureAuth disabled
- [x] Phases 7-9 (🟡 MEDIUM): sudo cleanup done, fail2ban done, Tor verified (active use)
- [x] Phases 10-12 (🟢 LOW): Cloudflare perms done, Docker verified (active use), bird-auth perms done
- **All 12 phases complete.**

## 2. Google APIs — Complete OAuth Flow
**Google Cloud Project "Clawd" ✅ | OAuth credentials saved ✅ | Test user added ✅**
**Credentials:** `~/.config/clawd/google-oauth.json`

**APIs enabled (all free unless noted):**
- Google Drive API
- Google Calendar API
- Gmail API
- YouTube Data API v3
- Google Chat API
- Google Tasks API
- CalDAV API
- Google Sheets API
- Google Docs API
- Google Keep API
- People API (Contacts)
- Google Slides API
- Apps Script API
- Cloud Speech-to-Text API ⚠️ (paid — use sparingly)

**NOT enabled:** Generative Language API (Gemini) — paid, revisit later

### At laptop:
- [x] Run OAuth browser flow to get access/refresh tokens ✅ (2026-01-27)
- [x] Build token management script (`~/clawd/scripts/google-oauth.py`) ✅ (2026-01-27)
- [x] Test each API: ✅ (2026-01-27)
  - [x] Calendar — 3 upcoming events
  - [x] Tasks — 3 task lists
  - [x] YouTube Data — connected
  - [x] Drive — 3 files visible
  - [x] Gmail — chaplaincen@gmail.com verified
- [x] Integrate Calendar + Tasks into morning brief ✅ (2026-01-29 — via arnoldos.py + morning-brief-data.py)
- [ ] Integrate YouTube Data API into morning brief (Trading Fraternity summaries)
- [x] **ArnoldOS Phase 1 (read-only)** ✅ COMPLETE (2026-01-29)
- [x] **ArnoldOS Phase 2 (supervised writes)** — APPROVED (2026-01-29). Every write requires Rick's confirmation.
- [ ] **ArnoldOS Phase 3 (future):** Evaluate removing confirmation requirement for routine operations once write operations proven reliable

### Gemini (future, optional)
- Enable Generative Language API in the Clawd project (paid — unlocks latest models like gemini-2.5-pro)
- Also try: run `gemini` CLI interactively to see if it can use the existing Clawd project OAuth
- **⚠️ Previous attempt broke things — do NOT modify clawdbot gateway config or env vars during this process**

## 2b. Browser Logins & Extensions — PARTIAL (2026-01-27)
- [x] **Chrome Browser Relay** — connected, 4 tabs attached (Grok, ITC, Logos, GospelTruth)
- [x] **IntoTheCryptoverse** — logged in via Chrome relay
- [x] **TradingView** — logged in via Chrome relay
- [x] **Grok "Mika1" chat** — logged in, share link accessible, but relay snapshot fails (see bug below)
- [ ] **Gmail** — verify access works (may already work via Google login)
- ⚠️ **Browser relay 404 bug** — tabs appear in `tabs` list but `snapshot` returns 404 on some/all tabs. Known since Jan 26. Blocks ITC scraping, Fear & Greed screenshots, Grok chat extraction. **Needs troubleshooting before browser-dependent integrations will be reliable.** Fallback for Grok: save chat as HTML locally.

## 3. Bio Project ✅ COMPLETE (2026-01-29)
- [x] Full Grok "Mika1" chat exported (654KB) → `rick_profile/raw/grok-chat.md`
- [x] 5-segment parallel processing via sub-agents → filtered and assembled
- [x] `memory/context/ricks-bio.md` — 31KB comprehensive bio
- [x] `memory/context/voice-profile.md` — 10-section voice profile
- [x] `memory/context/ricks-voice-profile.md` — extended voice analysis

## 4. X/Twitter Setup ✅ COMPLETE (2026-01-27)
- [x] bird cookies configured for @FaithFreedmBTC (`~/.config/bird/config.json5`, 600 perms)
- [x] Backup cookies at `~/.clawdbot/bird-env` (600 perms)
- [x] Tested: `bird whoami` → @FaithFreedmBTC confirmed
- [x] Tested: read timelines (Elon, Trump, Driscoll, Lyn Alden all working)
- [x] Tested: search working
- [x] Posting available via `bird tweet` — gated by AGENTS.md hard rule (never post without express permission)
- **Monitored accounts:** @elonmusk, @realDonaldTrump, @PastorMark (Driscoll), @LynAldenContact
- **Note:** @markdriscoll doesn't exist — correct handle is @PastorMark

## 5. Clawd Dashboard — Deploy to Vercel
**Repo:** github.com/PlebRick/clawd-dashboard (private) ✅ | MVP built ✅
- [ ] Go to vercel.com/new → Import `PlebRick/clawd-dashboard`
- [ ] Set env vars:
  - `GATEWAY_URL` = `https://ai.btctx.us`
  - `GATEWAY_TOKEN` = (gateway token — find via `clawdbot status` or config)
  - `DASHBOARD_PASSWORD` = (pick a password)
  - `JWT_SECRET` = (any random 32+ char string)
- [ ] Deploy
- [ ] Optional: set custom domain `dash.btctx.us` via Cloudflare CNAME
- [ ] **Upgrade Dashboard** — review current MVP, identify missing features, improve UI/UX. Spec: `memory/context/clawd-dashboard-spec.md`

## 6. Claude Code Re-Auth ✅ (2026-01-27)
- [x] Run `claude /login` to refresh OAuth token (account: chaplaincen@gmail.com)
- [x] Verified: `claude --version` → 2.1.21, responds to prompts
- Clawd can now use Claude Code as a coding sub-agent for building projects

## 7. Morning Brief ✅ COMPLETE (2026-01-27)
**Spec:** `memory/context/morning-brief-spec.md` (merged from original + new integrations)
**Data script:** `~/clawd/scripts/morning-brief-data.py`
**Cron job:** `a49b31c7-8e06-4fec-890e-ab70690ebccf` — 4:30 AM CST daily
**Delivery:** Telegram DM + Web UI (via isolated cron session, post-to-main=full)
**Old spec** (`morning-brief.md`) trashed. Old cron job deleted.
- [x] BTC price + Fear & Greed Index (29 = Fear) → CoinGecko + alternative.me
- [x] TSLA, ES Futures, Gold, DXY → Yahoo Finance
- [x] Homebuilder stocks (XHB, DHI, LEN, KBH) → Yahoo Finance
- [x] 10Y Yield / recession indicators → Yahoo Finance
- [x] Scripture — Revised Common Lectionary daily readings (ESV) → Brave Search
- [x] Google Calendar → today's schedule
- [x] Google Tasks → pending tasks
- [x] Gmail → unread count + flagged subjects
- [x] Brave Search → headlines (crypto, macro, wildcard)
- [x] YouTube → Trading Fraternity, Amit Investing, Into The Cryptoverse
- [x] Weather → wttr.in (Nashville, IL 62263)
- [x] Memory/daily logs → Clawd Notes section
- [x] X/Twitter → Elon, Trump, Driscoll (@PastorMark), Lyn Alden — reading works, wire into brief prompt
- [x] CNN Fear & Greed (traditional) → ✅ web-scout skill (2026-01-30), extracts index + 7 components
- [x] IntoTheCryptoverse paid data → ✅ web-scout skill (2026-01-30), Firebase auth, 118+ charts accessible
- [ ] Southern IL local news → find non-paywalled source

## Git Backup ✅ COMPLETE (2026-01-31)
- [x] Private repo: `github.com/PlebRick/ClawdBot_Backup` — 227 files, zero secrets
- [x] Comprehensive `.gitignore` — excludes logs, tmp, .trash, node_modules, __pycache__, cookies, secrets
- [x] Security audit: full grep for secret patterns across all scripts/skills — all clean (external paths only)
- [x] Gitleaks v8.21.2 pre-commit hook — blocks commits containing secrets
- [x] `RECOVERY.md` — 5-phase disaster recovery runbook with credential map, gateway config template, verification commands
- [x] `scripts/backup-to-github.sh` — updated to correct repo URL
- **Estimated recovery time:** 45-90 min from bare hardware

## 8. Brave Search API Key ✅ (2026-01-27)
- [x] API key added to gateway config (`tools.web.search.apiKey`)
- [x] Verified: `web_search` returns Brave results
- Unlocks: better news gathering, social media searching, morning brief improvements

## 9. Rules to Add
- [x] Add "never execute trades" hard rule to AGENTS.md ✅ (2026-01-27)

## 10. Misc
- [ ] Check 1 AM upgrade log (scheduled Jan 27)

## 11. 🦞 MoltBot Conversion — MONITOR UNTIL READY
**Status: ⏸️ WAITING — npm package is a placeholder (v0.1.0, 283 bytes). DO NOT install.**
**Plan:** `memory/context/moltbot-migration-plan.md`
- The real software is still published as `clawdbot` on npm — that's what we run
- The `moltbot` npm package has no actual code yet — just a name reservation
- **Monitor for readiness:** `npm view moltbot version` → when it shows `2026.x.x`, migration is ready
- Watch: GitHub releases, Discord (discord.gg/clawd), npm page
- When ready: install `moltbot`, run `moltbot doctor`, swap systemd services, update scripts
- **Do NOT run `clawdbot onboard` or modify services until migration is complete** (see AGENTS.md hard rule)

## 🐛 Known Bugs
- **Browser relay snapshot 404** — `browser.snapshot` and `browser.navigate` return `404: tab not found` even when tabs appear in `browser.tabs` list. First seen 2026-01-26. Affects all browser-dependent features (ITC scraping, Fear & Greed screenshots, Grok chat extraction). Needs root-cause investigation — may be extension version, relay server, or tab attachment issue.

---
*Updated: 2026-01-31 (Git backup complete)*

## LOS PRD v2.1 — Phase Tracker

### Phase 0: Grok Harvest ✅ COMPLETE
### Phase 1: Identity Depth ✅ COMPLETE
- [x] Voice profile created (`memory/context/voice-profile.md` + `memory/training/voice-profile.md`)
- [x] USER.md enriched with lean pointers
- [x] ArnoldOS skill built and operational

### Phase 2: Ministry Skills ✅ COMPLETE (2026-01-30)
- [x] `sermon-writer` skill built — voice-card, voice-phrases catalog, length tiers
- [x] `bible-brainstorm` skill built — 5-phase workflow, .docx output, Drive upload
- [x] Voice comparison: ClawdBot vs Claude.ai Sermon Enhancer — merged, banned phrases propagated
- [x] Trigger detection tested — 10/10 pass (sermon-writer)
- [x] Voice authenticity test — Rick rated 3-4/5 on Romans 5:1-11
- [x] End-to-end workflow test — Ephesians 2:1-10 brainstorm through all 5 phases
- [x] Finney research sub-agent spawned and producing (`finney-research` — reusable)
- [x] Autonomous exception: bible-brainstorm .docx → Drive Ministry/Brainstorm
- [x] ArnoldOS `complete-task` command built and tested (first Phase 2 write)

### Phase 3: Remaining Skills — ❌ ABANDONED AS WRITTEN (2026-01-30)
Opus ruling: Phase 3 as originally scoped is obsolete. Components redistributed.

| Original Item | Disposition |
|---|---|
| `morning-brief` skill | **Closed** — already running as cron job. No skill needed. |
| `trading-analysis` skill | **Moved to Future Integrations** — depends on portfolio tracking (Plaid). See `memory/context/future-integrations-roadmap.md`. |
| `chapel-schedule` skill | **Moved to Future Integrations** — needs separate PRD and workflow discovery. See `memory/context/future-integrations-roadmap.md`. |

## Restructure supervisor-project for append-friendliness
**Added:** 2026-02-01
**Priority:** Low — do when files get unwieldy
**What:** Split frequently-updated sections out of `supervisor-project/Clawdbot supervisor current state.md` (35KB+) into separate append-friendly files. Main doc links to them.
**Candidates to extract:**
- "What's Working" table → `supervisor-project/whats-working.md`
- Decisions log / model assignments → `supervisor-project/decisions-log.md`
- Cron job inventory → `supervisor-project/cron-inventory.md`
**Why:** Reduces token burn on doc updates. Currently requires full file read (~19KB) just to insert a few lines.

## ElevenLabs Integration
**Added:** 2026-02-01 (reminder — already on future integrations roadmap)
**Priority:** Medium — Rick wants this set up when time allows
**What:** Connect ElevenLabs API for text-to-speech using Rick's cloned voice
**Rick has:** ElevenLabs account, cloned voice, custom voice
**Integration:** Python SDK, build a skill for sermon/content audio generation
**Use cases:** Audio sermons, devotional recordings, content narration

## Telegram TTS Auto-Reply (Not Working)
**Added:** 2026-02-02
**Priority:** Medium
**Status:** Config set, gateway not processing

**What's configured:**
- `messages.tts.auto: "inbound"` ✅
- `messages.tts.provider: "elevenlabs"` ✅
- `messages.tts.elevenlabs.apiKey` ✅
- `messages.tts.elevenlabs.voiceId: "Jp1DEyuCpm4kaPZ7xjRk"` (Wise Elder Narrator) ✅
- `messages.tts.elevenlabs.modelId: "eleven_multilingual_v2"` ✅
- ElevenLabs API works (tested manually)
- `[[tts:...]]` tags in replies not being processed by gateway

**What's not working:**
- Gateway doesn't convert replies to audio on voice message inbound
- No TTS-related entries in logs even with `diagnostics.flags: ["tts.*"]`
- `/tts on` command doesn't create prefs file

**Next steps:**
- Ask in Clawdbot Discord for help
- Check for gateway version issues
- Deep dive into gateway source if needed

## Ara Voice Setup (Gara)
**Added:** 2026-02-02
**Priority:** Medium
**Blocked by:** TTS auto-reply fix above

**What we want:**
- Ara agent uses "Gara" voice (`NAM0QTodmV1cEDQ2EpSE`) for TTS
- Clawd uses "Wise Elder Narrator" (`Jp1DEyuCpm4kaPZ7xjRk`)
- Per-agent TTS voice override needed

**Current blocker:**
- Schema doesn't support `agents.list[].identity.voiceId`
- May need per-agent TTS config or feature request
