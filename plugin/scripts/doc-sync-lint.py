#!/usr/bin/env python3
"""Mechanical pre-pass for /scrapalot-doc-sync.

Deterministic drift detector for the docs/README_*.md files **and the CLAUDE.md
files**. It extracts every source path a doc cites, resolves it against ALL
subproject roots (so a cross-repo citation is not mistaken for drift), skips
template/example placeholders, and reports only genuinely dead references — the
paths a doc points at that no longer exist anywhere in the workspace.

CLAUDE.md is checked because it is loaded into context at the start of every
session, so a dead path there costs more than one in a README. It also needs a
different matcher: its "Key Files" tables cite a full path once and then bare
basenames (`chat-message.tsx`, `chat-input.tsx`), which the anchored README
regex cannot see. Those resolve by filename anywhere in the workspace.

The root `/opt/scrapalot/CLAUDE.md` is the reason this exists: it is **not in
any git repo**, so deleting a file in a subproject leaves no trace in it — no
diff, no `git status`, no review signal. It was carrying a reference to a hook
deleted four days earlier and nothing could have caught it.

This is the cheap "repository knowledge graph" the docs already carry latently:
the cited paths ARE the doc->code edges. We just read them back and check them.

Secondary, advisory: it surfaces numeric count claims ("22 strategies") next to
where they appear, with a grep to verify — it does NOT judge these, because a
generic counter produces false positives. A human/agent verifies them.

Usage:
    python3 .claude/scripts/doc_sync_lint.py [chat|backend|ui|gw|all]

Exit code is always 0 — this is a report, not a gate.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import os

# Not derived from __file__: this script ships with the plugin, whose install
# directory is nowhere near the workspace it lints.
WORKSPACE = Path(os.environ.get("CLAUDE_PROJECT_DIR", "/opt/scrapalot"))

SUBPROJECTS = {
    "chat": "scrapalot-chat",
    "backend": "scrapalot-backend",
    "ui": "scrapalot-ui",
    "gw": "scrapalot-gw",
}

# Roots a cited path may be relative to. Checked under every subproject.
ANCHORS = ("src/", "tests/", "alembic/", "db/", "scripts/")

# A citation is a path anchored on one of ANCHORS ending in a code extension.
PATH_RE = re.compile(
    r"(?<![\w./-])(" + "|".join(re.escape(a) for a in ANCHORS) + r")"
    # Longest extensions first — alternation is ordered, so `json` must precede
    # `js` or `foo.json` gets truncated to a phantom `foo.js`.
    r"[\w./-]+\.(?:tsx|ts|jsx|json|js|kts|kt|py|yaml|yml)"
)

# Template / example / placeholder paths — real docs cite these on purpose
# (e.g. "create src/main/.../your_connector/connector.py"). Never flag them.
# `NNN_` needs no leading slash here: CLAUDE.md writes the Liquibase changeset
# template as a bare `NNN_desc.yaml`, with nothing in front of it.
IGNORE_RE = re.compile(
    r"(your_|_your\b|new_agent|new_connector|example|sample|placeholder"
    r"|\bfoo\b|\bbar\b|<[^>]+>|\bNNN_|\.\.\.)",
    re.IGNORECASE,
)

# CLAUDE.md citation: a backtick-quoted path OR bare filename ending in a code
# extension. The stem must be 2+ chars so a type-suffix fragment like `.d.ts`
# is not read as a file. Longest extensions first, same reason as PATH_RE.
CLAUDE_CITE_RE = re.compile(
    r"`([\w./-]*[\w-]{2,}\.(?:tsx|ts|jsx|json|js|kts|kt|py|yaml|yml))`"
)

# Directories that are never source of record: vendored, generated, build
# output, CI checkouts, and other sessions' worktrees.
_SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "dist", "build", ".venv", "venv",
    "_work", "worktrees", ".gradle", "gradle", "android-sdk", "actions-runner",
    "data", ".vitepress", "site-packages",
}

_by_name: dict[str, list[str]] | None = None


def _name_index() -> dict[str, list[str]]:
    """filename -> every workspace-relative path with that name. Built once."""
    global _by_name
    if _by_name is None:
        idx: dict[str, list[str]] = {}
        for p in WORKSPACE.rglob("*"):
            if _SKIP_DIRS.intersection(p.parts) or not p.is_file():
                continue
            idx.setdefault(p.name, []).append(p.relative_to(WORKSPACE).as_posix())
        _by_name = idx
    return _by_name


def cite_is_alive(cite: str) -> bool:
    """Is this CLAUDE.md citation still backed by a real file?

    CLAUDE.md deliberately writes *abbreviated* paths in its Key Files tables —
    a full path once, then `redis/RedisEventPublisher.kt` or a bare
    `chat-input.tsx` for the rest. Those are suffixes of a real path, not paths
    from a repo root, so anything not starting at a known anchor is matched as
    a path suffix. Only an anchored citation (`src/...`) has to resolve exactly.
    """
    hits = _name_index().get(Path(cite).name)
    if not hits:
        return False
    if cite.startswith(ANCHORS):
        return path_exists_anywhere(cite) is not None
    if "/" not in cite:
        return True
    return any(h == cite or h.endswith("/" + cite) for h in hits)

# Count claims worth a human's eyes. Advisory only.
COUNT_RE = re.compile(
    r"\b(\d{1,3})\s+"
    r"(strateg\w+|orchestrator\w*|agent\w*|controller\w*|packet\s*types?"
    r"|connector\w*|changeset\w*|spec\s*files?|migrations?|endpoints?|queues?)\b",
    re.IGNORECASE,
)

# Roots to search when resolving a cited path (all subprojects + workspace).
_SEARCH_ROOTS = [WORKSPACE / d for d in SUBPROJECTS.values()] + [WORKSPACE]


def path_exists_anywhere(rel: str) -> Path | None:
    """Return the first root under which `rel` resolves, else None."""
    for root in _SEARCH_ROOTS:
        if (root / rel).is_file():
            return root
    return None


def _claude_md_targets(keys: list[str]) -> list[tuple[str, Path]]:
    """(label, path) for the root CLAUDE.md plus each requested subproject's."""
    out: list[tuple[str, Path]] = []
    root = WORKSPACE / "CLAUDE.md"
    if root.is_file():
        out.append(("CLAUDE.md (workspace root — NOT in git)", root))
    for key in keys:
        p = WORKSPACE / SUBPROJECTS[key] / "CLAUDE.md"
        if p.is_file():
            out.append((f"{SUBPROJECTS[key]}/CLAUDE.md", p))
    return out


def lint_claude_md(keys: list[str]) -> tuple[int, int]:
    """Return (dead_count, file_count) across the CLAUDE.md files."""
    targets = _claude_md_targets(keys)
    if not targets:
        return 0, 0

    print(f"\n{'=' * 68}\n  CLAUDE.md files  ({len(targets)})\n{'=' * 68}")

    total_dead = 0
    for label, md in targets:
        text = md.read_text(encoding="utf-8", errors="replace")
        dead, skipped = [], 0
        for cite in sorted({m.group(1) for m in CLAUDE_CITE_RE.finditer(text)}):
            if IGNORE_RE.search(cite):
                skipped += 1
            elif not cite_is_alive(cite):
                hits = _name_index().get(Path(cite).name)
                note = f"   (name exists at {hits[0]})" if hits else ""
                dead.append(f"{cite}{note}")

        if dead:
            total_dead += len(dead)
            print(f"\n  ✗ {label}")
            for p in dead:
                print(f"      DEAD  {p}")
            if skipped:
                print(f"      (skipped {skipped} example/placeholder path(s))")

    if total_dead == 0:
        print("\n  ✓ no dead source references")

    return total_dead, len(targets)


def lint_subproject(key: str) -> tuple[int, int]:
    """Return (dead_count, readme_count) for one subproject."""
    sub = WORKSPACE / SUBPROJECTS[key]
    docs = sorted(sub.glob("docs/README_*.md"))
    if not docs:
        return 0, 0

    print(f"\n{'=' * 68}\n  {SUBPROJECTS[key]}  ({len(docs)} README files)\n{'=' * 68}")

    total_dead = 0
    all_counts: list[tuple[str, str, str]] = []  # (readme, number, noun)

    for md in docs:
        text = md.read_text(encoding="utf-8", errors="replace")
        cited = sorted({m.group(0) for m in PATH_RE.finditer(text)})
        # A *_PLAN.md doc describes intended code — a citation to a file that
        # doesn't exist yet is the plan, not drift. Report it, don't count it.
        is_plan = "_PLAN" in md.name

        dead, skipped = [], []
        for p in cited:
            if IGNORE_RE.search(p):
                skipped.append(p)
            elif path_exists_anywhere(p) is None:
                dead.append(p)

        for m in COUNT_RE.finditer(text):
            all_counts.append((md.name, m.group(1), m.group(2).lower()))

        if dead:
            label = "PLANNED" if is_plan else "DEAD"
            if not is_plan:
                total_dead += len(dead)
            print(f"\n  {'◦' if is_plan else '✗'} docs/{md.name}"
                  f"{'  (plan — not counted as drift)' if is_plan else ''}")
            for p in dead:
                print(f"      {label}  {p}")
            if skipped:
                print(f"      (skipped {len(skipped)} example/placeholder path(s))")

    if total_dead == 0:
        print("\n  ✓ no dead source references")

    if all_counts:
        print(f"\n  {'-' * 60}\n  Count claims to verify manually (NOT auto-checked):")
        for readme, num, noun in all_counts[:40]:
            print(f"      {num:>4}  {noun:<16} — {readme}")
        if len(all_counts) > 40:
            print(f"      ... and {len(all_counts) - 40} more")

    return total_dead, len(docs)


def main() -> int:
    arg = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    targets = list(SUBPROJECTS) if arg in ("all", "") else [arg]
    if arg not in ("all", "") and arg not in SUBPROJECTS:
        print(f"unknown target '{arg}' — use one of: {', '.join(SUBPROJECTS)}, all")
        return 0

    grand_dead = grand_docs = 0
    for key in targets:
        d, n = lint_subproject(key)
        grand_dead += d
        grand_docs += n

    claude_dead, claude_files = lint_claude_md(targets)
    grand_dead += claude_dead
    grand_docs += claude_files

    print(f"\n{'=' * 68}")
    print(f"  TOTAL: {grand_dead} dead reference(s) across {grand_docs} doc file(s)")
    print(f"         ({claude_dead} of them in CLAUDE.md)")
    print(f"{'=' * 68}")
    print("\n  Dead references are the starting checklist for the manual sync pass.")
    print("  Verify each: was the file renamed, moved, or removed? Update the doc")
    print("  to the current path, or delete the stale mention. Do NOT touch the")
    print("  skipped example paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
