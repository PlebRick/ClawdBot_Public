---
name: arnoldos
description: Access Rick's Google Workspace (ArnoldOS) — calendar events, tasks, Drive files, conflicts, and schedule across all 7 life domains. Use for questions about Rick's own schedule, tasks, or Drive content.
---

# ArnoldOS — Rick's Life Operating System

Read and supervised write access to Rick's Google Workspace: Calendar, Tasks, and Drive.

## Phase Status
**Current: Phase 2 — SUPERVISED WRITES**
- ✅ Read calendar events, tasks, Drive files
- ✅ Create/modify calendar events — **requires Rick's explicit confirmation**
- ✅ Create/modify tasks — **requires Rick's explicit confirmation**
- ✅ Upload files to Drive — **requires Rick's explicit confirmation**
- ❌ No autonomous writes — every operation must be proposed and confirmed
- **On error:** Stop immediately, diagnose before continuing

## Commands

Run via: `python3 scripts/arnoldos.py <command>`

### Read Commands
| Command | What it does |
|---------|-------------|
| `today` | Today's events across all 7 calendars |
| `week` | This week's events across all calendars |
| `tasks` | All incomplete tasks grouped by domain tag |
| `conflicts` | Check today for scheduling conflicts |
| `conflicts-week` | Check this week for conflicts |
| `drive-inbox` | List files in Drive 00_Inbox |
| `brief` | Full morning brief output |
| `calendars` | List all calendar names/IDs |
| `preaching-schedule` | Upcoming preaching events with prep status |
| `drive-read <file_id>` | Read a Drive file's content |

### Write Commands

**create-event** — Create a calendar event:
```bash
# Timed event
python3 scripts/arnoldos.py create-event Ministry "Team Meeting" 2026-02-03T14:00:00 2026-02-03T15:00:00

# All-day event
python3 scripts/arnoldos.py create-event Personal "Day Off" 2026-02-05 2026-02-06

# With description and location
python3 scripts/arnoldos.py create-event Chapel "Service" 2026-02-09T10:00:00 2026-02-09T12:00:00 \
  --description "PREACHING: Romans 8:1-11" --location "Chapel Building"
```

**update-event** — Update an existing event:
```bash
python3 scripts/arnoldos.py update-event Ministry <event_id> --summary "New Title" --description "Updated"
```
Options: `--summary`, `--description`, `--location`, `--start`, `--end`

**create-task** — Create a task:
```bash
python3 scripts/arnoldos.py create-task "[MINISTRY] Sermon prep: Feb 15" --due 2026-02-14 --notes "Romans 8"
```
Options: `--notes`, `--due YYYY-MM-DD`

**complete-task** — Mark a task complete:
```bash
python3 scripts/arnoldos.py complete-task "Sermon prep: Feb 15"
```

**drive-upload** — Upload a file to Drive:
```bash
python3 scripts/arnoldos.py drive-upload Ministry/Brainstorm 2026-02-15-romans-8.docx ./local-file.docx
```
Folder keys: `Ministry`, `Ministry/Brainstorm`, `Ministry/Sermons`, `Chapel`, `Trading`, `Dev`, `Family`, `Personal`, `00_Inbox`

### JSON Output
Add `--json` flag to any command for programmatic use:
```bash
python3 scripts/arnoldos.py create-task "[DEV] Fix bug" --json
```

## Domain Mapping

| Domain | Calendar | Drive Folder |
|--------|----------|-------------|
| Ministry | Ministry | `/Ministry/` |
| Chapel | 2026 Chapel Schedule | `/Chapel/` |
| Trading | Trading | `/Trading/` |
| Dev | Dev | `/Dev/` |
| Family | Family | `/Family/` |
| Personal | Primary | `/Personal/` |
| Content | (uses Personal) | `/Content/` |

## When NOT to Use This Skill
- Generic calendar questions not about Rick's schedule
- Weather, sermons, brainstorming, email — other skills handle those

## Quick Capture (Natural Language)

**quick** — Create tasks with auto-detected domain:
```bash
arnoldos.py quick "UCG Passover reminder March 31"
# → [CHAPEL] UCG Passover reminder (due 2026-03-31)

arnoldos.py quick "review bitcoin chart Friday"
# → [TRADING] review bitcoin chart (due 2026-02-07)

arnoldos.py quick "finish sermon draft"
# → [MINISTRY] finish sermon draft

# Force domain if ambiguous
arnoldos.py quick "meeting tomorrow" --domain DEV
```

**quick-event** — Create calendar events with auto-detected domain:
```bash
arnoldos.py quick-event "bitcoin review Friday 10am"
# → Trading calendar, 10:00-11:00

arnoldos.py quick-event "dentist Thursday 2pm"
# → Family calendar, 14:00-15:00

arnoldos.py quick-event "sermon prep meeting Tuesday 9am" --domain MINISTRY
```

### Domain Keywords
- **CHAPEL**: ucg, passover, chapel, prison, chaplain, sabbath, feast days
- **MINISTRY**: sermon, preach, st. peter's, church, brainstorm, liturgy
- **TRADING**: bitcoin, btc, crypto, tsla, stock, market, portfolio
- **DEV**: code, deploy, dashboard, api, github, script, clawdbot
- **FAMILY**: groceries, kids, household, doctor, appointment, dentist
- **CONTENT**: youtube, video, record, edit, upload, channel
- **PERSONAL**: workout, gym, health, book, personal, hobby

### Date/Time Parsing
- Dates: "March 31", "Thursday", "tomorrow", "next week"
- Times: "2pm", "14:00", "10:30am"
- Default event duration: 1 hour
