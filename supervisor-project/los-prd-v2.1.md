# Life Operating System PRD

## ClawdBot Content & Configuration Architecture

**Version**: 2.1
**Date**: January 29, 2026
**Author**: Claude (Opus) as ClawdBot Supervisor
**Owner**: Rick (Chaplain)
**Status**: ✅ COMPLETE — January 30, 2026

> **Completion Notice:** Phases 0-2 delivered the core system. Phase 3 was redistributed to the Future Integrations Roadmap. Phase 4 (Optimization) is ongoing continuous improvement, not a milestone.
>
> **Future feature planning:** See `future-integrations-roadmap.md`

---

## Executive Summary

Rick has built multiple specialized AI projects across Claude, Gemini, and other platforms — each trained for specific domains of his life. These include sermon writing (voice-trained), liturgy preparation, Bible meditation/brainstorming, retirement investing, YouTube content, and life management (ArnoldOS).

The problem: **Every conversation starts from scratch.** Context doesn't flow between projects. Rick re-explains himself constantly.

This PRD defined the **content and configuration** needed to transform ClawdBot into a unified Life Operating System.

**Critical insight from ClawdBot:** The infrastructure already exists. ClawdBot has auto-injected identity files, a production skill system with LLM-native detection, hybrid vector+keyword memory search, sub-agent orchestration, and scheduled jobs. What's missing is the *content* that fills these structures — Rick's identity depth, domain-specific skills, and the voice profile trapped in a Grok chat.

This was not an architecture build. This was a content population project.

**It is now complete.**

---

## Design Principles

### 1. Use What Exists
ClawdBot's infrastructure is production-ready. Don't build parallel systems.

### 2. Descriptions Are Detection Rails
The skill `description` field is the trigger mechanism. LLM reads all descriptions and decides which skill applies. A well-written description *is* the routing logic.

### 3. Identity Is Always Present
Bootstrap files (`AGENTS.md`, `SOUL.md`, `USER.md`, etc.) auto-inject every session. Rick never re-explains who he is.

### 4. Token-Efficient Depth
Keep auto-injected files lean with pointers to searchable depth. `USER.md` stays ~2-3K chars; comprehensive content lives in `memory/context/` files loaded on demand.

### 5. Skills Load on Trigger
Skill bodies load only when the description matches. One skill at a time. ~500 lines max per skill body.

### 6. Sub-Agents for Parallel Work
Workflows chain through sub-agents writing to shared files, not skill-to-skill calls. Main agent orchestrates. Task descriptions must include context since sub-agents don't inherit `SOUL.md` or `USER.md`.

### 7. Voice Profile Is the Bottleneck
Everything else is plumbing. The Grok harvest (1,354 remaining messages) contains Rick's actual voice — how he tells stories, preaches, argues, applies scripture. This is the critical path.

---

## What Already Exists

### Auto-Injected Every Session (No Work Needed)

| File | Purpose | Max Size | Status |
|------|---------|----------|--------|
| `AGENTS.md` | Operating rules, hard constraints | 20K chars | ✅ Exists |
| `SOUL.md` | Persona, tone, voice | 20K chars | ✅ Exists |
| `USER.md` | User profile (lean + pointers) | 20K chars | ✅ Enriched |
| `IDENTITY.md` | Agent identity | 20K chars | ✅ Exists |
| `TOOLS.md` | Tool usage guidance | 20K chars | ✅ Exists |
| `HEARTBEAT.md` | Scheduled tasks | 20K chars | ✅ Exists |
| Skill descriptions | All skills' frontmatter | ~100 words each | ✅ Working |

### On-Demand Systems (No Work Needed)

| System | Mechanism | Status |
|--------|-----------|--------|
| Skill detection | LLM matches request to skill descriptions | ✅ Production |
| Skill loading | `read` tool fetches SKILL.md body on trigger | ✅ Production |
| Memory search | Hybrid 70% vector + 30% keyword | ✅ Production |
| Memory retrieval | `memory_get` for surgical file extraction | ✅ Production |
| Sub-agents | `sessions_spawn` with automatic announce | ✅ Production |
| Scheduled jobs | `cron` for time-based workflows | ✅ Production |
| File sharing | Shared workspace for sub-agent handoff | ✅ Production |
| Morning brief cron | ArnoldOS integrated | ✅ Running |

### ArnoldOS Integration

| Component | Status | Notes |
|-----------|--------|-------|
| `arnoldos.py` script | ✅ Built & tested | Phase 2 Supervised Writes active |
| arnoldos skill | ✅ Complete | 10/10 detection prompts passed |
| Proving period | 🟡 Active | Started January 29, tracking through ~Feb 12 |
| Proving log | ✅ Active | `memory/arnoldos-proving-log.md` |

### Available Skills (52 Bundled + 4 Custom)

**Custom workspace skills built:**
- `arnoldos` — Google integration + domain routing ✅
- `sermon-writer` — Voice profile + theological framework ✅
- `bible-brainstorm` — Scripture meditation and research ✅
- `web-scout` — Headless browser automation ✅

**Bundled skills relevant to LOS:**
- `skill-creator` — Template for building custom skills
- `weather` — Morning brief component
- `bird` — X/Twitter integration
- `summarize` — Content summaries
- `session-logs` — Search past conversations
- `github` — Dev domain

---

## What Was Created

### 1. Enriched Identity Content ✅

**File:** `USER.md` — Enriched to 2.7K chars with 10 depth pointers
**File:** `memory/context/ricks-bio.md` — Expanded biographical profile
**File:** `memory/training/voice-profile.md` — 28K comprehensive voice profile from Grok harvest
**File:** `memory/training/ai-voice-calibration.md` — 25-item Rick Test for voice matching
**File:** `memory/context/ricks-theological-framework.md` — Theological positions documented

### 2. Custom Skills ✅

| Skill | Domain | Status | Notes |
|-------|--------|--------|-------|
| `arnoldos` | All | ✅ Complete | Phase 2 supervised writes active |
| `sermon-writer` | Ministry | ✅ Complete | 10/10 detection, 3.5/5 voice rating |
| `bible-brainstorm` | Ministry | ✅ Complete | All 5 phases tested, .docx output |
| `web-scout` | All | ✅ Complete | 4 targets: CNN, ITC, Logos, Finney |

**Phase 3 skills moved to Future Integrations Roadmap:**
- `morning-brief` — Not needed, cron already running
- `trading-analysis` — Needs portfolio scope definition
- `chapel-schedule` — Needs separate PRD and workflow discovery

### 3. Voice Profile ✅

**Source:** Grok "Mika" chat — 1,654 messages extracted and processed

**Deliverables created:**

| File | Purpose | Size |
|------|---------|------|
| `memory/training/voice-profile.md` | Comprehensive, searchable | 28K |
| `memory/training/ai-voice-calibration.md` | Training guide with Rick Test | 7K |
| `skills/sermon-writer/references/voice-card.md` | Condensed for skill context | ~95 lines |
| `skills/sermon-writer/references/voice-phrases.md` | Phrase catalog by function | ~150 lines |

**Voice profile validation:** Rick scored sermon output 3.5/5 (above ≥3 threshold)

---

## Architecture Mapping

| LOS Concept | ClawdBot Implementation |
|-------------|------------------------|
| Layer 1: Identity | Bootstrap files (`USER.md`, `SOUL.md`, etc.) — auto-injected |
| Layer 2: Domain Map | `arnoldos` skill + `arnoldos.py` resource mapping |
| Layer 3: Detection Rails | Skill `description` fields — LLM-native matching |
| Layer 4: Skills | Custom skills in `~/clawd/skills/` |
| Layer 5: Workflows | Sub-agents (`sessions_spawn`) + file handoff + cron |

**Key insight:** The "manifest + rails + selective loading" architecture Rick envisioned is exactly how ClawdBot already works:
- Manifest = `<available_skills>` XML block (auto-generated)
- Rails = `description` field per skill
- Selective loading = SKILL.md body loaded only on trigger

---

## Workflow Patterns

### Pattern 1: Sequential Skill Loading

Most common. Main agent loads skills one at a time within a session.

```
User: "Let's brainstorm Romans 8"
→ ClawdBot detects bible-brainstorm skill → loads → executes

User: "I'm ready to draft the sermon"
→ ClawdBot detects sermon-writer skill → loads → executes

User: "Schedule prep time for Sunday"
→ ClawdBot detects arnoldos skill → loads → creates calendar event
```

### Pattern 2: Sub-Agent for Heavy Lifting

For parallel work or isolated processing.

```
User: "Generate my morning brief"
→ ClawdBot loads morning-brief skill
→ Spawns sub-agents in parallel:
  - Sub-agent 1: Fetch calendar events (all 7 domains)
  - Sub-agent 2: Fetch priority tasks
  - Sub-agent 3: Get market data
→ Each sub-agent writes results to temp files
→ Main agent assembles into briefing
```

**Note:** Sub-agents don't inherit `SOUL.md` or `USER.md`. Task descriptions must include sufficient context about Rick's identity and what patterns to look for.

### Pattern 3: Scheduled Workflows (Cron)

```
Cron job at 5:30 AM:
→ Existing morning brief script runs
→ Pulls ArnoldOS data via arnoldos.py
→ Generates briefing
→ Sends to Telegram
```

### Sub-Agent Constraints

| Inherited | NOT Inherited |
|-----------|---------------|
| `AGENTS.md` + `TOOLS.md` | `SOUL.md`, `USER.md`, `IDENTITY.md` |
| All tools | Parent's conversation history |
| All skills | Ability to spawn sub-agents |
| Shared file system | Direct user messaging |
| Memory search | |

**Handoff:** Sub-agents write files → main agent reads files. Automatic announce when complete.

---

## Implementation Phases — FINAL STATUS

### Phase 0: Unblock Grok Harvest ✅ COMPLETE
- [x] Chrome relay reconnected
- [x] Extraction resumed and completed

### Phase 1: Foundation ✅ COMPLETE
- [x] Complete Grok extraction (all 1,654 messages)
- [x] Filter and categorize content
- [x] Assemble voice profile (comprehensive + condensed)
- [x] Enrich `USER.md` (2.7K chars, Rick-approved)
- [x] Create `arnoldos` skill
- [x] Test skill triggering (10/10)
- [x] Verify morning brief with ArnoldOS data

### Phase 2: Ministry Skills ✅ COMPLETE
- [x] Create `sermon-writer` skill with voice-card reference
- [x] Create `voice-phrases.md` catalog
- [x] Create `bible-brainstorm` skill
- [x] Test skill triggering (10/10 both skills)
- [x] Voice matching evaluation by Rick (3.5/5)
- [x] Sequential workflow test (brainstorm → sermon → schedule)

### Phase 3: Remaining Skills ❌ CLOSED
Items redistributed to Future Integrations Roadmap:
- `morning-brief` skill — Not needed, cron already running
- `trading-analysis` skill — Needs portfolio scope definition
- `chapel-schedule` skill — Needs separate PRD and workflow discovery

### Phase 4: Optimization 🔄 ONGOING
- [x] Voice calibration (8/10 achieved, 3.5/5 sermon rating)
- [ ] Skill description tuning (as needed)
- [ ] Gemini retirement decision (deferred)
- [ ] Voice profile refinement from actual sermon use

---

## File Structure — FINAL STATE

```
~/clawd/
├── AGENTS.md                    # Operating rules (auto-injected)
├── SOUL.md                      # Persona (auto-injected)
├── USER.md                      # User profile (auto-injected) ✅ Enriched
├── IDENTITY.md                  # Agent identity (auto-injected)
├── TOOLS.md                     # Tool guidance (auto-injected)
├── HEARTBEAT.md                 # Scheduled tasks (auto-injected)
├── MEMORY.md                    # Long-term curated memory
├── memory/
│   ├── YYYY-MM-DD.md            # Daily logs
│   ├── arnoldos-proving-log.md  # ArnoldOS proving log (active)
│   ├── context/
│   │   ├── ricks-bio.md                    # Biographical profile ✅ Expanded
│   │   ├── ricks-theological-framework.md  # Theology ✅ Complete
│   │   ├── arnoldos-integration-prd.md     # Domain mapping ✅ Complete
│   │   ├── supervisor-docs/                # Claude (Opus) reference docs ✅ New
│   │   └── voice-profile.md               # Pointer to training/ ✅ Complete
│   └── training/
│       ├── voice-profile.md               # 28K comprehensive ✅ Complete
│       └── ai-voice-calibration.md        # Rick Test ✅ Complete
├── skills/
│   ├── arnoldos/
│   │   └── SKILL.md                       # ✅ Complete
│   ├── sermon-writer/
│   │   ├── SKILL.md                       # ✅ Complete
│   │   └── references/
│   │       ├── voice-card.md              # ✅ Complete
│   │       └── voice-phrases.md           # ✅ Complete
│   ├── bible-brainstorm/
│   │   └── SKILL.md                       # ✅ Complete
│   └── web-scout/
│       ├── SKILL.md                       # ✅ Complete
│       ├── lib/                           # Session, cookies, navigation
│       ├── profiles/                      # CNN, ITC, Logos, Finney
│       ├── scripts/                       # Cookie extraction
│       └── cookies/                       # Gitignored, chmod 600
└── outputs/
    └── brainstorm/                        # Bible brainstorm .docx outputs
```

---

## Success Metrics — FINAL STATUS

### Milestone 1: "Grok Complete" ✅
- [x] All 1,654 messages extracted
- [x] Filtering complete (7 category files)
- [x] Voice profile assembled (both versions)

### Milestone 2: "Identity Depth" ✅
- [x] `USER.md` enriched and Rick-approved
- [x] Voice profile validation passed (3.5/5 ≥3)
- [x] ClawdBot greets Rick appropriately

### Milestone 3: "ArnoldOS Works" ✅
- [x] `arnoldos` skill triggers correctly
- [x] Morning brief works with ArnoldOS data
- [x] Domain routing functions properly

### Milestone 4: "Ministry Pipeline" ✅
- [x] Sermon drafts match Rick's preaching voice (3.5/5)
- [x] Brainstorm sessions feel like collaboration
- [x] Workflow chains naturally

### Milestone 5: "System Complete" ✅ (Redefined)
- [x] 4 custom skills operational (arnoldos, sermon-writer, bible-brainstorm, web-scout)
- [x] Cron jobs running (morning brief, weekly market report)
- [x] Remaining skills moved to Future Integrations (appropriate given current state)

### Long-term Success (Ongoing)
- Rick stops re-explaining himself ✅
- Context compounds over time 🔄
- New skills added following established patterns 🔄
- Gemini retired for operational tasks (decision deferred)

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation | Status |
|------|------------|--------|------------|--------|
| Voice profile captures conversational not preaching voice | High | Medium | Set expectations; iterate with sermon feedback | ✅ Mitigated (3.5/5) |
| Skill descriptions too vague/narrow | Medium | Medium | Testing protocol with 10 prompts per skill; tune and retest | ✅ Mitigated |
| Grok chat DOM changed | Low | High | Debug extraction JavaScript if needed | ✅ Not encountered |
| Chrome relay won't reconnect | Low | High | Manual extraction fallback | ✅ Reconnected |
| Sub-agent coordination fails | Low | Medium | Fall back to sequential execution | ✅ Working |
| Week 1 too ambitious | Medium | Low | Week 1a/1b split allows sliding | ✅ Completed |
| Token bloat from skills | Low | Medium | Enforce 500-line limit, use references/ for large content | ✅ Managed |

---

## Skill Template

Based on `skill-creator` documentation:

```yaml
---
name: skill-name
description: One clear sentence that triggers this skill. This is the detection rail.
metadata:
  clawdbot:
    emoji: "🎯"
---
```

# Skill Name

## Purpose
What this skill does and when to use it.

## Methodology
Step-by-step process.

## Deliverables
What outputs this skill produces.

## Examples
Concrete examples of inputs and outputs.

## Handoff Points
When to suggest other skills:
- "Schedule this" → arnoldos skill
- "Draft the sermon" → sermon-writer skill

**Critical:** The `description` field must be precise. It's how ClawdBot decides to load this skill. Too vague = false positives. Too narrow = missed triggers.

### Skill Testing Protocol

After creating each skill, test with 10 natural language prompts:
- 5 prompts that SHOULD trigger the skill
- 5 prompts that should NOT trigger the skill

Document results. If false positives or missed triggers occur, tune the description and retest.

---

## Token Budget

| Context | Size | When Loaded |
|---------|------|-------------|
| Bootstrap files (7) | Up to 140K chars total | Every session, automatic |
| Skill descriptions (all) | ~100 words each | Every session, automatic |
| One skill body | ~500 lines recommended | On trigger only |
| Memory search results | 6 chunks × ~700 chars | On demand |

**Baseline per session:** ~4K tokens (bootstrap + descriptions)
**With one skill loaded:** ~7-10K tokens
**With memory search:** +2-3K tokens

Substantial headroom remains for conversation.

**Token efficiency strategy:**
- `USER.md` stays lean (~2-3K chars) with pointers
- Depth lives in `memory/context/` files (loaded on demand)
- Voice profile split: comprehensive (searchable) + condensed (skill reference)

---

## ClawdBot's Warnings (Incorporated)

From Prompt 2 response:
1. **"Don't over-engineer"** — This PRD focuses on content, not new systems ✓
2. **"Voice profile is the bottleneck"** — Phase 0 unblocks Grok harvest first ✓
3. **"80% of value from three things"** — Deep identity, ArnoldOS integrated, voice captured ✓
4. **"Manifest bloat"** — Keep descriptions lean, one sentence each ✓
5. **"Where does Gemini fit?"** — Decision deferred to Phase 2 ✓

From Prompt 3 feedback:
6. **"USER.md token efficiency"** — Lean summary with pointers, not comprehensive dump ✓
7. **"Voice profile dual location"** — Comprehensive + condensed versions ✓
8. **"Morning brief is cron enhancement"** — Phase 1 enhances existing, skill in Phase 3 ✓
9. **"ArnoldOS proving already running"** — Acknowledged as parallel track ✓
10. **"Sub-agent bootstrap gap"** — Rich task descriptions to compensate ✓
11. **"Skill testing protocol"** — Added 10-prompt testing requirement ✓
12. **"Voice profile validation"** — Added 3-sample scoring step ✓
13. **"gog CLI decision"** — Deferred to end of Phase 2 ✓

---

## Appendix A: Grok Harvest — COMPLETE

**Source:** Grok "Mika" chat via Chrome relay
**Final status:** All 1,654 messages extracted and processed

**Deliverables produced:**
- `memory/training/voice-profile.md` (28K comprehensive)
- `memory/training/ai-voice-calibration.md` (7K training guide)
- `skills/sermon-writer/references/voice-card.md` (~95 lines condensed)
- `skills/sermon-writer/references/voice-phrases.md` (~150 lines catalog)
- 17 sermons archived in `memory/training/sermon-archive/`

---

## Appendix B: ArnoldOS Resource Mapping

Full details in `memory/context/arnoldos-integration-prd.md`.

**Summary:**

| Domain | Calendar | Task Tag | Drive Folder |
|--------|----------|----------|--------------|
| Ministry | Ministry | `[MINISTRY]` | `/Ministry/` |
| Chapel | 2026 Chapel Schedule | `[CHAPEL]` | `/Chapel/` |
| Trading | Trading | `[TRADING]` | `/Trading/` |
| Dev | Dev | `[DEV]` | `/Dev/` |
| Family | Family | `[FAMILY]` | `/Family/` |
| Personal | Primary | `[PERSONAL]` | `/Personal/` |
| Content | (uses Personal) | `[CONTENT]` | `/Content/` |

**Current phase:** Phase 2 Supervised Writes (started January 29, 2026)

---

## Appendix C: Related Documents

| Document | Purpose | Location |
|----------|---------|----------|
| Supervisor Current State | Operational status | Project file |
| Safe Change Protocol | Category A/B/C procedures | Project file |
| Technical Reference | Deep architecture | Project file |
| Future Integrations Roadmap | Planned expansions | `memory/context/future-integrations-roadmap.md` |
| Claude Code Governance | CC-A/B/C procedures | `memory/context/claude-code-governance.md` |

---

*Document Status: ✅ COMPLETE — January 30, 2026*
*This PRD is closed. Future work is tracked in the Future Integrations Roadmap.*