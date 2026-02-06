Gateway Architecture Learnings
Author: Claude (Opus) — ClawdBot Supervisor
Date: February 2, 2026
Context: Discovered during dashboard file browser implementation
________________




Critical Distinction: Provider Tools vs Native Tools
The gateway exposes two classes of tools with different availability:
Provider Tools (Agent-Only)
Injected by the LLM provider during agent conversation turns. NOT available via HTTP API.
Tool
        Purpose
        API Access
        exec
        Shell command execution
        ❌ Agent only
        read
        Read files (provider injected)
        ❌ Agent only
        write
        Write files (provider injected)
        ❌ Agent only
        Native Tools (Always Available)
Registered with the gateway, accessible via /tools/invoke HTTP endpoint.
Tool
        Purpose
        API Access
        memory_search
        Hybrid vector+keyword search
        ✅ HTTP API
        memory_get
        Read memory-scoped files
        ✅ HTTP API
        sessions_spawn
        Create sub-agents
        ✅ HTTP API
        sessions_send
        Message sub-agents
        ✅ HTTP API
        cron
        Scheduled jobs
        ✅ HTTP API
        web
        HTTP requests
        ✅ HTTP API
        Key implication: External services (like the Vercel dashboard) cannot call exec to read arbitrary files or run commands. They must use native tools or workarounds.
________________




memory_get Scope Limitation
The memory_get tool is not a general file reader. It only reads files within the memory subsystem:
Path
        Works?
        MEMORY.md
        ✅ Yes
        memory/cache/tree.json
        ✅ Yes
        memory/context/*.md
        ✅ Yes
        memory/2026-02-02.md
        ✅ Yes
        AGENTS.md
        ❌ No — "path required"
        TOOLS.md
        ❌ No
        scripts/*.py
        ❌ No
        skills/*/SKILL.md
        ❌ No
        The "path required" error from memory_get indicates the file is outside its scope, not that the path format is wrong.
________________




Cron-Cache Pattern
Since the dashboard can't call exec to fetch fresh data, ClawdBot uses a cron-cache pattern:
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Cron Job    │────▶│ Cache File   │────▶│ Dashboard   │
│ (host)      │     │ memory/cache │     │ (Vercel)    │
│             │     │              │     │             │
│ Runs script │     │ JSON output  │     │ memory_get  │
│ e.g. 60s    │     │              │     │ reads cache │
└─────────────┘     └──────────────┘     └─────────────┘




Cache files:
* memory/cache/tasks.json — Google Tasks (every 60s)
* memory/cache/today.json — Today's calendar (every 60s, staggered)
* memory/cache/week.json — Week's calendar (every 5 min)
* memory/cache/tree.json — Workspace tree (every 30 min)
* memory/cache/cron.json — Cron job status
* memory/cache/gateway-status.json — Gateway health
Scripts: ~/clawd/scripts/cache-*.sh and cache-*.py
________________




File Server Solution
To enable full file access for the dashboard, we deployed a dedicated file server:
Architecture
Dashboard (Vercel)
    │
    ▼
Cloudflare Tunnel (ai.btctx.us)
    │
    ├── /files/* → File Server (:18790)
    │
    └── /* → Gateway (:18789)




Components
* Script: ~/clawd/scripts/file-server.py
* Service: clawd-files.service (systemd)
* Port: 18790 (localhost only)
* Security: Auth token, blocklist, path traversal protection
Blocklist
BLOCKLIST = [
    ".clawdbot/*",      # API keys, config
    "**/cookies/*.json", # Auth cookies
    "*.key", "*.pem",   # Certificates
    ".env*", "*-env",   # Environment files
    "**/*.gpg",         # Encrypted backups
]




________________




Debugging Lessons
Error Pattern Recognition
Error
        Likely Cause
        NOT the cause
        "path required" from memory_get
        File outside memory scope
        Path format
        "Tool not available: exec"
        Calling provider tool via API
        Gateway misconfiguration
        500 on POST
        API logic error
        Network/auth issue
        Hang on page load
        Rendering issue (if data returns 200)
        API issue
        Diagnostic Approach
1. Check tool class first — Is it provider-injected or native?
2. Check scope — Is the file/operation within the tool's allowed scope?
3. Binary search UI issues — Replace components with placeholders to isolate
4. Network tab first — Status codes tell you where the problem is
Anti-Patterns (Learned the Hard Way)
* ❌ Adjusting path formats repeatedly when tool doesn't support the file type
* ❌ Assuming API error means formatting issue
* ❌ Continuing to debug without checking architectural constraints
* ✅ Recognizing scope limitations early and proposing architectural changes
________________




Public Mirror for Supervisor Access
For supervisor sessions, the public GitHub mirror provides file access without ClawdBot token cost:
Repo: github.com/PlebRick/ClawdBot_Public
 Raw URL: https://raw.githubusercontent.com/PlebRick/ClawdBot_Public/main/<path>
Included: skills/, scripts/, memory/context/, supervisor-project/, system/, AGENTS.md, TOOLS.md, RECOVERY.md
Excluded: Personal content (rick_profile/, USER.md, SOUL.md, sermons/, voice training)
Usage: Fetch before building features to get current implementation state.
________________




Summary Table: Capability by Access Method
Capability
        ClawdBot Chat
        Gateway HTTP API
        Dashboard
        Public Mirror
        Read any file
        ✅ exec
        ❌
        ✅ file server
        ⚠️ public only
        Read memory files
        ✅
        ✅ memory_get
        ✅
        ⚠️ if synced
        Execute commands
        ✅ exec
        ❌
        ❌
        ❌
        Write files
        ✅
        ❌
        ❌
        ❌
        Search memory
        ✅
        ✅ memory_search
        ✅
        ❌
        Spawn sub-agents
        ✅
        ✅ sessions_spawn
        ❌
        ❌
        Manage cron
        ✅
        ✅
        ❌
        ❌
        ________________




This document should be updated when new architectural constraints or workarounds are discovered.
