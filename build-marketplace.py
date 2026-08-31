#!/usr/bin/env python3
"""Regenerate .claude-plugin/marketplace.json from what the bundle actually holds.

The inventory under `metadata.components` is the point of this script: it is the
human-readable record of every command, skill, agent and hook in the plugin, so a
lost server is a `git clone` away from the full set rather than an archaeology
project. Claude Code itself discovers components from the conventional
directories — the inventory is documentation, not wiring, which is why it can be
regenerated at will without changing what gets loaded.

Usage: python3 build-marketplace.py [--check]
       --check exits 1 if the committed file is stale (for CI / pre-commit).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLUGIN = ROOT / "plugin"
OUT = ROOT / ".claude-plugin" / "marketplace.json"

# The plugin is delivered from git, never from this JSON's own location: a
# marketplace added by URL downloads only the manifest, so a relative "./plugin"
# source would not resolve for anyone installing from api.scrapalot.app.
PLUGIN_REPO = "sime2408/scrapalot-claude-plugin"
PLUGIN_SOURCE = {
    "source": "git-subdir",
    "url": f"https://github.com/{PLUGIN_REPO}.git",
    "path": "plugin",
    "ref": "main",
}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(errors="replace")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    fields: dict[str, str] = {}
    key = None
    for line in match.group(1).split("\n"):
        pair = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if pair:
            key = pair.group(1)
            fields[key] = pair.group(2).strip().strip('"').strip("'")
        elif key and line.startswith(("  ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def one_line(text: str, limit: int = 300) -> str:
    collapsed = " ".join(text.split())
    return collapsed if len(collapsed) <= limit else collapsed[: limit - 1].rstrip() + "…"


def components() -> dict[str, list[dict[str, str]]]:
    commands = [
        {"name": p.stem, "invoke": f"/scrapalot:{p.stem}",
         "description": one_line(frontmatter(p).get("description", ""))}
        for p in sorted(PLUGIN.glob("commands/*.md"))
    ]
    skills = [
        {"name": p.parent.name, "invoke": f"/scrapalot:{p.parent.name}",
         "description": one_line(frontmatter(p).get("description", ""))}
        for p in sorted(PLUGIN.glob("skills/*/SKILL.md"))
    ]
    agents = [
        {"name": p.stem, "invoke": f"scrapalot:{p.stem}",
         "description": one_line(frontmatter(p).get("description", ""))}
        for p in sorted(PLUGIN.glob("agents/*.md"))
    ]
    wired = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
    hooks = []
    for event, entries in sorted(wired.items()):
        for entry in entries:
            for hook in entry.get("hooks", []):
                hooks.append({
                    "event": event,
                    "matcher": entry.get("matcher", "*"),
                    "script": hook["command"].split("/")[-1],
                })
    return {"commands": commands, "skills": skills, "agents": agents, "hooks": hooks}


def build() -> dict:
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    inventory = components()
    return {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": "scrapalot",
        "description": "Claude Code tooling for the Scrapalot AI stack — corpus audits, RAG grading, an autonomous DevOps fix loop, and the per-stack code-quality passes.",
        "owner": {"name": "Scrapalot", "url": "https://scrapalot.app"},
        "metadata": {"version": manifest["version"]},
        "plugins": [
            {
                "name": manifest["name"],
                "displayName": manifest["displayName"],
                "description": manifest["description"],
                "version": manifest["version"],
                "author": manifest["author"],
                "homepage": manifest["homepage"],
                "repository": f"https://github.com/{PLUGIN_REPO}",
                "license": manifest["license"],
                "keywords": manifest["keywords"],
                "category": "development",
                "source": PLUGIN_SOURCE,
                "metadata": {
                    "counts": {k: len(v) for k, v in inventory.items()},
                    "components": inventory,
                },
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the committed file is stale")
    args = parser.parse_args()
    rendered = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != rendered:
            print(f"{OUT} is stale — run: python3 {Path(__file__).name}", file=sys.stderr)
            return 1
        print(f"{OUT} is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered)
    counts = {k: len(v) for k, v in components().items()}
    print(f"wrote {OUT} — {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
