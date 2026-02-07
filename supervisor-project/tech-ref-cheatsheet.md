ClawdBot Technical Reference — Supervisor Cheat Sheet
Purpose: Quick-reference for supervision decisions. Full doc on Google Drive (02_ClawdBot/supervisor-project/).


________________


Skill System
Structure: skill-name/SKILL.md (YAML frontmatter + markdown body) Detection: LLM reads all skill description fields every session → picks best match → loads that SKILL.md body. Description IS the detection rail. Precedence (high→low): Extra/plugin dirs → Bundled → Managed (~/.clawdbot/skills/) → Workspace (~/clawd/skills/) Limit: ~500 lines recommended per SKILL.md body. Never loads more than one skill up front. Chaining: Skills can't call each other directly. Chain via sub-agents, sequential loading, or cron.


Custom Skills (5): arnoldos, sermon-writer, bible-brainstorm, web-scout, liturgy


________________


Memory Architecture
Hierarchy:


* MEMORY.md — long-term curated knowledge (searchable)
* memory/*.md — daily session logs (searchable)
* memory/context/ — structured reference files (searchable)
* memory/training/ — voice profile content (searchable)
* Bootstrap files (AGENTS/SOUL/USER/etc.) — auto-injected, different mechanism


Search: Hybrid vector (0.7 weight, Gemini embeddings) + keyword (0.3 weight, FTS5/BM25). Returns top 6 results, min score 0.35. Chunks are ~400 tokens with 80-token overlap. SQLite at ~/.clawdbot/state/memory/main.sqlite.


Tools: memory_search(query) → snippets with file paths. memory_get(file, from, lines) → surgical extraction.


________________


Bootstrap Files (Auto-Loaded Every Session)
File
	Sub-Agent?
	Purpose
	AGENTS.md
	✅
	Hard rules, constraints
	SOUL.md
	❌
	Persona, tone
	USER.md
	❌
	Rick's identity
	IDENTITY.md
	❌
	Agent identity
	TOOLS.md
	✅
	Tool guidance
	HEARTBEAT.md
	❌
	Cron definitions
	BOOTSTRAP.md
	❌
	First-run (if exists)
	

Max: 20K chars each (70% head / 20% tail if truncated). Total ceiling: ~140K chars. In practice, kept small with stubs.


________________


Sub-Agents
What they are: Isolated background sessions via sessions_spawn(task, label, model, cleanup). Inherit: AGENTS.md + TOOLS.md, all tools, all skills, memory search, filesystem. Don't inherit: SOUL/USER/IDENTITY, conversation history, ability to spawn more sub-agents. Handoff: Automatic announce (summary), file-based (large outputs), or sessions_send (mid-task messaging). Cannot nest. Sub-agents cannot spawn sub-agents.


________________


Token Budgets
* Baseline (bootstrap + skill descriptions): ~4K tokens
* With one skill loaded: ~7-10K tokens
* With memory search: +2-3K tokens


________________


Cron Job Model Assignments
Job
	Model
	Reason
	Morning Brief (4:30 AM)
	Opus
	Writing quality
	Weekly Market (Fri 4 AM)
	Opus
	Heavy analysis
	Ara Check-in (11 AM/4 PM)
	Opus
	Personality
	Proton reminders (3x/yr)
	Gemini Flash
	Simple message
	Update Check (Mon 10 AM)
	Gemini Flash
	Two shell commands
	Weekend Weather (Sat 8 AM)
	Qwen3 (OpenRouter)
	Test job
	Sermon Prep Reminder (Mon 8 AM)
	Gemini Flash
	Simple message
	

________________


Provider Tools vs Native Tools
Critical constraint: Provider tools (exec, read, write) are injected by the LLM provider during agent turns only — NOT available via Gateway HTTP invoke. Only native ClawdBot tools (memory, sessions, web, cron) work via /tools/invoke. This is why the dashboard uses cron-cached JSON files instead of direct API calls through the gateway.


________________


Quick Capture (arnoldos.py)
python3 arnoldos.py quick "<text>" [--domain DOMAIN]


* 70+ keywords auto-map to domains (Chapel, Ministry, Trading, Dev, Family, Personal)
* Time patterns in text → calendar event instead of task
* --json flag for structured output


________________


File Server
Port 18790, https://ai.btctx.us/files/* via CF path routing. Bearer token auth, read-only, scoped to ~/clawd/. Service: clawd-files.service (systemd user service — systemctl --user commands).


________________


Config Snippets to Know
trustedProxies: ["127.0.0.1", "::1"]     ← both required


gateway.auth.mode: "token" or "password"  ← NO "none" option


Models must be in agents.defaults.models  ← or "model not allowed" error


models.providers.* = Category C           ← missing baseUrl crashes gateway


________________




Full doc: Google Drive > 02_ClawdBot > supervisor-project > Clawdbot technical reference