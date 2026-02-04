Dashboard Command Center PRD
Overview
Transform the Clawd Dashboard from a read-only status viewer into a domain-organized command center with write capability. The dashboard will be organized around Rick's 7 Life Operating System (LOS) domains, pulling actionable tasks from Google Tasks and calendar events from Google Calendar, with write operations (create/complete/edit tasks, create events, trigger skills) available through supervised write patterns.
Architecture
* Frontend: Next.js 16 + Tailwind CSS 4 + shadcn/ui (existing stack)
* Hosting: Vercel (stateless, no database)
* Data flow (READ): Dashboard → Next.js API proxy (/api/gateway/invoke) → Clawdbot Gateway → memory_get→ cron-cached JSON files
* Data flow (WRITE): Dashboard → Next.js API route (/api/tasks/complete) → Google Tasks API (direct, via tasks-only OAuth token)
* Auth: Single-user password login, JWT cookie (existing)
* Google Auth (read): arnoldos.py uses full-scope OAuth token on local machine, cron writes cache files
* Google Auth (write): Separate tasks-only OAuth client (Clawd Dashboard - Tasks Only), refresh token stored in Vercel env vars
* Future option: Replace cron-cached reads with direct Google API calls from Next.js for lower latency
Key Repos
* arnoldos.py: ~/clawd/scripts/arnoldos.py — Google Workspace integration (Clawd's territory)
* Dashboard: ~/Projects/clawd-dashboard — Next.js app (GitHub: PlebRick/clawd-dashboard)
* Production URL: https://clawd-dashboard-nine.vercel.app
Phase Plan
Phase
	What
	Effort
	Status
	1
	Add --json output to arnoldos.py (tasks, today, week, complete-task, conflicts, drive-inbox, calendars)
	Small
	✅ Complete
	2
	Build domain tab navigation + layout in dashboard
	Medium
	✅ Complete
	3
	Wire domain tabs to Google Tasks (read)
	Medium
	✅ Complete
	4
	Add task completion (write via direct Google Tasks API)
	Small
	✅ Complete
	5
	Add task creation (inline form, auto-tagging)
	Small
	✅ Complete
	5.5
	Add task editing (inline edit of existing tasks)
	Small
	✅ Complete
	6
	Add calendar read per domain
	Medium
	✅ Complete
	7
	Build "Today's Focus" cross-domain view
	Medium
	✅ Complete
	8
	Add "Start Brainstorm" button (Ministry domain)
	Medium
	⬜
	9
	Add calendar event creation
	Medium
	⬜
	10
	Polish & Performance
	Medium
	⬜
	JSON Schemas
tasks --json
{
  "command": "tasks",
  "total": 12,
  "domains": {
    "CHAPEL": [
      {
        "id": "google-task-id",
        "title": "Review liturgy for Sunday",
        "raw": "[CHAPEL] Review liturgy for Sunday",
        "due": "2026-02-02",
        "notes": ""
      }
    ],
    "MINISTRY": [],
    "TRADING": [],
    "INBOX": []
  }
}


today --json
{
  "command": "today",
  "date": "2026-02-01",
  "domains": {
    "Chapel": [
      {
        "id": "event-id",
        "summary": "Sunday Service",
        "start": "2026-02-01T10:30:00-06:00",
        "end": "2026-02-01T12:00:00-06:00",
        "startFormatted": "10:30 AM",
        "allDay": false,
        "location": "St. Peter's Stone Church",
        "description": ""
      }
    ]
  }
}


week --json
{
  "command": "week",
  "startDate": "2026-02-01",
  "endDate": "2026-02-08",
  "domains": {
    "Chapel": [],
    "Ministry": []
  }
}


Same event schema as today. Dashboard groups by date client-side.
complete-task --json
Success:
{
  "command": "complete-task",
  "success": true,
  "task": { "id": "abc123", "title": "[CHAPEL] Review liturgy" }
}


Failure:
{
  "command": "complete-task",
  "success": false,
  "error": "No task found matching: \"sermon\"",
  "matches": []
}


Ambiguous:
{
  "command": "complete-task",
  "success": false,
  "error": "Multiple tasks match \"sermon\"",
  "matches": [
    { "id": "abc", "title": "[MINISTRY] Write sermon outline" },
    { "id": "def", "title": "[MINISTRY] Review sermon notes" }
  ]
}


conflicts --json
{
  "command": "conflicts",
  "count": 1,
  "conflicts": [
    {
      "a": { "domain": "Chapel", "summary": "Service", "start": "...", "end": "..." },
      "b": { "domain": "Family", "summary": "Lunch", "start": "...", "end": "..." }
    }
  ]
}


drive-inbox --json
{
  "command": "drive-inbox",
  "count": 3,
  "files": [
    { "id": "file-id", "name": "document.docx", "mimeType": "application/...", "modifiedTime": "2026-02-01T..." }
  ]
}


calendars --json
{
  "command": "calendars",
  "calendars": { "Chapel": "calendar-id", "Ministry": "calendar-id", ... }
}


Domain Configuration
Domain
	Calendar ID Key
	Task Tag
	Drive Folder Key
	Emoji
	Ministry
	Ministry
	[MINISTRY]
	Ministry
	⛪
	Chapel
	Chapel
	[CHAPEL]
	Chapel
	🕯️
	Trading
	Trading
	[TRADING]
	Trading
	📈
	Dev
	Dev
	[DEV]
	Dev
	💻
	Family
	Family
	[FAMILY]
	Family
	👨👩👧
	Personal
	Personal
	[PERSONAL]
	Personal
	🧘
	Content
	(none yet)
	[CONTENT]
	Content Creation
	📝
	Calendar IDs, task list ID, and Drive folder IDs are all in arnoldos.pyconstants.
Dashboard Navigation Structure
🦞 Clawd Command Center
├── OVERVIEW
│   ├── Dashboard (system status — existing /)
│   └── Today's Focus (cross-domain tasks + calendar)
├── DOMAINS (Google Tasks + Calendar per domain)
│   ├── ⛪ Ministry (+ sermon prep card later)
│   ├── 🕯️ Chapel
│   ├── 📈 Trading
│   ├── 💻 Dev
│   ├── 👨👩👧 Family
│   ├── 🧘 Personal
│   └── 📝 Content
└── SYSTEM
    ├── Projects (workspace TODO files — renamed from /todos)
    ├── Memory
    ├── Sessions
    └── Cron


Dashboard Data Architecture
Provider vs Native Tools
The Gateway HTTP invoke endpoint (/tools/invoke) only exposes Clawdbot-native tools — not provider-supplied tools. This means:
Available via HTTP Invoke
	NOT Available via HTTP Invoke
	memory_get, memory_search
	exec, process, bash
	sessions_list, sessions_send
	read, write, edit
	web_search, web_fetch
	apply_patch
	cron, gateway, browser


	Provider tools (exec, read, write, etc.) are injected by the LLM provider (Anthropic) and only exist within agent chat turns — they're never registered in the Gateway's tool registry.
Read Path: cron → file → memory_get
Since the dashboard can't call exec to run arnoldos.py on demand, we use a file-based cache:
System crontab (every 60s)
  → scripts/cache-tasks.sh
    → python3 arnoldos.py tasks --json
      → memory/cache/tasks.json (atomic write via tmp+mv)


Dashboard (browser)
  → Next.js API proxy (/api/gateway/invoke)
    → Gateway /tools/invoke
      → memory_get("memory/cache/tasks.json")
        → { details: { text: "<raw JSON>" } }
          → JSON.parse in useTasks hook


Max staleness: 60 seconds (acceptable for task lists and calendar data).
Write Path: Direct Google Tasks API
Phase 4 established the write pattern — dashboard calls Google Tasks API directly from Next.js server-side API routes, bypassing the Gateway entirely.
Dashboard (browser)
  → POST /api/tasks/complete { taskId }
    → Next.js API route (server-side)
      → OAuth token refresh (tasks-only scope)
        → PATCH Google Tasks API
          → Response to client


Undo:
  → DELETE /api/tasks/complete { taskId }
    → PATCH status back to "needsAction"


Auth: Separate OAuth client (Clawd Dashboard - Tasks Only) with only https://www.googleapis.com/auth/tasks scope. Refresh token stored in Vercel env vars. This limits blast radius if Vercel is compromised.
Optimistic UI: Task removed from local SWR state immediately. If API fails, state reverts. After undo, task reappears on next cron cache refresh (≤60s).
Reuse for future phases:
* Phase 5 (task creation/edit): Same API route pattern, same OAuth token
* Phase 6 (calendar read): Add cache-today.sh and cache-week.sh to cron pattern
* Phase 7 (Today's Focus): Combine cached tasks + calendar data client-side
* Phase 9 (calendar write): New OAuth client with calendar scope, or expand existing
Files:
* Cache script: ~/clawd/scripts/cache-tasks.sh
* Cache output: ~/clawd/memory/cache/tasks.json
* Crontab entry: * * * * * /home/ubuntu76/clawd/scripts/cache-tasks.sh
Vercel Environment Variables
Variable
	Purpose
	Scope
	GATEWAY_URL
	Clawdbot Gateway URL
	Read path (proxy)
	GATEWAY_TOKEN
	Gateway auth token
	Read path (proxy)
	JWT_SECRET
	Dashboard login auth
	Auth
	LOGIN_PASSWORD
	Dashboard password
	Auth
	GOOGLE_CLIENT_ID
	Tasks-only OAuth client
	Write path
	GOOGLE_CLIENT_SECRET
	Tasks-only OAuth secret
	Write path
	GOOGLE_REFRESH_TOKEN
	Tasks-only refresh token
	Write path
	GOOGLE_TOKEN_URI
	Google token endpoint
	Write path
	GOOGLE_TASK_LIST_ID
	Rick's Google Tasks list ID
	Write path
	Decisions Log
Date
	Decision
	Rationale
	2026-01-31
	Pivot from exec to memory_get + cron caching
	exec is a provider tool, not exposed via Gateway HTTP invoke. Cron writes cache file every 60s, dashboard reads via memory_get. Opus-approved
	2026-02-01
	Google Tasks = single source of truth for actionable tasks
	Workspace TODO files are project trackers, not daily tasks
	2026-02-01
	No database — keep dashboard stateless
	All state lives in Google APIs, accessed through Gateway
	2026-02-01
	Sermon prep: start with task-based tracking (Option A), add visual card later
	Don't build UI for a workflow not yet settled
	2026-02-01
	Skip /browser page fix (known 404 bug) — not part of this project
	Separate Clawdbot-level issue
	2026-02-01
	--json flag on arnoldos.py as Phase 1 (not direct API calls from Next.js)
	Move fast now, refactor later if needed
	2026-02-01
	Hybrid context strategy: PRD in CB memory + PLAN.md in dashboard repo + CC for React work
	Spans two codebases with different tools
	2026-02-01
	Direct Google Tasks API from Next.js for writes (Option 4)
	Sub-second checkbox UX, no new services, task IDs already in cached JSON. Opus-approved
	2026-02-01
	Separate tasks-only OAuth client (Option B)
	Full-scope token in Vercel = excessive blast radius. 30 min setup for proper scope isolation. Opus-approved
	2026-02-01
	Undo toast (5s) instead of confirmation modal for task completion
	Human clicking checkbox IS the confirmation. Modal would be hostile UX. Opus-approved
	2026-02-01
	Support undo/uncomplete via checkbox toggle + toast
	Task completion is non-destructive and reversible. Opus-approved
	Backlog (Non-Phase Items)
Item
	Priority
	Notes
	Status dashboard: model/uptime/session count not displaying
	Low
	Pre-existing — session_statusdetails don't contain model/uptimefields; sessions_list returns {count, sessions} not array. Unrelated to Phase 3.
	Rotate Brave search API key
	Low
	Visible in config snippet shared in chat history
	Google Tasks token health check
	Low
	Phase 4.5 — /api/health/google-tasks endpoint to validate token, surface on System page. Token expires after 6 months of inactivity.
	Undo optimistic re-add
	Low
	After undo, task doesn't visually reappear until cron cache refreshes (≤60s). Could optimistically re-add to local state.
	Completed Changes
(Updated after each phase)
Phase 5: Task creation — ✅ COMPLETE (2026-02-01)
* Commit: e55a3e8 on PlebRick/clawd-dashboard
* Built by: ClawdBot (Opus) — manual file writes, CC-B governance review
* Files created: src/lib/google-tasks.ts, src/app/api/tasks/create/route.ts, src/components/task-create.tsx
* Files modified: src/hooks/useTasks.ts (added createTask with temp→real ID swap), src/app/api/tasks/complete/route.ts (DRY refactor to shared lib), src/app/(dashboard)/domains/[domain]/page.tsx (wired TaskCreate)
* Features: Inline creation form (title + optional due date), domain auto-tagging server-side, optimistic prepend with temp→real Google Task ID swap, shared google-tasks.ts helper lib
* Build: Clean, no TypeScript errors
* Deploy: Vercel auto-deploy triggered on push
Phase 4: Task completion with undo — ✅ COMPLETE (2026-02-01)
* Commit: f11dcdb on PlebRick/clawd-dashboard
* Built by: ClawdBot (Opus) — manual file writes, CC-B governance review
* OAuth setup: New client Clawd Dashboard - Tasks Only in Google Cloud Console, tasks-only scope, refresh token in Vercel env vars
* Files created: src/app/api/tasks/complete/route.ts
* Files modified: src/hooks/useTasks.ts (added completeTask/undoComplete), src/components/task-list.tsx (enabled checkboxes, undo toast, completing state), src/app/(dashboard)/domains/[domain]/page.tsx(wired new props)
* Features: Direct Google Tasks API (POST=complete, DELETE=undo), optimistic SWR updates with revert on failure, 5-second undo toast, DRY token refresh helper
* Security: Tasks-only OAuth scope, no full-scope token in Vercel
* Known limitation: After undo, task reappears on next cron cache refresh (≤60s)
* Build: Clean, no TypeScript errors
* Deploy: Vercel auto-deploy triggered on push
Phase 3: Wire domain tabs to Google Tasks (read) — ✅ COMPLETE (2026-01-31)
* Commits: b89dce9 (initial), 8b416a4 (pivot to memory_get), 3cc661b (path arg fix), 6223e21 (proxy envelope unwrap), 9fb3b19 (projects page fix)
* Built by: Claude Code v2.1.27 via exec -p --permission-mode bypassPermissions
* Files created: src/lib/api/tasks.ts, src/hooks/useTasks.ts, src/components/task-list.tsx
* Files modified:src/app/(dashboard)/domains/[domain]/page.tsx (server → client component)
* Features: SWR hook with 60s refresh, TaskList with relative due dates, overdue red highlighting, tag stripping, null due date handling, skeleton loading, error state
* Pivot (2026-01-31): Discovered exec not available via HTTP invoke (provider-supplied tool). Switched to cron-cached memory/cache/tasks.json read via memory_get. Added system crontab (cache-tasks.sh every 60s). Commit 8b416a4.
* Build: Clean, no TypeScript errors
* Deploy: Vercel auto-deploy triggered on push
Phase 2: Domain tab navigation + layout — ✅ COMPLETE (2026-01-31)
* Commit: b772616 on PlebRick/clawd-dashboard
* Built by: Claude Code v2.1.27 via exec -p --permission-mode bypassPermissions
* Files created: src/lib/domains.ts, src/app/(dashboard)/domains/[domain]/page.tsx, src/app/(dashboard)/today/page.tsx, PLAN.md
* Files modified: src/components/sidebar.tsx (3-section grouped nav)
* Files moved: src/app/(dashboard)/todos/ → src/app/(dashboard)/projects/
* Build: Clean, all routes verified
* Deploy: Vercel auto-deploy triggered on push
Phase 1: --json output for arnoldos.py — ✅ COMPLETE (2026-01-31)
* Files modified: ~/clawd/scripts/arnoldos.py
* Changes: Added --json global flag, 4 new JSON helper functions (json_output, tasks_json, events_json, complete_task_json), updated __main__ dispatch with JSON branches for all commands
* Smoke tests passed:
   * tasks --json → 28 tasks, proper domain grouping, Google Task IDs present ✅
   * today --json → 2 events (Chapel, Family), full event schema ✅
   * week --json → 27 events across 3 domains ✅
   * conflicts --json → 1 conflict detected (Chapel/Family overlap) ✅
   * drive-inbox --json → empty inbox, proper schema ✅
   * calendars --json → all 7 calendar IDs ✅
   * Human-readable output (no --json) → unchanged, no regression ✅
Phase 6: Calendar read per domain — ✅ COMPLETE (2026-01-31)
Commit: 85b1d1d + 317a175
What shipped:
* cache-today.sh (every min, staggered 30s) and cache-week.sh (every 5 min) added to crontab
* src/lib/api/calendar.ts — CalendarEvent, TodayResponse, WeekResponse types + getter functions
* src/hooks/useCalendar.ts — useCalendarToday (60s refresh) + useCalendarWeek (5min refresh)
* src/components/event-list.tsx — EventCard with time column, location, sort by time, skeleton loading
* Domain page updated: calendar events card above tasks (only for domains with calendar config)
* Content domain correctly excluded (calendar: null in domains.ts)
Cron staggering: tasks at :00, today at :30, week every 5min at :00. Avoids simultaneous arnoldos.py calls.
Phase 7: Today's Focus cross-domain view — ✅ COMPLETE (2026-01-31)
Commit: 4ff1b10 + 67f9864
What shipped:
* /today rewritten from placeholder to full focus view
* Merges all calendar events across domains with emoji prefixes (via EventList showDomain prop)
* Classifies tasks into overdue (red-bordered card) and due today — future/undated excluded
* FocusTask extends TaskItem with domain + domainEmoji for correct completion wiring
* Clean empty state: "All caught up for today ✨" hides all sections when nothing actionable
* Date handling: en-CA locale + America/Chicago timezone for reliable CST comparison
* No new hooks, API routes, or caching — pure client-side aggregation of existing data
Phase 5.5: Inline task editing — ✅ COMPLETE (2026-01-31)
Commit: 5a7dc37
What shipped:
* PATCH /api/tasks/update — updates title and/or due date, null vs undefined distinction for clearing due dates
* EditableTask component: click to edit, Enter/Escape, auto-focus+select, checkbox-during-edit completes original
* Clear due date via ✕ button (sends due: null)
* Only changed fields sent (no-op edits silently cancel, no API call)
* Optimistic update + revert on failure in useTasks.updateTask
* onUpdate optional — Today's Focus page stays read-only, domain pages get editing
* [color-scheme:dark] on date picker for dark mode consistency
