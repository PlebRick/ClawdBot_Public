---
name: knowledge-graph
description: >
  Structured knowledge store for entities (people, projects, concepts, organizations),
  their facts, and relationships across all seven life domains. Use when Rick mentions
  new facts about people or entities, asks about connections, needs to track institutional
  knowledge, or queries what he knows about a person, project, or concept. Triggers on:
  "who is", "what do I know about", "connections between", "add to knowledge graph", "/kg",
  entity relationship queries, domain-wide queries, and when new facts emerge in conversation.
metadata:
  clawdbot:
    emoji: "🔗"
---

# Knowledge Graph — Structured Entity-Relationship Storage

Typed entities with atomic facts, supersede chains, typed relationships, and auto-generated
summaries that feed into `memory_search` (searches `memory/**/*.md` recursively).

## When to Use

- Rick mentions a **new fact about a person, project, or concept** — add it
- Rick asks **"who is X"** or **"what do I know about X"** — query the KG
- Rick asks about **connections between** people/projects/concepts
- Rick says **"add to knowledge graph"** or **/kg**
- **Domain-wide queries**: "what's going on in ministry?" or "show me trading entities"
- When new **institutional knowledge** emerges in conversation (roles, milestones, preferences)
- Rick wants to **track evolving information** (supersede old facts with new ones)

## Quick Start

```bash
# Add an entity
python3 skills/knowledge-graph/scripts/kg.py add-entity --type person --name "John Smith" --domains ministry

# Add a fact
python3 skills/knowledge-graph/scripts/kg.py add-fact person/john-smith --fact "Volunteer at St. Peter's" --category role

# Query it
python3 skills/knowledge-graph/scripts/kg.py query person/john-smith

# Search across everything
python3 skills/knowledge-graph/scripts/kg.py search "volunteer"
```

## Commands

Run via: `python3 skills/knowledge-graph/scripts/kg.py <command>`

| Command | What it does |
|---------|-------------|
| `add-entity` | Create a new entity with type, name, domains, aliases |
| `add-fact` | Add an atomic fact to an entity |
| `supersede` | Replace an old fact with a new one (preserves history) |
| `add-relation` | Create a typed relationship between two entities |
| `query` | Return entity metadata + all active facts |
| `connections` | Show outbound relations; `--reverse` for inbound too |
| `search` | Full-text search across names, aliases, domains, facts, summaries |
| `domain` | Filter entities by life domain |
| `list` | List all entities, optionally filtered by `--type` |
| `stats` | Counts by type, domain, total/active facts, archived |
| `summarize` | Regenerate summary.md — single entity, `--all`, or `--dirty` |
| `archive` | Archive an entity; `--unarchive` to restore |
| `merge` | Merge source entity into target (moves facts, updates relations) |
| `seed` | Populate KG with built-in seed data (~17 entities) |

## Command Reference

### add-entity
```bash
python3 skills/knowledge-graph/scripts/kg.py add-entity --type person --name "John Smith" --domains "ministry,family" --aliases "Johnny"
# --force to skip duplicate/alias collision check
```

### add-fact
```bash
python3 skills/knowledge-graph/scripts/kg.py add-fact person/john-smith --fact "Started volunteering Feb 2026" --category milestone
# Categories: role, activity, relationship, status, preference, belief, skill, milestone, note
# Max 500 characters per fact
```

### supersede
```bash
python3 skills/knowledge-graph/scripts/kg.py supersede person/john-smith john-smith-001 --fact "Now leads the volunteer team"
# Marks old fact as superseded, creates new fact inheriting category
```

### add-relation
```bash
python3 skills/knowledge-graph/scripts/kg.py add-relation person/john-smith organization/st-peters-stone-church --relation-type member_of
# Auto-generates fact text if --fact not provided
# Relation types: member_of, works_with, leads, part_of, relates_to, uses, created_by, taught_in, illustrates, opposes
```

### query
```bash
python3 skills/knowledge-graph/scripts/kg.py query person/rick-arnold
python3 skills/knowledge-graph/scripts/kg.py query person/rick-arnold --include-archived
```

### connections
```bash
python3 skills/knowledge-graph/scripts/kg.py connections person/rick-arnold
python3 skills/knowledge-graph/scripts/kg.py connections person/rick-arnold --reverse
```

### search
```bash
python3 skills/knowledge-graph/scripts/kg.py search "chaplain"
python3 skills/knowledge-graph/scripts/kg.py search "bitcoin" --include-archived
```

### domain
```bash
python3 skills/knowledge-graph/scripts/kg.py domain ministry
python3 skills/knowledge-graph/scripts/kg.py domain trading
```

### list
```bash
python3 skills/knowledge-graph/scripts/kg.py list
python3 skills/knowledge-graph/scripts/kg.py list --type person
python3 skills/knowledge-graph/scripts/kg.py list --include-archived
```

### stats
```bash
python3 skills/knowledge-graph/scripts/kg.py stats
```

### summarize
```bash
python3 skills/knowledge-graph/scripts/kg.py summarize person/rick-arnold
python3 skills/knowledge-graph/scripts/kg.py summarize --all
python3 skills/knowledge-graph/scripts/kg.py summarize --dirty   # only stale summaries
```

### archive / unarchive
```bash
python3 skills/knowledge-graph/scripts/kg.py archive person/old-contact
python3 skills/knowledge-graph/scripts/kg.py archive person/old-contact --unarchive
```

### merge
```bash
python3 skills/knowledge-graph/scripts/kg.py merge person/duplicate-name person/canonical-name
# Moves all facts, merges aliases/domains, updates cross-entity relation targets, deletes source
```

### seed
```bash
python3 skills/knowledge-graph/scripts/kg.py seed
python3 skills/knowledge-graph/scripts/kg.py seed --force   # re-seed even if entities exist
```

## Entity Types

| Type | Description | Examples |
|------|-------------|---------|
| `person` | People Rick knows or references | Rick Arnold, Maria Arnold, Mark Driscoll |
| `project` | Active or planned projects | ClawdBot, ArnoldOS, Sermon Pipeline |
| `concept` | Theological or intellectual concepts | Prevenient Grace, Molinism, Theological Triage |
| `organization` | Churches, institutions, companies | St. Peter's, Centralia CC, Pinckneyville CC |
| `resource` | Tools, documents, references | Voice Profile, Morning Brief |
| `event` | Specific events or milestones | Conferences, missions trips |
| `place` | Locations | Nashville IL, mission field locations |

## Relationship Types

| Type | Meaning | Example |
|------|---------|---------|
| `member_of` | Belongs to organization/group | Rick member_of Centralia CC |
| `works_with` | Collaborates with | Person works_with Person |
| `leads` | Leadership role | Rick leads St. Peter's |
| `part_of` | Component/subset | ArnoldOS part_of ClawdBot |
| `relates_to` | General association | Concept relates_to Concept |
| `uses` | Employs/utilizes | Rick uses Molinism |
| `created_by` | Authorship/creation | ClawdBot created_by Rick |
| `taught_in` | Educational context | Concept taught_in Organization |
| `illustrates` | Demonstrates/exemplifies | Event illustrates Concept |
| `opposes` | Contradicts/conflicts | Concept opposes Concept |

## Fact Categories

| Category | Use for |
|----------|---------|
| `role` | Current positions, titles, responsibilities |
| `activity` | Ongoing activities, projects, habits |
| `relationship` | Auto-set for relation facts |
| `status` | Current state, phase, condition |
| `preference` | Likes, dislikes, preferences |
| `belief` | Theological positions, convictions |
| `skill` | Abilities, competencies |
| `milestone` | Achieved events, dates, accomplishments |
| `note` | General notes that don't fit other categories |

## Data Location

```
memory/context/kg/
  person/
    rick-arnold/
      entity.json    # metadata: name, type, domains, aliases, status
      facts.json     # array of atomic facts with supersede chains
      summary.md     # auto-generated, searchable by memory_search
    maria-arnold/
      ...
  project/
    clawdbot/
      ...
  concept/
    prevenient-grace/
      ...
  organization/
    ...
```

## Workflow Examples

### When Rick mentions someone new
```
Rick: "I had lunch with Dave Thompson — he's the new youth pastor at First Baptist"

1. kg.py add-entity --type person --name "Dave Thompson" --domains ministry
2. kg.py add-fact person/dave-thompson --fact "Youth pastor at First Baptist" --category role
3. kg.py add-relation person/dave-thompson organization/first-baptist --relation-type member_of
```

### When a fact changes
```
Rick: "Dave moved to the senior pastor role"

1. kg.py query person/dave-thompson   # find the current role fact ID
2. kg.py supersede person/dave-thompson dave-thompson-001 --fact "Senior pastor at First Baptist"
```

### When Rick asks "what do I know about X"
```
1. kg.py query person/dave-thompson
2. kg.py connections person/dave-thompson --reverse
# Present entity facts + incoming/outgoing relationships
```

### Periodic maintenance
```bash
kg.py summarize --dirty    # regenerate stale summaries
kg.py stats                # check overall KG health
```

## When NOT to Use

- Transient information (today's schedule, weather) — use ArnoldOS
- Sermon content or Bible study — use sermon-writer, bible-brainstorm
- File operations on Drive — use ArnoldOS
- Quick facts that don't need to persist across sessions
