# Future Integrations Roadmap








**Created:** January 29, 2026
**Updated:** February 1, 2026
**Author:** Claude (Opus) as ClawdBot Supervisor
**Status:** Planning — Items listed here are NOT approved for implementation
**Purpose:** Capture future expansion ideas so they aren't forgotten








---








## Overview








This document tracks potential integrations and capabilities discussed for future phases, after the current LOS foundation is solid. Items here are ideas, not commitments.








**Prerequisite:** LOS Phase 2 (Ministry Skills) is complete. Future work proceeds as capacity allows.








---








## Recently Completed








### Git Backup ✅ (January 31, 2026)








**Status:** Complete — Full workspace backed up to private GitHub repo








- **Repo:** `github.com/PlebRick/ClawdBot_Backup` (private)
- **Files:** 227 committed, zero secrets (full security audit performed)
- **Safety:** Gitleaks v8.21.2 pre-commit hook blocks any secret from entering git history
- **Recovery:** `RECOVERY.md` — 5-phase disaster recovery runbook (system → clone → credentials → gateway → verify)
- **Estimated recovery time:** 45-90 minutes from bare hardware
- **Backup script:** `scripts/backup-to-github.sh` (uses `gh auth token` at runtime)
















### Liturgy Skill ✅ (February 7, 2026)








**Status:** Complete — Integrated into preaching pipeline








Generates formatted .docx liturgy handouts for St. Peter's Stone Church.








| Component | Status |
|-----------|--------|
| RCL lookup (rcl-lookup.js) | ✅ Working — all seasons, Year A/B/C |
| .docx generator (generate-liturgy.py) | ✅ Working — full format with boilerplate |
| Skill (SKILL.md) | ✅ Complete — 8-step workflow |
| Pipeline spec updated | ✅ Done |








**Features:**
- Automatic RCL reading lookup from date (uses lectionary npm + lectionarypage.net)
- Responsive Call to Worship generated from Psalm reading
- Scripture-based Benediction selection
- Reading reorder (preaching passage last as Chaplain)
- Fixed boilerplate: Apostles' Creed, Lord's Prayer (KJV debtor), hymn slots








**Remaining:**
- `drive-upload` command needed in arnoldos.py for automatic Drive upload to `Ministry/Liturgy/`
- Currently saves locally to `outputs/liturgy/`
















### OpenRouter Multi-Model Integration ✅ (February 1, 2026)








**Status:** Complete — Three-provider model architecture live and tested








- **Provider:** OpenRouter (openrouter.ai) — single API key, access to 100+ models
- **Models added:** Qwen3 235B, Grok 4.1 Fast, Grok 4, Gemini 3 Pro, Nano Banana (image gen)
- **Test job:** Weekend Weather Digest (Saturdays 8 AM, Qwen3 via OpenRouter) — verified working
- **Image generation:** Nano Banana Pro tested, generated sermon illustration successfully
- **Cost optimization:** Lightweight cron jobs moved to Gemini Flash (free) and Qwen3 ($0.07/M)
- **Architecture:** Anthropic (primary) → Google free (basic crons) → OpenRouter (flexible pool)
- **Rules:** No Claude via OpenRouter; Grok/Gemini Pro/Nano Banana on-demand only; spend cap in dashboard
















### Web Scout Skill ✅ (January 30, 2026)








**Status:** Complete — All phases delivered








Headless browser automation via Playwright, replacing the unreliable Chrome relay extension.








| Target | Auth | Status |
|--------|------|--------|
| CNN Fear & Greed | None | ✅ Working |
| IntoTheCryptoverse | Firebase | ✅ Working (118+ charts) |
| Logos | Cookie | ✅ Working (7,500 books) |
| Gospel Truth (Finney) | None | ✅ Working (851 sermons) |








**Remaining integration work (non-blocking):**
- Integrate CNN F&G into morning brief cron
- Integrate ITC data into weekly market report cron
- Register in formal skill registry








---








## Content Publishing Pipeline








### Vision








```
Written Content (sermon, article, devotional)
                    ↓
        ┌───────┼───────┐
        ↓       ↓       ↓
  ElevenLabs  Substack  YouTube
   (audio)  (newsletter) (video)
```








Rick writes once. ClawdBot distributes to multiple platforms.








### ElevenLabs Integration








**Purpose:** Generate audio sermons and content in Rick's voice








**Current State:**
- ✅ Rick has ElevenLabs account
- ✅ Rick's voice is cloned
- ✅ Custom voice also available
- ❌ No ClawdBot integration yet








**Integration Approach:**
- ElevenLabs has Python SDK
- Skill wraps API calls for text-to-speech
- Guardrail: Explicit approval + cost awareness per generation








**Considerations:**
- Cost per character generated
- Audio quality settings
- File storage location
- Naming conventions for generated files








### YouTube Integration








**Purpose:** Publish sermon audio with visual to YouTube channel








**Current State:**
- ✅ Google OAuth working (YouTube read access)
- ❌ YouTube upload not yet configured
- ❌ No ClawdBot integration yet








**Planned Format:**
- Audio from ElevenLabs
- Static relevant image (not video production)
- Auto-generated closed captions








**Integration Approach:**
- Expand Google OAuth to include YouTube upload scope
- Skill handles: upload video, set metadata, manage captions
- Guardrail: Explicit approval before any publish








**Considerations:**
- Image sourcing (stock? generated? manual selection?)
- Caption accuracy review
- Scheduling vs immediate publish
- Playlist organization








### Substack Integration








**Purpose:** Distribute written content as newsletter








**Current State:**
- ❌ No integration yet
- Need to investigate Substack API or email-to-publish








**Integration Approach:**
- Option A: Substack API (if available)
- Option B: Email-to-publish feature
- Guardrail: Explicit approval before any publish








**Considerations:**
- Formatting preservation (Markdown → Substack)
- Image handling
- Scheduling
- Subscriber segmentation (if applicable)








---








## Cron Integration Work








### Morning Brief Enhancement








**Current state:** Morning brief cron runs at 4:30 AM CST with ArnoldOS data.








**Enhancement:** Add CNN Fear & Greed data via Web Scout.








**Approach:**
1. Call `node skills/web-scout/scripts/fetch-cnn-fg.js` from cron script
2. Include index + components in brief
3. Flag extreme values (Extreme Fear / Extreme Greed)








**Priority:** Low — enhancement, not blocking








### Weekly Market Report Enhancement








**Current state:** Weekly report runs Fridays 4:00 AM CST.








**Enhancement:** Add ITC data via Web Scout.








**Approach:**
1. Call Web Scout to fetch key ITC metrics (recession probability, BTC risk, etc.)
2. Include in weekly report
3. Handle session expiry gracefully (skip section, note unavailable)








**Priority:** Low — enhancement, not blocking








---








## Additional Skills (Deferred)








### Trading Analysis Skill








**Status:** Needs scoping








**Blocker:** Portfolio scope undefined. What accounts? What data sources? What analysis?








**When to revisit:** When Rick defines what "trading analysis" means for ClawdBot.








### Chapel Schedule Skill








**Status:** Needs separate PRD








**Blocker:** Workflow not documented. How does Rick currently manage chapel scheduling?








**When to revisit:** When Rick has time to walk through current process.








---








## MCP Capabilities








### Current Understanding








**MoltBot MCP Status:**
- ✅ MCP Client capability via `mcporter` skill (can connect TO external MCP servers)
- ❌ MCP Server capability (cannot expose itself AS an MCP server)








### CLI vs MCP Philosophy








The MoltBot maintainer prefers CLIs over MCP because:








| Factor | MCP | CLI |
|--------|-----|-----|
| Setup | Server process + protocol | Install + auth once |
| Token cost | Protocol overhead | Just command + output |
| Maintenance | Keep MCP server updated | Vendor maintains CLI |
| Flexibility | Limited to exposed tools | Full CLI capability |








**For ClawdBot:** Since it has shell access, wrapping CLIs in skills is often simpler than MCP integration.








### Potential MCP Server for Supervisor Access








**Discussed:** Building an MCP server so Claude (Opus) could have read-only access to ClawdBot status.








**Decision:** Deferred. Current project file approach works. Would be Category C change requiring full Safe Change Protocol.








**If revisited, scope would be:**
- Read-only: config (sanitized), service status, logs, device list, memory files
- No writes, no commands, no control








---








## Additional Integrations (Ideas)








### Voice Assistant Integration








**Idea:** Connect ClawdBot to voice interfaces (Alexa, Google Home, or local)








**Status:** Not investigated








### Home Automation








**Idea:** Connect to Home Assistant or similar








**Status:** Not investigated. Note: Home Assistant has MCP server support.








### Financial Data Sources








**Idea:** Additional market data APIs beyond current setup








**Status:** Web Scout now provides ITC access. Additional sources TBD.








### Email Automation








**Idea:** Expanded Gmail capabilities (auto-triage, smart replies)








**Status:** Gmail OAuth working. Guardrails in place. Could expand in future.








---








## Guardrails for Publishing Integrations








All publishing integrations (YouTube, Substack, ElevenLabs) should follow:








**Hard Rules (add to AGENTS.md when implemented):**
1. **Publishing requires explicit approval** — No autonomous posting to public platforms
2. **Cost-generating operations require awareness** — ElevenLabs charges per character
3. **Preview before publish** — Content should be reviewable before going live








**Suggested Review Process:**
1. Content generated/formatted
2. Preview surfaced to Rick
3. Explicit approval received
4. Publish executed
5. Confirmation sent








---








## Priority Order (Suggested)








| Priority | Integration | Rationale | Status |
|----------|-------------|-----------|--------|
| ~~1~~ | ~~Headless Browser~~ | ~~Enables data access~~ | ✅ Done (Web Scout) |
| ~~2~~ | ~~Git Backup~~ | ~~Disaster recovery~~ | ✅ Done (2026-01-31) |
| 3 | ElevenLabs | Enables audio sermons, prerequisite for YouTube | Not started |
| 4 | YouTube | Distributes audio content, high visibility | Not started |
| 5 | Substack | Newsletter distribution, lower complexity | Not started |
| 6 | Others | As needed | — |








---








## Implementation Notes








### When Ready to Implement








Each integration should:
1. Get its own skill in `~/clawd/skills/`
2. Have clear guardrails documented
3. Be tested thoroughly before production use
4. Have rollback/undo capability where possible
5. Follow Claude Code governance if code generation needed








### Tracking








When an integration moves from "idea" to "in progress":
1. Update this document with status
2. Create detailed spec if complex
3. Log decision in current-state.md








---








## Open Questions








1. **Substack API availability** — Does it exist? What are the capabilities?
2. **YouTube caption workflow** — Auto-generate vs manual review vs hybrid?
3. **Image sourcing for YouTube** — Manual selection, stock library, AI generation?
4. **Cost monitoring** — How to track ElevenLabs spend over time?
5. **Cross-posting coordination** — Same content to multiple platforms simultaneously?
6. **Trading analysis scope** — What does Rick actually want here?
7. **Chapel schedule workflow** — How does Rick currently manage this?








---








*This document captures ideas for future reference. Items here are not approved or scheduled. Update when decisions are made or priorities change.*