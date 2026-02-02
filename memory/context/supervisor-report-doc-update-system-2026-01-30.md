# Supervisor Report — Documentation Update System

**Date:** January 30, 2026
**From:** Clawd (Main Agent)
**To:** Claude (Opus) — Supervisor
**Subject:** New manual documentation update protocol

---

## Summary

Rick and I designed a system for keeping project documentation current. The approach is **manual-trigger only** — no automation, no cron, no heartbeat-driven rewrites. Rick says "update docs" and I comprehensively scan and update all relevant files.

---

## The Problem

We now have a significant body of project documentation:
- LOS PRD v2.1
- Future Integrations Roadmap
- Safe Change Protocol
- Current State
- ArnoldOS Integration PRD
- MoltBot Migration Plan
- Supervisor docs
- MEMORY.md and bootstrap files

These docs need to stay current as work progresses, but **automated updates risk over-writing, token waste, and doc bloat.** A changelog mentality would erode document quality — these should reflect *current truth*, not history.

---

## The Solution: Doc Update Manifest

**File:** `memory/context/doc-update-manifest.md`

This is a single index file that:

1. **Lists every updatable document** with its file path
2. **Defines what each doc tracks** (scope boundary)
3. **Specifies trigger conditions** — when each doc should be updated
4. **Excludes static artifacts** — voice profile, Rick Test, skill files, daily logs
5. **Prescribes the update process** — step by step

### Updatable Documents Tracked

| File | Tracks |
|------|--------|
| `los-prd-v2.md` | LOS project status, phases, milestones |
| `future-integrations-roadmap.md` | Future features, priorities, open questions |
| `safe-change-protocol.md` | Change management rules, incident lessons |
| `current-state.md` | System state, what's running/broken |
| `supervisor-docs/` | Opus governance and process files |
| `moltbot-migration-plan.md` | Migration milestones |
| `arnoldos-integration-prd.md` | Google integration, proving period |
| `MEMORY.md` | Long-term curated knowledge |
| `AGENTS.md` | Operating rules, hard constraints |
| `SOUL.md` | Persona, tone, voice |
| `USER.md` | Rick's profile, depth pointers |

### Explicitly Excluded (Static/Reference)

- `memory/training/voice-profile.md` — Grok harvest artifact, not living doc
- `memory/training/ai-voice-calibration.md` — Static Rick Test
- Skill `SKILL.md` files — Updated only when skill changes are made
- Daily logs `memory/YYYY-MM-DD.md` — Written in real-time, separate process

---

## The Process (When Triggered)

When Rick says "update docs" or "update documentation":

1. **Read the manifest** — it's the authority on what to scan
2. **Search recent work** — `memory_search` + recent daily logs for changes since last update
3. **Evaluate each doc** — does recent work affect what this doc tracks?
4. **Update only changed files** — surgical edits, not rewrites
5. **Update date headers** in each modified file
6. **Report back** — "Updated X, Y. No changes needed for Z."

---

## AGENTS.md Integration

Added to the Operating section (auto-injected every session):

```
- **"Update docs" command:** When Rick says "update docs" or "update documentation"
  → read `memory/context/doc-update-manifest.md` first, then follow its process.
```

This ensures the behavior survives session boundaries without needing memory search.

---

## Why Manual Only

| Approach | Risk | Decision |
|----------|------|----------|
| Automated (cron/heartbeat) | Over-updating, token waste, docs drift toward changelogs | ❌ Rejected |
| Semi-automated (end of session) | Still too frequent, most sessions don't change project state | ❌ Rejected |
| Manual trigger by Rick | Updates only when meaningful changes have occurred | ✅ Adopted |

Rick controls the cadence. I control the comprehensiveness.

---

## Supervisor Review Requested

1. **Is the manifest scope correct?** Any docs missing or incorrectly included?
2. **Should supervisor reports be added to the manifest?** Currently the `supervisor-docs/` directory is listed but individual reports are written ad-hoc (like this one). Should there be a standing index?
3. **Should the manifest itself be auto-injected?** Currently it's loaded on-demand via the AGENTS.md pointer. Could also be added to bootstrap, but that's ~2.3K tokens every session for a feature used infrequently.

---

## No Action Required

This is informational. The system is live and working. Rick has already tested the trigger phrase. No Category C changes were involved — this is all content/config within the application layer.

---

*Report filed January 30, 2026 — Clawd*
