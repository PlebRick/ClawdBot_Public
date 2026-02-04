# API Routing PRD Implementation — Session Briefing


## What Happened (2025-07-22)
Rick added OpenRouter-backed Anthropic models as fallback APIs, in case Anthropic eventually disables OAuth for third-party apps like Clawdbot.


### Changes Made
- Added `openrouter/anthropic/claude-opus-4-5` (alias: `or-opus`) to models config
- Added `openrouter/anthropic/claude-sonnet-4` (alias: `or-sonnet`) to models config
- Added `openrouter/anthropic/claude-opus-4-5` as first fallback (before Gemini Flash)
- Backed up config before changes: `~/.clawdbot/clawdbot.backup-YYYYMMDD-HHMMSS.json`
- **OAuth is UNTOUCHED and remains the primary auth path for Anthropic. Do NOT modify it.**


### Current State
- **Primary:** `anthropic/claude-opus-4-5` via OAuth (direct Anthropic)
- **Fallbacks:** `openrouter/anthropic/claude-opus-4-5` → `google/gemini-2.5-flash`
- **All OR models:** grok, grok-think, gemini-pro, nano-banana, qwen3, or-opus, or-sonnet
- **Direct:** opus (Anthropic OAuth), flash (Google API key)
- **Gateway has NOT been restarted yet** — changes pending reload


### What's Coming Next
Rick's supervisor (likely Opus via another session) is sending a large PRD about cost-effective API routing across all these providers. The PRD will define rules for when to use which model/provider.


### Your Job
1. **Read the PRD carefully** when Rick pastes it
2. **Implement what makes sense** for Clawdbot's architecture
3. **Push back** on anything that doesn't fit how Clawdbot actually works — the supervisor may not understand Clawdbot internals perfectly
4. Key things the supervisor might not know:
   - Clawdbot config lives at `~/.clawdbot/clawdbot.json`
   - Model routing is configured via `agents.defaults.model.primary` and `.fallbacks`
   - Per-model aliases let users switch manually with `/model alias`
   - Clawdbot doesn't have built-in cost-based routing or token counting middleware — any "smart routing" would need to be understood in context of what the gateway actually supports
   - The fallback chain is sequential, not conditional (no "use X for tasks under Y tokens" natively)
5. **Do not break OAuth.** Rick was explicit: OAuth stays as primary. Period.
6. **Do not restart gateway** without Rick's explicit go-ahead


### Pricing Reference
- Claude Opus 4.5 (direct): $15/M input, $75/M output
- Claude Sonnet 4 (direct): $3/M input, $15/M output
- OpenRouter adds ~5-15% markup on top of base pricing
- Gemini Flash: essentially free tier / very cheap
- Grok, Qwen via OR: varies


### Config File Location
`/home/ubuntu76/.clawdbot/clawdbot.json`
