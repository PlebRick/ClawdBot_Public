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
- ✅ Create/modify tasks in 00_Inbox with `[DOMAIN]` tags — **requires Rick's explicit confirmation**
- ✅ Drive writes to test folder only — **requires Rick's explicit confirmation**
- ❌ No Drive writes to production folders yet
- ❌ No autonomous writes — every operation must be proposed and confirmed
- **On error:** Stop immediately, diagnose before continuing
- **Log all writes:** Update `memory/arnoldos-proving-log.md` with each operation and outcome

## Commands

Run via: `python3 scripts/arnoldos.py <command>`

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
| `complete-task "title"` | Mark a task as completed (Phase 2 — requires Rick's confirmation) |

## Drive Access

For browsing Drive beyond the inbox, use Python directly:

```python
from scripts.arnoldos import get_creds, list_drive_folder
creds = get_creds()
items = list_drive_folder(creds, '<folder_id>')
```

Default Drive root: `01_ArnoldOS_Gemini` (ID: `12aczo3TPXamKkKQQc2iunPUqvfoBJovG`)

## Domain Mapping

7 life domains, each with its own calendar and Drive folder. Full mapping with IDs: `memory/context/arnoldos-integration-prd.md`

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
