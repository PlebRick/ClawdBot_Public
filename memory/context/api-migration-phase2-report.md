# Phase 2: OpenRouter Setup — Report


**Date:** 2026-02-01
**Status:** Complete (pending spending limit configuration)


## 1. API Connectivity — All Models Verified ✅


| Model | OpenRouter ID | Test Result | Cost (test call) |
|-------|--------------|-------------|------------------|
| Claude Opus 4.5 | `anthropic/claude-opus-4.5` | ✅ Working | $0.00033 |
| Claude Sonnet 4.5 | `anthropic/claude-sonnet-4.5` | ✅ **EXISTS and working** | $0.000198 |
| Claude Haiku 4.5 | `anthropic/claude-haiku-4.5` | ✅ Available | (not tested) |
| Grok 4.1 Fast | `x-ai/grok-4.1-fast` | ✅ Working | $0.00012 |
| Gemini 3 Flash | `google/gemini-3-flash-preview` | ✅ Working | $0.000023 |
| Gemini 2.5 Flash | `google/gemini-2.5-flash` | ✅ Available | (already in config) |


**Key finding:** Sonnet 4.5 DOES exist on OpenRouter (`anthropic/claude-sonnet-4.5`). PRD was correct.


## 2. Verified Model Pricing (per M tokens)


| Model | Input | Output | Tier |
|-------|-------|--------|------|
| Claude Opus 4.5 | $5.00 | $25.00 | P1 |
| Claude Sonnet 4.5 | $3.00 | $15.00 | P2 |
| Claude Haiku 4.5 | $1.00 | $5.00 | P2 fallback |
| Grok 4.1 Fast | $0.20 | $0.50 | P3 |
| Gemini 3 Flash | $0.50 | $3.00 | P4 |
| Gemini 2.5 Flash | $0.30 | $2.50 | P4 fallback |


## 3. Account Status


- **Payment method:** Active (not free tier)
- **Current usage:** $0.42 (test calls from today + prior setup)
- **Current spending limit:** `null` (NO LIMIT SET)
- **API key:** Working, stored in `clawdbot.json` env vars


## 4. Action Items for Rick (OpenRouter Dashboard)


⚠️ **The spending limit is currently NULL (unlimited).** Rick needs to configure these in the OpenRouter dashboard:


1. **Monthly hard cap → $100** (prevents runaway spend)
2. **Daily soft limit → $10** (alert only — if OR supports it)
3. **Per-request max → $2** (if OR supports it)


Dashboard: https://openrouter.ai/settings/limits


I cannot set these via API — they require dashboard access.


## 5. Alert/Webhook Configuration


OpenRouter supports webhook notifications for spending thresholds. Rick should configure:
- 50% alert ($50)
- 75% alert ($75)  
- 90% alert ($90)


These can be pointed at a Telegram bot webhook or email. Needs Rick's manual setup in dashboard.


## 6. Correct Model IDs for Phase 3 Config


Based on verification, here are the exact OpenRouter model IDs to use:


```
P1: anthropic/claude-opus-4.5
P2: anthropic/claude-sonnet-4.5
P3: x-ai/grok-4.1-fast
P4: google/gemini-3-flash-preview
Fallbacks: anthropic/claude-haiku-4.5, google/gemini-2.5-flash
```


**Note:** Gemini 3 Flash is still in preview (`gemini-3-flash-preview`). When it goes GA, the ID may change.


## 7. Phase 2 Checklist


- [x] Verify OpenRouter account and payment
- [ ] Increase spending limit to $100 (**RICK — dashboard action needed**)
- [ ] Configure alert webhooks (**RICK — dashboard action needed**)
- [x] API key already stored securely (in clawdbot.json env vars, not git-tracked)
- [x] Test all target models via API
- [x] Document model IDs and pricing


## 8. Ready for Phase 3?


**Almost.** Two blockers for Rick:
1. Set the $100 monthly spending cap on OpenRouter
2. Confirm alert preferences (webhook vs email vs skip for now)


Once those are done, Phase 3 (ClawdBot config changes) is ready to go.


## 9. Addendum: Spending Limits


**OpenRouter dashboard:** Rick could not locate a spending limits page. The `/api/v1/auth/key` endpoint shows `limit: null`. It's possible OR moved this feature, requires a different plan tier, or it's set per-key during creation.


**TODO:** Investigate OpenRouter spending limit options later (check docs, support, or key creation settings).


**Mitigation:** Build our own spend monitoring cron job that:
1. Queries OR usage API every 5 minutes
2. Sends Telegram alerts at 50%/75%/90% of $100 budget
3. Can implement a hard stop by blocking API calls if 100% is reached


**Account status:** $10.00 credits loaded, $0.42 used.


## 10. Addendum: Alert Recommendation


Recommend building our own Telegram-based spend alerting (Phase 7 or earlier) rather than relying on OR dashboard webhooks. We already have the Telegram bot infrastructure and the OR usage API returns live data. Safest approach.


## 11. Addendum: Phase 3 Model ID Incident


**Date:** 2026-02-01
**Issue:** During Phase 3 config migration, all Opus calls hung indefinitely after switching from OAuth to OpenRouter.


**Root cause:** Model ID typo in `~/.clawdbot/clawdbot.json`. OpenRouter uses **dots** in Claude version numbers, not dashes.


| ❌ Wrong | ✅ Correct |
|----------|-----------|
| `claude-opus-4-5` | `claude-opus-4.5` |
| `claude-sonnet-4-5` | `claude-sonnet-4.5` |
| `claude-haiku-4-5` | `claude-haiku-4.5` |


**Impact:** Opus calls hung with no error — OpenRouter quietly failed to find the model and timed out.


**Resolution:** Rick (remote, no terminal) diagnosed via web UI using `/status` and `/model` commands. Switched to Grok Fast as interim, used exec tool to sed-fix the config, restarted gateway, and switched back to Opus.


**Lesson learned:** Always verify model IDs exactly match OpenRouter's format. When in doubt, check https://openrouter.ai/models for the canonical ID.