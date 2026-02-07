# Claude Code Governance — Safe Change Protocol Extension
**Author:** Clawd (drafted) / Claude Opus (supervisor review) / Rick (final approval)
**Date:** January 29, 2026
**Status:** ✅ APPROVED — Supervisor (Opus) approved 2026-01-29, Rick approved 2026-01-29
**Integrates with:** `memory/context/safe-change-protocol.md`


---


## 1. Context


Claude Code is a standalone coding agent (CLI) that ClawdBot can spawn via the `exec` tool. It runs as a **native process on the host machine** with full filesystem access. It does NOT inherit ClawdBot's system prompt, AGENTS.md hard rules, SOUL.md, or any governance documents.


This means ClawdBot can delegate work to an agent that has no knowledge of our operational constraints. This governance section exists to close that gap.


---


## 2. Task Categories


Every Claude Code invocation must be categorized before spawning.


| Category | Description | Examples | Required Review |
|----------|-------------|----------|-----------------|
| **CC-A** | Low risk. Contained workspace, disposable output. | Utility script in temp dir, one-off data analysis, scratch prototyping, generating boilerplate in isolated folder | Task description only |
| **CC-B** | Medium risk. Creates or modifies project artifacts. | New skill creation, `arnoldos.py` changes, morning brief script updates, new helper scripts in `~/clawd/scripts/` | Task description + code review before deployment |
| **CC-C** | High risk. Touches system behavior. | System config, services, cron jobs, auth, networking, `~/clawd/` bootstrap files (`AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`), `gateway.json`, systemd units, cloudflared config | Task description + code review + Rick present |


### Category Assignment Rules
- **When in doubt, go up a level.** If you're unsure whether something is CC-A or CC-B, treat it as CC-B.
- **Scope creep is re-categorization.** If a CC-A task ends up touching project files, STOP. Re-categorize and follow the higher protocol.
- **`~/clawd/` is never CC-A.** Any write to the ClawdBot workspace is CC-B at minimum.
- **Bootstrap files, config, and services are always CC-C.** No exceptions.


---


## 3. Flag Restrictions


| Flag | Risk Level | When Allowed |
|------|-----------|--------------|
| **Default (interactive)** | Low | Always permitted. However, ClawdBot cannot relay Claude Code's interactive approval prompts to the user, so practical utility is limited. Best for monitored sessions where ClawdBot reads output and relays questions manually. |
| **`--full-auto`** | Medium | **CC-A tasks only.** Workspace must be contained (temp dir or isolated project folder). Never on `~/clawd/` or system directories. |
| **`--yolo`** | Extreme | **Never without explicit supervisor (Opus) + Rick approval in the same session.** Both must sign off before the command is executed. This flag removes all sandboxing and all approval gates. |


### Flag Escalation
If a task requires `--yolo` to work, that's a signal the task is more complex than expected. Pause and reassess:
- Can the task be broken into smaller `--full-auto` steps?
- Can the dangerous parts be done manually with Claude Code handling only the safe parts?
- Does the task need to be rearchitected?


---


## 4. Mandatory Pre-Spawn Checklist


### CC-A Tasks
- [ ] Task description stated (what is Claude Code being asked to do?)
- [ ] Working directory specified (must be temp dir or isolated workspace)
- [ ] Flag mode: default or `--full-auto` only


### CC-B Tasks — All of the above, plus:
- [ ] Working directory is appropriate and scoped (not `~/clawd/` root)
- [ ] Flag mode justified (why `--full-auto` if used?)
- [ ] Output review plan stated: "I will read the generated files at [path] and surface them for review before deployment"
- [ ] Deployment is blocked until code review is complete


### CC-C Tasks — All of the above, plus:
- [ ] Rick is present in the session
- [ ] Task description approved by Rick before spawning
- [ ] Rollback procedure documented before execution
- [ ] Code review by supervisor (Opus) AND Rick before any deployment
- [ ] Changes logged in the appropriate proving log or change log


---


## 5. Post-Execution Review Protocol


### CC-A
- No formal review required
- ClawdBot may optionally check output for sanity


### CC-B
- ClawdBot reads all generated/modified files
- Code is surfaced to supervisor (Opus) for review
- Supervisor approves or requests changes
- Only after approval: files moved to production location, scripts made executable, etc.
- If code modifies existing files: diff surfaced (before/after)


### CC-C
- Everything from CC-B, plus:
- **Review order is sequential, not parallel:** Code surfaced → Opus reviews → Opus approves → Rick reviews → Rick approves → Deploy
- Rick reviews the code (or a plain-language summary if code is lengthy)
- Rick explicitly approves deployment
- Rollback tested or documented
- Change logged in `memory/context/safe-change-protocol.md` or relevant log file


---


## 6. Prohibited Actions


The following are **never permitted** regardless of category or approval:


1. **`--yolo` for convenience.** The flag exists for extreme edge cases, not to skip the approval process because it's faster.
2. **"I'll spawn Claude Code to fix this" without a task description.** Every invocation must have a clear, stated objective before the command runs.
3. **Generated code deployed without review.** For CC-B and CC-C, code must be surfaced and approved before it enters production.
4. **Tasks that touch system behavior categorized as CC-A.** If it affects how ClawdBot runs, how services operate, how auth works, or how the system is configured — it is CC-B or CC-C. Period.
5. **Spawning Claude Code inside `~/clawd/` without CC-B or CC-C protocol.** The ClawdBot workspace is the live operating environment. It is never a scratch pad.
6. **Chain-spawning.** ClawdBot must not spawn Claude Code which then spawns additional agents or processes without the original task description covering that scope.


---


## 7. Working Directory Rules


| Directory | Minimum Category | Notes |
|-----------|-----------------|-------|
| `/tmp/*` or `mktemp -d` | CC-A | Disposable scratch work |
| `~/Projects/*` (non-clawdbot) | CC-A | Isolated project work |
| `~/clawd/scripts/` | CC-B | Helper scripts for ClawdBot |
| `~/clawd/skills/` | CC-B | Skill creation/modification |
| `~/clawd/memory/` | CC-B | Memory file generation (not bootstrap) |
| `~/clawd/` (root) | CC-C | Bootstrap files, workspace config |
| `~/.clawdbot/` | CC-C | Gateway config, secrets |
| `~/.config/clawd/` | CC-C | OAuth tokens, credentials |
| `/etc/*` | CC-C | System config (cloudflared, systemd) |
| `~/Projects/clawdbot/` | CC-C | Live ClawdBot source — NEVER checkout branches here |


---


## 8. Logging


All CC-B and CC-C invocations must be logged:


```
## Claude Code Invocation Log Entry
- Date/Time:
- Category: CC-A / CC-B / CC-C
- Task Description:
- Working Directory:
- Flag Mode:
- Spawned By: (ClawdBot / Rick direct)
- Output Review: (pending / approved by [who] / not required)
- Deployment Status: (deployed / pending / rolled back)
- Notes:
```


Log location: `memory/context/claude-code-invocation-log.md` (created on first CC-B or CC-C invocation)


**Note:** CC-A invocations may be optionally logged for audit trail but are not required.


---


## 9. Emergency Override


In a genuine emergency (system down, data loss in progress), Rick may verbally authorize skipping the checklist. If this happens:
1. Execute the fix
2. Immediately after: document what was done, why the override was needed, and what checklist steps were skipped
3. Post-incident review within 24 hours
4. Log in `memory/context/safe-change-protocol.md` incident section


---


## 10. Review and Amendment


This governance document is reviewed:
- After any Claude Code incident or near-miss
- When new capabilities are added to Claude Code
- At Phase 3 evaluation (alongside ArnoldOS authority decision)
- On Rick's or supervisor's request


Amendments require supervisor (Opus) review and Rick's approval, logged with date and reason.


---


*Drafted by Clawd, January 29, 2026*
*Pending: Supervisor review → Rick approval → Integration into Safe Change Protocol*