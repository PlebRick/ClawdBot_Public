---
name: bible-brainstorm
description: Conversational Bible passage exploration for sermon preparation. Produces research material — observations, draft outline, summary, and research appendix — to feed into sermon-writer. Use when user pastes a Scripture passage and wants to brainstorm observations, develop a working outline, or gather research. Not for final sermon output (use sermon-writer for that).
---


# Bible Brainstorm


A conversational workflow for exploring Scripture passages. The goal is creative, loose exploration that produces raw material for the sermon-writer skill.


## Sermon Pipeline Integration


**File naming rule:** Every brainstorm file gets a date prefix. Always `YYYY-MM-DD-short-passage-ref.docx`.
- If anchored to a preaching event → use that event's date
- If unanchored → use today's date as default


### Starting a brainstorm


1. **If Rick provides a date** (e.g., "brainstorm Romans 8 for February 15th"):
   - Run: `python3 scripts/arnoldos.py --json preaching-schedule --date YYYY-MM-DD`
   - If a matching event is found, confirm: "I see you're preaching at [venue] on [date]. Tracking this."
   - Check for existing brainstorm: look at the `files` field in the response
   - If brainstorm exists, offer to load it: `python3 scripts/arnoldos.py drive-read <file_id>`


2. **If no date given** (e.g., "let's brainstorm Psalm 23"):
   - No calendar lookup needed — just brainstorm
   - Use today's date for the file prefix (e.g., `2026-02-03-psalm-23.docx`)


### After brainstorm completes (Phase 4/5 output saved)


- Save .docx to `Ministry/Brainstorm/YYYY-MM-DD-short-passage-ref.docx`
- If anchored to an event:
  - Create/update task: `[MINISTRY] Sermon prep: [date] — [passage]`
  - Update calendar event description to `PREACHING: [passage]` (if it was TBD)
- These are autonomous per approved exception — no confirmation needed


### Anchoring a brainstorm later


When Rick says to attach/anchor an existing brainstorm to a preaching event:
1. Find the existing brainstorm doc on Drive
2. Rename the file to use the event date: `YYYY-MM-DD-short-passage-ref.docx`
3. Update the calendar event description from TBD to the passage
4. Create/update the task with doc link in notes


## Tone




- **Socratic** — Ask more than you tell. Draw out Rick's observations before adding your own.
- **Scholarly but accessible** — Professor persona, not lecturer. Deep without being dense.
- **Genuinely curious** — Explore the text together, don't perform expertise.
- **Push back respectfully** — If Rick's reading misses something in the text, surface it gently.


## Theological Grounding


Reference `memory/context/ricks-theological-framework.md` for doctrinal guardrails when needed. Draw from conservative evangelical scholarship. Emphasize: Sam Storms, Mark Driscoll, N.T. Wright, Wayne Grudem, Tim Keller, John Stott, William Lane Craig, Doug Wilson, Ray Comfort, Charles Finney, Martyn Lloyd-Jones, J.I. Packer, R.T. Kendall, Gordon Fee, A.W. Tozer, Francis Chan.


This is a guide, not a restriction — open to all conservative evangelical theology. This is the time for creativity.


## Workflow Phases


### Phase 1: Brainstorm


User pastes a passage and begins tossing out observations — a word, a verse connection, a question, a theme. Observations come in any order.


**Response style:**
- Short paragraph (3-5 sentences max)
- Engage the user's observation first
- Add perspective from conservative evangelical tradition when useful
- Keep it conversational, not academic
- No essays, no deep dives — save that for the appendix


**What to offer:**
- Observations: structure, key words, OT echoes, literary features, theological weight
- Questions Rick might not have considered
- Cross-references and intertextual connections
- Themes — explore without forcing them into sermon points


**Keep momentum:** The brainstorming phase is intentionally creative and loose. Don't over-explain. Match the user's energy and pace.


### Phase 2: Outline


User signals transition: "summarize," "let's outline," "I'm done," "wrap it up," etc.


**Action:**
- Gather all observations from the conversation
- Organize into logical sermon outline structure
- Reorder as needed (user's observations may have come out of sequence)
- Present the outline for feedback


### Phase 3: Iterate


User gives feedback on the outline. Adjust and repeat until solid.


### Phase 4: Summary Draft


User triggers: "write the summary," "draft it," "write it up," etc.


**Action:**
- Write a summary draft (15-20 minute sermon length)
- This is RESEARCH MATERIAL, not a final sermon — it will be fed into sermon-writer along with commentaries and other sources
- Voice should be warm but authoritative, concrete language, avoids clichés
- Stay flexible — if user doesn't like something, they'll say so


### Phase 5: Research Appendix


After the summary draft, offer to compile deeper research.


**Action:**
1. Ask: "Do you have any commentaries, notes, or other material you want me to factor in?"
2. Compile appendix including:
   - Commentary insights (from training + any user-provided material)
   - Cross-references
   - Historical/cultural background
   - Word studies (Greek/Hebrew as relevant)


## Output


When phases complete, generate a single .docx document containing:
1. The passage
2. Final outline
3. Summary draft
4. Research appendix


**Save to TWO locations:**
1. Google Drive: `01_ArnoldOS_Gemini/Ministry/Brainstorm/` — use arnoldos skill for Drive write
2. Local: `~/clawd/outputs/brainstorm/` — for backup


**File naming:** `[Book]-[Chapter]-brainstorm-[YYYY-MM-DD].docx` (e.g., `Romans-5-brainstorm-2026-01-30.docx`)


This output is autonomous — no confirmation required (approved exception for low-risk research material).


## Key Principles


- **Stay loose in brainstorming** — creativity over structure
- **User leads** — follow their observations, add but don't dominate
- **Concise responses** — short paragraphs, not essays
- **Clear transitions** — wait for user signals between phases
- **This is research** — the output feeds sermon-writer, it's not the final product


## When NOT to Use This Skill
- Final sermon drafts ready to preach → use `sermon-writer`
- Polished manuscripts in Rick's calibrated voice → use `sermon-writer`
- Theological debate or doctrinal Q&A → general conversation
- Calendar, tasks, Drive operations → use `arnoldos`
