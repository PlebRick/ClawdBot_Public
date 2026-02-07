#!/usr/bin/env python3
"""Knowledge Graph — Structured entity-relationship storage for ClawdBot.

Typed entities, atomic facts with supersede chains, typed relationships,
and auto-generated summaries that feed into memory_search.

Usage:
  python3 skills/knowledge-graph/scripts/kg.py <command> [args]
  python3 skills/knowledge-graph/scripts/kg.py --help
"""

import sys
import os
import json
import re
import tempfile
import argparse
from datetime import datetime
from pathlib import Path

# --- Constants ---

KG_ROOT = Path.home() / "clawd" / "memory" / "context" / "kg"
LOG_FILE = Path.home() / "clawd" / "logs" / "kg.log"

ENTITY_TYPES = ["person", "project", "concept", "organization", "resource", "event", "place"]
RELATION_TYPES = [
    "member_of", "works_with", "leads", "part_of", "relates_to",
    "uses", "created_by", "taught_in", "illustrates", "opposes",
]
FACT_CATEGORIES = [
    "role", "activity", "relationship", "status", "preference",
    "belief", "skill", "milestone", "note",
]

MAX_FACT_LENGTH = 500

# --- Utilities ---


def log(msg: str):
    """Timestamped append to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def output(data):
    """JSON output to stdout."""
    print(json.dumps(data, indent=2))


def error_out(msg: str):
    """Output error JSON and exit."""
    output({"error": msg})
    sys.exit(1)


def slugify(name: str) -> str:
    """Lowercase, replace non-alnum with hyphens, collapse multiples."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def validate_slug(slug: str) -> bool:
    return bool(re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", slug)) or bool(re.match(r"^[a-z0-9]$", slug))


def validate_entity_id(entity_id: str) -> tuple:
    """Parse and validate 'type/slug'. Returns (type, slug) or raises."""
    parts = entity_id.split("/")
    if len(parts) != 2:
        error_out(f"Invalid entity ID '{entity_id}': must be type/slug")
    etype, slug = parts
    if etype not in ENTITY_TYPES:
        error_out(f"Invalid entity type '{etype}': must be one of {ENTITY_TYPES}")
    if not validate_slug(slug):
        error_out(f"Invalid slug '{slug}': must be [a-z0-9-] only")
    return etype, slug


def entity_dir(entity_id: str) -> Path:
    """Return Path for entity, with path traversal check."""
    etype, slug = validate_entity_id(entity_id)
    d = KG_ROOT / etype / slug
    if not d.resolve().as_posix().startswith(KG_ROOT.resolve().as_posix()):
        error_out(f"Path traversal detected in '{entity_id}'")
    return d


def atomic_write_json(path: Path, data):
    """Write JSON atomically via tempfile + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.rename(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, text: str):
    """Write text atomically via tempfile + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.rename(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_entity(entity_id: str) -> dict:
    """Load entity.json for given entity ID."""
    d = entity_dir(entity_id)
    path = d / "entity.json"
    if not path.exists():
        error_out(f"Entity '{entity_id}' not found")
    with open(path) as f:
        return json.load(f)


def load_facts(entity_id: str) -> list:
    """Load facts.json for given entity ID."""
    d = entity_dir(entity_id)
    path = d / "facts.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def save_facts(entity_id: str, facts: list):
    """Save facts.json for given entity ID."""
    d = entity_dir(entity_id)
    atomic_write_json(d / "facts.json", facts)


def save_entity(entity_id: str, entity: dict):
    """Save entity.json for given entity ID."""
    d = entity_dir(entity_id)
    atomic_write_json(d / "entity.json", entity)


def list_all_entity_ids() -> list:
    """Iterate KG_ROOT to find all entity IDs."""
    ids = []
    if not KG_ROOT.exists():
        return ids
    for etype_dir in sorted(KG_ROOT.iterdir()):
        if not etype_dir.is_dir():
            continue
        etype = etype_dir.name
        if etype not in ENTITY_TYPES:
            continue
        for slug_dir in sorted(etype_dir.iterdir()):
            if not slug_dir.is_dir():
                continue
            if (slug_dir / "entity.json").exists():
                ids.append(f"{etype}/{slug_dir.name}")
    return ids


def find_by_alias(name: str, exclude_id: str = None) -> list:
    """Scan all entities for name/alias collisions. Returns list of matching entity IDs."""
    matches = []
    name_lower = name.lower().strip()
    slug = slugify(name)
    for eid in list_all_entity_ids():
        if eid == exclude_id:
            continue
        entity = load_entity(eid)
        if entity["name"].lower().strip() == name_lower:
            matches.append(eid)
        elif slug == eid.split("/")[1]:
            matches.append(eid)
        elif name_lower in [a.lower() for a in entity.get("aliases", [])]:
            matches.append(eid)
    return matches


def next_fact_id(facts: list, slug: str) -> str:
    """Generate next fact ID based on max existing."""
    max_num = 0
    for f in facts:
        fid = f.get("id", "")
        parts = fid.rsplit("-", 1)
        if len(parts) == 2:
            try:
                max_num = max(max_num, int(parts[1]))
            except ValueError:
                pass
    return f"{slug}-{max_num + 1:03d}"


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# --- Commands ---


def cmd_add_entity(args):
    """Create a new entity."""
    etype = args.type
    name = args.name.strip()
    slug = slugify(name)

    if not validate_slug(slug):
        error_out(f"Name '{name}' produces invalid slug '{slug}'")

    entity_id = f"{etype}/{slug}"

    # Path traversal check
    d = entity_dir(entity_id)

    # Duplicate check
    if not args.force:
        collisions = find_by_alias(name)
        if collisions:
            error_out(f"Name/alias collision with: {collisions}. Use --force to override.")

    if d.exists() and (d / "entity.json").exists():
        if not args.force:
            error_out(f"Entity '{entity_id}' already exists. Use --force to overwrite.")

    domains = [x.strip() for x in args.domains.split(",")] if args.domains else []
    aliases = [x.strip() for x in args.aliases.split(",")] if args.aliases else []

    entity = {
        "id": entity_id,
        "type": etype,
        "name": name,
        "slug": slug,
        "aliases": aliases,
        "domains": domains,
        "status": "active",
        "created": now_iso(),
        "updated": now_iso(),
    }

    d.mkdir(parents=True, exist_ok=True)
    atomic_write_json(d / "entity.json", entity)
    atomic_write_json(d / "facts.json", [])
    atomic_write_text(d / "summary.md", f"# {name}\n\nNo facts recorded yet.\n")

    log(f"add-entity: {entity_id}")
    output({"ok": True, "entity_id": entity_id, "entity": entity})


def cmd_add_fact(args):
    """Add a fact to an entity."""
    entity_id = args.entity_id
    entity = load_entity(entity_id)

    if entity.get("status") == "archived":
        error_out(f"Entity '{entity_id}' is archived. Unarchive first.")

    fact_text = args.fact.strip()
    if len(fact_text) > MAX_FACT_LENGTH:
        error_out(f"Fact too long ({len(fact_text)} chars, max {MAX_FACT_LENGTH})")

    category = args.category
    if category not in FACT_CATEGORIES:
        error_out(f"Invalid category '{category}': must be one of {FACT_CATEGORIES}")

    facts = load_facts(entity_id)
    slug = entity_id.split("/")[1]
    fact_id = next_fact_id(facts, slug)

    fact = {
        "id": fact_id,
        "text": fact_text,
        "category": category,
        "status": "active",
        "created": now_iso(),
        "source": args.source or "conversation",
    }

    facts.append(fact)
    save_facts(entity_id, facts)

    # Update entity timestamp
    entity["updated"] = now_iso()
    save_entity(entity_id, entity)

    log(f"add-fact: {entity_id} {fact_id}")
    output({"ok": True, "entity_id": entity_id, "fact": fact})


def cmd_supersede(args):
    """Supersede an existing fact with a new one."""
    entity_id = args.entity_id
    old_fact_id = args.old_fact_id
    entity = load_entity(entity_id)

    if entity.get("status") == "archived":
        error_out(f"Entity '{entity_id}' is archived. Unarchive first.")

    facts = load_facts(entity_id)
    old_fact = None
    for f in facts:
        if f["id"] == old_fact_id:
            old_fact = f
            break

    if not old_fact:
        error_out(f"Fact '{old_fact_id}' not found in '{entity_id}'")
    if old_fact.get("status") == "superseded":
        error_out(f"Fact '{old_fact_id}' is already superseded")

    fact_text = args.fact.strip()
    if len(fact_text) > MAX_FACT_LENGTH:
        error_out(f"Fact too long ({len(fact_text)} chars, max {MAX_FACT_LENGTH})")

    # Mark old fact as superseded
    old_fact["status"] = "superseded"
    old_fact["superseded_at"] = now_iso()

    # Create new fact inheriting category and relation
    slug = entity_id.split("/")[1]
    new_fact_id = next_fact_id(facts, slug)
    new_fact = {
        "id": new_fact_id,
        "text": fact_text,
        "category": old_fact.get("category", "note"),
        "status": "active",
        "created": now_iso(),
        "supersedes": old_fact_id,
        "source": args.source or "conversation",
    }
    if "relation" in old_fact:
        new_fact["relation"] = old_fact["relation"]

    facts.append(new_fact)
    save_facts(entity_id, facts)

    entity["updated"] = now_iso()
    save_entity(entity_id, entity)

    log(f"supersede: {entity_id} {old_fact_id} -> {new_fact_id}")
    output({"ok": True, "entity_id": entity_id, "old_fact_id": old_fact_id, "new_fact": new_fact})


def cmd_add_relation(args):
    """Add a relationship fact between two entities."""
    entity_id = args.entity_id
    target_id = args.target_id
    relation_type = args.relation_type

    entity = load_entity(entity_id)
    if entity.get("status") == "archived":
        error_out(f"Entity '{entity_id}' is archived. Unarchive first.")

    # Validate target exists
    target = load_entity(target_id)

    if relation_type not in RELATION_TYPES:
        error_out(f"Invalid relation type '{relation_type}': must be one of {RELATION_TYPES}")

    # Auto-generate fact text if not provided
    if args.fact:
        fact_text = args.fact.strip()
    else:
        fact_text = f"{entity['name']} {relation_type.replace('_', ' ')} {target['name']}"

    if len(fact_text) > MAX_FACT_LENGTH:
        error_out(f"Fact too long ({len(fact_text)} chars, max {MAX_FACT_LENGTH})")

    facts = load_facts(entity_id)
    slug = entity_id.split("/")[1]
    fact_id = next_fact_id(facts, slug)

    fact = {
        "id": fact_id,
        "text": fact_text,
        "category": "relationship",
        "status": "active",
        "created": now_iso(),
        "source": args.source or "conversation",
        "relation": {
            "type": relation_type,
            "target": target_id,
        },
    }

    facts.append(fact)
    save_facts(entity_id, facts)

    entity["updated"] = now_iso()
    save_entity(entity_id, entity)

    log(f"add-relation: {entity_id} --{relation_type}--> {target_id}")
    output({"ok": True, "entity_id": entity_id, "fact": fact})


def cmd_query(args):
    """Return entity + active facts."""
    entity_id = args.entity_id
    entity = load_entity(entity_id)

    if entity.get("status") == "archived" and not args.include_archived:
        error_out(f"Entity '{entity_id}' is archived. Use --include-archived to view.")

    facts = load_facts(entity_id)
    if not args.include_archived:
        active_facts = [f for f in facts if f.get("status") == "active"]
    else:
        active_facts = facts

    result = {
        "entity": entity,
        "facts": active_facts,
        "total_facts": len(facts),
        "active_facts": len([f for f in facts if f.get("status") == "active"]),
    }

    # Include summary if exists
    summary_path = entity_dir(entity_id) / "summary.md"
    if summary_path.exists():
        result["summary_exists"] = True

    output(result)


def cmd_connections(args):
    """Show connections for an entity."""
    entity_id = args.entity_id
    _ = load_entity(entity_id)  # validate exists

    outbound = []
    facts = load_facts(entity_id)
    for f in facts:
        if f.get("status") == "active" and "relation" in f:
            outbound.append({
                "fact_id": f["id"],
                "relation_type": f["relation"]["type"],
                "target": f["relation"]["target"],
                "text": f["text"],
            })

    result = {"entity_id": entity_id, "outbound": outbound}

    if args.reverse:
        inbound = []
        for eid in list_all_entity_ids():
            if eid == entity_id:
                continue
            for f in load_facts(eid):
                if f.get("status") == "active" and "relation" in f:
                    if f["relation"]["target"] == entity_id:
                        inbound.append({
                            "fact_id": f["id"],
                            "source_entity": eid,
                            "relation_type": f["relation"]["type"],
                            "text": f["text"],
                        })
        result["inbound"] = inbound

    output(result)


def cmd_search(args):
    """Search all entities by text."""
    query = args.query.lower().strip()
    if not query:
        error_out("Search query cannot be empty")

    results = []
    for eid in list_all_entity_ids():
        entity = load_entity(eid)
        if entity.get("status") == "archived" and not args.include_archived:
            continue

        matched = False
        match_reasons = []

        # Match name
        if query in entity["name"].lower():
            matched = True
            match_reasons.append("name")

        # Match aliases
        for alias in entity.get("aliases", []):
            if query in alias.lower():
                matched = True
                match_reasons.append("alias")
                break

        # Match domains
        for domain in entity.get("domains", []):
            if query in domain.lower():
                matched = True
                match_reasons.append("domain")
                break

        # Match facts
        matching_facts = []
        for f in load_facts(eid):
            if f.get("status") != "active":
                continue
            if query in f["text"].lower():
                matching_facts.append(f)
                if not matched:
                    matched = True
                    match_reasons.append("fact")

        # Match summary
        summary_path = entity_dir(eid) / "summary.md"
        if summary_path.exists():
            summary_text = summary_path.read_text()
            if query in summary_text.lower():
                if not matched:
                    matched = True
                    match_reasons.append("summary")

        if matched:
            results.append({
                "entity_id": eid,
                "name": entity["name"],
                "type": entity["type"],
                "match_reasons": match_reasons,
                "matching_facts": matching_facts[:5],
            })

    output({"query": query, "results": results, "count": len(results)})


def cmd_domain(args):
    """Filter entities by domain."""
    domain = args.domain.lower().strip()
    results = []
    for eid in list_all_entity_ids():
        entity = load_entity(eid)
        if entity.get("status") == "archived" and not args.include_archived:
            continue
        entity_domains = [d.lower() for d in entity.get("domains", [])]
        if domain in entity_domains:
            results.append({
                "entity_id": eid,
                "name": entity["name"],
                "type": entity["type"],
                "domains": entity.get("domains", []),
            })

    output({"domain": domain, "entities": results, "count": len(results)})


def cmd_list(args):
    """List all entities."""
    results = []
    for eid in list_all_entity_ids():
        entity = load_entity(eid)
        if entity.get("status") == "archived" and not args.include_archived:
            continue
        if args.type and entity["type"] != args.type:
            continue
        facts = load_facts(eid)
        active_count = len([f for f in facts if f.get("status") == "active"])
        results.append({
            "entity_id": eid,
            "name": entity["name"],
            "type": entity["type"],
            "domains": entity.get("domains", []),
            "status": entity.get("status", "active"),
            "active_facts": active_count,
        })

    results.sort(key=lambda x: x["name"].lower())
    output({"entities": results, "count": len(results)})


def cmd_stats(args):
    """Show counts by type, domain, total facts, etc."""
    by_type = {}
    by_domain = {}
    total_facts = 0
    active_facts = 0
    archived_entities = 0

    for eid in list_all_entity_ids():
        entity = load_entity(eid)
        etype = entity["type"]
        by_type[etype] = by_type.get(etype, 0) + 1

        if entity.get("status") == "archived":
            archived_entities += 1

        for d in entity.get("domains", []):
            by_domain[d] = by_domain.get(d, 0) + 1

        facts = load_facts(eid)
        total_facts += len(facts)
        active_facts += len([f for f in facts if f.get("status") == "active"])

    total_entities = sum(by_type.values())

    output({
        "total_entities": total_entities,
        "by_type": by_type,
        "by_domain": by_domain,
        "total_facts": total_facts,
        "active_facts": active_facts,
        "archived_entities": archived_entities,
    })


def generate_summary(entity_id: str) -> str:
    """Generate summary.md content for an entity."""
    entity = load_entity(entity_id)
    facts = load_facts(entity_id)
    active = [f for f in facts if f.get("status") == "active"]

    lines = []
    lines.append(f"# {entity['name']}")
    lines.append("")

    # Metadata line
    meta_parts = [f"**Type:** {entity['type']}"]
    if entity.get("domains"):
        meta_parts.append(f"**Domains:** {', '.join(entity['domains'])}")
    if entity.get("aliases"):
        meta_parts.append(f"**Aliases:** {', '.join(entity['aliases'])}")
    lines.append(" | ".join(meta_parts))
    lines.append("")

    # Separate relation vs non-relation facts
    relation_facts = [f for f in active if "relation" in f]
    non_relation_facts = [f for f in active if "relation" not in f]

    # Active Facts section
    if non_relation_facts:
        lines.append("## Active Facts")
        lines.append("")

        # If >10, keep 10 most recent + all role/status facts
        if len(non_relation_facts) > 10:
            priority = [f for f in non_relation_facts if f.get("category") in ("role", "status")]
            rest = [f for f in non_relation_facts if f.get("category") not in ("role", "status")]
            rest.sort(key=lambda x: x.get("created", ""), reverse=True)
            keep = rest[:10]
            shown = list({f["id"]: f for f in priority + keep}.values())
            shown.sort(key=lambda x: x.get("created", ""))
        else:
            shown = non_relation_facts

        for f in shown:
            cat = f.get("category", "note")
            lines.append(f"- [{cat}] {f['text']}")
        lines.append("")

    # Relationships section
    if relation_facts:
        lines.append("## Relationships")
        lines.append("")
        for f in relation_facts:
            rel = f["relation"]
            lines.append(f"- {rel['type'].replace('_', ' ')} → {rel['target']}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*{len(active)} active facts | Last updated: {entity.get('updated', 'unknown')}*")
    lines.append("")

    return "\n".join(lines)


def cmd_summarize(args):
    """Regenerate summary.md for one or all entities."""
    if args.all:
        entity_ids = list_all_entity_ids()
    elif args.dirty:
        entity_ids = []
        for eid in list_all_entity_ids():
            entity = load_entity(eid)
            summary_path = entity_dir(eid) / "summary.md"
            if not summary_path.exists():
                entity_ids.append(eid)
                continue
            updated_str = entity.get("updated", "")
            if updated_str:
                entity_mtime = datetime.fromisoformat(updated_str).timestamp()
                summary_mtime = summary_path.stat().st_mtime
                if entity_mtime > summary_mtime:
                    entity_ids.append(eid)
    elif args.entity_id:
        entity_ids = [args.entity_id]
    else:
        error_out("Specify an entity ID, --all, or --dirty")

    summaries = []
    for eid in entity_ids:
        _ = load_entity(eid)  # validate
        text = generate_summary(eid)
        summary_path = entity_dir(eid) / "summary.md"
        atomic_write_text(summary_path, text)
        summaries.append(eid)
        log(f"summarize: {eid}")

    output({"ok": True, "summarized": summaries, "count": len(summaries)})


def cmd_archive(args):
    """Archive or unarchive an entity."""
    entity_id = args.entity_id
    entity = load_entity(entity_id)

    if args.unarchive:
        if entity.get("status") != "archived":
            error_out(f"Entity '{entity_id}' is not archived")
        entity["status"] = "active"
        entity["updated"] = now_iso()
        save_entity(entity_id, entity)
        log(f"unarchive: {entity_id}")
        output({"ok": True, "entity_id": entity_id, "status": "active"})
    else:
        if entity.get("status") == "archived":
            error_out(f"Entity '{entity_id}' is already archived")
        entity["status"] = "archived"
        entity["updated"] = now_iso()
        save_entity(entity_id, entity)
        log(f"archive: {entity_id}")
        output({"ok": True, "entity_id": entity_id, "status": "archived"})


def cmd_merge(args):
    """Merge source entity into target entity."""
    import shutil

    source_id = args.source_id
    target_id = args.target_id

    if source_id == target_id:
        error_out("Cannot merge an entity into itself")

    source = load_entity(source_id)
    target = load_entity(target_id)

    source_facts = load_facts(source_id)
    target_facts = load_facts(target_id)

    target_slug = target_id.split("/")[1]

    # Re-ID source facts with target's slug
    for f in source_facts:
        new_id = next_fact_id(target_facts + source_facts, target_slug)
        old_id = f["id"]
        f["id"] = new_id
        f["merged_from"] = f"{source_id}:{old_id}"
        # Update supersedes references
        if "supersedes" in f:
            # Find the new ID for the superseded fact
            for f2 in source_facts:
                if f2.get("merged_from", "").endswith(f":{f['supersedes']}"):
                    f["supersedes"] = f2["id"]
                    break
        target_facts.append(f)

    # Merge aliases
    source_aliases = source.get("aliases", [])
    target_aliases = target.get("aliases", [])
    # Add source name as alias if different from target name
    if source["name"].lower() != target["name"].lower():
        source_aliases.append(source["name"])
    for alias in source_aliases:
        if alias not in target_aliases and alias.lower() != target["name"].lower():
            target_aliases.append(alias)
    target["aliases"] = target_aliases

    # Merge domains
    source_domains = source.get("domains", [])
    target_domains = target.get("domains", [])
    for d in source_domains:
        if d not in target_domains:
            target_domains.append(d)
    target["domains"] = target_domains

    # Update cross-entity relation targets
    for eid in list_all_entity_ids():
        if eid == source_id:
            continue
        facts = load_facts(eid)
        changed = False
        for f in facts:
            if "relation" in f and f["relation"]["target"] == source_id:
                f["relation"]["target"] = target_id
                changed = True
        if changed:
            save_facts(eid, facts)

    target["updated"] = now_iso()
    save_entity(target_id, target)
    save_facts(target_id, target_facts)

    # Delete source directory
    source_dir = entity_dir(source_id)
    shutil.rmtree(source_dir)

    log(f"merge: {source_id} -> {target_id}")
    output({
        "ok": True,
        "merged": source_id,
        "into": target_id,
        "facts_moved": len(source_facts),
    })


# --- Seed Data ---

SEED_DATA = {
    "entities": [
        {
            "type": "person", "name": "Rick Arnold",
            "domains": ["ministry", "chapel", "trading", "dev", "family", "personal", "content"],
            "aliases": ["Rick"],
            "facts": [
                ("role", "Senior chaplain at Centralia Correctional Center (IDOC)"),
                ("role", "Part-time pastor at St. Peter's Stone Church — preaches bimonthly"),
                ("activity", "Leads Walking in the Spirit teaching series (2026)"),
                ("activity", "Developing On Mission with the Master — Romans expository series"),
                ("skill", "Expository preaching influenced by Stott, Driscoll, Finney style"),
                ("preference", "Bible-based, Christ-centered, Spirit-filled, Mission-minded"),
                ("belief", "Prevenient grace, unlimited atonement, corporate election"),
                ("belief", "Molinism — middle knowledge framework for sovereignty and freedom"),
                ("status", "Ordained through Evangelical Church Alliance"),
                ("milestone", "12 years missions: Russia, India, Afghanistan, Egypt, Malaysia, Serbia (1998-2010)"),
                ("preference", "Serious Bitcoin/crypto investor — follows Benjamin Cowen"),
                ("skill", "Runs Ubuntu Linux server (System76) for ClawdBot infrastructure"),
            ],
        },
        {
            "type": "person", "name": "Maria Arnold",
            "domains": ["family"],
            "aliases": ["Maria"],
            "facts": [
                ("role", "Rick's wife of 25+ years"),
                ("milestone", "Met at missionary training school where she was an instructor"),
                ("activity", "Still goes on missions trips — Rick finances them"),
                ("note", "Super diligent, hardworking — they hope to serve together after retirement"),
            ],
        },
        {
            "type": "person", "name": "Mark Driscoll",
            "domains": ["ministry"],
            "aliases": [],
            "facts": [
                ("role", "Preacher and author — theological influence on Rick"),
                ("note", "Rick takes preaching style and directness from Driscoll"),
            ],
        },
        {
            "type": "person", "name": "Benjamin Cowen",
            "domains": ["trading"],
            "aliases": ["Ben Cowen"],
            "facts": [
                ("role", "Into The Cryptoverse host — crypto analyst"),
                ("note", "Rick's primary crypto analysis source"),
            ],
        },
        {
            "type": "person", "name": "Charles Finney",
            "domains": ["ministry"],
            "aliases": ["Finney"],
            "facts": [
                ("role", "19th century revivalist preacher"),
                ("note", "Rick loves his preaching style and illustrations but rejects entire sanctification theology"),
                ("note", "Used as rhetorical model, not theological one — gospeltruth.net for material"),
            ],
        },
        {
            "type": "person", "name": "N.T. Wright",
            "domains": ["ministry"],
            "aliases": ["Tom Wright"],
            "facts": [
                ("role", "New Testament scholar and theologian"),
                ("note", "Rick appreciates Wright's covenant faithfulness, kingdom now/not-yet, resurrection of all things"),
            ],
        },
        {
            "type": "project", "name": "ClawdBot",
            "domains": ["dev"],
            "aliases": ["Clawd"],
            "facts": [
                ("status", "Active — Rick's AI assistant running on System76 Ubuntu server"),
                ("note", "Gateway at ai.btctx.us, Claude API backend, custom skills architecture"),
                ("note", "Manages calendar, tasks, Drive, memory, sermon pipeline, morning brief"),
            ],
        },
        {
            "type": "project", "name": "ArnoldOS",
            "domains": ["dev"],
            "aliases": [],
            "facts": [
                ("status", "Active — Rick's life operating system skill for ClawdBot"),
                ("note", "Google Workspace integration: Calendar, Tasks, Drive across 7 life domains"),
            ],
        },
        {
            "type": "project", "name": "Sermon Pipeline",
            "domains": ["ministry", "dev"],
            "aliases": [],
            "facts": [
                ("status", "Active — ClawdBot skill for sermon development workflow"),
                ("note", "Stages: lectionary reading -> research -> outline -> draft -> review -> delivery"),
            ],
        },
        {
            "type": "organization", "name": "St. Peter's Stone Church",
            "domains": ["ministry"],
            "aliases": ["St. Peter's"],
            "facts": [
                ("note", "Small church where Rick preaches bimonthly as part-time pastor"),
            ],
        },
        {
            "type": "organization", "name": "Centralia Correctional Center",
            "domains": ["chapel"],
            "aliases": ["Centralia CC"],
            "facts": [
                ("note", "IDOC medium-security facility — Rick's current chaplain assignment"),
                ("note", "Rick transferred here after 11 years at Pinckneyville — likes it much better"),
            ],
        },
        {
            "type": "organization", "name": "Pinckneyville Correctional Center",
            "domains": ["chapel"],
            "aliases": ["Pinckneyville CC"],
            "facts": [
                ("note", "IDOC facility where Rick served 11 years as sole chaplain (2014-2025)"),
            ],
        },
        {
            "type": "concept", "name": "Prevenient Grace",
            "domains": ["ministry"],
            "aliases": [],
            "facts": [
                ("belief", "God's grace precedes and enables the human response to the gospel"),
                ("note", "Rick's soteriology order: prevenient grace -> conviction -> repentance -> faith -> regeneration"),
            ],
        },
        {
            "type": "concept", "name": "Molinism",
            "domains": ["ministry"],
            "aliases": ["Middle Knowledge"],
            "facts": [
                ("belief", "God knows what any free creature would do in any circumstance"),
                ("note", "William Lane Craig's framework — preserves genuine freedom and sovereign plan"),
                ("note", "Rick's preferred framework for divine sovereignty and human freedom tension"),
            ],
        },
        {
            "type": "concept", "name": "Theological Triage",
            "domains": ["ministry"],
            "aliases": [],
            "facts": [
                ("belief", "Four buckets: Essentials, Convictions, Opinions, Questions"),
                ("note", "ESV Study Bible model — Rick promotes unity, don't major on minors (Romans 14)"),
            ],
        },
        {
            "type": "resource", "name": "Voice Profile",
            "domains": ["content", "dev"],
            "aliases": [],
            "facts": [
                ("note", "Rick's voice and communication style reference for ClawdBot content generation"),
                ("note", "Direct, storyteller, providence-oriented, practical theologian"),
            ],
        },
        {
            "type": "resource", "name": "Morning Brief",
            "domains": ["dev", "personal"],
            "aliases": [],
            "facts": [
                ("note", "Daily briefing generated by ClawdBot — schedule, tasks, conflicts, preaching prep"),
            ],
        },
    ],
    # Relations use entity names — resolved to IDs at seed time via slugify
    "relations": [
        ("Rick Arnold", "person", "St. Peter's Stone Church", "organization", "leads", None),
        ("Rick Arnold", "person", "Centralia Correctional Center", "organization", "member_of", "Rick is senior chaplain at Centralia CC"),
        ("Rick Arnold", "person", "ClawdBot", "project", "created_by", "Rick built and maintains ClawdBot"),
        ("Rick Arnold", "person", "ArnoldOS", "project", "created_by", "Rick designed ArnoldOS life operating system"),
        ("Rick Arnold", "person", "Prevenient Grace", "concept", "uses", "Core to Rick's soteriology"),
        ("Rick Arnold", "person", "Molinism", "concept", "uses", "Rick's framework for sovereignty and freedom"),
        ("Rick Arnold", "person", "Theological Triage", "concept", "uses", "Rick's method for categorizing doctrines"),
        ("ClawdBot", "project", "ArnoldOS", "project", "part_of", "ArnoldOS is a ClawdBot skill"),
    ],
}


def cmd_seed(args):
    """Seed the knowledge graph with built-in data."""
    if not args.force:
        existing = list_all_entity_ids()
        if existing:
            error_out(f"KG already has {len(existing)} entities. Use --force to seed anyway.")

    created_entities = []
    created_facts = []
    created_relations = []

    for e in SEED_DATA["entities"]:
        etype = e["type"]
        name = e["name"]
        slug = slugify(name)
        entity_id = f"{etype}/{slug}"
        d = KG_ROOT / etype / slug

        domains = e.get("domains", [])
        aliases = e.get("aliases", [])

        entity = {
            "id": entity_id,
            "type": etype,
            "name": name,
            "slug": slug,
            "aliases": aliases,
            "domains": domains,
            "status": "active",
            "created": now_iso(),
            "updated": now_iso(),
        }

        d.mkdir(parents=True, exist_ok=True)
        atomic_write_json(d / "entity.json", entity)

        facts = []
        for category, text in e.get("facts", []):
            fact_id = next_fact_id(facts, slug)
            fact = {
                "id": fact_id,
                "text": text,
                "category": category,
                "status": "active",
                "created": now_iso(),
                "source": "seed",
            }
            facts.append(fact)
            created_facts.append(fact_id)

        atomic_write_json(d / "facts.json", facts)
        created_entities.append(entity_id)

    # Add relations (resolve names to entity IDs)
    for src_name, src_type, tgt_name, tgt_type, rel_type, fact_text in SEED_DATA["relations"]:
        source_id = f"{src_type}/{slugify(src_name)}"
        target_id = f"{tgt_type}/{slugify(tgt_name)}"
        source_slug = slugify(src_name)
        facts = load_facts(source_id)

        if not fact_text:
            source_entity = load_entity(source_id)
            target_entity = load_entity(target_id)
            fact_text = f"{source_entity['name']} {rel_type.replace('_', ' ')} {target_entity['name']}"

        fact_id = next_fact_id(facts, source_slug)
        fact = {
            "id": fact_id,
            "text": fact_text,
            "category": "relationship",
            "status": "active",
            "created": now_iso(),
            "source": "seed",
            "relation": {
                "type": rel_type,
                "target": target_id,
            },
        }
        facts.append(fact)
        save_facts(source_id, facts)
        created_relations.append(f"{source_id} --{rel_type}--> {target_id}")

    # Generate summaries for all
    for eid in created_entities:
        text = generate_summary(eid)
        summary_path = entity_dir(eid) / "summary.md"
        atomic_write_text(summary_path, text)

    log(f"seed: {len(created_entities)} entities, {len(created_facts)} facts, {len(created_relations)} relations")
    output({
        "ok": True,
        "entities_created": len(created_entities),
        "facts_created": len(created_facts),
        "relations_created": len(created_relations),
        "entity_ids": created_entities,
    })


# --- Argument Parser ---


def build_parser():
    parser = argparse.ArgumentParser(
        description="Knowledge Graph — Structured entity-relationship storage",
        prog="kg.py",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # add-entity
    p = subparsers.add_parser("add-entity", help="Create a new entity")
    p.add_argument("--type", required=True, choices=ENTITY_TYPES, help="Entity type")
    p.add_argument("--name", required=True, help="Entity name")
    p.add_argument("--domains", default="", help="Comma-separated domains")
    p.add_argument("--aliases", default="", help="Comma-separated aliases")
    p.add_argument("--force", action="store_true", help="Skip duplicate check")

    # add-fact
    p = subparsers.add_parser("add-fact", help="Add a fact to an entity")
    p.add_argument("entity_id", help="Entity ID (type/slug)")
    p.add_argument("--fact", required=True, help="Fact text (max 500 chars)")
    p.add_argument("--category", required=True, choices=FACT_CATEGORIES, help="Fact category")
    p.add_argument("--source", default=None, help="Fact source (default: conversation)")

    # supersede
    p = subparsers.add_parser("supersede", help="Supersede a fact with a new one")
    p.add_argument("entity_id", help="Entity ID (type/slug)")
    p.add_argument("old_fact_id", help="ID of fact to supersede")
    p.add_argument("--fact", required=True, help="New fact text")
    p.add_argument("--source", default=None, help="Fact source")

    # add-relation
    p = subparsers.add_parser("add-relation", help="Add a relationship between entities")
    p.add_argument("entity_id", help="Source entity ID")
    p.add_argument("target_id", help="Target entity ID")
    p.add_argument("--relation-type", required=True, choices=RELATION_TYPES, help="Relationship type")
    p.add_argument("--fact", default=None, help="Custom fact text (auto-generated if omitted)")
    p.add_argument("--source", default=None, help="Fact source")

    # query
    p = subparsers.add_parser("query", help="Query an entity and its facts")
    p.add_argument("entity_id", help="Entity ID (type/slug)")
    p.add_argument("--include-archived", action="store_true", help="Include archived facts")

    # connections
    p = subparsers.add_parser("connections", help="Show entity connections")
    p.add_argument("entity_id", help="Entity ID (type/slug)")
    p.add_argument("--reverse", action="store_true", help="Include inbound connections")

    # search
    p = subparsers.add_parser("search", help="Search all entities")
    p.add_argument("query", help="Search text")
    p.add_argument("--include-archived", action="store_true", help="Include archived entities")

    # domain
    p = subparsers.add_parser("domain", help="Filter entities by domain")
    p.add_argument("domain", help="Domain name")
    p.add_argument("--include-archived", action="store_true", help="Include archived entities")

    # list
    p = subparsers.add_parser("list", help="List all entities")
    p.add_argument("--type", choices=ENTITY_TYPES, help="Filter by entity type")
    p.add_argument("--include-archived", action="store_true", help="Include archived entities")

    # stats
    p = subparsers.add_parser("stats", help="Show knowledge graph statistics")

    # summarize
    p = subparsers.add_parser("summarize", help="Regenerate summary.md")
    p.add_argument("entity_id", nargs="?", default=None, help="Entity ID (or use --all/--dirty)")
    p.add_argument("--all", action="store_true", help="Summarize all entities")
    p.add_argument("--dirty", action="store_true", help="Summarize only entities with stale summaries")

    # archive
    p = subparsers.add_parser("archive", help="Archive or unarchive an entity")
    p.add_argument("entity_id", help="Entity ID (type/slug)")
    p.add_argument("--unarchive", action="store_true", help="Unarchive instead of archive")

    # merge
    p = subparsers.add_parser("merge", help="Merge source entity into target")
    p.add_argument("source_id", help="Source entity ID (will be deleted)")
    p.add_argument("target_id", help="Target entity ID (will receive facts)")

    # seed
    p = subparsers.add_parser("seed", help="Seed knowledge graph with built-in data")
    p.add_argument("--force", action="store_true", help="Seed even if entities exist")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "add-entity": cmd_add_entity,
        "add-fact": cmd_add_fact,
        "supersede": cmd_supersede,
        "add-relation": cmd_add_relation,
        "query": cmd_query,
        "connections": cmd_connections,
        "search": cmd_search,
        "domain": cmd_domain,
        "list": cmd_list,
        "stats": cmd_stats,
        "summarize": cmd_summarize,
        "archive": cmd_archive,
        "merge": cmd_merge,
        "seed": cmd_seed,
    }

    fn = commands.get(args.command)
    if fn:
        try:
            fn(args)
        except SystemExit:
            raise
        except Exception as e:
            error_out(f"Unexpected error: {e}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
