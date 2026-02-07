# Knowledge Graph Skill — Phase 1 Implementation Plan

## What We're Building

A knowledge graph skill for ClawdBot that stores entities (people, projects, concepts, organizations, resources, events, places) and their relationships across all seven life domains (Ministry, Chapel, Trading, Dev, Family, Personal, Content). File-based, integrates with existing memory search, never bloats context.

## Architecture (Confirmed by ClawdBot)

**Location:** `memory/context/kg/<type>/<slug>/`
- `entity.json` — identity + metadata
- `facts.json` — atomic facts array (append-only, supersede pattern)
- `summary.md` — auto-generated search surface (~300 tokens max)

**Why this works:**
- Memory search glob is `memory/**/*.md` — recursive, catches all summary.md files automatically
- JSON files are NOT indexed by memory search — that's fine, `kg.py` reads them directly via filesystem
- No bootstrap impact — KG files only enter context via memory_search results
- At 200 entities (~60K tokens of summaries), search performance is trivial (~200-300 vectors)

**Core principle: Thin retrieval, deep on demand.** Summaries are the search surface. JSON is depth. Skill only loads when triggered. Typical KG interaction adds <2K tokens to context.

## Deliverables (Phase 1 — CC-B)

### 1. `skills/knowledge-graph/SKILL.md`

```yaml
---
name: knowledge-graph
description: >
  Maintain ClawdBot's knowledge graph of people, projects, concepts, and their
  relationships across all seven life domains. Use when Rick mentions new facts
  about people or entities, asks about connections between things, needs to track
  institutional knowledge, or queries what he knows about a person, project, or
  concept. Triggers on: "who is", "what do I know about", "connections between",
  "add to knowledge graph", "/kg", entity relationship queries, domain-wide
  queries, and when new facts emerge in conversation.
---
```

Body should include: command reference, entity types, category examples, usage guidance. Stay under 500 lines.

### 2. `skills/knowledge-graph/scripts/kg.py`

Single Python script. No external dependencies (stdlib only). All commands via CLI:

**Commands for Phase 1:**
- `add-entity` — Create entity directory + files. **Must check aliases of existing entities first to prevent duplicates.**
- `add-fact` — Append fact to facts.json with auto-incrementing ID
- `supersede` — Mark old fact as superseded, add new fact referencing it
- `add-relation` — Add relationship fact with structured relation metadata (unidirectional storage)
- `query` — Return entity summary + all active facts (reads files directly, not via memory_get)
- `connections` — Return all relationships for an entity. Include `--reverse` flag that scans other entities for inbound relationships.
- `search` — Search across all entity summaries and facts by keyword
- `domain` — List entities filtered by domain
- `list` — List all entities, optionally filtered by `--type`
- `stats` — Count entities by type and domain
- `summarize` — Regenerate summary.md from active facts. Include `--all` flag to regenerate all summaries. Include `--dirty` flag to only regenerate where facts.json mtime > summary.md mtime.
- `merge` — Merge two entities: move facts from source to target, update relationship references, redirect aliases, delete source directory.
- `archive` — Soft-delete: set entity status to "archived", excluded from normal queries but data preserved. `--include-archived` flag on query/list/search to show them.

**Security requirements (non-negotiable):**
- Slugs sanitized to `[a-z0-9-]` only — reject anything else
- No path traversal — validate all paths stay within `memory/context/kg/`
- No network calls
- No subprocess/eval/os.system
- Atomic writes — write to temp file, then os.rename()
- Maximum fact length enforced (e.g., 500 chars)
- Input validation on all parameters with clear error messages

**Entity types:** person, project, concept, organization, resource, event, place

**Relationship types (starter set):** member_of, works_with, leads, part_of, relates_to, uses, created_by, taught_in, illustrates, opposes

**Fact categories (starter set):** role, activity, relationship, status, preference, belief, skill, milestone, note

### 3. Summary generation rules

The `summarize` command must produce markdown under ~300 tokens:
- Entity name as H1
- Type, domains, aliases on one line
- "Active Facts" section — if >10 active facts, include only the 10 most recent + any with category "role" or "status" (these are identity-defining)
- "Relationships" section — all active relationships, one line each
- Footer with total fact count and last updated date

### 4. Seed data

After building, seed 10-20 entities from MEMORY.md to validate:
- Key people (family members, elders, key volunteers)
- Active projects (dashboard, web-scout, clawdbot)
- 2-3 theological concepts Rick references often
- Key organizations (Centralia CC, St. Peter's Stone Church)

This validates the schema before organic growth.

## entity.json schema

```json
{
  "id": "<type>/<slug>",
  "type": "<entity_type>",
  "slug": "<slug>",
  "name": "<display name>",
  "aliases": ["<alias1>", "<alias2>"],
  "domains": ["<domain1>", "<domain2>"],
  "status": "active",
  "created": "<ISO 8601>",
  "updated": "<ISO 8601>"
}
```

## facts.json schema

```json
[
  {
    "id": "<slug>-001",
    "fact": "<atomic fact text, max 500 chars>",
    "category": "<fact_category>",
    "source": "conversation|document|import|manual",
    "created": "<ISO 8601>",
    "status": "active|superseded",
    "supersedes": "<fact_id or null>",
    "superseded_by": "<fact_id or null>",
    "relation": {
      "type": "<relationship_type>",
      "target": "<type/slug>",
      "context": "<brief context>"
    }
  }
]
```

The `relation` field is only present on facts with category "relationship".

## Testing

After implementation, run a 10-prompt skill detection test:
1. "Add Elder James to the knowledge graph"
2. "What do I know about the dashboard project?"
3. "/kg list --type person"
4. "Who's connected to St. Peter's Stone Church?"
5. "Note that Elder James leads the men's Bible study"
6. "Show me all my trading concepts"
7. "/kg domain chapel"
8. "What are the connections between my sermon series and theological concepts?"
9. "/kg stats"
10. "Archive the old prayer group project"

Target: 8/10 correct triggers.

Also test:
- Path traversal attempt: `kg.py add-entity --type person --slug "../../etc/passwd"` → must reject
- Alias collision: create entity, then create another with same alias → must warn
- Supersede chain: create fact, supersede it, verify summary only shows active
- Archive: archive entity, verify it's hidden from normal list but visible with --include-archived
- Merge: create two entities, merge them, verify facts consolidated and source removed
- Summary token size: entity with 20+ facts → summary must still be under ~300 tokens

## Governance

This is CC-B: plan → code review → push. No --full-auto, no --yolo. Code review before deploying to skills/.
