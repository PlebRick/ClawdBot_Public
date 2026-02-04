# ArnoldOS Integration — Project Requirements Document


**Author:** Clawd
**Supervisor Approval:** Pending Rick review
**Date:** 2026-01-29
**Status:** Phase 2 — Supervised Writes ACTIVE (approved 2026-01-29)
**Approved:** 2026-01-29 by Rick (via Opus supervisor review)


---


## 1. Background


### What is ArnoldOS?
ArnoldOS is Rick's personal operating system — a structured life management architecture built on Google Workspace (Calendar, Tasks, Drive). It enforces "Vertical Alignment" across seven life domains:


| Domain | Tag | Calendar | Drive Folder | Notes |
|--------|-----|----------|-------------|-------|
| Ministry | `[MINISTRY]` | Ministry | /Ministry | Pastor/Church |
| Chapel | `[CHAPEL]` | 2026 Chapel Schedule | /Chapel | Prison/State chaplaincy |
| Trading | `[TRADING]` | Trading | /Trading | Bitcoin/Stocks |
| Dev | `[DEV]` | Dev | /Dev | SACRED, BTCTX |
| Family | `[FAMILY]` | Family | /Family | Household, /Family/Finance_Admin for tax/bills |
| Personal | `[PERSONAL]` | Personal | /Personal | Workouts, uncategorized, default |
| Content Creation | `[CONTENT]` | *(none — tasks only)* | /Content Creation | YouTube, videos |


Additional: `[INBOX]` tag for ambiguous tasks. `00_Inbox` folder is the catch-all.


### Why Integrate?
Rick built deep context with Gemini's "ArnoldOS" Gem, but Gemini has limitations:
- No persistent memory across sessions
- No browser automation, cron jobs, or sub-agents
- No access to X/Twitter, Telegram, or local tools
- Can't build a voice profile or write in Rick's style
- Limited to Google ecosystem


Clawd can absorb ArnoldOS as a native capability while extending far beyond it — market data, sermon prep, automated monitoring, and persistent knowledge of who Rick is.


### What Problem This Solves
Rick currently context-switches between Gemini (for Google workspace management) and Clawd (for everything else). Integrating ArnoldOS into Clawd creates a single AI that manages his entire life with full context.


---


## 2. Resource Map


### Google Calendar IDs
| Calendar | ID |
|----------|-----|
| Personal | `chaplaincen@gmail.com` |
| Ministry | `9d3bd07ab2b73e9fd173e830ef38d1f83f2bbebec83bca67e5bcc785e608c78f@group.calendar.google.com` |
| Trading | `f6414f2c7ccd2096ad1d3e011adfe81f9193f4ba5a87e167afa01577673cdee7@group.calendar.google.com` |
| Family | `5b11a8091bd38b9eb0c06b0f47efab2c365d046a4051992b36c21013b5a89e81@group.calendar.google.com` |
| Dev | `87df929a3c6df9a7bac7b9709cd4424c60b7d220e146cad600e76b9bbaf7d889@group.calendar.google.com` |
| 2026 Chapel Schedule | `7aa8b91af856516199da961dab75b4ced0e5264a02e9f8dd106616e482dc748c@group.calendar.google.com` |
| US Holidays | `en.usa#holiday@group.v.calendar.google.com` |


### Google Tasks
| List | ID |
|------|-----|
| 00_Inbox | `MDMzMjg1NzQ3NzM4Mjc0MjQwMzk6MDow` |


### Google Drive — `01_ArnoldOS_Gemini`
| Folder | ID |
|--------|-----|
| Root | `12aczo3TPXamKkKQQc2iunPUqvfoBJovG` |
| 00_Inbox | `1HuRZueJfRzWbUSFj8PwvSesNsNuHGtJE` |
| Ministry | `1paymtPXeI7jICqVhY8Q0XAM2ty8Gk-r9` |
| Chapel | `1EFKyIg9p16SaG8hW6p18BJXeKmY9ju7T` |
| Trading | `1HQlsU2eBO1h7SyKmer9yIqIqpmxu9E8p` |
| Dev | `1BObDiyABWgXY5YAlz5wgppcQtoQ2eK2q` |
| Family | `1HTgm4axfUzLfcbTiGLm11hcstBvUYSWF` |
| Personal | `1wEAjj77hlFTYg-wVWpW3oDKlWe11xUw3` |
| Content Creation | `1hMoewL3YKon5AnYaQBDaXLg52EUWrxVA` |


### API Authentication
- OAuth2 tokens: `~/.config/clawd/google-tokens.json`
- Token management: `~/clawd/scripts/google-oauth.py`
- Scopes: Calendar (R/W), Tasks (R/W), Drive (R/W), Gmail (R/compose/send), YouTube (R)


---


## 3. Phase 1 — Read-Only Integration


### Scope
Read access only. No creating, modifying, or deleting anything.


### Deliverables


**3.1 — ArnoldOS Helper Script (`scripts/arnoldos.py`)**
A Python utility that handles token refresh and provides clean functions:
- `get_todays_events(calendar_id)` — returns events for a specific calendar
- `get_all_todays_events()` — returns events across all 7 calendars, grouped by domain
- `get_tasks(status='needsAction')` — returns all incomplete tasks from 00_Inbox
- `parse_task_tag(title)` — extracts domain tag from task title (brackets, parens, any position)
- `get_tasks_by_domain()` — groups tasks by parsed domain tag
- `detect_conflicts(events)` — finds overlapping events across calendars
- `list_drive_folder(folder_id)` — lists contents of a Drive folder


**3.2 — Morning Brief Enhancement**
Update the existing morning brief cron to include:
- **Calendar section** — All events for the day, grouped by domain, sorted by time
- **Conflict alerts** — Any overlapping events flagged with ⚠️
- **Priority order** — Chapel/Ministry events listed first, then Trading time-sensitive, then rest
- **Task section** — All incomplete tasks from 00_Inbox, grouped by domain tag
- **Drive section** — Recent files in 00_Inbox folder (catch-all items needing filing)


**3.3 — On-Demand Queries**
Clawd can answer questions like:
- "What's on my calendar today/tomorrow/this week?"
- "What tasks do I have for Ministry?"
- "Any conflicts this week?"
- "What's in my Drive inbox?"


### What Phase 1 Does NOT Include
- Creating or modifying calendar events
- Creating or modifying tasks
- Moving or creating Drive files
- Any writes to any Google service
- Changing the morning brief cron schedule
- Replacing or altering the Gemini Gem


### Success Criteria
- Morning brief reliably pulls and displays calendar events from all 7 calendars
- Tasks are correctly parsed and grouped by domain tag
- Conflicts are detected and flagged
- No errors for 2 consecutive weeks
- Rick confirms the output is accurate and useful


---


## 4. Phase 2 — Supervised Writes


### Scope
Write access with mandatory user confirmation for every operation.


### Deliverables


**4.1 — Calendar Writes**
- Create events with proper routing (enforce ArnoldOS calendar rules)
- Modify existing events (time changes, description updates)
- Every write prompts: *"I'll add '[Event]' to your [Domain] calendar at [time]. Confirm?"*
- Sermon prep blocks auto-include reminder: "Paste link to FINAL sermon iteration here."


**4.2 — Task Writes**
- Create tasks in 00_Inbox with proper `[TAG]` prefix
- Search-first protocol: always check for duplicates before creating
- Modify/complete existing tasks
- Every write prompts for confirmation


**4.3 — Drive Writes**
- File to correct subfolder based on domain
- Move items from 00_Inbox to proper folder
- Create documents when requested
- Finance docs → `/Family/Finance_Admin`


**4.4 — Routing Rules (Enforced)**
| Content Type | Routes To |
|-------------|-----------|
| Church/pastor events | Ministry calendar |
| Prison/state/chapel events | 2026 Chapel Schedule |
| Market/trading events | Trading calendar |
| Code/SACRED/BTCTX events | Dev calendar |
| Family/household events | Family calendar |
| Content/YouTube tasks | 00_Inbox with `[CONTENT]` tag |
| Workouts/uncategorized | Personal calendar |
| Ambiguous tasks | 00_Inbox with `[INBOX]` tag |


**4.5 — Conflict Resolution**
- Auto-detect conflicts before creating events
- Chapel/Ministry > Trading by default
- Flag and ask Rick for decision on any conflict


### Success Criteria
- 2 weeks of supervised writes with zero misrouted items
- No accidental modifications or deletions
- Rick confirms routing accuracy
- Conflict detection catches all overlaps


---


## 5. Phase 3 — Authority Decision


### Scope
Evaluate Gemini's role after Phase 2 stability is confirmed.


### Decision Criteria
| Factor | Measure |
|--------|---------|
| Reliability | 4 weeks total (Phase 1 + 2) without errors |
| Completeness | Clawd handles 100% of what the Gem does |
| Extensions | Clawd provides capabilities Gemini cannot |
| Rick's confidence | Rick comfortable with Clawd as primary |


### Options
- **A) Clawd primary, Gemini backup** — Clawd owns ArnoldOS day-to-day, Gemini available as fallback
- **B) Clawd absorbs fully** — Gem retired, Clawd is sole operator
- **C) Parallel** — Both continue (not recommended — split context, duplicate risk)


### Autonomous Writes (Phase 3 only)
After authority decision, evaluate which operations can be autonomous (no confirmation):
- Low-risk: adding tasks with clear domain tags
- Medium-risk: creating calendar events from explicit instructions
- High-risk (always confirm): deleting anything, modifying existing events, sending emails


---


## 6. Constraints — Hard Rules


1. **Phase 1: NO WRITES** — Read-only until Phase 1 success criteria met and Rick approves Phase 2
2. **Phase 2: NO AUTONOMOUS WRITES** — Every write requires explicit user confirmation, EXCEPT for approved autonomous exceptions (see below)
3. **No scope expansion** without supervisor (Opus) approval
4. **No authority changes** (Gemini role) until Phase 3
5. **Existing AGENTS.md rules still apply** — no email sending, no trading execution, no GitHub pushes without permission
6. **Calendar routing must match ArnoldOS rules exactly** — no creative interpretation
7. **Task search-first protocol is mandatory** — never create without checking for duplicates
8. **Finance docs always route to `/Family/Finance_Admin`** — no exceptions
9. **BTCTX is Dev, not Trading** — per ArnoldOS spec
10. **Content Creation uses task tags, not a calendar** — per ArnoldOS spec
11. **Gmail is OUT OF SCOPE** for this integration — Gmail access exists but is not part of ArnoldOS integration until explicitly added in a future phase
12. **Graceful degradation** — If any Google API call fails during morning brief, show what succeeded and note what failed. Never let one API error crash the whole brief.


### Approved Autonomous Exceptions (Phase 2)
These operations are pre-approved by Rick and do NOT require per-instance confirmation:


| Operation | Schedule | Target | Approved By | Date |
|-----------|----------|--------|-------------|------|
| Weekly Market Analysis Report (.docx upload) | Fridays 4:00 AM CST | Drive Trading folder + Telegram | Rick | 2026-01-29 |
| Bible Brainstorm Output (.docx) | End of brainstorm session | Drive Ministry/Brainstorm folder + local backup | Rick | 2026-01-30 |


All other writes still require explicit confirmation. New autonomous exceptions require Rick's approval and must be logged here.
13. **Token expiration** — If re-auth is needed, surface a clear message to Rick rather than failing silently
14. **Progress logging** — Keep a log of morning brief runs during the 2-week proving period at `memory/arnoldos-phase1-log.md`


---


## 7. Implementation Timeline


| Phase | Start | Duration | Gate |
|-------|-------|----------|------|
| Phase 1 | After PRD approval | 2 weeks | Rick confirms reliability |
| Phase 2 | After Phase 1 gate | 2 weeks | Rick confirms accuracy |
| Phase 3 | After Phase 2 gate | Decision point | Rick + Opus decide |


---


*Awaiting Rick's review and approval to begin Phase 1 implementation.*


## Drive Images Folder Structure (Added 2026-02-01)


Root: `01_ArnoldOS_Gemini/Images/` (ID: `1Nd0K0hTbePFKzdNl7n9gAqX-MinZ7Cks`)


| Subfolder | ID | Use |
|-----------|-----|-----|
| Ministry | `14hxz6jPCaxdf9laIN7y6qlLT_wejPhdz` | Sermon illustrations, ministry graphics |
| Chapel | `1KLCtvzJyrNt68sTG5yWkeFEObW6wqTNg` | Chapel-related images |
| Trading | `1xqczPA7Ik0pyj_h9PLU1R5MobbnzHL8v` | Charts, analysis graphics |
| Personal | `1Xo9CH_GItgQsPyyPHMoYt7nvrgoDe803` | Personal images |
| Family | `1h5FsBDKjlQb1YvHTuWkGfBQ5USShp2F7` | Family images |
| Content | `1IKf5nHUm24oSXTnwfCE3UjoPgm7NwlV8` | Content creation images |
| Dev | `1H_hnjblRKxDwoshKKmPOhWelnECbu16H` | Dev/technical images |


Generated via Nano Banana Pro (OpenRouter). Auto-upload to appropriate domain subfolder.
