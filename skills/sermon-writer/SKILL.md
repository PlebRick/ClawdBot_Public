Sermon Preparation Workflow Guide Cost-Optimized Collaboration Between Supervisor (Claude.ai) and ClawdBot


________________




Overview This workflow splits sermon preparation between two AI systems to optimize for both quality and cost:


System Role Cost Model Supervisor (Claude.ai) Brainstorming, training iterations, feedback capture Flat rate (Max subscription) ClawdBot Draft generation, voice-card updates, file management Per-token API cost


Principle: Do expensive iteration (back-and-forth) on flat-rate. Do one-shot generation on per-token.


________________




System Roles Supervisor (Claude.ai / Claude Desktop) Handles:


* Passage brainstorming — unlimited back-and-forth exploration
* Training iterations — line-by-line feedback on drafts
* Pattern extraction — identifying generalizable voice rules
* Feedback formatting — structured output CB can ingest


Has access to:


* bible-brainstorming skill (Claude.ai project)
* This workflow guide
* Context from ongoing conversation


Does NOT have:


* ClawdBot's voice training corpus


* Direct file access to CB's memory


* The full voice-card (but understands the format) ClawdBot Handles:


* Draft generation — one-shot sermon manuscript


* Voice-card application — loads trained voice rules


* Calibration digestion — updates voice-card from feedback sessions


* File management — stores all training artifacts


Has access to:


* sermon-writer skill with voice-card
* Full training corpus (memory/training/)
* Sermon archive for reference
* Theological framework


________________




The Workflow Phase 1: Brainstorming (Supervisor — Free) Where: Claude.ai or Claude Desktop


Process:


1. Share the Scripture passage
2. Use bible-brainstorming skill or natural conversation
3. Explore observations, structure, theological connections
4. Go as many rounds as needed — it's flat rate


Output: Brainstorm document (observations, outline ideas, key themes)


Handoff: Save or copy brainstorm output for Phase 2


________________




Phase 2: Draft Generation (ClawdBot — 1 API Call) Where: ClawdBot (web UI, Telegram, etc.)


Process:


1. Provide ClawdBot with:


   * The Scripture passage
   * Your brainstorm output
   * Any commentary or notes you've gathered
   * Specific instructions (length, focus, occasion)


2. ClawdBot triggers sermon-writer skill:


   * Loads voice-card.md (required)
   * Loads theological framework if needed
   * Generates full manuscript draft


Output: Complete sermon manuscript


Handoff: Copy draft back to Supervisor for Phase 3


________________




Phase 3: Training Iteration (Supervisor — Free) Where: Claude.ai or Claude Desktop


Process:


1. Paste ClawdBot's draft


2. Read through together, marking lines:


   * ✅ YES — Sounds like Rick, keep it
   * ❌ TWEAK — Close but needs adjustment
   * ❌ REJECT — Doesn't sound like Rick at all


3. For each TWEAK/REJECT:


   * Rick provides his actual wording
   * Supervisor identifies the pattern/rule


Output: Calibration session file (see format below)


Handoff: Save as voice-calibration-session-N.md for Phase 4


________________




Phase 4: Sync to ClawdBot (Automatic via Drive Sync) Process:


1. Save calibration session file to Drive:


Ministry/Voice-Profile/calibration-sessions/voice-calibration-session-N.md


2. Bi-directional sync runs every 15 minutes — file appears in ClawdBot at:


~/clawd/memory/training/voice-calibration-session-N.md


3. Tell ClawdBot:


"New calibration session added. Please review and update voice-card if patterns warrant."


4. ClawdBot digests patterns and proposes voice-card updates


Frequency: After each sermon, or batch 2-3 sessions together


________________




Feedback Format Use this exact format during training iterations so output can be directly saved as a calibration file:
Voice Calibration Session [N] — [YYYY-MM-DD]
Sermon: [Title or passage reference]


Lines Reviewed: [count]


Verdict Breakdown: [X] YES / [Y] TWEAK / [Z] REJECT


________________


Patterns Learned
Vocabulary
* "singular in its focus" → "all about self"


* "the scandal of grace" → "the paradox of grace"
Structure
* [Pattern identified]
Tone
* [Pattern identified]
Theological Emphasis
* [Pattern identified]


________________


Line-by-Line Feedback
✅ YES
"This is the part where religion gets nervous."


Verdict: Authentic Rick. Conversational, slightly provocative.


________________


❌ TWEAK
"The text presents a singular focus on divine initiative."


Rick's version: "This passage is all about what God does, not what we do."


Pattern: Avoid academic phrasing. Say it plainly. First person plural when addressing congregation.


________________


❌ REJECT
"We must wrestle with the theological implications of this pericope."


Rick's version: "So what does this mean for us? Let's dig in."


Pattern: Never use "pericope" — say "passage" or "text." Rhetorical questions over declarative statements.


________________


Summary
Key rules to add to voice-card:


1. [Rule]


2. [Rule]


3. [Rule]


Phrases to add to voice-phrases.md:


* "[phrase]" — [function: transition / emphasis / application]


________________




File Locations Google Drive (Source of Truth) Folder Contents Ministry/Voice-Profile/core/ Voice profile, bio, theology, calibration guide Ministry/Voice-Profile/reference/ Voice card, phrases, themes Ministry/Voice-Profile/sermon-archive/ Sermon outlines and INDEX Ministry/Voice-Profile/calibration-sessions/ Training feedback files ClawdBot (Synced Every 15 Min) File Path Purpose Voice Card skills/sermon-writer/references/voice-card.md Active rules, loaded every generation Voice Phrases skills/sermon-writer/references/voice-phrases.md Approved phrases by rhetorical function Calibration Sessions memory/training/voice-calibration-session-N.md Structured feedback from training Full Voice Profile memory/context/ricks-voice-profile.md Exhaustive analysis (reference) Theological Framework memory/context/ricks-theological-framework.md Non-negotiable positions Sermon Archive memory/training/sermon-archive/ Full manuscripts for reference


________________




Cross-Platform Access All platforms read from the same Drive folder:


Platform Access Method ClawdBot Bi-directional rclone sync (every 15 min) Claude.ai Google Drive connector Cowork Google Drive MCP Gemini Native Google integration


Any platform can:


* Read voice profile and training materials
* Conduct calibration sessions
* Save new calibration files to calibration-sessions/


Only ClawdBot can:


* Generate sermons using the full skill system
* Update voice-card.md directly (then syncs to Drive)


________________




Periodic Maintenance Every 3-5 Calibration Sessions Ask ClawdBot:


"Review recent calibration sessions and propose updates to voice-card.md. Show me the diff before applying." Monthly Ask ClawdBot:


"Audit voice-card against calibration sessions. Are there any contradictions or outdated rules?" After Major Feedback If a session reveals a significant pattern (e.g., "I never use passive voice in application sections"), tell ClawdBot to update voice-card immediately rather than waiting for the batch.


________________




Quick Reference Card Phase Where Cost Output 1. Brainstorm Supervisor Free Brainstorm doc 2. Draft ClawdBot ~$2-5 Manuscript 3. Train Supervisor Free Calibration file 4. Sync Automatic Free Updated everywhere


Total per sermon: ~$2-5 vs. potentially $20+ doing all iteration on ClawdBot


________________




Commands for ClawdBot Generate sermon:


"Write a sermon on [passage]. Here's my brainstorm: [paste]. Target length: [X] minutes."


Digest calibration:


"New calibration session added. Review and propose voice-card updates."


Check voice-card:


"Show me current voice-card.md contents."


Update voice-card:


"Add this rule to voice-card: [rule]"


________________




Troubleshooting CB draft doesn't sound like Rick:


* Check that voice-card.md was loaded (ask CB to confirm)
* May need more calibration sessions to capture the pattern
* Consider adding specific examples to voice-phrases.md


Feedback format getting messy:


* Supervisor can help clean up at end of session
* Ask: "Format our feedback as a calibration session file"


Voice-card getting too long:


* Ask CB to consolidate similar rules
* Move examples to voice-phrases.md, keep rules abstract in voice-card


Sync not working:


* Check ~/clawd/logs/voice-sync.log on ClawdBot
* Manual sync: bash ~/clawd/scripts/voice-profile-sync.sh sync
* Verify rclone remote: rclone lsd gdrive:


________________




Last Updated: February 2026
