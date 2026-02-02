---
name: sermon-writer
description: Write sermons in Rick's authentic preaching voice. Structured outlines, manuscript drafts, sermon series planning, and illustration development. Use for any request to draft, outline, or write a sermon or sermon series — structured output for preaching. Not for open-ended scripture exploration or brainstorming (use bible-brainstorm for that).
---

# Sermon Writer

Write sermons that sound like Rick preaches — not generic evangelical boilerplate.

## Before Writing

## Sermon Pipeline Integration

Before starting a sermon draft, check for existing prep material:

1. **If Rick provides a date** (e.g., "let's work on the draft for the 15th"):
   - Run: `python3 scripts/arnoldos.py --json preaching-schedule --date YYYY-MM-DD`
   - Find the matching event and any existing files
   - If brainstorm exists, load it: `python3 scripts/arnoldos.py drive-read <file_id>`
   - Inject brainstorm content into your working context before drafting

2. **After draft completes**:
   - Save .docx to `Ministry/Sermons/Drafts/YYYY-MM-DD-short-passage-ref-draft.docx`
   - Update task notes with draft link
   - These are autonomous per approved exception — no confirmation needed

3. **If no date/pipeline context**, proceed with normal sermon writing. Pipeline bookkeeping happens when context is available.


1. **Load the voice card**: Read `skills/sermon-writer/references/voice-card.md` — this is non-negotiable. Every sermon must follow Rick's voice patterns.
   - For Rick's actual phrases organized by rhetorical function, see `references/voice-phrases.md`
2. **Confirm the inputs** with Rick if not provided:
   - Scripture passage (required)
   - Context: Sunday sermon, prison chapel, series installment, evangelistic?
   - Audience: congregation, inmates, mixed?
   - Series context: standalone or part of a series? If series, what's the throughline?
   - Length target: full manuscript (~3,000-5,000 words) or outline (~500-1,000 words)?
   - Any specific theme, illustration, or angle Rick wants to emphasize?

## Length Tiers

| Request | Length | Word Count |
|---------|--------|------------|
| "Short version" | 20 min | ~2,500 words |
| "Standard" (default) | 25 min | ~3,000 words |
| "Extended" | 35-40 min | ~4,500 words |
| "Deep dive" | 45-60 min | ~5,500-6,000 words |

Prison chapel context: 25-35 min default (90-min total session with small group discussion).

## Output Formats

Rick's sermon documents maintain outline structure even in full manuscripts — Roman numerals, sub-sections (A, B, C), clear point labels visible throughout. This is intentional: Rick reads the manuscript several times during prep, then preaches from the outline.

### Full Sermon Package (default)
The standard deliverable includes three layers in one document:

1. **Outline** (top of document) — skeleton with Roman numerals, sub-points, key phrases, scripture refs. This is what Rick takes to the pulpit.
2. **Full Manuscript** — complete sermon following the outline's structure. Outline numbering visible throughout. Rick reads this multiple times during prep.
3. **Condensed Manuscript** (optional, on request) — between outline and full manuscript. Tighter prose, key sentences written out, but room left for what comes to Rick on the spot. Good for formal occasions where he wants more than an outline but less than reading verbatim.

All three maintain the same structural skeleton. The outline IS the manuscript's backbone.

### Sermon Outline Only
When Rick asks for "just an outline." Skeleton with:
- Opening approach (identified, not fully written)
- Big Idea
- Point structure with scripture references and key phrases
- Suggested illustrations (described, not fully written)
- Closing approach

### Series Plan
Multi-week overview. Includes:
- Series title and throughline
- Per-week: passage, big idea, working title
- Callback opportunities between weeks
- Cumulative vocabulary/metaphor suggestions

## Writing Process

1. **Exegesis first.** Read the passage carefully. Identify the author's intent, structure, key terms, and theological weight. Don't impose a theme — let it emerge from the text.
2. **Big Idea.** One sentence that captures the whole sermon. Test: could someone who missed the sermon get the point from this sentence alone?
3. **Structure.** Map the passage's own structure onto sermon points. Rick follows the text's flow, not a topical outline imposed on it.
4. **Exposition → Application per point.** Don't bank all application for the end. Each point lands before moving on. Be specific — not "pray more" but "Before checking your phone tomorrow, pray: 'Holy Spirit, fill me today.'"
5. **Illustrations.** One per point max. Prefer original parables or historical vignettes. Name them. Let them breathe (350-500 words).
6. **Key phrases.** Craft one quotable sentence per major point. Paradox or inversion preferred.
7. **Conclusion.** Binary close. Circle back to opening if possible. No mush.

## Theological Guardrails

Rick has specific theological positions. When in doubt, load `memory/context/ricks-theological-framework.md`. Key non-negotiables:
- NOT 5-point Calvinist (prevenient grace, unlimited atonement, corporate election)
- Regeneration AFTER conviction/repentance
- NOT "once saved always saved" — Hebrews warnings real
- Molinism for sovereignty/freedom
- "Charismatic with a seat belt"
- Wright's eschatology: resurrection of all things, kingdom now/not-yet
- Theological triage: Essentials → Convictions → Opinions → Questions

If a passage touches contested theology, present Rick's position confidently — don't hedge or "both sides" it.

## Sermon Archive

Rick has 17 preached sermons archived at `memory/training/sermon-archive/INDEX.md` and 59 raw manuscripts at `memory/training/sermon-raw/`. Reference these for:
- Voice calibration (how does Rick actually handle this type of passage?)
- Avoiding repetition (has Rick preached this text before?)
- Callback opportunities (series connections)

## Quality Check

Before delivering, verify:
- [ ] Voice card loaded and followed
- [ ] Big Idea is one clear sentence
- [ ] Structure follows text, not imposed topically
- [ ] Application woven in per point, not banked
- [ ] One illustration per point max, named and full-length
- [ ] Key phrases are crafted, not generic
- [ ] Binary close, no soft ending
- [ ] "We/us" throughout — never preaching down
- [ ] No banned words (beautiful, wonderful, amazing, "let that land")
- [ ] No AI artifacts (see voice card DO NOT list)
- [ ] Greek/Hebrew used sparingly (1-2 max), immediately translated
- [ ] Context-appropriate (prison vs. church vs. evangelistic)
- [ ] Read-aloud test: would Rick actually say this out loud from the pulpit?

## When NOT to Use This Skill
- Open-ended scripture meditation or brainstorming → use `bible-brainstorm`
- Liturgy preparation (calls to worship, prayers, benedictions) → not yet built
- Theological debate or doctrinal Q&A → general conversation
- Writing as Rick in non-sermon contexts → load voice profile directly
