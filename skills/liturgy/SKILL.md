---
name: liturgy
description: Generate a liturgy handout for St. Peter's Stone Church from RCL readings. Use when Rick says "build a liturgy handout", "liturgy for [date]", or "St. Peter's handout". Not for sermon writing (use sermon-writer) or brainstorming (use bible-brainstorm).
metadata:
  clawdbot:
    emoji: "⛪"
---

# Liturgy Handout Generator

Generates a formatted .docx liturgy handout for St. Peter's Stone Church following a fixed order of worship with Revised Common Lectionary readings.

## Venue

This skill is **only** for St. Peter's Stone Church. Never used for Chapel or other venues.

## Workflow

### Step 1: Get the Date

Ask Rick: **"What date are you preaching at St. Peter's?"**

If Rick provides a date, proceed. If he says something like "this Sunday" or "next time," resolve to a concrete date.

### Step 2: Look Up RCL Readings

Run the RCL lookup script:

```bash
node skills/liturgy/scripts/rcl-lookup.js YYYY-MM-DD
```

This returns:
- Liturgical Sunday name (e.g., "7th Sunday of Epiphany")
- Lectionary Year (A, B, or C)
- Four readings: OT, Psalm, NT, Gospel

Present the readings to Rick and ask: **"Which passage are you preaching from?"**

### Step 3: Determine Reading Order

The passage Rick is preaching goes **last** with **(Chaplain)**. All other readings get **(Liturgist)**.

**Default order** (when Rick preaches from the NT epistle):
1. Old Testament (Liturgist)
2. Psalm (Liturgist)
3. Gospel (Liturgist)
4. New Testament (Chaplain) ← preaching passage last

**If Rick preaches from the Gospel:**
1. Old Testament (Liturgist)
2. Psalm (Liturgist)
3. New Testament (Liturgist)
4. Gospel (Chaplain) ← preaching passage last

**If Rick preaches from OT:**
1. Psalm (Liturgist)
2. New Testament (Liturgist)
3. Gospel (Liturgist)
4. Old Testament (Chaplain) ← preaching passage last

**General rule:** The preaching passage always goes last. Remaining readings follow canonical order: OT → Psalm → Gospel → NT (skipping whichever Rick is preaching).

### Step 4: Get the Sermon Title

Ask Rick: **"Do you already have a sermon title, or would you like me to generate one?"**

If Rick provides a title, use it exactly. If he wants one generated, craft a title from the preaching passage that captures the theme.

The title is used for:
- The document header (e.g., "2 Peter 1:16–21 The Spirit Who Speaks")
- The Theme line
- The Sermon line in the order of worship
- The filename

### Step 5: Generate Creative Content

Generate two pieces of creative content:

**Call to Worship** (responsive Leader/People format):
- **Primary source:** The Psalm reading for that Sunday
- Some Psalms lend themselves to direct quoting with responsive echo; others need creative adaptation
- Always end with a Leader line inviting worship and a People response of commitment
- Typically 3 Leader / 3 People exchanges (6 lines total)
- Add a parenthetical note after "Call to Worship:" indicating the source Psalm: e.g., "Call to Worship: (Based on Psalm 2)"

**Benediction:**
- A Scripture quotation that ties to the sermon theme
- Does NOT need to come from the day's readings — any relevant biblical passage works
- Format: quoted text + (Book Chapter:Verse, Translation)
- Prefer ESV, NKJV, or NIV translations
- Common benediction passages: Romans 15:13, Numbers 6:24-26, 2 Corinthians 13:14, Hebrews 13:20-21, Jude 1:24-25, Ephesians 3:20-21, Philippians 4:7

### Step 6: Present for Review

Show Rick the complete liturgy in chat **before** generating the .docx. This lets him:
- Adjust the Call to Worship
- Change the benediction
- Modify the sermon title/theme
- Correct any reading issues

Ask: **"Does this look good, or do you want to adjust anything?"**

### Step 7: Generate .docx

Once approved, generate the document:

```bash
python3 skills/liturgy/scripts/generate-liturgy.py --json '<payload>' --output outputs/liturgy/YY-MM-DD_Passage_Ch_Vs-Vs_Title.docx
```

**Filename convention:** `YY-MM-DD_Book_Ch_Vs-Vs_Title.docx`
- Example: `25-02-23_Luke_6_27-38_Love_Your_Enemies.docx`
- Use underscores for spaces in title
- Match Rick's naming pattern

### Step 8: Save to Drive + Local

1. **Local backup:** `outputs/liturgy/` (create dir if needed)
2. **Google Drive:** Upload to `Ministry/Liturgy/` folder

```bash
# drive-upload not yet implemented in arnoldos.py
# For now, save locally and tell Rick the file is ready for manual upload
# TODO: Add drive-upload command to arnoldos.py
```

If the `Ministry/Liturgy` folder doesn't exist on Drive yet, tell Rick and ask him to create it (or create it if arnoldos.py supports folder creation).

## Fixed Boilerplate

These elements are **always the same** and never change:

### Introduction
- Ringing of the bell
- Prelude – music
- Light enters the sanctuary
- Welcome
- Announcements
- Share peace and greetings

### Worship
- Hymn: To be selected
- Opening Prayer (Chaplain: extemporaneous)

### After Sermon
- Moment of silence for reflection and response accompanied by music
- (Hymn to be chosen)

### Prayer of Confession (Default)
The Apostles' Creed with ellipsis:
> I believe in God, the Father almighty, creator of heaven and earth. I believe in Jesus Christ, his only Son, our Lord, who was conceived by the Holy Spirit and born of the virgin Mary. He suffered under Pontius Pilate, was crucified, died, and was buried... The third day he rose again from the dead. He ascended to heaven and is seated at the right hand of God the Father almighty. From there he will come to judge the living and the dead.

Rick occasionally changes this, but Apostles' Creed is the default. Use it unless told otherwise.

### Prayer and Offering
- Hymn: To be selected
- Prayers of the faithful (Prayer requests of the congregation)
- The Lord's Prayer (KJV, debtor version):
> Our Father which art in heaven, Hallowed be thy name. Thy kingdom come, Thy will be done in earth, as it is in heaven. Give us this day our daily bread. And forgive us our debts, as we forgive our debtors. And lead us not into temptation, but deliver us from evil: For thine is the kingdom, and the power, and the glory, for ever. Amen.
- (Matthew 6:9-13)
- Offering (Prayer of blessing over offering)

### Closing
- Closing hymn: To be selected
- All: Amen!
- Postlude - music

## Document Format

```
[Passage] [Title]                          ← centered, bold, 16pt
Date: [Full date]                          ← centered, 11pt
[Liturgical Sunday], Year [A/B/C]          ← centered, 11pt
Theme: [Title]                             ← centered, bold, 11pt

Introduction                               ← section header, bold, 13pt
• [bullet items]

Worship                                    ← section header
• Hymn: To be selected
• Call to Worship: (Based on Psalm N)
    Leader: ...
    People: ...
• Opening Prayer
  (Chaplain: extemporaneous)

The Word: Scripture Reading                ← section header
• Old Testament: [citation] (Liturgist)
• Psalm: [citation] (Liturgist)
• [varies]: [citation] (Liturgist)
• [preaching passage]: [citation] (Chaplain)
• Sermon: [Title]

[moment of silence / hymn]

• Prayer of Confession
  All: [Apostles' Creed]

Prayer and Offering                        ← section header
• Hymn: To be selected
• Prayers of the faithful
• The Lord's prayer
• Offering

Closing                                    ← section header
• Closing hymn: To be selected
• Benediction: "[scripture]" (reference)
• All: Amen!
• Postlude - music
```

## Pipeline Integration

This skill chains naturally from the sermon pipeline:
- **Before liturgy:** Rick has typically done a brainstorm and/or sermon draft
- **After liturgy:** The .docx gets sent to the elder at St. Peter's

The liturgy skill can also be used standalone — Rick doesn't always brainstorm or draft before building the handout.

## Handoff Points

- "Let's brainstorm this passage" → bible-brainstorm skill
- "Draft the sermon" → sermon-writer skill
- "Check my preaching schedule" → arnoldos skill
