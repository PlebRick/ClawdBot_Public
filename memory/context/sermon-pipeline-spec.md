# Sermon Pipeline System — Approved Spec
*Created: 2026-01-31 | Status: APPROVED — Ready to implement*
*Approved by: Rick + Supervisor (Opus) + ClawdBot*


## Calendar Convention


| Field | Format | Example |
|-------|--------|---------|
| Title | Normal event title | `Sunday Afternoon Service` or `St. Peter's Stone Church` |
| Description | `PREACHING: [passage or TBD]` | `PREACHING: Romans 8:1-11` or `PREACHING: TBD` |


**Calendars to scan:** Chapel + Ministry
**Detection:** Events with description starting with `PREACHING:`


### Calendar Description Overwrite Rules
Only overwrite if current description is:
- Empty
- `PREACHING: TBD`
- Already starts with `PREACHING:`


If description contains other content not matching these patterns, confirm with Rick before overwriting.


## Drive File Naming


```
Ministry/Brainstorm/YYYY-MM-DD-short-passage-ref.docx
Ministry/Sermons/YYYY-MM-DD-short-passage-ref-draft.docx
Ministry/Sermons/YYYY-MM-DD-short-passage-ref-final.docx
```


Examples:
- `2026-02-15-romans-8.docx`
- `2026-02-15-romans-8-draft.docx`
- `2026-02-15-romans-8-final.docx`


## Task Format


```
[MINISTRY] Sermon prep: Feb 15 — Romans 8:1-11
```


Notes field contains:
- Venue (from calendar event title)
- Link to brainstorm doc (once created)
- Link to draft doc (once created)


## Autonomous Exception (Rick Approved)


> **Sermon Pipeline Bookkeeping:** During active brainstorm or sermon-writer sessions, ClawdBot may autonomously create/update Ministry tasks and update calendar event descriptions related to the sermon being prepared.


## Implementation Order


| Step | Change | Category | Status |
|------|--------|----------|--------|
| 1 | `arnoldos.py: preaching-schedule` command | A | ✅ |
| 2 | `arnoldos.py: drive-read` command | A | ✅ |
| 3 | `bible-brainstorm` SKILL.md preamble update | A | ✅ |
| 4 | `sermon-writer` SKILL.md preamble update | A | ✅ |
| 5 | AGENTS.md: Add autonomous exception | Rick approved ✓ | ✅ |
| 6 | `cache-preaching.sh` for dashboard | A | ✅ |
| 7 | Dashboard: Ministry pipeline component | CC-B | ✅ |


## Workflow: Brainstorm


When Rick says: "Let's brainstorm Romans 8 for February 15th"


1. Run `preaching-schedule` → find Feb 15 event with `PREACHING:` on Chapel or Ministry calendar
2. Confirm match: "I see you're preaching at St. Peter's on Feb 15. Tracking this."
3. Check Drive for existing `2026-02-15-*.docx` in `Ministry/Brainstorm/`
4. If none, proceed with brainstorm
5. Save output to `Ministry/Brainstorm/2026-02-15-romans-8.docx`
6. Create task: `[MINISTRY] Sermon prep: Feb 15 — Romans 8:1-11` (or update if exists)
7. Update calendar event description: `PREACHING: Romans 8:1-11`
8. Update task notes with Drive doc link


## Workflow: Draft


When Rick says: "Let's work on the draft for the 15th"


1. Run `preaching-schedule` → find Feb 15 event
2. Run `drive-read` → load brainstorm content from `Ministry/Brainstorm/2026-02-15-romans-8.docx`
3. Inject into sermon-writer context
4. Proceed with drafting
5. Save to `Ministry/Sermons/2026-02-15-romans-8-draft.docx`
6. Update task notes with draft link


## Decisions


| Decision | Rationale |
|----------|-----------|
| Intelligence in arnoldos.py, not skills | Skills are prompt instructions; Google API logic belongs in arnoldos.py |
| Autonomous exception (Option A) | Frictionless — the whole point is no interruptions during creative work |
| Full description overwrite (with safety check) | Rick doesn't put other content in preaching event descriptions |
| 30-day lookahead for dashboard | Beyond that is noise for sermon prep |
| Liturgy separate | Different workflow, different spec, don't bloat |
| Sys Theo opt-in via PREACHING: marker | Convention handles naturally — Rick adds marker only when he's preaching |


## Prerequisites (Rick's Action Items)


1. Add St. Peter's preaching events to Ministry calendar with `PREACHING: [passage or TBD]`
2. Add `PREACHING:` to Chapel events where Rick is preaching


## Magic Phrase


"Let's start the sermon pipeline implementation."


## Design Decision: Brainstorm File Dating (2026-02-03)


**Rule:** Every brainstorm file always gets a date prefix (`YYYY-MM-DD-short-passage-ref.docx`).
- Anchored to event → use event date
- Unanchored → use today's date
- Anchored later → rename file to event date, wire up calendar + task


This ensures the dashboard file existence check always works by date prefix.


## Drive Folder Update (2026-01-31)


**Drafts subfolder added:** `Ministry/Sermons/Drafts/`


Updated file routing:
- Brainstorms → `Ministry/Brainstorm/YYYY-MM-DD-short-passage-ref.docx`
- Working drafts → `Ministry/Sermons/Drafts/YYYY-MM-DD-short-passage-ref-draft.docx`
- Finals only → `Ministry/Sermons/YYYY-MM-DD-short-passage-ref-final.docx`


Drafts folder is a scratch space. Purge periodically after finals are promoted.
Draft naming convention: append `-draft-clawd`, `-draft-rick`, `-v2`, etc. to distinguish versions.


## Liturgy Handout Stage (Added 2026-02-07)


**Skill:** `liturgy` (standalone, St. Peter's Stone Church only)
**Trigger:** "build a liturgy handout", "liturgy for [date]", "St. Peter's handout"


### Workflow
1. Ask Rick for the date
2. Look up RCL readings via `node skills/liturgy/scripts/rcl-lookup.js YYYY-MM-DD`
3. Present readings, ask which passage Rick is preaching
4. Reorder readings (preaching passage last with Chaplain, others with Liturgist)
5. Generate Call to Worship (from Psalm) and Benediction (any relevant scripture)
6. Present for review
7. Generate .docx → local `outputs/liturgy/` + Drive `Ministry/Liturgy/`


### File Naming
`YY-MM-DD_Book_Ch_Vs-Vs_Title.docx` (e.g., `25-02-23_Luke_6_27-38_Love_Your_Enemies.docx`)


### Dependencies
- `skills/liturgy/scripts/rcl-lookup.js` — RCL date → readings lookup
- `skills/liturgy/scripts/generate-liturgy.py` — .docx generator
- `python-docx` pip package
- `lectionary` npm package (in skills/liturgy/scripts/)


### Note
Drive upload (`drive-upload` command) not yet implemented in arnoldos.py. Currently saves locally only.


## Sermon Prep Reminder Cron


**Schedule:** Mondays 8:00 AM CST
**Model:** Gemini Flash (free tier, lightweight)
**Script:** `scripts/sermon-prep-reminder.sh`


Checks `preaching.json` for upcoming sermons within 7 days and sends a Telegram reminder if any are in "not_started" or "brainstorm" status without a draft.


Example output:
> 📅 Sermon prep reminder: You're preaching at St. Peter's on Saturday (Feb 15) — Romans 8:1-11. Brainstorm done, no draft yet. ~6 days to go.
