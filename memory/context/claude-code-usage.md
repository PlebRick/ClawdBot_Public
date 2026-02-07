# Claude Code Usage Guide


## What Claude Code Is


Claude Code (CC) is an external CLI tool (`claude`) for autonomous coding tasks. It is NOT a ClawdBot agent — you cannot use `sessions_spawn` with CC.


## What Does NOT Work


```bash
# WRONG — CC is not a ClawdBot agent
sessions_spawn agentId:claude-code task:"..."


# WRONG — interactive mode hangs waiting for input
exec command:"claude 'prompt'"


# WRONG — restrictive allowedTools blocks normal dev work
claude -p "prompt" --allowedTools "Bash(cat:*)"
```


## Correct Invocation Template


### Short tasks (< 30 seconds)
```bash
exec workdir:~/Projects/your-repo command:"claude -p 'TASK PROMPT' --permission-mode bypassPermissions"
```


### Long tasks (builds, multi-file changes)
```bash
exec pty:true workdir:~/Projects/your-repo background:true command:"claude -p 'TASK PROMPT' --permission-mode bypassPermissions"
```


Then monitor with:
```bash
process action:poll sessionId:XXX   # Check if still running
process action:log sessionId:XXX    # View output
```


## Flags Reference


| Flag | Purpose |
|------|---------|
| `-p "prompt"` | Non-interactive print mode — runs to completion and exits |
| `--permission-mode bypassPermissions` | Full file read/write/bash without permission prompts |
| `pty:true` | Allocate pseudo-terminal (needed for some CLI tools) |
| `background:true` | Run in background, don't block |


## Key Behaviors


- CC exits with code 0 on success
- No interactive prompts, no hanging
- Has full access to read/write/edit files and run bash in the workdir
- Workspace trust prompt appears on first use per directory (approve with Enter)
- After first approval, subsequent runs skip the trust prompt


## Governance


CC invocations follow Claude Code Governance Protocol:
- **CC-A:** Contained workspace, task description only
- **CC-B:** Task description + code review before deployment
- **CC-C:** Task description + code review + Rick present


See `memory/context/claude-code-governance.md` for full protocol.


## Verified Working (January 31, 2026)


- `claude` CLI v2.1.27
- Auth: Opus 4.5 via Claude Max (chaplaincen@gmail.com)
- Creates/edits/deletes files ✓
- Runs bash commands (npm run build, cat, rm, mv) ✓
- Exits cleanly on completion ✓
- PTY mode works for background monitoring ✓