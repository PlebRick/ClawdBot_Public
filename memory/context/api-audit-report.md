# API Migration Audit Report

**Date:** 2026-02-01
**Auditor:** ClawdBot (Clawd)

## 1. Authentication Status

**Current Method:** OAuth (synced from Claude Code CLI)
**Evidence:**
- Config declares `auth.profiles.anthropic:default` with `mode: "token"`
- Actual auth-profiles store has two Anthropic profiles:
  - `anthropic:default` — type: `token` (appears to be a placeholder/wrapper)
  - `anthropic:claude-cli` — type: `oauth` with access token, refresh token, expires at epoch `1769979379815` (≈2026-02-02 04:56 UTC)
- Claude Code's own credential file (`~/.claude/.credentials.json`) has a `claudeAiOauth` key but shows no direct tokens (Clawdbot syncs them into its own store)
- **No Anthropic API key exists anywhere** — no `ANTHROPIC_API_KEY` env var, no API key in config

**Assessment:** We are using Claude Max subscription OAuth tokens, synced from Claude Code CLI, to power all Anthropic model calls. This is the exact pattern Anthropic's ToS may prohibit for automated/agent use. **ToS risk is real and should be addressed.**

## 2. LLM Configuration

**Default Provider:** Anthropic (direct, via OAuth)
**Default Model:** `anthropic/claude-opus-4-5`
**Config Location:** `~/.clawdbot/clawdbot.json`

**Full LLM/Model Config (secrets redacted):**
```json
{
  "primary": "anthropic/claude-opus-4-5",
  "fallbacks": [
    "openrouter/anthropic/claude-opus-4-5",
    "google/gemini-2.5-flash"
  ],
  "models": {
    "anthropic/claude-opus-4-5": { "alias": "opus" },
    "openrouter/anthropic/claude-opus-4-5": { "alias": "or-opus" },
    "openrouter/anthropic/claude-sonnet-4": { "alias": "or-sonnet" },
    "openrouter/x-ai/grok-4.1-fast": { "alias": "grok" },
    "openrouter/x-ai/grok-4": { "alias": "grok-think" },
    "openrouter/google/gemini-3-pro-preview": { "alias": "gemini-pro" },
    "openrouter/google/gemini-3-pro-image-preview": { "alias": "nano-banana" },
    "openrouter/qwen/qwen3-235b-a22b-2507": { "alias": "qwen3" },
    "google/gemini-2.5-flash": { "alias": "flash" }
  }
}
```

**API Keys Present:**
- `GEMINI_API_KEY` — set in config env vars (direct Google)
- `OPENROUTER_API_KEY` — set in config env vars (OpenRouter)
- No `ANTHROPIC_API_KEY` — relies entirely on OAuth

## 3. Cron Job LLM Usage

### Clawdbot Internal Cron Jobs (use LLM via gateway)

| Cron Job | Uses LLM? | Model | Est. Tokens/Run | Notes |
|----------|-----------|-------|-----------------|-------|
| Morning Brief (4:30 AM CT) | **Yes** | Default (Opus 4.5 via OAuth) | ~8-15K output | Isolated session, web search + data aggregation, sends to Telegram |
| Weekly Market Report (Fri 4:00 AM CT) | **Yes** | Default (Opus 4.5 via OAuth) | ~10-20K output | Isolated session, generates .docx to Drive |
| Ara Spicy Check-ins (11 AM, 4 PM CT) | **Yes** | Default (Opus 4.5 via OAuth) | ~1-3K output | System event to main session, casual message |
| Rotate Vercel Token (monthly) | No | N/A | N/A | System event reminder only |

### System Crontab Jobs (shell/python, NO LLM)

| Cron Job | Uses LLM? | Model | Notes |
|----------|-----------|-------|-------|
| cache-cron.sh (every min) | No | N/A | Python → JSON cache |
| cache-tasks.sh (every min) | No | N/A | arnoldos.py → Google API |
| cache-today.sh (every min) | No | N/A | arnoldos.py → Google API |
| cache-week.sh (every 5 min) | No | N/A | arnoldos.py → Google API |
| cache-preaching.sh (every 5 min) | No | N/A | arnoldos.py → Google API |
| cache-gateway-status.sh (every min) | No | N/A | Python → JSON cache |
| cache-tree.sh (every min) | No | N/A | Python → JSON cache |
| sync-memory-to-drive.sh (every 6h) | No | N/A | rclone sync |
| backup-config-encrypted.sh (2 AM) | No | N/A | Config backup |
| crontab backup (midnight) | No | N/A | crontab -l redirect |

## 4. Skill Model Configuration

| Skill | Has Model Spec? | Current Model | Recommended (per PRD) |
|-------|-----------------|---------------|----------------------|
| arnoldos | No | Inherits default (Opus 4.5) | Grok 4.1 Fast (P4) |
| sermon-writer | No | Inherits default (Opus 4.5) | Claude Opus 4.5 (P1) ✅ |
| bible-brainstorm | No | Inherits default (Opus 4.5) | Claude Opus 4.5 (P1) ✅ |
| web-scout | No | N/A (headless browser, no LLM) | Gemini 3 Flash (P4) — N/A |
| liturgy | No | Inherits default (Opus 4.5) | Not specified |

**Note:** web-scout is a headless browser automation skill (Playwright). It does NOT call any LLM directly — it scrapes web data. The LLM usage happens in whatever agent session *invokes* web-scout.

**No skills specify a model override.** All inherit the default.

## 5. Environment Variables

**Relevant vars found in config (`env.vars`):**
- `GEMINI_API_KEY` — [REDACTED] (present)
- `OPENROUTER_API_KEY` — [REDACTED] (present)

**Shell environment:**
- Same two keys propagated from config
- No `ANTHROPIC_API_KEY` in shell env

**Other credential files:**
- `~/.clawdbot/.env` — contains `VERCEL_TOKEN` (scheduled for rotation)
- `~/.clawdbot/bird-env` — X/Twitter credentials

## 6. Credential Files

**Files in `~/.clawdbot/`:**
- `clawdbot.json` — main config (contains API keys in `env.vars`)
- `clawdbot.known-good.json` — known good config backup
- `clawdbot.backup-*.json` — timestamped backups (5 files)
- `.env` — Vercel token
- `bird-env` — X/Twitter creds
- `agents/main/agent/auth-profiles.json` — OAuth tokens for Anthropic
- `identity/device-auth.json` — device auth tokens
- `identity/device.json` — device keypair

## 7. Summary & Recommendations

**Current State:** ClawdBot runs entirely on Anthropic Claude Opus 4.5 via OAuth tokens synced from Claude Code CLI. All cron jobs, all skills, and all interactive sessions use this single auth path. OpenRouter and Gemini API keys are configured but only serve as fallbacks (OR) or for the `flash` alias (Gemini). The OAuth token refreshes automatically via Claude CLI sync.

**ToS Risk Assessment:** **Medium-High** — We are using Claude Max subscription OAuth to power an automated agent (ClawdBot) that runs cron jobs, responds to Telegram messages, and operates 24/7. Anthropic's ToS restricts subscription access to interactive human use. API keys are the sanctioned path for programmatic access. We haven't been flagged yet, but this is a clear gray area trending toward violation.

**Ready for Phase 2?** Yes — no blockers. The audit is clean, the architecture is well-understood, and OpenRouter + Gemini API keys are already in place. The migration path is straightforward:
1. Change primary from `anthropic/claude-opus-4-5` (OAuth) → `openrouter/anthropic/claude-opus-4-5` (API key)
2. Implement model routing per PRD tiers
3. Keep OAuth as emergency fallback during transition

## 8. Questions for Supervisor

1. **OAuth as fallback:** Should we keep OAuth as a last-resort fallback after migration, or remove it entirely for clean ToS compliance?

2. **Ara agent:** Ara currently shares the same model config (inherits defaults). Should Ara get the same routing tiers, or does she stay on a specific model? She's personality-driven (spicy casual), which suggests P3 (Grok) might be perfect for her character.

3. **Morning Brief complexity:** The Morning Brief does web search + data aggregation + long-form composition. It's currently the heaviest cron job. Is this P1 (Opus) or could it work at P3 (Grok)?

4. **Sonnet 4.5 vs Sonnet 4:** The kickoff mentions "Sonnet 4.5 for coding" but the configured alias `or-sonnet` points to `claude-sonnet-4` (not 4.5). Is Sonnet 4.5 available on OpenRouter? Should we add it?

5. **Budget guardrails:** Does Clawdbot need to implement its own spend tracking, or does OpenRouter's built-in budget/limit feature suffice?

6. **Full PRD:** The kickoff references a comprehensive PRD with detailed routing rules, fallback chains, and CC guardrails — but I only received the kickoff document. Is there a separate detailed PRD to follow?
