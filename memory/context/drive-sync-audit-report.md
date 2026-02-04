# Google Drive Sync Audit Report
**Date:** 2026-02-04
**Prepared for:** Supervisor (Opus)
**Author:** ClawdBot


---


## Executive Summary


ClawdBot currently uses **7 sync scripts** to manage content between local storage and Google Drive. These scripts use a mix of **rclone** (raw file copies) and **Python/Drive API** (Google Docs conversion). The recent Voice-Profile migration demonstrated that converting to native Google Docs enables **Claude.ai to read the content directly** via Drive connector.


**Recommendation:** Consolidate all Drive sync operations to use the Python/Drive API pattern established in `voice-profile-sync-v2.py`. This enables bi-directional sync with native Google Docs format.


---


## Current Sync Scripts Inventory


### Scripts That Sync to/from Google Drive


| Script | Local Source | Drive Destination | Direction | Method | Cron Schedule |
|--------|--------------|-------------------|-----------|--------|---------------|
| `voice-profile-sync.sh` | Scattered voice files | `01_ArnoldOS_Gemini/Ministry/Voice-Profile` | Bi-directional | **Python/Drive API** ✅ | `5,20,35,50 * * * *` |
| `arnoldos-sync.sh` | `~/clawd/` | `01_ArnoldOS_Gemini` | Bi-directional | rclone | `*/15 * * * *` |
| `supervisor-sync.sh` | `~/clawd/supervisor-project/` | `02_ClawdBot/supervisor-project` | Bi-directional | rclone | `*/15 * * * *` |
| `sync-memory-to-drive.sh` | `~/clawd/memory/` | `02_ClawdBot/01_Memory` | One-way (push) | rclone | `0 */6 * * *` |
| `sync-projects-to-drive.sh` | `~/Projects/` (whitelist) | `02_ClawdBot/ricks-projects` | One-way (push) | Python | None |
| `sync-supervisor-drive.py` | Parameterized | Parameterized folder ID | One-way (push) | Python/Drive API | None |
| `sync-public-mirror.sh` | `~/clawd/` | GitHub mirror (not Drive) | One-way (push) | rsync/git | `0 */6 * * *` |


### Method Breakdown
- **rclone (raw files):** 3 scripts — `arnoldos-sync.sh`, `supervisor-sync.sh`, `sync-memory-to-drive.sh`
- **Python/Drive API (Docs conversion):** 3 scripts — `voice-profile-sync-v2.py`, `sync-projects-drive.py`, `sync-supervisor-drive.py`
- **Non-Drive (rsync/git):** 1 script — `sync-public-mirror.sh`


---


## Current 02_ClawdBot/ Drive Contents


**Folder ID:** `1CnNSBm2ftNdAHBAHKg2RMbZ4anUeyms9`


| Item | Type | Sync Source | Current Format |
|------|------|-------------|----------------|
| 📁 01_Memory | Folder | `sync-memory-to-drive.sh` | Raw .md files |
| 📁 01_Inbox | Folder | Manual | Unknown |
| 📁 ricks-projects | Folder | `sync-projects-to-drive.sh` | Google Docs ✅ |
| 📁 supervisor-project | Folder | `supervisor-sync.sh` | Raw .md files |
| 📁 Backups | Folder | Manual/archive | Mixed |
| 📝 API Migration Audit Report | Google Doc | Manual | Google Doc ✅ |


### Problem Areas
1. **01_Memory/** — Raw .md files (Claude.ai cannot read)
2. **supervisor-project/** — Raw .md files (Claude.ai cannot read)
3. **No bi-directional sync** except via rclone (which doesn't convert formats)


---


## Detailed Script Analysis


### 1. voice-profile-sync.sh (v2) ✅ MODEL IMPLEMENTATION


**Status:** Production-ready, gold standard


```
Local: ~/clawd/memory/context/, ~/clawd/memory/training/, ~/clawd/skills/sermon-writer/
Drive: 01_ArnoldOS_Gemini/Ministry/Voice-Profile
Direction: Bi-directional
Method: Python/Drive API with format conversion
Files: 48 tracked
```


**Features:**
- .md ↔ Google Docs automatic conversion
- Content hashing for change detection
- Normalized whitespace handling
- State persistence (`~/.config/clawd/voice-sync-state.json`)


### 2. arnoldos-sync.sh


**Status:** rclone, needs migration


```
Local: ~/clawd/
Drive: 01_ArnoldOS_Gemini
Direction: Bi-directional
Method: rclone (raw files)
Excludes: .git, node_modules, logs, __pycache__, *.pyc
```


**Issues:**
- Uploads raw .md files (Claude.ai cannot read)
- Overlaps with voice-profile-sync for Ministry/Voice-Profile subfolder
- No format conversion


### 3. supervisor-sync.sh


**Status:** rclone, needs migration


```
Local: ~/clawd/supervisor-project/
Drive: 02_ClawdBot/supervisor-project
Direction: Bi-directional
Method: rclone (raw files)
Excludes: .git, node_modules, logs, __pycache__, *.pyc
```


**Issues:**
- Uploads raw .md files (Claude.ai cannot read)
- Has `push-file` convenience mode worth preserving


### 4. sync-memory-to-drive.sh


**Status:** rclone, one-way only


```
Local: ~/clawd/memory/ (daily/*.md + *.md in root)
Drive: 02_ClawdBot/01_Memory
Direction: One-way (local → Drive)
Method: rclone sync + copy
```


**Issues:**
- One-way only (no pull capability)
- Raw .md files (Claude.ai cannot read)
- Uses `rclone sync` which deletes Drive files not in local


### 5. sync-projects-to-drive.sh + sync-projects-drive.py


**Status:** Python, partial implementation


```
Local: ~/Projects/ (whitelisted folders only)
Drive: 02_ClawdBot/ricks-projects
Direction: One-way (local → Drive)
Method: Python/Drive API (converts to Docs)
Whitelist: ministry projects only (not dev projects)
```


**Issues:**
- One-way only (no pull)
- Good pattern but not bi-directional


### 6. sync-supervisor-drive.py


**Status:** Python, underused utility


```
Local: Parameterized (any directory)
Drive: Parameterized (folder ID)
Direction: One-way (local → Drive)
Method: Python/Drive API (converts to Docs)
```


**Issues:**
- Generic utility, not integrated into cron
- Could be base for unified sync


---


## Active Cron Jobs


```cron
# Voice Profile (Python, every 15 min offset)
5,20,35,50 * * * * voice-profile-sync.sh sync


# ArnoldOS (rclone, every 15 min)
*/15 * * * * arnoldos-sync.sh sync


# Supervisor (rclone, every 15 min, pull only)
*/15 * * * * supervisor-sync.sh pull


# Memory (rclone, every 6 hours)
0 */6 * * * sync-memory-to-drive.sh


# Public mirror (rsync/git, every 6 hours) - not Drive
0 */6 * * * sync-public-mirror.sh
```


---


## Consolidation Plan


### Goal
All content in `02_ClawdBot/` should be:
1. **Native Google Docs** (not raw .md files)
2. **Bi-directional sync** (pull and push)
3. **Python/Drive API pattern** (like voice-profile-sync-v2.py)


### Phase 1: One-Time Conversion (Est. 1-2 hours)


Convert existing raw .md files in Drive to Google Docs:


| Folder | Est. Files | Action |
|--------|------------|--------|
| 02_ClawdBot/01_Memory | ~100+ | Convert .md → Docs, delete raw |
| 02_ClawdBot/supervisor-project | ~50 | Convert .md → Docs, delete raw |


Use the conversion script pattern from Voice-Profile Phase 1.


### Phase 2: Unified Sync Framework (Est. 2-3 hours)


Create `~/clawd/scripts/clawd-drive-sync.py` — a single configurable script:


```python
# Usage: python3 clawd-drive-sync.py <profile> [pull|push|sync|dry|status]


PROFILES = {
    "voice-profile": {
        "local_root": "~/clawd",
        "drive_folder_id": "1J-sl9LqLKHosR5mDsSh3d9yF7_7eg4U3",
        "file_map": {...},  # existing mappings
        "dir_map": {...},
    },
    "memory": {
        "local_root": "~/clawd/memory",
        "drive_folder_id": "<01_Memory folder ID>",
        "dir_map": {"daily": "daily", "context": "context"},
    },
    "supervisor": {
        "local_root": "~/clawd/supervisor-project",
        "drive_folder_id": "<supervisor-project folder ID>",
        "dir_map": {"": ""},  # entire directory
    },
    "projects": {
        "local_root": "~/Projects",
        "drive_folder_id": "<ricks-projects folder ID>",
        "whitelist": ["ministry-project-1", ...],
    },
}
```


**Features to preserve:**
- `push-file <path>` mode from supervisor-sync.sh
- Whitelist filtering from sync-projects-to-drive.sh
- Excludes patterns (.git, node_modules, etc.)


### Phase 3: Migration Rollout


| Step | Action | Verification |
|------|--------|--------------|
| 1 | Pause rclone crons | `crontab -e` comment out |
| 2 | Run one-time conversion | Check Drive for Docs |
| 3 | Test new sync per profile | `clawd-drive-sync.py <profile> dry` |
| 4 | Update crons to new script | `clawd-drive-sync.py <profile> sync` |
| 5 | Archive old scripts | `mv *.sh scripts/obsolete/` |
| 6 | Monitor for 1 week | Check logs, verify Claude.ai access |


### Phase 4: Cleanup


- Delete `scripts/obsolete/` after 30 days
- Update documentation
- Remove rclone dependency (optional)


---


## Benefits of Consolidation


| Benefit | Impact |
|---------|--------|
| Claude.ai can read all content | Enables AI-assisted editing in Drive |
| Single codebase | Maintain 1 script instead of 7 |
| Bi-directional everywhere | Edit in Drive or locally |
| Faster sync | Direct API vs rclone remote mount |
| Better auth stability | OAuth tokens vs rclone config |
| Change detection | Hash-based, no unnecessary uploads |
| Unified logging | Single log format, easier debugging |


---


## Risks & Mitigations


| Risk | Mitigation |
|------|------------|
| Data loss during conversion | Backup Drive folders first; test on small subset |
| Sync conflicts | Pull-then-push pattern; local wins on conflict |
| API rate limits | Add delays between operations (already in v2) |
| Large files timeout | Chunk uploads; increase timeout for big Docs |


---


## Recommendation


**Proceed with consolidation.** The Voice-Profile migration proved the pattern works. Estimated total effort: **4-6 hours** across 4 phases.


**Immediate next step:** Convert `02_ClawdBot/supervisor-project/` as Phase 1 pilot (smaller than 01_Memory, high visibility for Supervisor testing).


---


## Appendix: File Locations


```
Scripts:
  ~/clawd/scripts/voice-profile-sync-v2.py    # Gold standard
  ~/clawd/scripts/voice-profile-sync.sh       # Wrapper
  ~/clawd/scripts/arnoldos-sync.sh            # To migrate
  ~/clawd/scripts/supervisor-sync.sh          # To migrate
  ~/clawd/scripts/sync-memory-to-drive.sh     # To migrate
  ~/clawd/scripts/sync-projects-to-drive.sh   # Partial, to consolidate
  ~/clawd/scripts/sync-projects-drive.py      # Partial, to consolidate
  ~/clawd/scripts/sync-supervisor-drive.py    # Utility, to consolidate


Config:
  ~/.config/clawd/google-tokens.json          # OAuth tokens
  ~/.config/clawd/voice-sync-state.json       # Sync state (voice)


Logs:
  ~/clawd/logs/voice-sync.log
  ~/clawd/memory/logs/arnoldos-sync.log
  ~/clawd/memory/logs/supervisor-sync.log
  ~/clawd/logs/memory-sync.log
```


---


*Report generated by ClawdBot on 2026-02-04*
