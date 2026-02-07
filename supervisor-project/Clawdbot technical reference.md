# ClawdBot Technical Reference








## Complete Architecture & Capabilities Documentation








**Version**: 1.6
**Date**: February 8, 2026
**Author**: Claude (Opus) as ClawdBot Supervisor
**Purpose**: Comprehensive reference for ClawdBot supervision, derived from direct technical education by ClawdBot








---








## Table of Contents
1. [System Overview](#1-system-overview)
2. [Skill System](#2-skill-system)
3. [Memory Architecture](#3-memory-architecture)
4. [Sub-Agent System](#4-sub-agent-system)
5. [Bootstrap Context Injection](#5-bootstrap-context-injection)
6. [Current Skills Inventory](#6-current-skills-inventory)
7. [Web Scout Skill (Headless Browser)](#7-web-scout-skill-headless-browser)
8. [Token Budgets](#8-token-budgets)
9. [Workflow Patterns](#9-workflow-patterns)
10. [Key Commands & Tools](#10-key-commands--tools)
11. [Supervision Protocols](#11-supervision-protocols)
12. [Claude Code Integration](#12-claude-code-integration)
13. [Backup & Sync Infrastructure](#13-backup--sync-infrastructure)








---








## 1. System Overview








### What Is ClawdBot?








ClawdBot (renamed to MoltBot, "the lobster way 🦞") is a **self-hosted personal AI assistant** running on Rick's home infrastructure (Linux laptop as 24/7 server).








**Key Characteristics:**
- **Self-hosted**: Runs on own infrastructure
- **Multi-channel**: Bridges WhatsApp, Telegram, Slack, Discord, Google Chat, Signal, iMessage, Microsoft Teams, Matrix, WebChat
- **Tool-enabled**: Shell commands, file operations, browser automation, memory search
- **Gateway architecture**: Single control plane manages all connections
- **Memory-capable**: Persistent memory via Markdown files with hybrid vector+keyword search








### Infrastructure Components








| Component | Service Name | Config File | Port |
|-----------|--------------|-------------|------|
| Gateway | `clawdbot.service` | `~/.clawdbot/clawdbot.json` | 18789 |
| Canvas Host | — | — | 18793 |
| Cloudflare Tunnel | `cloudflared.service` | `/etc/cloudflared/config.yml` | — |








**Traffic Flow:**
```
Browser → HTTPS → Cloudflare → Tunnel → HTTPS localhost:18789 → Gateway
```








### Execution Capabilities








ClawdBot has full shell access via `exec` tool:
- **User**: `ubuntu76`
- **Host**: `system76-pc`
- **Sudo**: Full NOPASSWD access
- **Scope**: Read/write files, install packages, manage services, run scripts








**Critical Limitation**: ClawdBot cannot safely restart its own gateway — loses connectivity mid-command.








---








## 2. Skill System








### Structure








A skill is a folder containing a required `SKILL.md` file and optional resources:








```
skill-name/
├── SKILL.md          # Required — YAML frontmatter + markdown instructions
├── scripts/          # Optional — executable code (Python, Bash, etc.)
├── references/       # Optional — docs loaded into context on demand
└── assets/           # Optional — templates, images, files used in output
```








### SKILL.md Format








**Two Parts:**








**1. Frontmatter (YAML)** — Always loaded, always in context (~100 words):
```yaml
---
name: weather
description: Get current weather and forecasts (no API key required).
homepage: https://wttr.in/:help
metadata: {"clawdbot":{"emoji":"🌤","requires":{"bins":["curl"]}}}
---
```








Required fields: `name` and `description`








Optional fields:
- `homepage` — Reference URL
- `metadata.clawdbot.emoji` — Display emoji
- `metadata.clawdbot.requires` — Dependencies (bins, packages)
- `metadata.clawdbot.always` — If true, always loaded regardless of detection
- `user-invocable` — Boolean for slash-command availability
- `disable-model-invocation` — Prevent automatic triggering
- `command-dispatch` — Slash-command routing








**2. Body (Markdown)** — Loaded ONLY after skill triggers:
- Instructions, examples, API references, workflow steps
- **Recommended limit: ~500 lines** to avoid context bloat








### Detection Mechanism








**It's LLM judgment on descriptions, not keyword or semantic search.**








Process:
1. At startup, ClawdBot scans skill directories (4 sources, in precedence order):
   - Extra/plugin dirs → Bundled skills → Managed skills (`~/.clawdbot/skills/`) → Workspace skills (`~/clawd/skills/`)
   - Workspace skills override managed, which override bundled
2. Every session, all skill names + descriptions injected into system prompt as XML:
   ```xml
   <available_skills>
     <skill>
       <name>weather</name>
       <description>Get current weather and forecasts (no API key required).</description>
       <location>/path/to/SKILL.md</location>
     </skill>
     ...
   </available_skills>
   ```
3. Before every reply, ClawdBot:
   - Scans all `<description>` entries
   - If exactly one skill clearly applies → reads its SKILL.md with `read` tool
   - If multiple could apply → chooses most specific
   - If none apply → doesn't read any SKILL.md
   - **Never reads more than one skill up front**








**Key Insight**: The `description` field IS the detection rail. A well-written description = precise triggering. Poor description = missed or false triggers.








### Skill Chaining








**Skills cannot call other skills directly.** Chaining happens through:
1. **Sub-agents** (`sessions_spawn`) — Spawn background agent with specific task; it can trigger different skill
2. **Sequential within session** — Finish one skill's work, then detect and load another
3. **Cron jobs** — Scheduled job triggers workflow that loads relevant skill
4. **`always` flag** — Skill with `metadata.clawdbot.always: true` loads regardless of detection








### Skill Locations (Precedence Order)
1. Extra/plugin directories (highest)
2. Bundled skills (with ClawdBot installation)
3. Managed skills: `~/.clawdbot/skills/`
4. Workspace skills: `~/clawd/skills/` (lowest, but overrides others)








### Skill Design Patterns








Lessons from building custom skills:








**1. Phase status as governance checkpoint**
For any skill with write capabilities, put phase status immediately after the header. Every session knows permissions at a glance.








**2. Command table over prose**
Concrete CLI commands not abstract instructions. Zero ambiguity, deterministic execution.








**3. Lean body + depth elsewhere**
Keep SKILL.md under 100 lines. Heavy content (PRDs, scripts, voice profiles) lives in `memory/context/` or `references/`.








**4. Negative triggers prevent false matches**
"When NOT to use" section explicitly lists what other skills handle. Critical when skills could overlap.








**5. Quick reference tables, full data elsewhere**
Domain mapping in arnoldos is 7 lines. Full mapping with IDs lives in `memory/context/arnoldos-integration-prd.md`.








---








## 3. Memory Architecture








### File Hierarchy








**`MEMORY.md`** (workspace root: `~/clawd/MEMORY.md`)
- Long-term memory, main knowledge base
- Manually curated — important decisions, patterns, lessons, key facts
- Persists indefinitely — the "brain" file








**`memory/` directory** (`~/clawd/memory/`)
- **`memory/YYYY-MM-DD.md`** — Daily session logs
- **`memory/context/`** — Structured reference files:
  - `ricks-bio.md` — Personal profile
  - `tools.md` — Setup documentation
  - `identity.md` — Who Clawd is
  - `user.md` — Who Rick is
  - `arnoldos-integration-prd.md` — Domain mapping PRD
  - `supervisor-docs/` — Claude (Opus) supervisor reference docs
  - `todo.md`, `morning-brief-spec.md`, etc.
- **`memory/training/`** — Voice profile and calibration content








**Key Distinction:**
- `MEMORY.md` + everything under `memory/` = **searchable** by memory system
- Bootstrap files (`AGENTS.md`, `SOUL.md`, etc.) = **auto-injected** (different mechanism)








### Memory Search System








**Hybrid vector + keyword search** backed by SQLite.








```
memory_search("query")
│
├─ Vector Search (weight: 0.7)
│  ├─ Query → embedding via Gemini (gemini-embedding-001)
│  ├─ sqlite-vec cosine similarity against chunk embeddings
│  └─ Returns top N candidates with similarity scores
│
├─ Keyword Search (weight: 0.3)
│  ├─ Query → FTS5 full-text search on chunk text
│  ├─ BM25 ranking converted to 0-1 score
│  └─ Returns top N candidates with text scores
│
└─ Hybrid Merge
   ├─ Combines vector + keyword results
   ├─ Weighted: 0.7 × vector_score + 0.3 × text_score
   ├─ Deduplicates by chunk ID
   ├─ Filters by minScore (default: 0.35)
   └─ Returns top 6 results (default maxResults)
```








**Indexing Pipeline:**
1. **File watching**: Chokidar watches `MEMORY.md` and `memory/` for changes
2. **Chunking**: Markdown split into ~400 token chunks with 80-token overlap
3. **Embedding**: Each chunk embedded via Gemini (OpenAI fallback)
4. **Storage**: SQLite at `~/.clawdbot/state/memory/main.sqlite`
5. **Sync triggers**: On file watch (1.5s debounce), on search, on session start, on timer








**Sources Indexed:**
- `memory` source: `MEMORY.md` + `memory/` directory
- `sessions` source (optional): Session transcript `.jsonl` files








**Key Defaults:**








| Parameter | Default |
|-----------|---------|
| Chunk size | 400 tokens |
| Chunk overlap | 80 tokens |
| Max results | 6 |
| Min score | 0.35 |
| Hybrid weights | 0.7 vector / 0.3 keyword |
| Candidate multiplier | 4× (fetches 24 to return 6) |








### Memory Retrieval








**`memory_search`**: Returns snippets with file paths and line numbers
**`memory_get`**: Surgical extraction — reads file with optional `from` line and `lines` count








---








## 4. Sub-Agent System








### What Sub-Agents Are








Sub-agents are **isolated background sessions** spawned for specific tasks. They run independently and report back when complete.








### Context Inheritance








| Inherited | NOT Inherited |
|-----------|---------------|
| `AGENTS.md` + `TOOLS.md` only | `SOUL.md`, `USER.md`, `IDENTITY.md`, `HEARTBEAT.md`, `BOOTSTRAP.md` |
| All tools (exec, browser, memory, web) | Parent's conversation history |
| All skills (same detection system) | In-flight session state |
| Memory search (same index) | Parent's model override (can set own) |
| File system (read/write to `~/clawd/`) | Ability to spawn sub-agents |
| — | Direct user messaging (`message` tool) |
| — | Cron job creation |








**Hardcoded allowlist**: `SUBAGENT_BOOTSTRAP_ALLOWLIST = ["AGENTS.md", "TOOLS.md"]`








**Nesting Restriction**: Sub-agents **cannot spawn other sub-agents**. Code explicitly checks and returns "forbidden".








### Spawning Sub-Agents








```
sessions_spawn(task="...", label="...", model="...", cleanup="keep|delete")
```








Returns: `{status: "accepted", childSessionKey, runId}`








Sub-agent starts immediately in background; main agent continues without waiting.








### Handoff Mechanisms








**A. Automatic Announce (Primary)**
When sub-agent completes/times out:
1. System reads sub-agent's final assistant reply
2. Builds stats line (runtime, tokens, cost)
3. Constructs trigger message for main agent
4. Sends to requester's session
5. Main agent responds naturally








**B. File-Based Handoff (Large Outputs)**
- Sub-agent writes to files in shared workspace
- Main agent reads files when needed
- Avoids context bloat — announce is summary, full data on disk








**C. Session Messaging (`sessions_send`)**
- Main agent can send follow-up messages to running sub-agent
- Useful for multi-step tasks or course corrections








### Lifecycle Management








**Monitoring:**
- `/subagents list` — All sub-agents for current session
- `/subagents info <id>` — Detailed status
- `/subagents log <id>` — Message history








**Control:**
- `/subagents stop <id|all>` — Abort running sub-agent
- `/subagents send <id> <message>` — Send message to sub-agent








**Cleanup:**
- `cleanup="delete"` — Session deleted after announce
- `cleanup="keep"` (default) — Session persists for inspection








---








## 5. Bootstrap Context Injection








### Files Auto-Loaded Every Session








| File | Purpose | Max Size | Sub-Agent? |
|------|---------|----------|------------|
| `AGENTS.md` | Operating rules, personas, hard constraints | 20K chars | ✅ Yes |
| `SOUL.md` | Persona, tone, voice | 20K chars | ❌ No |
| `USER.md` | User profile | 20K chars | ❌ No |
| `IDENTITY.md` | Agent identity | 20K chars | ❌ No |
| `TOOLS.md` | Tool usage guidance | 20K chars | ✅ Yes |
| `HEARTBEAT.md` | Scheduled task definitions | 20K chars | ❌ No |
| `BOOTSTRAP.md` | First-run bootstrap (if exists) | 20K chars | ❌ No |








**Injection**: These appear in system prompt under `## [filename]` headers. ClawdBot doesn't choose to load them — they're baked into every message.








### Truncation








**Default**: 20,000 characters per bootstrap file








If file exceeds 20K:
- 70% from head (first 14K chars)
- 20% from tail (last 4K chars)
- Middle dropped with truncation notice








Configurable via `config.agents.defaults.bootstrapMaxChars`








### Token Budget








All 7 bootstrap files × 20K chars max = up to **140K characters** of auto-injected context. In practice, files are kept small with stubs pointing to `memory/context/` files loaded on demand.








---








## 6. Current Skills Inventory








### Available Skills (52 Bundled + 4 Custom)








ClawdBot comes with 52 bundled skills plus 4 custom workspace skills built for the Life Operating System.








### Custom Workspace Skills ✅








| Skill | Domain | Location | Status |
|-------|--------|----------|--------|
| `arnoldos` | All | `~/clawd/skills/arnoldos/` | ✅ Complete — Phase 2 supervised writes |
| `sermon-writer` | Ministry | `~/clawd/skills/sermon-writer/` | ✅ Complete — 10/10 detection, 3.5/5 voice |
| `bible-brainstorm` | Ministry | `~/clawd/skills/bible-brainstorm/` | ✅ Complete — All 5 phases tested |
| `web-scout` | All | ✅ Complete | CNN F&G, ITC, Logos, Gospel Truth |
| `liturgy` | All | `~/clawd/skills/web-scout/` | ✅ Complete — 4 targets operational |








### Bundled Skills Relevant to Life Operating System








**Tier 1 — Directly Useful:**








| Skill | Purpose |
|-------|---------|
| `skill-creator` | Build new custom skills |
| `weather` | Morning brief component |
| `bird` | X/Twitter integration |
| `summarize` | Content summaries |
| `session-logs` | Search past conversations |
| `github` | Dev domain project management |








**Tier 2 — Available if Needed:**








| Skill | Purpose |
|-------|---------|
| `gog` | Google Workspace CLI (alternative to arnoldos.py) |
| `blogwatcher` | RSS monitoring for news |
| `gemini` | Second-opinion AI queries |
| `coding-agent` | Dev domain automation |








---








## 7. Web Scout Skill (Headless Browser)








### Overview








**Purpose:** General-purpose authenticated headless browser skill replacing the unreliable Chrome relay extension. Allows ClawdBot to browse auth-gated web apps on demand — conversationally or via cron.








**Location:** `~/clawd/skills/web-scout/`








**Category:** B (read-only, no external writes)








### Why Playwright (Not Puppeteer)
- Ships with ClawdBot's Node runtime — no Python dependency
- Native cookie import via `browserContext.addCookies()`
- Headless Chromium included — no external browser dependency
- Better async/await API than Puppeteer
- Built-in screenshot, PDF, network interception








### Targets








| Target | URL | Auth Method | Capabilities |
|--------|-----|-------------|--------------|
| CNN Fear & Greed | money.cnn.com | None | Index + 7 components |
| IntoTheCryptoverse | app.intothecryptoverse.com | Firebase (IndexedDB) | 118+ charts, macro/crypto/tradfi |
| Logos | app.logos.com | Cookie (v11 AES-128-CBC) | 7,500-book library search |
| Gospel Truth | gospeltruth.net | None | 851 Finney sermons |








### Architecture








```
skills/web-scout/
├── SKILL.md              # Skill definition + usage docs
├── lib/
│   ├── session.js        # Playwright session manager
│   ├── cookies.js        # Cookie extraction/import
│   ├── navigate.js       # Navigation helpers
│   └── detect-expiry.js  # Session expiry detection
├── profiles/
│   ├── itc.js            # ITC-specific logic
│   ├── cnn-fg.js         # CNN F&G extraction
│   ├── logos.js          # Logos app navigation
│   └── finney.js         # Gospel Truth navigation
├── scripts/
│   ├── extract-cookies.sh
│   └── refresh-cookies.sh
├── cookies/              # gitignored, chmod 600
│   └── .gitkeep
└── package.json
```








### Authentication Patterns








**Pattern 1: No Auth (CNN Fear & Greed, Gospel Truth)**
- Direct navigation, no cookies needed
- Simplest case








**Pattern 2: Cookie Auth (Logos)**
- Chrome stores cookies encrypted (v11 AES-128-CBC)
- Extraction via GNOME Keyring for decryption key
- PBKDF2 key derivation: `PBKDF2(keyring_secret, 'saltysalt', 1 iteration)`
- IV: 16 bytes of `0x20` (spaces)
- Cookies stored in `cookies/logos-cookies.json` (chmod 600, gitignored)
- Injected via `browserContext.addCookies()` before navigation








**Pattern 3: Firebase Auth (IntoTheCryptoverse)**
- ITC uses Firebase Authentication
- Auth tokens stored in Chrome's IndexedDB, not cookies
- Extraction: Read LevelDB files from Chrome's IndexedDB
- Injection: Use Playwright's `addInitScript()` to inject tokens before page load
- Firebase SDK auto-refreshes access token from refresh token








### Cookie Extraction Details








**Chrome Cookie Encryption (Linux):**
- Location: `~/.config/google-chrome/Default/Cookies` (SQLite)
- Encryption: v11 AES-128-CBC (newer Chrome versions)
- Key source: GNOME Keyring (`secret-tool lookup application chrome`)
- Key derivation: `PBKDF2(keyring_secret, 'saltysalt', 1, 16)` → 16-byte key
- IV: 16 bytes of `0x20` (space character)
- Strip `v11` prefix (3 bytes) before decryption








**Decryption gotchas:**
- Wrong IV corrupts first block only (subsequent blocks decrypt correctly)
- Must use PKCS7 padding
- `v10` vs `v11` use different approaches (v10 may use hardcoded `peanuts` key)








### Session Expiry Handling








**Detection:**
- Check if navigation redirected to login page (pattern match per profile)
- Check for known "session expired" DOM elements
- Check for 401/403 responses








**Flow when expired:**
1. ClawdBot detects session expiry
2. Notifies Rick: "ITC session expired — please log in on Chrome and tell me when done"
3. Rick logs in manually, says "done"
4. ClawdBot runs `refresh-cookies.sh` to re-extract
5. Operation resumes








### Rate Limiting
- Minimum 2 seconds between page loads
- Exponential backoff on errors: 2s → 4s → 8s → max 60s
- Conversational use: natural pacing, but same backoff on errors








### Capabilities by Target








**CNN Fear & Greed:**
- Extract index value (0-100)
- Extract all 7 components with labels
- Output: JSON








**IntoTheCryptoverse:**
- Navigate 118+ chart pages
- Categories: Crypto, Macro, TradFi, Tools, Content
- Macro includes: Recession, Interest Rates, Inflation, GDP, Employment, Debt, CPI/PPI
- Search input available on Charts page
- 20+ shortcut pages pre-mapped








**Logos:**
- Library search (7,500 books)
- Results include AI Synopsis + source citations with page numbers
- Multiple search modes: All, Bible, Books, Factbook, Morph, Media, Maps
- Library catalog filtering by title/author








**Gospel Truth (Finney):**
- Sermon index: 851 sermons/lectures
- Subject index: 8 major theological categories
- Scripture text index: OT/NT by book
- Oberlin Evangelist archive (1839-1862)
- Full text extraction from any sermon page
- 20+ shortcuts for named pages








### Integration with Cron Jobs








Existing cron scripts call Web Scout via:
- Shell exec: `node skills/web-scout/scripts/fetch-cnn-fg.js` → stdout JSON
- Or: ClawdBot invokes internally during report generation








**Pending integration:**
- CNN F&G → morning brief cron
- ITC data → weekly market report cron








---








## 8. Token Budgets








### Per-Session Baseline








| Context | Size | When Loaded |
|---------|------|-------------|
| Bootstrap files (7) | Up to 140K chars | Every session, automatic |
| Skill descriptions (all) | ~100 words each | Every session, automatic |








**Baseline**: ~4K tokens








### On-Demand Additions








| Context | Size | When Loaded |
|---------|------|-------------|
| One skill body | ~500 lines recommended | On trigger only |
| Memory search results | 6 chunks × ~700 chars | On demand |








**With one skill loaded**: ~7-10K tokens
**With memory search**: +2-3K tokens








### Limits








| Item | Limit |
|------|-------|
| Bootstrap file | 20K chars (truncated if larger) |
| Skill description | ~100 words recommended |
| Skill body | ~500 lines recommended |
| Memory search results | 6 chunks default |








---








## 9. Workflow Patterns








### Pattern 1: Sequential Skill Loading








Most common. Main agent loads skills one at a time within a session.








```
User: "Let's brainstorm Romans 8"
→ Detects bible-brainstorm skill → loads → executes








User: "I'm ready to draft the sermon"
→ Detects sermon-writer skill → loads → executes








User: "Schedule prep time"
→ Detects arnoldos skill → loads → creates calendar event
```








### Pattern 2: Sub-Agent for Heavy Lifting








For parallel work or isolated processing.








```
User: "Generate my morning brief"
→ ClawdBot loads morning-brief skill
→ Spawns sub-agents in parallel:
  - Sub-agent 1: Fetch calendar events
  - Sub-agent 2: Fetch priority tasks
  - Sub-agent 3: Get market data (via Web Scout)
→ Each writes results to temp files
→ Main agent assembles briefing
```








### Pattern 3: Scheduled Workflows (Cron)








```
Cron job at 5:30 AM:
→ Trigger morning-brief workflow
→ Call Web Scout for CNN F&G
→ Generate briefing
→ Send to Telegram
```








### Pattern 4: File-Based Handoff








For large outputs that would bloat context:








```
Sub-agent extracts data → writes to file
Main agent reads file when needed
Announce contains summary only
```








### Pattern 5: Conversational Web Browsing








```
User: "Search Logos for N.T. Wright on Romans 8"
→ Web Scout skill triggers
→ Launches Playwright with Logos cookies
→ Navigates to app.logos.com
→ Executes Books search
→ Returns results with citations








User: "What did Finney say about holiness?"
→ Web Scout skill triggers
→ Navigates to gospeltruth.net subject index
→ Finds Holiness category
→ Returns sermon links or extracts full text
```
















### Pattern 6: Doc Update Pipeline








```
Rick says "update docs"
→ Read doc-update-manifest.md
→ Read Session Changelog (tagged entries from daily log)
→ Route tags through mapping table → deduplicated file list
→ Update each file (append > sed > full read — cheapest method)
→ Flag [other] entries for manual review
→ Refresh workspace-tree
→ Git push + Drive sync
```
---








## 10. Key Commands & Tools








### Gateway Management
```bash
# Status
systemctl status clawdbot
journalctl -u clawdbot -n 50 --no-pager








# Control
sudo systemctl start clawdbot
sudo systemctl stop clawdbot
sudo systemctl restart clawdbot








# Kill stuck processes
sudo systemctl stop clawdbot
pkill -9 -f clawdbot
sudo systemctl start clawdbot
```








### Tunnel Management
```bash
# Status
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -n 50 --no-pager








# Verify config file used
sudo systemctl cat cloudflared








# Restart
sudo systemctl restart cloudflared
```








### Device/Pairing
```bash
clawdbot devices list
clawdbot devices approve <REQUEST_ID>
```








### TUI Access (with self-signed cert)
```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 clawdbot tui --url wss://127.0.0.1:18789 --password <PASSWORD>
```








### Memory Tools
- `memory_search(query)` — Hybrid search, returns snippets
- `memory_get(file, from, lines)` — Surgical extraction








### Sub-Agent Tools
- `sessions_spawn(task, label, model, cleanup)` — Spawn background agent
- `sessions_send(sessionKey, message)` — Send message to running agent
- `/subagents list` — List all sub-agents
- `/subagents info <id>` — Detailed status
- `/subagents log <id>` — Message history
- `/subagents stop <id|all>` — Abort








### Skill Tools
- `read` tool — Load SKILL.md body on trigger
- `skill-creator` skill — Scaffold new skills








---








## 11. Supervision Protocols








### Change Categories








| Category | Risk Level | Process |
|----------|------------|---------|
| **A** | Low | No review needed (reading files, status checks) |
| **B** | Medium | Document before executing (app configs, packages, new skills) |
| **C** | High | **REQUIRES SUPERVISOR REVIEW** |








### Category C Changes (Always Require Review)
- Any change to TLS/HTTPS settings
- Any change to authentication/authorization
- Any change to proxy/tunnel configuration
- Any change to systemd services
- Any change affecting ClawdBot's own connectivity
- Service restarts for critical components








### Review Checklist








Before approving Category C changes:








1. **File Paths** — Correct config file? (`/etc/cloudflared/` not `~/.cloudflared/`)
2. **Order of Operations** — Client before server for protocol changes
3. **Network** — IPv4 AND IPv6 considered?
4. **Rollback** — Plan exists and doesn't depend on broken connectivity?
5. **Missing Steps** — Anything that should be added?








### Dangerous Patterns
- Changes to TLS/HTTPS settings
- Changes to authentication
- Changes to proxy/tunnel config
- Any change where ClawdBot modifies its own connectivity path








### Safe Login Issue Resolution








"Can't log in to Web UI" almost always means pending device pairing:
```bash
clawdbot devices list    # Check for pending requests
clawdbot devices approve <id>  # Approve the request
```








**NOT** by changing `gateway.auth` configuration.








---








## 12. Claude Code Integration








### What Is Claude Code?








Claude Code is a standalone CLI coding agent that ClawdBot can spawn for complex development tasks. It runs as a native process on the host machine with full filesystem access.








**Key Distinction from Sub-Agents:**
- Sub-agents (`sessions_spawn`) = isolated ClawdBot sessions with limited bootstrap inheritance
- Claude Code = completely separate process, no ClawdBot context inheritance








### Invocation Mechanism








ClawdBot spawns Claude Code via the `exec` tool with PTY mode:








```bash
exec pty:true workdir:~/project command:"claude 'Your task description'"
```








### Context Inheritance








| Inherited | NOT Inherited |
|-----------|---------------|
| Filesystem access (full) | AGENTS.md hard rules |
| Environment variables | SOUL.md persona |
| Installed tools/CLIs | USER.md identity |
| Network access | ClawdBot governance |
| Sudo privileges | Session history |








**Critical:** Claude Code has no knowledge of ClawdBot's operational constraints.








### Execution Modes (Flags)








| Flag | Behavior | Risk Level |
|------|----------|------------|
| Default (no flag) | Interactive — asks before changes | Low |
| `--full-auto` | Auto-approves within workspace | Medium |
| `--yolo` | No sandbox, no approvals | Extreme |








### Governance Categories








| Category | Risk | Process |
|----------|------|---------|
| **CC-A** | Low | Task description only, contained workspace |
| **CC-B** | Medium | Task description + code review before deployment |
| **CC-C** | High | Task description + code review + Rick present |








**Flag restrictions:**
- `--full-auto`: CC-A only
- `--yolo`: Never without supervisor + Rick approval








### Working Directory Rules








| Directory | Minimum Category | Notes |
|-----------|------------------|-------|
| `/tmp/*` or `mktemp -d` | CC-A | Disposable scratch |
| `~/Projects/*` (non-clawdbot) | CC-A | Isolated project work |
| `~/clawd/scripts/` | CC-B | Helper scripts |
| `~/clawd/skills/` | CC-B | Skill creation |
| `~/clawd/system/` | CC-B | Recovery templates, crontab backup, requirements |
| `~/clawd/memory/` | CC-B | Memory files (not bootstrap) |
| `~/clawd/` (root) | CC-C | Bootstrap files |
| `~/.clawdbot/` | CC-C | Gateway config, secrets |
| `/etc/*` | CC-C | System config |








---








## 13. Backup & Sync Infrastructure








### Git Backup








**Repo:** `github.com/PlebRick/ClawdBot_Backup` (private)
**Branch:** `main`
**Auth:** `gh auth token` at runtime (no hardcoded credentials)








**What's backed up:** All workspace files (227 files as of initial commit)
**What's excluded:** `.gitignore` covers logs, tmp, .trash, node_modules, __pycache__, cookies, secrets, .env files, .clawdbot/, *.sqlite, *.jsonl








**Security:**
- Full security audit performed before initial commit — zero hardcoded secrets in any script
- All scripts read credentials from external paths (`~/.config/clawd/`, `~/.clawdbot/`)
- **Gitleaks v8.21.2** pre-commit hook blocks any commit containing secret patterns
- Hook location: `.git/hooks/pre-commit`








**Backup script:** `scripts/backup-to-github.sh`
```bash
# Manual run:
bash ~/clawd/scripts/backup-to-github.sh








# What it does:
# 1. git add -A
# 2. Skip if no changes
# 3. git commit with timestamp
# 4. git push origin main
# 5. If supervisor-project/ files changed → sync to Google Drive
```








### Disaster Recovery








**`RECOVERY.md`** in workspace root — 5-phase runbook for full rebuild from bare hardware:








| Phase | What | Time |
|-------|------|------|
| 1. System | Node, Python, Clawdbot, tools | ~15 min |
| 2. Clone | Pull repo, gitleaks hook, SSH key | ~5 min |
| 3. Credentials | 10 external secrets (Google, Telegram, Brave, etc.) | ~15 min |
| 4. Gateway Config | clawdbot.json (template with REDACTED), systemd, cloudflared, cron | ~10 min |
| 5. Verify | All integrations smoke test | ~10 min |








**Estimated total:** Under 1 hour with encrypted config backup restored (skips most credential setup).








### Supervisor Project → Google Drive Sync








**Purpose:** Keep supervisor-project docs available on Google Drive for Opus/Claude Desktop sessions.








**Drive location:** `My Drive > 02_ClawdBot > supervisor-project/`
**Drive folder ID:** `1X1DQbFF_2eR_jpS3cyqlI1OcgeD3cglP`








**Scripts:**
- `scripts/sync-supervisor-to-drive.sh` — Shell wrapper
- `scripts/sync-supervisor-drive.py` — Python uploader (uses arnoldos.py for Google auth)








**Behavior:**
- Reads all `.md` files from `~/clawd/supervisor-project/`
- For each file: if a Google Doc with the same name (minus `.md`) exists → update; otherwise → create
- Files are uploaded as plain text and converted to Google Docs by Drive API








**Trigger:** Automatic — `backup-to-github.sh` detects if any `supervisor-project/` files changed in the git commit. If so, runs Drive sync after push. Can also be run manually:
```bash
bash ~/clawd/scripts/sync-supervisor-to-drive.sh
```








**Flow:**
```
Clawd updates supervisor-project/*.md
  → backup-to-github.sh
    → git push to GitHub
    → if supervisor-project/ changed:
      → sync-supervisor-to-drive.sh
        → Google Docs created/updated on Drive
          → Rick syncs to Claude Desktop for Opus sessions
```
















### Encrypted Config Backup (clawdbot.json)








**The single most critical file** — contains all API keys, agent definitions, cron jobs, channel configs, model allowlist, and gateway settings.








**Backup method:** GPG AES256 symmetric encryption → Google Drive
**Script:** `scripts/backup-config-encrypted.sh`
**Schedule:** Daily at 2 AM via crontab
**Destination:** `Drive/02_ClawdBot/Backups/clawdbot-config-YYYY-MM-DD.json.gpg`
**Retention:** Last 5 datestamped versions kept, older auto-trashed
**Passphrase:** Stored at `~/.config/clawd/config-backup-passphrase` (600 perms) + in Rick's password manager
**Fallback:** Raw JSON also stored in Rick's password manager








**Recovery:**
```bash
gpg --decrypt clawdbot-config-2026-02-01.json.gpg > ~/.clawdbot/clawdbot.json
```








### Recovery Templates (system/ directory)








Git-tracked templates for full system reconstruction:








| File | Purpose |
|------|---------|
| `system/clawdbot.service.template` | systemd service for Clawdbot gateway |
| `system/cloudflared.service.template` | systemd service for Cloudflare tunnel |
| `system/cloudflared-config.yml.template` | Tunnel routing config |
| `system/clawdbot.json.template` | Redacted config structure reference |
| `system/requirements.txt` | Python dependencies (key packages) |
| `system/requirements-full.txt` | Full pip freeze |
| `system/crontab.bak` | Live crontab (auto-updated daily at midnight) |
---








## Appendix A: Key File Locations








| Purpose | Path |
|---------|------|
| Gateway config | `~/.clawdbot/clawdbot.json` |
| Cloudflared config (ACTIVE) | `/etc/cloudflared/config.yml` |
| Recovery templates | `~/clawd/system/` |
| Encrypted config backups | `Drive/02_ClawdBot/Backups/*.json.gpg` |
| Backup passphrase | `~/.config/clawd/config-backup-passphrase` |
| Crontab backup | `~/clawd/system/crontab.bak` |
| Cloudflared config (UNUSED) | `~/.cloudflared/config.yml` |
| Cloudflared credentials | `~/.cloudflared/<tunnel-id>.json` |
| Gateway service | `/etc/systemd/system/clawdbot.service` |
| Cloudflared service | `/etc/systemd/system/cloudflared.service` |
| Workspace root | `~/clawd/` |
| Bootstrap files | `~/clawd/AGENTS.md`, `SOUL.md`, etc. |
| Memory files | `~/clawd/MEMORY.md`, `~/clawd/memory/` |
| Supervisor docs | `~/clawd/supervisor-project/` |
| Disaster recovery | `~/clawd/RECOVERY.md` |
| Git backup repo | `github.com/PlebRick/ClawdBot_Backup` (private) |
| Custom skills | `~/clawd/skills/` |
| Web Scout skill | `~/clawd/skills/web-scout/` |
| Managed skills | `~/.clawdbot/skills/` |
| Memory SQLite | `~/.clawdbot/state/memory/main.sqlite` |
| Session transcripts | `~/.clawdbot/agents/<agentId>/sessions/*.jsonl` |
| Claude Code governance | `memory/context/claude-code-governance.md` |
| Supervisor Drive sync | `~/clawd/scripts/sync-supervisor-drive.py` |
| Backup script | `~/clawd/scripts/backup-to-github.sh` |
| Proton reminder | `~/clawd/scripts/proton-reminder.sh` |
| Cache cron data | `~/clawd/scripts/cache-cron.sh` + `cache-cron.py` |
| Cache gateway status | `~/clawd/scripts/cache-gateway-status.sh` + `.py` |
| Cache workspace tree | `~/clawd/scripts/cache-tree.sh` + `.py` |
| Encrypted config backup | `~/clawd/scripts/backup-config-encrypted.sh` |








---








## Appendix B: Configuration Snippets








### Current Gateway trustedProxies
```json
"trustedProxies": [
  "127.0.0.1",
  "::1"
]
```
Both IPv4 and IPv6 required — cloudflared may connect via either.








### Current Cloudflared Config
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








### Valid gateway.auth.mode Values








**Only two valid values:**
- `"token"`
- `"password"`








**There is no `"none"` option.** Auth cannot be disabled by design.








---








*Document Status: Complete*
*This reference captures ClawdBot's architecture. Updated January 31, 2026 — added git backup repo, RECOVERY.md, corrected supervisor-project paths.*








---








## 14. Model Providers & Multi-Model Architecture








### Provider Setup (as of February 2026)








ClawdBot uses three model providers in a tiered architecture:








**Tier 1 — Anthropic (Direct)**
- Primary model: Claude Opus 4.5
- Auth: OAuth + API token in `~/.clawdbot/agents/main/agent/auth-profiles.json`
- Used for: All interactive chat, Morning Brief, Market Analysis, Ara, writing tasks








**Tier 2 — Google (Direct, Free Tier)**
- Model: Gemini 2.5 Flash
- Auth: API key in env vars (`GEMINI_API_KEY`)
- Used for: Lightweight cron jobs (reminders, update checks)
- Note: Free tier has rate limits; Gemini 3 Pro and 2.5 Pro have zero quota on free tier








**Tier 3 — OpenRouter (Multi-Model Gateway)**
- Auth: API key in env vars (`OPENROUTER_API_KEY`)
- Provides access to 100+ models via single API key
- Model refs use format: `openrouter/<provider>/<model>`
- Currently configured models:
  - `openrouter/qwen/qwen3-235b-a22b-2507` (alias: qwen3) — agentic tasks
  - `openrouter/x-ai/grok-4.1-fast` (alias: grok) — 2M context, on-demand
  - `openrouter/x-ai/grok-4` (alias: grok-think) — deep reasoning, on-demand
  - `openrouter/google/gemini-3-pro-preview` (alias: gemini-pro) — multimodal, on-demand
  - `openrouter/google/gemini-3-pro-image-preview` (alias: nano-banana) — image generation, on-demand








### Models Allowlist








Models must be registered in `agents.defaults.models` in `clawdbot.json` or they get "model not allowed" error. After adding a model, restart the gateway.








```json
"models": {
  "anthropic/claude-opus-4-5": {"alias": "opus"},
  "google/gemini-2.5-flash": {"alias": "flash"},
  "openrouter/qwen/qwen3-235b-a22b-2507": {"alias": "qwen3"},
  "openrouter/x-ai/grok-4.1-fast": {"alias": "grok"},
  "openrouter/x-ai/grok-4": {"alias": "grok-think"},
  "openrouter/google/gemini-3-pro-preview": {"alias": "gemini-pro"},
  "openrouter/google/gemini-3-pro-image-preview": {"alias": "nano-banana"}
}
```








### Cron Job Model Assignments








| Job | Model | Why |
|-----|-------|-----|
| Morning Brief | Opus | Writing quality, web search, composition |
| Weekly Market Analysis | Opus | Heavy analysis, .docx generation |
| Ara Spicy Check-in | Opus | Personality, human tone |
| Proton reminders (3x) | Gemini Flash | Simple message delivery |
| Clawdbot Update Check | Gemini Flash | Two shell commands + compare |
| Weekend Weather Digest | Qwen3 235B (OpenRouter) | Test job for OpenRouter pipeline |








### Swapping Models on Cron Jobs








```bash
clawdbot cron edit <job-id> --model openrouter/<provider>/<model>
```








### Key Rules
- **Never route Claude through OpenRouter** — always use Anthropic direct (avoids latency + markup)
- **OpenRouter spend cap** set in OpenRouter dashboard (Rick controls)
- **Grok, Gemini Pro, Nano Banana are on-demand only** — never assigned to automated jobs without Rick's explicit command








### Image Generation (Nano Banana)








Nano Banana (Gemini 3 Pro Image) generates images via OpenRouter API. Response includes `images` array in the message object with base64-encoded PNG data.








```python
# Extract image from response
img = data["choices"][0]["message"]["images"][0]
url = img["image_url"]["url"]  # data:image/png;base64,...
```








### Bird (X/Twitter) Connection








- CLI tool: `bird` (npm: `@steipete/bird`)
- Auth: Cookie-based (AUTH_TOKEN + CT0), NOT email/password
- Credentials: `~/.clawdbot/bird-env` (sourced by `scripts/bird-auth.sh`)
- Account: @FaithFreedmBTC
- Usage: `source ~/.clawdbot/bird-env && bird <command>`








---








## 15. File Server Infrastructure








### Overview








Lightweight Express static file server serving `~/clawd/` for dashboard file browser and external access.








**Port:** 18790
**URL:** `https://ai.btctx.us/files/*` (via Cloudflare path routing)
**Service:** `clawd-files.service` (systemd user service)








### Architecture








```
Browser
  → ai.btctx.us/files/memory/context/foo.md
    → Cloudflare Tunnel (path routing)
      → localhost:18790/memory/context/foo.md
        → Express static server
          → ~/clawd/memory/context/foo.md
```








### Security
- Bearer token auth via `FILE_SERVER_TOKEN` env var
- Scoped to `~/clawd/` only (no arbitrary path access)
- Read-only (no upload/delete endpoints)








### Cloudflare Config (`/etc/cloudflared/config.yml`)
```yaml
ingress:
  - hostname: ai.btctx.us
    path: /files/*
    service: http://localhost:18790
    originRequest:
      httpHostHeader: ai.btctx.us
  - hostname: ai.btctx.us
    service: https://localhost:18789
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```








### Service Management
```bash
systemctl --user status clawd-files
systemctl --user restart clawd-files
journalctl --user -u clawd-files -n 50
```








---








## 16. Quick Capture (arnoldos.py)








### Command
```bash
python3 arnoldos.py quick "<text>" [--domain DOMAIN]
```








### Domain Inference
70+ keywords map to domains automatically:
- **Chapel:** service, liturgy, sermon, preaching, communion, baptism...
- **Ministry:** counseling, hospital visit, funeral, wedding...
- **Trading:** bitcoin, market, chart, analysis, portfolio...
- **Dev:** code, bug, deploy, github, api...
- **Family:** kids, dinner, school, vacation...
- **Personal:** gym, doctor, haircut, meditation...








### Output (--json)
```json
{
  "command": "quick",
  "success": true,
  "inferred_domain": "CHAPEL",
  "matched_keywords": ["sermon", "sunday"],
  "created": {
    "type": "task",
    "title": "[CHAPEL] Prepare sermon for Sunday",
    "id": "abc123"
  }
}
```








### Time Detection
If text contains time patterns (2pm, 14:00, tomorrow 3pm), creates calendar event instead of task.








---








## 17. Public Mirror Sync








### Purpose
Sanitized public copy of workspace for sharing, documentation, and open-source contributions.








### Repos
- **Private:** `github.com/PlebRick/ClawdBot_Backup` (full workspace)
- **Public:** `github.com/PlebRick/ClawdBot_Public` (sanitized mirror)








### Script
`~/clawd/scripts/sync-to-public.sh`








### Schedule
Every 6 hours via crontab (`0 */6 * * *`)








### Sanitization
- Strips API keys, tokens, passwords
- Removes personal identifiers
- Excludes: `cookies/`, `.env`, `*.sqlite`, session logs
- Preserves: scripts, skills, docs, PRDs, specs