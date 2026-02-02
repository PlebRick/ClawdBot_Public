#!/usr/bin/env python3
"""Generate a tree structure of ~/clawd/ and output JSON."""
import json, os, sys
from datetime import datetime, timezone

ROOT = os.path.expanduser("~/clawd")
MAX_DEPTH = 4
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
EXCLUDE_EXTS = {".sqlite", ".jsonl"}


def build_tree(path, depth=0):
    name = os.path.basename(path)
    if os.path.isfile(path):
        ext = os.path.splitext(name)[1].lower()
        if ext in EXCLUDE_EXTS:
            return None
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        return {"name": name, "type": "file", "size": size}

    if name in EXCLUDE_DIRS:
        return None

    node = {"name": name, "type": "dir", "children": []}
    if depth >= MAX_DEPTH:
        # Count contents without recursing
        try:
            entries = os.listdir(path)
            count = len([e for e in entries if e not in EXCLUDE_DIRS])
            if count > 0:
                node["truncated"] = count
        except OSError:
            pass
        return node

    try:
        entries = sorted(os.listdir(path), key=lambda e: (not os.path.isdir(os.path.join(path, e)), e.lower()))
    except OSError:
        return node

    for entry in entries:
        child = build_tree(os.path.join(path, entry), depth + 1)
        if child:
            node["children"].append(child)

    return node


def count_tree(node):
    if node["type"] == "file":
        return 1, 0, node.get("size", 0)
    files, dirs, size = 0, 1, 0
    for child in node.get("children", []):
        f, d, s = count_tree(child)
        files += f
        dirs += d
        size += s
    return files, dirs, size


def render_text(node, prefix="", is_last=True, is_root=False):
    lines = []
    connector = "" if is_root else ("└── " if is_last else "├── ")
    label = node["name"]
    if node["type"] == "dir":
        label += "/"
        trunc = node.get("truncated")
        if trunc:
            label += f" ({trunc} items)"
    else:
        size = node.get("size", 0)
        if size >= 1024 * 1024:
            label += f" ({size / (1024*1024):.1f}MB)"
        elif size >= 1024:
            label += f" ({size / 1024:.1f}KB)"

    lines.append(f"{prefix}{connector}{label}")

    children = node.get("children", [])
    child_prefix = prefix + ("" if is_root else ("    " if is_last else "│   "))
    for i, child in enumerate(children):
        lines.extend(render_text(child, child_prefix, i == len(children) - 1))

    return lines


tree = build_tree(ROOT)
files, dirs, total_size = count_tree(tree)
text_lines = render_text(tree, is_root=True)

def fmt_size(b):
    if b >= 1024 * 1024:
        return f"{b / (1024*1024):.1f}MB"
    if b >= 1024:
        return f"{b / 1024:.1f}KB"
    return f"{b}B"

summary = f"{files} files, {dirs} directories, {fmt_size(total_size)} total"
text_lines.append("")
text_lines.append(summary)

output = {
    "cachedAt": datetime.now(timezone.utc).isoformat(),
    "cachedAtMs": int(__import__("time").time() * 1000),
    "root": ROOT,
    "maxDepth": MAX_DEPTH,
    "summary": {"files": files, "dirs": dirs, "totalBytes": total_size, "totalFormatted": fmt_size(total_size)},
    "tree": tree,
    "text": "\n".join(text_lines),
}

json.dump(output, sys.stdout, indent=2)
