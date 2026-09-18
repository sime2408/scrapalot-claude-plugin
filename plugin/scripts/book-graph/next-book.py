#!/usr/bin/env python3
"""The next book whose graph is worth building, or nothing.

A candidate is a document that (1) has a `parse_done_clean` row in
`postprocess/progress.txt` — the graph command's own precondition, because a
graph built on a wrong chapter layer is permanent — (2) sits in a collection
whose EFFECTIVE graph tier is 2, inheritance walked the way
`resolve_graph_tier()` walks it, (3) has no graph row yet, (4) was not stopped
at Phase 0 since its parse was last recorded clean, and (5) does not already fail
one of the two Phase 0 checks a single query can answer: its stored chapters are
not the chapter-lock recovery's equal runs (`chapter-windows.sh`), and no text
chunk was written more than an hour after its latest clean row (`parse-fresh.sh`).
Those books are skipped without a ledger or a row. A stale book comes back once a
parse pass records it clean over its stored chunks. An equal-runs book comes back
once its chapters are rewritten; the chapter-lock repair stamps `enriched_at` on
every chunk it rewrites, so the book then reads as stale until a parse pass. Phase
0 still runs both checks on the book this hands out. A book reopened in `book-graph/closed-books.tsv`
after its acceptance counts as having none, and comes before any new book, unless
it was stopped at Phase 0 since or fails (5).

Ordering is the owner's: the `books` workspace first, then everything else;
inside a workspace by collection, then by title, so a run is reproducible and a
human can predict what comes next.

    next-book.py            -> "<uuid>|<title>|<collection>" on stdout, exit 0,
                               and how many were skipped before it, why, on stderr
    next-book.py --count    -> how many candidates remain after the skips
    next-book.py --skipped  -> every skipped candidate with its reason
    exit 3                  -> no candidates left (the sweep is finished)
    exit 1                  -> could not tell (DB unreachable) — the caller must
                               NOT treat this as "finished"
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "/opt/scrapalot"))
PROGRESS = PROJECT / ".claude" / "postprocess" / "progress.txt"
CLOSED = PROJECT / ".claude" / "book-graph" / "closed-books.tsv"
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# The `books` workspace. Overridable, because the id is this deployment's fact
# rather than the plugin's.
PRIORITY_WORKSPACE = os.environ.get("PRIORITY_WORKSPACE", "0ebf2e09-7198-4b7a-a100-87b6dc969387")

# Marker rows. `parse_done_clean` is written by the parse sweep;
# `graph_done_clean` by this loop when a critic has said yes;
# `graph_blocked_chapter_layer` by this loop when a Phase 0 check finds the stored
# chapter layer is not the book's after all.
PARSE_MARKER = "parse_done_clean"
GRAPH_MARKER = "graph_done_clean"
BLOCKED_MARKER = "graph_blocked_chapter_layer"

# The margin parse-fresh.sh allows between a clean row and the chunks it vouches for.
STALE_MARGIN = timedelta(minutes=60)
# Candidates whose layers one query reads while looking for the next book.
LAYER_BATCH = 50

# Per document and chapter title: the first chunk_index, the chunks, and the latest
# enriched_at read as a time (it is stored as ISO text or as epoch seconds). Figure
# rows without a chunk_index are left out, as chapter-windows.sh leaves them out.
LAYER_SQL = """
SELECT cmetadata->>'document_id', min((cmetadata->>'chunk_index')::int), count(*),
       coalesce(to_char(max(CASE WHEN cmetadata->>'enriched_at' ~ '^[0-9]+([.][0-9]+)?$'
                                 THEN to_timestamp((cmetadata->>'enriched_at')::double precision)
                                 WHEN cmetadata->>'enriched_at' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}'
                                 THEN (cmetadata->>'enriched_at')::timestamptz END) AT TIME ZONE 'UTC',
                        'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'), '')
FROM langchain_pg_embedding
WHERE cmetadata->>'document_id' IN (:ids)
  AND NOT (coalesce((cmetadata->>'is_multimodal')::boolean, false) AND cmetadata->>'chunk_index' IS NULL)
GROUP BY cmetadata->>'document_id', coalesce(cmetadata->>'chapter_title', '');
"""

SQL = """
WITH RECURSIVE m AS (
    SELECT collection_id, collection_name, graph_tier, parent_collection_id, workspace_id, owner_user_id
    FROM collection_workspace_map
),
walk AS (
    SELECT collection_id AS root, graph_tier, parent_collection_id, 0 AS depth FROM m
    UNION ALL
    SELECT w.root, m.graph_tier, m.parent_collection_id, w.depth + 1
    FROM walk w JOIN m ON m.collection_id = w.parent_collection_id
    WHERE w.graph_tier IS NULL AND w.depth < 8
),
eff AS (
    SELECT DISTINCT ON (root) root AS collection_id, graph_tier
    FROM walk WHERE graph_tier IS NOT NULL ORDER BY root, depth
)
SELECT d.id, replace(coalesce(d.title, '(untitled)'), '|', ' '), m.collection_name
FROM documents d
JOIN m ON m.collection_id = d.collection_id
LEFT JOIN eff e ON e.collection_id = m.collection_id
WHERE d.deleted_at IS NULL
  AND coalesce(e.graph_tier, 0) = 2
  AND m.collection_name NOT LIKE '.test_%'
  AND m.owner_user_id <> '08326327-ab04-4cf0-9163-4e1cd4b859df'
ORDER BY (m.workspace_id::text = :priority) DESC, m.collection_name, d.title
"""


def _rows() -> list[tuple[str, str, str]]:
    sql = SQL.replace(":priority", f"'{PRIORITY_WORKSPACE}'")
    out = subprocess.run(
        ["docker", "exec", "pgvector", "psql", "-U", "scrapalot", "-d", "scrapalot", "-At", "-F", "|", "-c", sql],
        capture_output=True, text=True, timeout=120,
    )
    if out.returncode != 0:
        print(out.stderr.strip()[:200], file=sys.stderr)
        raise SystemExit(1)
    rows = []
    for line in out.stdout.splitlines():
        parts = line.split("|")
        if len(parts) == 3 and UUID_RE.fullmatch(parts[0]):
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def _marked(marker: str) -> set[str]:
    """Document ids whose STATUS column claims `marker`.

    The ledger's own header states the row format, and this reads it that way:

        ISO_TS|COLLECTION_UUID|COLLECTION_NAME|DOCUMENT_UUID|FILENAME|STATUS|BUG_COUNT|NOTE

    Two things this deliberately does NOT do, because both cost the sweep a book:

    * It does not scan the whole line. NOTE is free prose; a row that merely
      *mentions* another book's uuid, or says a status is pending, would
      otherwise mark that book done and the sweep would skip it forever.
    * It does not harvest every uuid on the row. COLLECTION_UUID sits in the
      same line, and 57 collections were being counted as finished books.

    The STATUS token is matched by PREFIX, not equality: passes append their own
    qualifier to it (`parse_done_clean_post_cat_i`), and those rows are the same
    claim. Anything the pass wants to say beyond the token goes after a `;`.
    """
    if not PROGRESS.exists():
        return set()
    ids: set[str] = set()
    for line in PROGRESS.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            continue
        fields = line.split("|")
        if len(fields) < 6:
            continue
        doc_id, status = fields[3].strip(), fields[5].strip()
        if not UUID_RE.fullmatch(doc_id):
            continue
        if status.split(";")[0].strip().startswith(marker):
            ids.add(doc_id)
    return ids


def _blocked() -> set[str]:
    """Books whose latest row, between a clean parse and a Phase 0 stop, is the stop.

    A `parse_done_clean` row is a claim about the chapter layer at the time of the
    audit, and a later reprocess can replace that layer: Ripley's Scroll kept its
    row while a reprocess rewrote its chapters as the opening words of hard-wrapped
    sentences ("A notable fact is", "We can shine a"). Without this, the stop leaves
    the book a candidate, and the sweep is handed the same book again. A block
    removes a reopened book as well. Rows are read in the order they were appended,
    so a later parse pass that records the book clean again makes it a candidate
    again.
    """
    if not PROGRESS.exists():
        return set()
    latest: dict[str, str] = {}
    for line in PROGRESS.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            continue
        fields = line.split("|")
        if len(fields) < 6:
            continue
        doc_id, status = fields[3].strip(), fields[5].strip().split(";")[0].strip()
        if not UUID_RE.fullmatch(doc_id):
            continue
        if status.startswith(PARSE_MARKER):
            latest[doc_id] = PARSE_MARKER
        elif status == BLOCKED_MARKER:
            latest[doc_id] = BLOCKED_MARKER
    return {doc for doc, marker in latest.items() if marker == BLOCKED_MARKER}


def _last_clean_times() -> dict[str, str]:
    """The time of each document's latest `parse_done_clean` row, in append order."""
    if not PROGRESS.exists():
        return {}
    times: dict[str, str] = {}
    for line in PROGRESS.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            continue
        fields = line.split("|")
        if len(fields) < 6:
            continue
        doc_id = fields[3].strip()
        if UUID_RE.fullmatch(doc_id) and fields[5].strip().split(";")[0].strip().startswith(PARSE_MARKER):
            times[doc_id] = fields[0].strip()
    return times


def _layers(doc_ids: list[str]) -> dict[str, tuple[list[int], str]]:
    """Each document's chapter sizes in reading order and its chunks' latest write."""
    groups: dict[str, list[tuple[int, int, str]]] = {}
    ids = ",".join(f"'{doc}'" for doc in doc_ids if UUID_RE.fullmatch(doc))
    if not ids:
        return {}
    out = subprocess.run(
        ["docker", "exec", "-i", "pgvector", "psql", "-U", "scrapalot", "-d", "scrapalot", "-At", "-F", "|", "-v", "ON_ERROR_STOP=1"],
        input=LAYER_SQL.replace(":ids", ids), capture_output=True, text=True, timeout=300,
    )
    if out.returncode != 0:
        print(out.stderr.strip()[:200], file=sys.stderr)
        raise SystemExit(1)
    unreadable: set[str] = set()
    for line in out.stdout.splitlines():
        parts = line.split("|")
        if len(parts) != 4 or not UUID_RE.fullmatch(parts[0]):
            continue
        if not parts[1].lstrip("-").isdigit():
            # A group with no chunk_index cannot be ordered; chapter-windows.sh sorts it last, and dropping it could
            # turn a good layer into equal runs, so the document is left for Phase 0 to read.
            unreadable.add(parts[0])
            continue
        groups.setdefault(parts[0], []).append((int(parts[1]), int(parts[2]), parts[3]))
    return {
        doc: ([n for _first, n, _w in sorted(rows)], max((w for _f, _n, w in rows), default=""))
        for doc, rows in groups.items()
        if doc not in unreadable
    }


def _equal_runs(sizes: list[int]) -> bool:
    """chapter-windows.sh's rule: every chapter but the last holds exactly chunks // chapters."""
    total, count = sum(sizes), len(sizes)
    per = total // count if count else 0
    return count >= 3 and per > 1 and all(size == per for size in sizes[:-1]) and sizes[-1] == total - per * (count - 1)


def _skip_reason(doc_id: str, layers: dict[str, tuple[list[int], str]], clean_times: dict[str, str]) -> str | None:
    """Why Phase 0 would stop this book, when one query can already tell; None when it cannot."""
    sizes, written = layers.get(doc_id, ([], ""))
    if sizes and _equal_runs(sizes):
        return "equal_runs"
    row = clean_times.get(doc_id, "")
    if written and row:
        try:
            row_time = datetime.fromisoformat(row.replace("Z", "+00:00"))
        except ValueError:
            return None
        if row_time.tzinfo is not None and datetime.fromisoformat(written) - row_time > STALE_MARGIN:
            return "stale_parse_row"
    return None


def _reopened() -> set[str]:
    """Books a later check found changed after a critic had accepted them.

    Their `graph_done_clean` row stays in progress.txt, which is append-only, so
    `_marked` alone counts them finished and they would never return to a critic.
    The latest row per document in closed-books.tsv decides.
    """
    if not CLOSED.exists():
        return set()
    latest: dict[str, str] = {}
    for line in CLOSED.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) >= 3 and UUID_RE.fullmatch(cols[1]):
            latest[cols[1]] = cols[2]
    return {doc for doc, state in latest.items() if state == "reopened"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", action="store_true", help="print how many candidates remain after the skips")
    ap.add_argument("--skipped", action="store_true", help="print every skipped candidate with its reason")
    args = ap.parse_args()

    parsed, graphed, reopened = _marked(PARSE_MARKER), _marked(GRAPH_MARKER), _reopened()
    parsed -= _blocked()
    rows = _rows()
    # A reopened book goes first: the graph a critic accepted no longer exists.
    candidates = [r for r in rows if r[0] in parsed and r[0] in reopened]
    candidates += [r for r in rows if r[0] in parsed and r[0] not in graphed and r[0] not in reopened]

    clean_times = _last_clean_times()
    everything = args.count or args.skipped
    skipped: dict[str, int] = {}
    skipped_reopened: list[str] = []
    remaining = 0
    chosen = None
    for start in range(0, len(candidates), LAYER_BATCH):
        batch = candidates[start : start + LAYER_BATCH]
        layers = _layers([doc for doc, _title, _collection in batch])
        for candidate in batch:
            reason = _skip_reason(candidate[0], layers, clean_times)
            if reason:
                # In a pick, only the skips before the chosen book are its story.
                if everything or chosen is None:
                    skipped[reason] = skipped.get(reason, 0) + 1
                    if candidate[0] in reopened:
                        skipped_reopened.append(f"{candidate[0]} ({reason})")
                if args.skipped:
                    print(f"{reason}|{'|'.join(candidate)}")
                continue
            remaining += 1
            if chosen is None:
                chosen = candidate
        if chosen is not None and not everything:
            break
    summary = ", ".join(f"{n} {reason}" for reason, n in sorted(skipped.items())) or "none"
    if skipped_reopened:
        summary += "; reopened books skipped: " + ", ".join(skipped_reopened)

    if args.count:
        print(remaining)
        print(f"skipped: {summary}", file=sys.stderr)
        return 0
    if args.skipped:
        return 0
    if chosen is None:
        print(f"no candidates: every parse-clean book in a tier-2 collection has a graph row or fails Phase 0 (skipped: {summary})", file=sys.stderr)
        return 3
    print("|".join(chosen))
    print(f"skipped before it: {summary}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
