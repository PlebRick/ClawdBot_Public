# Drive Roots Full Audit Report
**Date:** 2026-02-04
**Prepared for:** Supervisor (Opus)


---


## Executive Summary


Audited both Drive roots (`01_ArnoldOS_Gemini` and `02_ClawdBot`) to identify content needing conversion to Google Docs. Found **52 raw .md files** remaining that Claude.ai cannot read. Existing syncs (voice-profile, supervisor, memory) already cover the critical content. Only minor cleanup and one deprecated sync script remain.


---


## 01_ArnoldOS_Gemini (Rick's Personal Drive)


**Root ID:** `12aczo3TPXamKkKQQc2iunPUqvfoBJovG`


### Folder Structure


| Folder | Contents | Status |
|--------|----------|--------|
| `00_Inbox/` | 2 misc files | N/A |
| `Chapel/` | empty | — |
| `Chapel/idoc-chapel-policy/` | 7 Docs, 5 PDFs | ✅ Already Docs |
| `Content Creation/` | empty | — |
| `Dev/` | empty | — |
| `Family/` | empty | — |
| `Images/` | Image subfolders | N/A (not text) |
| `Ministry/Brainstorm/` | 3 Docs | ✅ Already Docs |
| `Ministry/Research/` | 2 Docs + subfolders | ✅ Already Docs |
| `Ministry/Sermons/` | 13 Docs, **1 .md** ⚠️ | Needs cleanup |
| `Ministry/St Peter's Stone Church/` | 4 Docs | ✅ Already Docs |
| `Ministry/Voice-Profile/` | 48 Docs (5 subfolders) | ✅ **Handled by voice-profile-sync** |
| `Personal/` | 1 Doc, **1 .md** ⚠️ | Needs cleanup |
| `Trading/` | 2 Docs | ✅ Already Docs |


### Raw .md Files Found: **2**
- `Ministry/Sermons/` — 1 file
- `Personal/` — 1 file


**Recommendation:** One-time manual conversion (2 files). Not worth a sync script.


---


## 02_ClawdBot (ClawdBot's Drive)


**Root ID:** `1CnNSBm2ftNdAHBAHKg2RMbZ4anUeyms9`


### Folder Structure


| Folder | Contents | Status |
|--------|----------|--------|
| `01_Inbox/` | empty | — |
| `01_Memory/` | 1 .md at root | See below |
| `01_Memory/daily/` | **50 .md** ⚠️ | **EXCLUDED by design** (local-only logs) |
| `01_Memory/daily/context/` | 44 Docs | ✅ **Handled by memory-sync** |
| `01_Memory/daily/todos/` | 3 Docs | ✅ **Handled by memory-sync** |
| `01_Memory/daily/training/` | raw files | ⚠️ Stale (voice-profile-sync uses ArnoldOS) |
| `01_Memory/daily/cache/` | JSON files | N/A (not convertible) |
| `01_Memory/daily/logs/` | log files | N/A (not convertible) |
| `Backups/` | 3 misc files | N/A |
| `ricks-projects/Finney/` | 7 Docs, 2 code | ✅ Already Docs |
| `ricks-projects/amillennialism/` | 1 Doc | ✅ Already Docs |
| `supervisor-project/` | 12 Docs | ✅ **Handled by supervisor-sync** |
| Root level | 2 Docs | ✅ Already Docs |


### Raw .md Files Found: **51**
- `01_Memory/` root — 1 file (MEMORY.md)
- `01_Memory/daily/` — 50 files (daily logs — **excluded by design**)


**Note:** The 50 daily logs in `01_Memory/daily/` were synced by the old rclone script. These are intentionally NOT converted — they're local memory files, not cross-platform reference. The old `sync-memory-to-drive.sh` uploaded them; the new `memory-sync.sh` only syncs `context/` and `todos/`.


---


## Current Sync Coverage


| Sync Script | Scope | Files | Status |
|-------------|-------|-------|--------|
| `voice-profile-sync.sh` | `01_ArnoldOS_Gemini/Ministry/Voice-Profile/` | 48 | ✅ Python/Docs |
| `supervisor-sync.sh` | `02_ClawdBot/supervisor-project/` | 12 | ✅ Python/Docs |
| `memory-sync.sh` | `02_ClawdBot/01_Memory/daily/context/` + `todos/` | 47 | ✅ Python/Docs |
| `arnoldos-sync.sh` | `01_ArnoldOS_Gemini/` (entire) | ? | ⚠️ **Still rclone** |


---


## Remaining Issues


### 1. `arnoldos-sync.sh` — Still rclone
- Syncs entire `~/clawd/` ↔ `01_ArnoldOS_Gemini/`
- Overlaps with `voice-profile-sync` (Ministry/Voice-Profile)
- Uploads raw .md files (doesn't convert to Docs)


**Recommendation:** **Deprecate `arnoldos-sync.sh`**
- Voice-Profile content already covered by dedicated sync
- Other ArnoldOS folders are Rick's personal content (not ClawdBot's concern)
- The 2 stray .md files can be converted manually


### 2. Stale content in `02_ClawdBot/01_Memory/daily/`
- 50 raw .md daily logs from old rclone sync
- `training/` subfolder has stale sermon files (duplicates Voice-Profile)


**Recommendation:** Clean up stale content
- Delete `01_Memory/daily/*.md` (daily logs)
- Delete `01_Memory/daily/training/` (stale duplicates)
- Keep only `context/` and `todos/` (handled by memory-sync)


### 3. Two stray .md files in ArnoldOS
- `Ministry/Sermons/` — 1 file
- `Personal/` — 1 file


**Recommendation:** Convert manually (not worth a sync)


---


## Proposed Action Plan


### Phase 1: Cleanup (5 min)
1. Convert 2 stray .md files in ArnoldOS → Docs
2. Delete stale content in `02_ClawdBot/01_Memory/daily/` (50 .md + training/)


### Phase 2: Deprecate arnoldos-sync (5 min)
1. Remove from cron
2. Move script to `scripts/obsolete/`
3. Voice-profile-sync already covers the important content


### Phase 3: Verify (2 min)
1. Confirm Claude.ai can read all critical content via Drive
2. All syncs running on Python/Docs pattern


---


## Final State (After Cleanup)


| Drive Root | Google Docs | Raw .md | Sync |
|------------|-------------|---------|------|
| `01_ArnoldOS_Gemini/Ministry/Voice-Profile/` | 48 | 0 | voice-profile-sync ✅ |
| `01_ArnoldOS_Gemini/` (other) | ~30 | 0 | N/A (Rick's content) |
| `02_ClawdBot/supervisor-project/` | 12 | 0 | supervisor-sync ✅ |
| `02_ClawdBot/01_Memory/context+todos/` | 47 | 0 | memory-sync ✅ |
| `02_ClawdBot/` (other) | ~10 | 0 | N/A (backups, projects) |
| **TOTAL** | **~147** | **0** | ✅ |


---


## Decision Needed


**Supervisor:** Approve the action plan?


1. ✅ Clean up stale .md files in `02_ClawdBot/01_Memory/daily/`
2. ✅ Convert 2 stray .md files in ArnoldOS
3. ✅ Deprecate `arnoldos-sync.sh` (remove from cron)


Say **"cleanup go"** to execute.


---


*Report generated by ClawdBot on 2026-02-04*
