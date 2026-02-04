# Drive Ministry Folder Reorg Plan
## Status: COMPLETED — Rick's approval before any moves


---


## Current State (messy)


```
Ministry/
├── Brainstorm/                          ← 1 file (pipeline)
│   └── Ephesians-2-brainstorm-2026-01-30.docx
├── Sermons/                             ← 1 file (pipeline)
│   └── 2026-02-15-2-peter-1-draft.docx
├── Research/                            ← 4 files (dupes)
│   ├── Walking_in_the_Spirit_Complete.docx (x2 dupes)
│   └── Walking_in_the_Spirit_Complete_Outline.docx (x2 dupes)
├── St Peter's Stone Church/             ← 14 files (mixed: liturgies, manuscripts, outlines, schedule)
│   ├── 2026 Schedule
│   ├── 2026_Lectionary_Readings_Full_Text.docx
│   ├── 25-12-24-Christmas Eve Service.docx
│   ├── 26-01-11_Liturgy_Baptism_of_the_Lord.docx
│   ├── 26-01-11_Spirit_Filled_Jesus_Manuscript.docx
│   ├── 26-01-11_Spirit_Filled_Jesus_Outline.docx
│   ├── 26-01-18_Liturgy_The Spirit that Remains.docx
│   ├── 26-02-15_The_Spirit_Who_Speaks_2Peter1_16-21.docx
│   ├── February_15_2026_The_Spirit_Who_Speaks.docx
│   ├── Sermon_Jan18_2026_Pulpit_Outline_Final.docx
│   ├── Sermon_Jan18_2026_The_Spirit_Who_Remains.docx
│   ├── Sermon_Outline_Jan18_2026_The_Spirit_Who_Remains.docx
│   ├── Spirit_Filled_Jesus_Manuscript_Trimmed.docx
│   └── The Spirit Who Remains_Outline Final
├── 2026_01_SE_Romans Series/            ← 12 items (passage subfolders + loose files)
│   ├── Archived/
│   ├── Romans 12:1-2/
│   ├── Romans 1:1-7 The Model Missionary/
│   ├── Romans 1:16-17/
│   ├── Romans 1:18-32/
│   ├── Romans 1:8-15 The Heart of a Missionary/
│   ├── Romans 2:1-11/
│   ├── Romans_12_Living_Sacrifice.docx
│   ├── Romans_13-16_Gospel_Shaped_Living.docx
│   ├── Romans_3_21-26_Gold_Standard.docx
│   └── Romans_Series_Framework_v2.md (x2 dupes)
├── Romans 12_1-2_LIving Sacrifices/     ← standalone folder (pre-pipeline AI experiment)
│   ├── Claude Output/
│   ├── Gemini Output/
│   ├── Grok Output/
│   ├── Merged_Final/
│   └── Original Material/
├── Jesus_Our_Wonderful_Savior_Sermon (1).md    ← loose file
├── John_4_Evangelism_Jesus_Way_Complete.docx    ← loose file
├── The Spirit Who Remains                       ← loose file (GDoc)
├── The_Praying_Jesus_Deep_Dive_Sermon.docx     ← loose file
└── True_False_Repentance_Sermon.docx           ← loose file
```


---


## Proposed Target State (clean)


```
Ministry/
├── Brainstorm/                          ← all brainstorm output (date-prefixed)
├── Sermons/                             ← all drafts & finals (date-prefixed, -draft/-final suffix)
├── Research/                            ← reference material, commentaries, deep dives (deduped)
├── St Peter's Stone Church/             ← church-specific ONLY: schedule, lectionary, liturgies
└── Series/
    └── 2026_Romans/                     ← archived series material (framework, passage folders)
```


---


## File-by-File Migration Plan


### LOOSE FILES IN MINISTRY ROOT → move to proper folders


| File | Current Location | Move To | Rationale |
|------|-----------------|---------|-----------|
| Jesus_Our_Wonderful_Savior_Sermon (1).md | Ministry/ (root) | Sermons/ | It's a sermon |
| John_4_Evangelism_Jesus_Way_Complete.docx | Ministry/ (root) | Sermons/ | It's a sermon |
| The Spirit Who Remains (GDoc) | Ministry/ (root) | Sermons/ | It's a sermon |
| The_Praying_Jesus_Deep_Dive_Sermon.docx | Ministry/ (root) | Sermons/ | It's a sermon |
| True_False_Repentance_Sermon.docx | Ministry/ (root) | Sermons/ | It's a sermon |


### ST PETER'S STONE CHURCH → keep church ops, move sermons out


| File | Action | Move To | Rationale |
|------|--------|---------|-----------|
| 2026 Schedule | **KEEP** | stays | Church ops |
| 2026_Lectionary_Readings_Full_Text.docx | **KEEP** | stays | Church reference |
| 25-12-24-Christmas Eve Service.docx | **MOVE** | Sermons/ | It's a sermon/service |
| 26-01-11_Liturgy_Baptism_of_the_Lord.docx | **KEEP** | stays | Liturgy = church ops |
| 26-01-11_Spirit_Filled_Jesus_Manuscript.docx | **MOVE** | Sermons/ | Sermon manuscript |
| 26-01-11_Spirit_Filled_Jesus_Outline.docx | **MOVE** | Sermons/ | Sermon outline |
| 26-01-18_Liturgy_The Spirit that Remains.docx | **KEEP** | stays | Liturgy = church ops |
| 26-02-15_The_Spirit_Who_Speaks_2Peter1_16-21.docx | **MOVE** | Sermons/ | Sermon (pre-pipeline version) |
| February_15_2026_The_Spirit_Who_Speaks.docx | **MOVE** | Sermons/ | Duplicate/earlier version — move, may trash later |
| Sermon_Jan18_2026_Pulpit_Outline_Final.docx | **MOVE** | Sermons/ | Sermon outline |
| Sermon_Jan18_2026_The_Spirit_Who_Remains.docx | **MOVE** | Sermons/ | Sermon manuscript |
| Sermon_Outline_Jan18_2026_The_Spirit_Who_Remains.docx | **MOVE** | Sermons/ | Sermon outline |
| Spirit_Filled_Jesus_Manuscript_Trimmed.docx | **MOVE** | Sermons/ | Sermon manuscript |
| The Spirit Who Remains_Outline Final | **MOVE** | Sermons/ | Sermon outline |


**St Peter's after cleanup:** 4 files (schedule, lectionary, 2 liturgies)


### RESEARCH → deduplicate


| File | Action | Rationale |
|------|--------|-----------|
| Walking_in_the_Spirit_Complete.docx (x2) | **KEEP 1, TRASH 1** | Duplicate |
| Walking_in_the_Spirit_Complete_Outline.docx (x2) | **KEEP 1, TRASH 1** | Duplicate |


### ROMANS SERIES FOLDER → move under Series/


| Item | Action | Rationale |
|------|--------|-----------|
| Entire `2026_01_SE_Romans Series/` folder | **RENAME** to `Series/2026_Romans/` | Series archive, not active pipeline |
| `Romans_Series_Framework_v2.md` (x2) | **KEEP 1, TRASH 1** | Duplicate |


### ROMANS 12 STANDALONE FOLDER → archive into series


| Item | Action | Rationale |
|------|--------|-----------|
| `Romans 12_1-2_LIving Sacrifices/` | **MOVE** into `Series/2026_Romans/` | It's part of the Romans series, pre-pipeline AI experiment |


---


## Questions for Rick Before Executing


1. **Christmas Eve service** — is that a full sermon or more of a liturgy/service order? If liturgy, it stays in St. Peter's.
2. **The two Spirit Who Speaks files** in St. Peter's (26-02-15 version + February_15 version) — are these different drafts or duplicates? Keep both or trash one?
3. **Romans 12 standalone folder** (Claude/Gemini/Grok outputs) — archive into Series, or trash entirely since it was an early experiment?
4. **Series/ subfolder** — do you want a top-level `Series/` folder, or just rename the existing Romans folder in place?
5. **Renaming old files** — want me to standardize the naming on moved files to match the pipeline convention (`YYYY-MM-DD-passage-ref-type.docx`), or leave original names?
