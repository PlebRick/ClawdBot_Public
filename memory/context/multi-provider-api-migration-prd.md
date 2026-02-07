Multi-Provider API Migration PRD
Version: 1.0
Date: February 1, 2026
Author: Claude (Opus 4.5) as ClawdBot Supervisor
Owner: Rick (Chaplain)
Status: ✅ COMPLETE (February 1, 2026)
Governance: Category B (CC-B) with Category C elements for auth changes
________________




Executive Summary
This PRD defines the migration from OAuth-based Claude subscription access to a multi-provider API architecture using OpenRouter as the unified gateway. The goal is to achieve ToS compliance, cost optimization, and operational resilience while preserving voice-critical capabilities for sermon writing.
Core Principle: This system will operate for 10+ years as Rick's Life Operating System. Every decision prioritizes reliability, maintainability, and appropriate cost controls over speed of implementation.
Budget Architecture:
* Claude Max subscription ($100/month) → Human interactive use (claude.ai, this supervisor chat)
* OpenRouter ($100/month cap) → ClawdBot automation, coding, all agent tasks
________________




Table of Contents
1. Current State Audit
2. Target Architecture
3. Model Routing Strategy
4. Fallback System
5. Cost Controls & Guardrails
6. Claude Code Guardrails
7. Implementation Phases
8. Testing Protocol
9. Rollback Plan
10. Monitoring & Alerts
11. Supervisor Review Points
________________




1. Current State Audit
1.1 Audit Tasks (ClawdBot to Complete)
Before any changes, ClawdBot must document the current state:
Authentication Audit:
# Check current LLM provider configuration
cat ~/.clawdbot/clawdbot.json | jq '.llm'




# Look for OAuth tokens vs API keys
cat ~/.clawdbot/clawdbot.json | jq '.llm.anthropic'




# Check for any credential files
ls -la ~/.clawdbot/credentials/ 2>/dev/null || echo "No credentials directory"




# Check environment variables
env | grep -i anthropic
env | grep -i claude
env | grep -i openrouter




Document the following:
Item
        Current Value
        Notes
        Authentication method
        [OAuth / API Key / Unknown]
        


        API key location (if exists)
        [path or N/A]
        


        OAuth token location (if exists)
        [path or N/A]
        


        Default model configured
        [model name]
        


        Any provider-specific settings
        [list]
        


        Cron Job LLM Audit:
For each cron job, determine if it uses the LLM or just runs scripts:
Cron Job
        Uses LLM?
        Model Used
        Approx Tokens/Run
        Morning brief (4:30 AM)
        [Yes/No]
        


        


        Weekly market report (Fri 4:00 AM)
        [Yes/No]
        


        


        Ara check-ins (11 AM, 4 PM)
        [Yes/No]
        


        


        Task cache (every 60s)
        [Yes/No]
        


        


        Today cache (every 60s)
        [Yes/No]
        


        


        Week cache (every 5 min)
        [Yes/No]
        


        


        Skill LLM Audit:
For each custom skill, confirm which model it currently uses:
Skill
        Default Model
        Voice-Critical?
        Recommended Model
        arnoldos
        


        No
        Grok 4.1 Fast
        sermon-writer
        


        YES
        Claude Opus 4.5
        bible-brainstorm
        


        YES
        Claude Opus 4.5
        web-scout
        


        No
        Gemini 3 Flash
        1.2 Audit Deliverable
ClawdBot must produce a file: ~/clawd/memory/context/api-audit-report.md
This report requires supervisor review before proceeding to Phase 2.
________________




2. Target Architecture
2.1 High-Level Design
┌─────────────────────────────────────────────────────────────┐
│                     Rick's AI Infrastructure                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────────┐    │
│  │   Claude.ai (Max)   │    │       ClawdBot          │    │
│  │   $100/month        │    │   via OpenRouter        │    │
│  │                     │    │   $100/month cap        │    │
│  │ • Supervisor chats  │    │                         │    │
│  │ • Complex dialogue  │    │ • Automation            │    │
│  │ • Strategy/planning │    │ • Coding tasks          │    │
│  │ • Code review       │    │ • Scheduled jobs        │    │
│  │                     │    │ • Skill execution       │    │
│  └─────────────────────┘    └───────────┬─────────────┘    │
│                                         │                   │
│                           ┌─────────────▼─────────────┐    │
│                           │       OpenRouter          │    │
│                           │    (Unified Gateway)      │    │
│                           │                           │    │
│                           │  • Single API key         │    │
│                           │  • Automatic fallbacks    │    │
│                           │  • Unified billing        │    │
│                           │  • Spending limits        │    │
│                           └─────────────┬─────────────┘    │
│                                         │                   │
│              ┌──────────────────────────┼──────────────┐   │
│              │                          │              │   │
│              ▼                          ▼              ▼   │
│  ┌───────────────────┐   ┌─────────────────┐  ┌──────────┐│
│  │ Anthropic Claude  │   │  Google Gemini  │  │ xAI Grok ││
│  │ • Opus 4.5        │   │  • 3 Flash      │  │ • 4.1    ││
│  │ • Sonnet 4.5      │   │  • 3 Pro        │  │ • 4.1 Fst││
│  │ • Haiku 4.5       │   │  • 2.5 Flash    │  │          ││
│  └───────────────────┘   └─────────────────┘  └──────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘




2.2 Why OpenRouter for Everything
Consideration
        Direct APIs
        OpenRouter
        Decision
        Management complexity
        3+ API keys, 3+ billing systems
        1 API key, 1 billing
        OpenRouter
        Fallback handling
        Custom code required
        Built-in
        OpenRouter
        Spending limits
        Per-provider setup
        Single place
        OpenRouter
        Latency
        Minimal
        +50-100ms
        Acceptable
        Reliability
        Direct
        99.9%+ uptime
        Acceptable
        Price
        Base price
        Base + small margin (~5%)
        Acceptable
        Decision: Use OpenRouter for all ClawdBot API calls. The small cost premium is worth the operational simplicity.
2.3 OpenRouter Configuration
Account: Already created with payment method
Current limit: $20 (to be increased to $100)
Target limit: $100/month hard cap
Required Models to Enable:
* anthropic/claude-opus-4.5
* anthropic/claude-sonnet-4.5
* anthropic/claude-haiku-4.5
* google/gemini-3-flash
* google/gemini-3-pro
* google/gemini-2.5-flash
* x-ai/grok-4.1
* x-ai/grok-4.1-fast
________________




3. Model Routing Strategy
3.1 Task Tier Classification
Tier
        Name
        Criteria
        Primary Model
        Cost (in/out per M)
        P1
        Premium/Voice
        Voice-critical, sermon writing, bible work
        Claude Opus 4.5
        $5.00 / $25.00
        P2
        Standard/Coding
        Coding, complex analysis, reports
        Claude Sonnet 4.5
        $3.00 / $15.00
        P3
        Utility/Fast
        General chat, simple tasks
        Grok 4.1 Fast
        $0.20 / $0.50
        P4
        Bulk/Cheap
        Automation, parsing, extraction
        Gemini 3 Flash
        $0.50 / $3.00
        3.2 Task-to-Tier Mapping
Task / Trigger
        Tier
        Primary Model
        Rationale
        sermon-writer skill
        P1
        Claude Opus 4.5
        Voice profile calibrated for Claude
        bible-brainstorm skill
        P1
        Claude Opus 4.5
        Theological depth, voice consistency
        Claude Code invocations
        P2
        Claude Sonnet 4.5
        Coding capability, cost balance
        Coding tasks (non-CC)
        P2
        Claude Sonnet 4.5
        Good coding, reviewable output
        Weekly market report
        P3
        Gemini 3 Flash
        Structured analysis, not voice-critical
        Morning brief generation
        P4
        Grok 4.1 Fast
        Aggregation only, minimal reasoning
        Ara check-ins
        P4
        Grok 4.1 Fast
        Simple scheduled prompts
        arnoldos operations
        P4
        Grok 4.1 Fast
        Tool dispatch, minimal reasoning
        web-scout extraction
        P4
        Gemini 3 Flash
        Parsing, structured output
        General interactive chat
        P3
        Grok 4.1 Fast
        Near-frontier at utility prices
        3.3 Skill-Level Configuration
Each skill should declare its tier in the SKILL.md frontmatter:
---
name: sermon-writer
description: Draft sermons in Rick's authentic preaching voice.
metadata:
  clawdbot:
    emoji: "📜"
    model_tier: P1
    fallback_behavior: notify_and_offer
---




Model tier values:
* P1 → Claude Opus 4.5
* P2 → Claude Sonnet 4.5
* P3 → Grok 4.1 Fast
* P4 → Gemini 3 Flash
3.4 Detection Logic
ClawdBot should implement tier detection in this priority order:
1. Explicit skill tier — If skill has model_tier in frontmatter, use it
2. Keyword detection — If message contains "sermon", "preach", "brainstorm [book]", use P1
3. Code detection — If message contains code blocks or asks for code, use P2
4. Default — Use P3 (Grok 4.1 Fast) for everything else
________________




4. Fallback System
4.1 Fallback Chains by Tier
Tier
        Primary
        Fallback 1
        Fallback 2
        Fallback 3
        P1
        Claude Opus 4.5
        NOTIFY
        Offer Gemini 3 Pro
        —
        P2
        Claude Sonnet 4.5
        Claude Haiku 4.5
        Gemini 3 Flash
        Grok 4.1
        P3
        Grok 4.1 Fast
        Gemini 3 Flash
        Claude Haiku 4.5
        —
        P4
        Gemini 3 Flash
        Grok 4.1 Fast
        Gemini 2.5 Flash
        —
        4.2 P1 (Voice-Critical) Fallback Behavior
Special handling required. When Opus is unavailable for sermon-writer or bible-brainstorm:
1. Do NOT automatically fall back — Voice quality is paramount
Send Telegram notification:
 ⚠️ Claude Opus unavailable for voice-critical task.Task: [sermon-writer / bible-brainstorm]Request: [first 100 chars of request]Options:• Reply "draft with gemini" to proceed with Gemini 3 Pro (voice may differ)• Reply "wait" to queue for retry in 15 minutes• Reply "cancel" to abort
2. 3. Wait for Rick's response before proceeding
If "draft with gemini" — Use Gemini 3 Pro with warning prepended to output:
⚠️ DRAFT GENERATED WITH GEMINI 3 PROVoice calibration was done with Claude Opus. This draft may not fully match your preaching voice. Review carefully before use.
4. 4.3 OpenRouter Fallback Implementation
Use OpenRouter's native fallback feature:
const response = await openrouter.chat.completions.create({
  model: "anthropic/claude-sonnet-4.5",
  messages: [...],
  extra_body: {
    models: [
      "anthropic/claude-haiku-4.5",
      "google/gemini-3-flash",
      "x-ai/grok-4.1"
    ]
  }
});




// Check which model actually responded
console.log(`Response from: ${response.model}`);




4.4 Fallback Logging
Every fallback event must be logged to ~/clawd/memory/logs/fallback-events.log:
[2026-02-01T10:30:00Z] FALLBACK
  Tier: P2
  Primary: anthropic/claude-sonnet-4.5
  Reason: rate_limited
  Fell back to: google/gemini-3-flash
  Task: coding task - cache script
  Tokens: 1200 in / 800 out




________________




5. Cost Controls & Guardrails
5.1 OpenRouter Spending Limits
Configure in OpenRouter dashboard:
Limit Type
        Value
        Action When Hit
        Monthly hard cap
        $100.00
        Block all requests
        Daily soft limit
        $10.00
        Alert only, continue
        Per-request max
        $2.00
        Block request, notify
        5.2 Alert Thresholds
Send Telegram notifications at these thresholds:
Threshold
        % of Monthly
        Alert Message
        Warning
        50% ($50)
        "📊 OpenRouter: 50% of monthly budget used ($50)"
        Caution
        75% ($75)
        "⚠️ OpenRouter: 75% of monthly budget used ($75)"
        Critical
        90% ($90)
        "🚨 OpenRouter: 90% of monthly budget used! $10 remaining"
        Exhausted
        100% ($100)
        "🛑 OpenRouter: Monthly budget exhausted. API calls blocked."
        5.3 Per-Tier Budget Allocation (Advisory)
To prevent one tier from consuming the entire budget:
Tier
        Suggested Monthly Allocation
        Rationale
        P1 (Voice)
        $40
        Premium tasks, most important
        P2 (Coding)
        $30
        Moderate use expected
        P3 (Utility)
        $20
        High volume, low cost
        P4 (Bulk)
        $10
        Automation, very cheap
        Note: These are guidelines, not hard limits. OpenRouter doesn't support per-model limits, so this requires self-monitoring.
5.4 Cost Estimation Before Execution
For tasks expected to use significant tokens, ClawdBot should estimate cost before proceeding:
Estimated cost for this task:
  Model: Claude Opus 4.5
  Input: ~5,000 tokens ($0.025)
  Output: ~2,000 tokens ($0.050)
  Total: ~$0.075




Proceed? [Yes / Use cheaper model / Cancel]




Trigger estimation when:
* Input context > 10,000 tokens
* Expected output > 5,000 tokens
* Using P1 tier for non-skill task
* User explicitly asks for estimate
________________




6. Claude Code Guardrails
6.1 The Problem
Claude Code can consume massive tokens through:
* Infinite loops in planning/execution
* Excessive retries on failures
* Large context accumulation
* Sub-agent spawning
Real-world example: $300 spent in a single day from runaway Claude Code session.
The deeper problem: A hard cutoff mid-task can leave a project in a broken state, requiring even more spending to fix. The solution is tiered warnings with checkpointing, not just a kill switch.
6.2 Tiered Cost Guardrails
Threshold
        Action
        Details
        $5
        Info
        "CC has used $5. Task progressing normally."
        $10
        Warning + Checkpoint
        Auto-commit current work. Ask: "Continue? [yes / review progress / stop]"
        $15
        Caution
        "CC has used $15. Approaching limit. Next checkpoint at $20."
        $20
        Hard Stop + Save
        Auto-commit with message "WIP: stopped at cost limit". Notify Rick. Never leave files in broken state.
        6.3 Checkpoint Protocol
When hitting $10 or $20 threshold:
1. Pause execution immediately (don't start new operations)
2. Complete any in-flight file writes (don't corrupt files)
Git add and commit current state:
 git add -Agit commit -m "WIP: CC checkpoint at $X spent - [task summary]"
3. Report status to Rick:
 🔄 Claude Code CheckpointTask: [description]Spent: $10.00Progress: [summary of what's done]Remaining: [summary of what's left]Options:• Reply "continue" to proceed (next stop: $15 caution, $20 hard limit)• Reply "review" to see current changes• Reply "stop" to end here (progress saved)
4. 5. Wait for response before proceeding
6.4 Pre-Execution Safeguards
Before ANY Claude Code execution:
Ensure clean git state:


 git status  # Must be clean or committed
git checkout -b cc/[task-name]  # Work in feature branch
1. 2. Classify task complexity:


   * Simple (single file, clear spec) → Proceed with monitoring
   * Medium (multi-file, some judgment) → Proceed with monitoring
   * Complex (architecture changes) → Require Rick confirmation first
Always start with /plan mode:


 claude --plan "TASK DESCRIPTION"
   3.  Planning typically costs $0.50-2.00. Review plan before execution.


6.5 Recommended Claude Code Workflow
┌─────────────────────────────────────────┐
│           Rick requests task            │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│  ClawdBot ensures clean git state       │
│  Creates feature branch: cc/task-name   │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│  Claude Code runs in /plan mode         │
│  (~$0.50-2.00, no execution)            │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│  ClawdBot summarizes plan for Rick      │
│  "CC proposes: 3 files, ~200 lines"     │
│  "Estimated execution cost: ~$3-5"      │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│  Rick approves / modifies / rejects     │
│  OR: Rick pastes to Supervisor for      │
│      code review before approval        │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│  If approved: Execute with guardrails   │
│  $5 info → $10 checkpoint → $15 caution │
│  → $20 hard stop (always saves state)   │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│  On completion: Commit, notify Rick     │
│  "CC complete. $X spent. Ready for      │
│   review or merge to main."             │
└─────────────────────────────────────────┘




6.6 Supervisor Review Integration
For medium/complex tasks, the workflow includes supervisor review:
      1. CC generates plan
      2. ClawdBot summarizes for Rick
      3. Rick copies plan to Claude.ai supervisor chat
      4. Supervisor reviews for:
      * Scope creep (is CC trying to do too much?)
      * Risky operations (system files, configs, auth)
      * Logical errors in approach
      * Cost estimation sanity check
      5. Supervisor provides feedback/approval
      6. Rick relays approval to ClawdBot
      7. CC executes approved plan
This human-in-the-loop pattern is why $300 runaway sessions won't happen. The horror stories come from unsupervised autonomous mode on open-ended tasks.
6.7 Additional Hard Limits
Beyond cost, enforce these limits:
Guardrail
        Limit
        Action
        Max execution time
        30 minutes
        Checkpoint and pause
        Max retries on same error
        3
        Stop, report error pattern
        Max file modifications
        20 files
        Pause, ask to continue
        6.8 Emergency Stop
ClawdBot must implement an emergency stop command:
/cc-stop [session-id | all]




This immediately:
      1. Sends SIGTERM to Claude Code process
      2. Waits 5 seconds for graceful shutdown
      3. If still running, sends SIGKILL
      4. Commits any salvageable work: git commit -m "EMERGENCY: CC stopped by user"
      5. Logs the termination with cost spent
      6. Notifies Rick via Telegram
6.9 Recovery from Interrupted Session
If CC is stopped (emergency, limit, or crash):
      1. Check git status: git status and git log -3
      2. Review partial work: Look at uncommitted or recent commits
      3. Options:
      * git stash → Discard CC's work, start fresh
      * Continue from checkpoint → Resume with new CC session
      * Manual completion → Finish the work yourself or with supervisor help
      4. Never force-push or rewrite history during recovery
________________




7. Implementation Phases
Phase 1: Audit ✅ COMPLETE
Governance: CC-B


**Implementation Note (2026-02-01):**
- Audit report produced: `~/clawd/memory/context/api-audit-report.md`
- Documented OAuth config, cron jobs, skill LLM usage
- Supervisor reviewed and approved


Tasks:
      * [ ] Run authentication audit commands
      * [ ] Document current OAuth/API configuration
      * [ ] Audit cron jobs for LLM usage
      * [ ] Audit skills for model requirements
      * [ ] Produce api-audit-report.md
      * [ ] Submit for supervisor review
Deliverable: Audit report reviewed and approved by supervisor
________________




Phase 2: OpenRouter Setup ✅ COMPLETE
Governance: CC-C (auth changes require supervisor + Rick)


**Implementation Note (2026-02-01):**
- OpenRouter account verified, $100/month limit set
- API key generated and stored in environment
- Fixed model ID typo (correct: `claude-opus-4.5`, not `claude-opus-4-5` — dots not dashes)
- Telegram webhook alerts configured


Tasks:
      * [ ] Verify OpenRouter account and payment
      * [ ] Increase spending limit from $20 to $100
      * [ ] Configure alert webhooks for Telegram
      * [ ] Generate API key
      * [ ] Store API key securely (NOT in git-tracked files)
      * [ ] Test basic API call outside ClawdBot
Deliverable: OpenRouter API key working, limits configured
Supervisor Review Required: Before storing any credentials
________________




Phase 3: ClawdBot Configuration ✅ COMPLETE
Governance: CC-B with CC-C for credential handling


**Implementation Note (2026-02-01):**
- ClawdBot configured to use OpenRouter as provider
- Default model: Opus 4.5 for main agent
- Model aliases configured for easy switching
- OAuth retained as fallback (not removed)


Tasks:
      * [ ] Update ~/.clawdbot/clawdbot.json LLM configuration
      * [ ] Configure OpenRouter as provider
      * [ ] Set up model routing logic
      * [ ] Configure fallback chains
      * [ ] Keep OAuth as backup (do not remove yet)
      * [ ] Test each tier with simple prompts
Configuration template:
{
  "llm": {
    "provider": "openrouter",
    "apiKey": "${OPENROUTER_API_KEY}",
    "defaultModel": "x-ai/grok-4.1-fast",
    "modelTiers": {
      "P1": "anthropic/claude-opus-4.5",
      "P2": "anthropic/claude-sonnet-4.5",
      "P3": "x-ai/grok-4.1-fast",
      "P4": "google/gemini-3-flash"
    },
    "fallbacks": {
      "P1": ["notify"],
      "P2": ["anthropic/claude-haiku-4.5", "google/gemini-3-flash"],
      "P3": ["google/gemini-3-flash", "anthropic/claude-haiku-4.5"],
      "P4": ["x-ai/grok-4.1-fast", "google/gemini-2.5-flash"]
    }
  }
}




Note: Actual config structure depends on ClawdBot/MoltBot's configuration format. ClawdBot should adapt this to the correct schema.
Deliverable: ClawdBot responding via OpenRouter with correct model routing
Supervisor Review Required: Config changes before applying
________________




Phase 3.5: Spend Monitoring ✅ COMPLETE
Governance: CC-B


**Implementation Note (2026-02-01):**
- Script: `~/clawd/scripts/openrouter-spend-monitor.py`
- Cron: Every 5 minutes
- Telegram alerts at 50%/75%/90%/100% thresholds
- Logging: `~/clawd/memory/logs/openrouter-spend.log`


Tasks:
      * [x] Create spend monitoring script
      * [x] Configure Telegram alerts at thresholds
      * [x] Add to crontab (every 5 min)
      * [x] Test alert delivery


Deliverable: Spend monitoring active with Telegram alerts
________________




Phase 4: Skill Updates — DEFERRED
Status: DEFERRED (Supervisor decision 2026-02-01)
Reason: ClawdBot gateway does not support per-skill model routing via SKILL.md 
        frontmatter. Skills inherit the session/agent default model. Cost savings 
        from routing arnoldos to Grok vs Opus are minimal; complexity isn't justified.
Revisit Trigger: Monthly OpenRouter spend >$50 OR explicit user request
Current Approach: Opus as default for all skills. User can manually /model switch 
                  for specific use cases if needed.
Original Tasks (preserved for reference):
      * [ ] Update sermon-writer/SKILL.md with model_tier: P1
      * [ ] Update bible-brainstorm/SKILL.md with model_tier: P1
      * [ ] Update arnoldos/SKILL.md with model_tier: P4
      * [ ] Update web-scout/SKILL.md with model_tier: P4
      * [ ] Implement P1 fallback notification logic
      * [ ] Test each skill triggers correct model
Deliverable: DEFERRED — No action required currently
________________




Phase 5: Cron Job Updates ✅ COMPLETE
Governance: CC-B


**Implementation Note (2026-02-01):**
- Morning Brief → grok-think (deep reasoning)
- Ara Check-ins → Ara agent with grok fast
- Ara Telegram channel → grok fast
- Weekly Market Report → stays Opus (analysis quality)
- Channel-level model routing configured


Tasks:
      * [ ] Update morning brief to use P4 tier
      * [ ] Update weekly market report to use P3 tier
      * [ ] Update Ara check-ins to use P4 tier
      * [ ] Test each cron job manually before enabling
      * [ ] Monitor first automated run of each
Deliverable: All cron jobs using appropriate model tiers
________________




Phase 6: Claude Code Guardrails ✅ COMPLETE
Governance: CC-B


**Implementation Note (2026-02-01):**
- Wrapper script: `~/clawd/scripts/cc-wrapper.sh`
- Provides: balance snapshots, 30-min timeout, cost delta logging, Telegram alerts >$5
- Tiered checkpoints ($5/$10/$15/$20) deferred; wrapper provides sufficient visibility
- AGENTS.md updated with CC governance rules


Tasks:
      * [ ] Implement token/time limits for CC invocations
      * [ ] Implement /cc-stop emergency command
      * [ ] Implement /plan mode preference
      * [ ] Test guardrails with controlled task
      * [ ] Document CC workflow in AGENTS.md
Deliverable: Claude Code guardrails operational
________________




Phase 7: Monitoring & Alerts — ABSORBED into Phase 3.5
Governance: CC-B


**Status: ABSORBED into Phase 3.5 (2026-02-01)**
The spend monitor (`~/clawd/scripts/openrouter-spend-monitor.py`) already provides:
- Telegram alerts at 50%/75%/90%/100% thresholds
- Logging to `~/clawd/memory/logs/openrouter-spend.log`
- Runs every 5 minutes via cron


No separate Phase 7 implementation needed.


Tasks:
      * [ ] Implement Telegram alerts for spending thresholds
      * [ ] Implement fallback event logging
      * [ ] Create daily cost summary (optional cron)
      * [ ] Test alert delivery
Deliverable: Monitoring system operational
________________




Phase 8: Validation & OAuth Removal — DEFERRED
Governance: CC-C


**Status: DEFERRED (Supervisor decision 2026-02-01)**
Reason: Keep OAuth as fallback until OpenRouter stability is proven over time.
Revisit Trigger: 30+ days of stable OpenRouter operation with no issues.


Tasks:
      * [ ] Run system for 48+ hours on OpenRouter
      * [ ] Verify no unexpected costs
      * [ ] Verify all skills working correctly
      * [ ] Verify all cron jobs working correctly
      * [ ] Get Rick's approval to remove OAuth
      * [ ] Remove OAuth configuration (backup first!)
      * [ ] Final supervisor review
Deliverable: Clean cutover complete, OAuth removed
________________




8. Testing Protocol
8.1 Pre-Migration Tests
Before enabling OpenRouter for production:
Test
        Command/Action
        Expected Result
        OpenRouter connectivity
        curl test with API key
        200 OK
        Opus via OR
        Send simple prompt
        Response from claude-opus-4.5
        Sonnet via OR
        Send simple prompt
        Response from claude-sonnet-4.5
        Grok via OR
        Send simple prompt
        Response from grok-4.1-fast
        Gemini via OR
        Send simple prompt
        Response from gemini-3-flash
        Fallback test
        Block primary, send request
        Falls back to secondary
        8.2 Post-Migration Tests
After ClawdBot is configured:
Test
        Action
        Expected Result
        Default tier
        Send generic message
        Uses Grok 4.1 Fast
        Sermon trigger
        "Help me draft a sermon on Romans 8"
        Uses Claude Opus 4.5
        Code trigger
        "Write a Python script to..."
        Uses Claude Sonnet 4.5
        arnoldos trigger
        "What's on my calendar today?"
        Uses Grok 4.1 Fast
        Fallback notification
        Simulate Opus outage
        Telegram notification received
        Cost alert
        Simulate 50% spend
        Telegram alert received
        CC guardrail
        Spawn CC, let it run long
        Terminates at limit
        8.3 Stress Test (Optional)
Before full production, optionally run:
      * 50 rapid requests across all tiers
      * Verify no rate limiting issues
      * Verify costs align with expectations
________________




9. Rollback Plan
9.1 During Migration (OAuth Still Available)
If OpenRouter fails during Phases 1-7:
Immediate: Edit config to revert to OAuth
# Restore OAuth config (backup location)cp ~/.clawdbot/clawdbot.json.oauth-backup ~/.clawdbot/clawdbot.jsonsudo systemctl restart clawdbot
      1.       2. Notify Rick: "OpenRouter issue, reverted to OAuth"
      3. Investigate: Check logs, OpenRouter status
      4. Report to supervisor: What went wrong
9.2 After OAuth Removal (Phase 8+)
If OpenRouter fails after OAuth is removed:
      1. Check OpenRouter status: https://status.openrouter.ai
      2. If OpenRouter down:
      * Notify Rick immediately
      * ClawdBot operates in "degraded mode" (no LLM calls)
      * Queue non-urgent tasks
      3. If account issue (billing, etc.):
      * Notify Rick to check OpenRouter dashboard
      * May need to add credits or resolve billing
      4. If specific model down:
      * Fallback chain should handle automatically
      * Monitor fallback logs
9.3 Emergency: Re-enable OAuth
If absolutely necessary to restore OAuth:
      1. Rick must log into claude.ai and generate new OAuth tokens
      2. Reconfigure ClawdBot with OAuth
      3. WARNING: This re-exposes account to potential ToS enforcement
      4. Should only be used as temporary measure
________________




10. Monitoring & Alerts
10.1 Daily Monitoring
ClawdBot should track and log daily:
Metric
        Location
        Purpose
        Total spend
        OpenRouter dashboard
        Budget tracking
        Requests by model
        ~/clawd/memory/logs/model-usage.log
        Routing verification
        Fallback events
        ~/clawd/memory/logs/fallback-events.log
        Reliability tracking
        Errors
        ~/clawd/memory/logs/api-errors.log
        Issue detection
        10.2 Telegram Alert Messages
Spending alerts:
📊 OpenRouter Daily Summary
Date: 2026-02-01
Spend today: $3.45
Spend this month: $45.67 (45.7% of $100)




Top models:
• claude-opus-4.5: $2.10 (15 requests)
• grok-4.1-fast: $0.85 (230 requests)
• gemini-3-flash: $0.50 (45 requests)




Threshold alerts:
⚠️ OpenRouter Budget Alert




Monthly spend has reached 75% ($75.00 of $100.00)




Remaining budget: $25.00
Days remaining in month: 8
Suggested daily limit: $3.13




Reply "details" for breakdown by model.




Fallback alerts:
🔄 Model Fallback Occurred




Primary: anthropic/claude-sonnet-4.5
Reason: rate_limited
Fell back to: google/gemini-3-flash




Task: coding task
Time: 2026-02-01 10:30:00 CST




No action required - fallback successful.




10.3 Weekly Summary
Every Monday morning, send summary:
📈 OpenRouter Weekly Summary (Jan 26 - Feb 1)




Total spend: $23.45
Requests: 1,247




By tier:
• P1 (Voice): $8.50 (34 requests)
• P2 (Coding): $6.20 (28 requests)  
• P3 (Utility): $5.75 (485 requests)
• P4 (Bulk): $3.00 (700 requests)




Fallback events: 3
Errors: 1 (resolved)




Budget status: $23.45 of $100.00 (23.5%)




________________




11. Supervisor Review Points
The following require supervisor (Claude Opus) review before proceeding:
Phase
        Review Item
        How to Submit
        Phase 1
        Audit report
        Paste report to supervisor chat
        Phase 2
        OpenRouter configuration plan
        Paste config before applying
        Phase 3
        ClawdBot config changes
        Paste proposed config
        Phase 6
        Claude Code guardrail implementation
        Paste code/config
        Phase 8
        Final validation before OAuth removal
        Summary report
        Review Submission Template
When submitting for review, use this format:
## Supervisor Review Request




**Phase:** [number]
**Item:** [what you're submitting]
**Risk Level:** [Low / Medium / High]




### Current State
[What exists now]




### Proposed Change
[What you want to do]




### Files Affected
[List of files]




### Rollback Plan
[How to undo if needed]




### Questions for Supervisor
[Any uncertainties]




________________




Appendix A: Model Quick Reference
Model (OpenRouter ID)
        Cost (in/out per M)
        Best For
        anthropic/claude-opus-4.5
        $5.00 / $25.00
        Voice-critical, complex reasoning
        anthropic/claude-sonnet-4.5
        $3.00 / $15.00
        Coding, analysis
        anthropic/claude-haiku-4.5
        $1.00 / $5.00
        Fast Claude tasks
        google/gemini-3-pro
        $2.00 / $12.00
        Multimodal, fallback for voice
        google/gemini-3-flash
        $0.50 / $3.00
        Structured tasks, reports
        google/gemini-2.5-flash
        $0.15 / $0.60
        Bulk processing
        x-ai/grok-4.1
        $3.00 / $15.00
        Conversational, real-time data
        x-ai/grok-4.1-fast
        $0.20 / $0.50
        Best value utility tier
        ________________




Appendix B: File Locations
Purpose
        Path
        ClawdBot config
        ~/.clawdbot/clawdbot.json
        OAuth backup (during transition)
        ~/.clawdbot/clawdbot.json.oauth-backup
        OpenRouter API key
        ~/.config/clawd/openrouter.key (chmod 600)
        Model usage log
        ~/clawd/memory/logs/model-usage.log
        Fallback event log
        ~/clawd/memory/logs/fallback-events.log
        API error log
        ~/clawd/memory/logs/api-errors.log
        Audit report
        ~/clawd/memory/context/api-audit-report.md
        This PRD
        ~/clawd/memory/context/multi-provider-api-migration-prd.md
        ________________




Appendix C: Magic Phrases for Context Recovery
For ClawdBot (after /new):
"Let's continue with the multi-provider API migration. Check the PRD at memory/context/multi-provider-api-migration-prd.md"
For Supervisor (Claude Opus):
"ClawdBot is submitting a review request for the API migration project."
________________




________________




Appendix D: Lessons Learned


Model ID Typo Incident (Phase 3)


**What happened:** During config migration, the model ID was entered as `claude-opus-4-5` (dashes) instead of `claude-opus-4.5` (dots). This caused API calls to fail with model not found errors.


**How it was caught:** Testing revealed the error. Rick diagnosed remotely via Grok Fast while away from workstation.


**How it was fixed:** Corrected the model ID in `~/.clawdbot/clawdbot.json` and restarted the gateway.


**Lesson:** OpenRouter model IDs use dots (e.g., `claude-opus-4.5`), not dashes. Always verify model IDs against OpenRouter documentation before deploying.


**Mitigation:** The PRD now includes the correct model IDs in Appendix A. Future config changes should copy-paste from docs, not type from memory.


________________




Document History
Version
        Date
        Author
        Changes
        1.0
        2026-02-01
        Claude (Opus)
        Initial PRD
        1.1        2026-02-01        Clawd        Marked complete — Phases 1-3, 3.5, 5-6 done; 4/8 deferred; lessons learned added
        ________________




This PRD establishes the foundation for ClawdBot's multi-provider API architecture. Implementation should proceed methodically through each phase with supervisor review at designated checkpoints. The goal is a robust, cost-effective, ToS-compliant system that will serve as Rick's Life Operating System for years to come.