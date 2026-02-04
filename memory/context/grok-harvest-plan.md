I'll analyze the constraints and design a strategy for this harvesting task.


# Plan: Harvesting Rick's Grok Chat with Mika1


## Core Challenge


The chat is enormous and browser snapshots are context-destroying (~200K per full snapshot). We need a **streaming extraction pipeline** that processes small chunks, saves immediately to disk, and never holds more than one chunk in memory/context at a time.


---


## Phase 0: Setup & Reconnaissance


1. Create directory structure:
   ```
   /home/ubuntu76/clawd/rick_profile/
   ├── raw/          # Raw extracted chunks
   ├── organized/    # Categorized content
   └── profile.md   # Final assembled profile
   ```


2. Take a **screenshot** (NOT snapshot) of the Grok chat to understand UI layout — button locations, scroll behavior, message structure. Screenshots are much smaller than snapshots.


3. Determine:
   - How to scroll to the top (oldest messages)
   - Message element selectors for extraction
   - Whether we can select/copy text vs. need OCR from screenshots


---


## Phase 1: Navigation to Chat Start


1. Scroll to the **very top** of the chat to begin from the oldest messages
2. Use keyboard shortcut `Home` or repeated `Page Up` to get there
3. Confirm we're at the top via a small screenshot


---


## Phase 2: Chunk-by-Chunk Extraction


**Key principle: Never take a full snapshot. Use targeted JavaScript extraction via `act` tool to pull text only.**


### Per-chunk loop:


1. **Extract via JS** — Use `act` with a JavaScript snippet to grab visible message text elements, returning plain text only (no DOM/HTML bloat). Example approach:
   ```js
   // Select visible messages, return text content only
   Array.from(document.querySelectorAll('[message-selector]'))
     .map(el => el.textContent).join('\n---\n')
   ```
   Adapt selector based on Phase 0 recon.


2. **Save raw chunk** to `/rick_profile/raw/chunk_NNN.txt` immediately


3. **Scroll down** one page worth of messages


4. **Check for overlap** — include a few lines from previous chunk end to detect duplicates and confirm continuity


5. **Check for end** — detect if we've reached the bottom of the chat


6. Repeat until end of chat


### Naming: `chunk_001.txt`, `chunk_002.txt`, etc.


### Error handling:
- If a chunk comes back empty, retry once, then screenshot to diagnose
- If scroll doesn't advance (stuck), try alternative scroll method
- Save a `progress.txt` file with last chunk number so we can resume


---


## Phase 3: Filtering & Categorization


Use **sub-agents** (Task tool) to process each raw chunk file. Each agent reads one chunk from disk and writes categorized output. This keeps context small per agent.


### Categories to extract:
- **life_story.md** — Biographical events, childhood, family, timeline
- **missions.md** — Missionary work, locations, experiences
- **sermons.md** — Sermon content, outlines, teachings
- **theology.md** — Theological positions, discussions, beliefs
- **relationships.md** — Key people, family details, friendships
- **personal_traits.md** — Personality, preferences, habits, values
- **other_notable.md** — Anything meaningful that doesn't fit above


### Agent prompt template:
> Read `/rick_profile/raw/chunk_NNN.txt`. Extract ONLY meaningful content (life events, stories, beliefs, sermons, history, relationships). SKIP casual filler ("hey", "lol", "thanks", small talk). Append relevant content to the appropriate category file under `/rick_profile/organized/`. Prefix each entry with `[Chunk NNN]` for traceability.


### Parallelism: Run 2-3 agents concurrently on different chunks to speed up.


---


## Phase 4: Profile Assembly


1. Read all organized category files
2. Use a sub-agent to **deduplicate** (overlap extraction may cause repeats)
3. Use a sub-agent to **assemble `profile.md`** — a single structured document:


```markdown
# Rick's Personal Profile


## Biography & Timeline
## Family & Relationships
## Missionary Work
## Sermons & Teachings
## Theological Positions
## Character & Values
```


---


## Context Management Rules


| Rule | Why |
|------|-----|
| NEVER use full browser `snapshot` | Blows context (~200K) |
| Use `screenshot` only for navigation/debugging | Images are smaller |
| Use `act` with JS to extract **text only** | Minimal context footprint |
| Save every chunk to disk immediately | Don't hold data in context |
| Use sub-agents for processing | Each gets fresh context |
| Never read more than 1 chunk at a time in main thread | Prevents buildup |


---


## Risk Mitigations


- **Chat too long / times out**: `progress.txt` tracks position; we resume from last chunk
- **JS selector wrong**: Phase 0 recon catches this early; fallback to screenshot + manual reading
- **Grok UI changes mid-session**: Re-screenshot and adapt selectors
- **Duplicate content from overlap**: Dedup pass in Phase 4
- **Browser disconnects**: Save state frequently; reconnect and scroll to last known position


---


## Estimated Chunk Count


If each visible page holds ~20-30 messages and the chat spans days of voice conversation, expect **50-200+ chunks**. The pipeline is designed to handle this without context issues.
