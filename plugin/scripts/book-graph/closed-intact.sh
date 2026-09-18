#!/usr/bin/env bash
# A closed ledger is not a stable fact. A book accepted 16/16 with 965 entities at
# 21:03Z on 2026-09-12 held 0 at 22:13Z — a resumed extraction purged the whole
# document — and no check existed that would ever have looked at it again. This
# is that look.
#
#   closed-intact.sh record <document_id> [note]     right after gate-check.py close
#   closed-intact.sh reopen <document_id> <reason>   when a closed book is found changed
#   closed-intact.sh check                           before every new book
#
# `check` re-reads every book whose latest row is `closed` and compares five
# numbers with those recorded at close: Book nodes, Book->Entity MENTIONS, Chunk
# nodes, Chunk nodes carrying an entity edge, chunk->entity edges. Any difference
# fails. So does a book this command closed — a gates/done/*-graph-<id8>*.md
# ledger with a graph_done_clean progress row — that was never recorded, because
# an unrecorded book is a book nobody re-checks. A reopened book is skipped until
# it is recorded again.
#
# The numbers are a tripwire, not a verdict: a legitimate re-extraction or a
# housekeeping merge moves them too. A difference is READ and explained before the
# next book starts, and the book is reopened when its graph is no longer what the
# critic accepted.
#
# FAILS CLOSED: an unreadable snapshot, an unreachable Neo4j or a missing row
# prints CLOSED_INTACT_FAIL, never a green line. `record` refuses an empty graph,
# so a wiped state can never become the reference.
set -uo pipefail
MODE="${1:-}"
case "$MODE" in
  record|reopen|check) ;;
  *) echo "usage: closed-intact.sh record <document_id> [note] | reopen <document_id> <reason> | check"; exit 2 ;;
esac
ROOT="${CLOSED_BOOKS_ROOT:-/opt/scrapalot/.claude}"
SNAP="${CLOSED_BOOKS_TSV:-$ROOT/book-graph/closed-books.tsv}"
PW=$(docker inspect neo4j --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep '^NEO4J_AUTH=' | cut -d/ -f2-)
[ -n "$PW" ] || { echo "CLOSED_INTACT_FAIL neo4j_password_unreadable"; exit 2; }

python3 - "$MODE" "$SNAP" "$ROOT" "$PW" "${@:2}" <<'PY'
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

mode, snap, root, pw, args = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], sys.argv[5:]
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
FIELDS = ("books", "entities", "chunk_nodes", "edged_chunks", "chunk_edges")
HEADER = "\t".join(("recorded_at", "document_id", "state", *FIELDS, "note"))


def fail(message, code=1):
    print(f"CLOSED_INTACT_FAIL {message}")
    sys.exit(code)


def cypher(query):
    r = subprocess.run(
        ["docker", "exec", "neo4j", "cypher-shell", "-u", "neo4j", "-p", pw, "--format", "plain",
         "--access-mode", "read", query],
        capture_output=True, text=True, timeout=280,
    )
    if r.returncode or r.stderr.strip():
        fail("neo4j_error: " + r.stderr.strip().replace("\n", " ")[:160])
    return [line for line in r.stdout.splitlines()[1:] if line.strip()]


def measure(doc_ids):
    # UNWIND anchors one row per id even when nothing matches, so a vanished graph
    # reads as zeros instead of as a missing row.
    rows = cypher(f"""UNWIND {json.dumps(sorted(doc_ids))} AS d
OPTIONAL MATCH (b:Book {{document_id: d}})
OPTIONAL MATCH (b)-[:MENTIONS]->(e:Entity)
WITH d, count(DISTINCT b) AS books, count(e) AS entities
OPTIONAL MATCH (c:Chunk {{document_id: d}})
OPTIONAL MATCH (c)-[r:MENTIONS|REFERENCES|DESCRIBES|DISCUSSES|DEFINES|QUOTES]->(:Entity)
WITH d, books, entities, c, count(r) AS n
RETURN d, books, entities, count(c), sum(CASE WHEN n > 0 THEN 1 ELSE 0 END), sum(n);""")
    out = {}
    for line in rows:
        parts = [p.strip().strip('"') for p in line.split(",")]
        out[parts[0]] = dict(zip(FIELDS, map(int, parts[1:6])))
    if set(out) != set(doc_ids):
        fail(f"rows={len(out)} expected={len(doc_ids)}")
    return out


def append(row):
    fresh = not snap.exists()
    with snap.open("a", encoding="utf-8") as fh:
        if fresh:
            fh.write(HEADER + "\n")
        fh.write("\t".join(row) + "\n")


now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if mode in ("record", "reopen"):
    if not args or not UUID.match(args[0]):
        fail("bad_document_id", 2)
    doc = args[0]
    text = " ".join(" ".join(args[1:]).split())
    got = measure([doc])[doc]
    numbers = [str(got[f]) for f in FIELDS]
    if mode == "record":
        if got["books"] != 1 or not all(got[f] for f in ("entities", "chunk_nodes", "edged_chunks", "chunk_edges")):
            fail("refusing_to_record " + " ".join(f"{f}={got[f]}" for f in FIELDS)
                 + " — a graph with an empty layer is not what a critic accepted")
        # Re-recording a CLOSED book whose numbers moved would quietly re-baseline
        # a change nobody explained. It has to be reopened and accepted again first.
        if snap.exists():
            previous = [line.split("\t") for line in snap.read_text(encoding="utf-8").splitlines()[1:]]
            previous = [cols for cols in previous if len(cols) == 9 and cols[1] == doc]
            if previous and previous[-1][2] == "closed":
                was = dict(zip(FIELDS, map(int, previous[-1][3:8])))
                if was != got:
                    fail(f"refusing_to_record {doc[:8]} changed since it was recorded at {previous[-1][0]} — "
                         "reopen it with the reason and have a critic accept it again first")
        append([now, doc, "closed", *numbers, text or "closed"])
        print(f"CLOSED_RECORDED {doc[:8]} " + " ".join(f"{f}={got[f]}" for f in FIELDS))
    else:
        if not text:
            fail("reopen_needs_a_reason", 2)
        append([now, doc, "reopened", *numbers, text])
        print(f"CLOSED_REOPENED {doc[:8]} {text}")
    sys.exit(0)

if not snap.exists():
    fail(f"no_snapshot_file {snap}")
lines = snap.read_text(encoding="utf-8").splitlines()
if not lines or lines[0] != HEADER:
    fail("snapshot_header_unrecognised")
latest = {}
for number, line in enumerate(lines[1:], 2):
    cols = line.split("\t")
    if len(cols) != 9 or not UUID.match(cols[1]) or cols[2] not in ("closed", "reopened"):
        fail(f"snapshot_row_unreadable line={number}")
    latest[cols[1]] = cols

closed = {d: cols for d, cols in latest.items() if cols[2] == "closed"}
reopened = sorted(d for d, cols in latest.items() if cols[2] == "reopened")
changed = 0
if closed:
    got = measure(list(closed))
    for d in sorted(closed):
        was = dict(zip(FIELDS, map(int, closed[d][3:8])))
        diffs = [f"{f} {was[f]}->{got[d][f]}" for f in FIELDS if was[f] != got[d][f]]
        if diffs:
            changed += 1
            print(f"    CLOSED_CHANGED {d[:8]} since {closed[d][0]}: " + ", ".join(diffs))
        else:
            print(f"    intact {d[:8]} entities={got[d]['entities']} chunk_edges={got[d]['chunk_edges']}")
for d in reopened:
    print(f"    reopened {d[:8]} since {latest[d][0]}: {latest[d][8]}")

# Every book this command closed must be watched — and without the closed ledgers
# there is nothing to prove that against, which is not the same as nothing to watch.
if not (root / "gates/done").is_dir():
    fail(f"no_closed_ledger_directory {root / 'gates/done'}")
clean = {}
for line in (root / "postprocess/progress.txt").read_text(encoding="utf-8", errors="replace").splitlines():
    cols = line.split("|")
    if len(cols) >= 6 and UUID.match(cols[3].strip()) and cols[5].strip().startswith("graph_done_clean"):
        clean.setdefault(cols[3].strip()[:8], set()).add(cols[3].strip())
unrecorded = []
for ledger in sorted((root / "gates/done").glob("*-graph-*.md")):
    m = re.search(r"-graph-([0-9a-f]{8})(?:-|\.md)", ledger.name)
    for d in sorted(clean.get(m.group(1), ())) if m else ():
        if d not in latest and d not in unrecorded:
            unrecorded.append(d)
            print(f"    CLOSED_UNRECORDED {d[:8]} ({ledger.name}) — closed by this command, never recorded")

if changed or unrecorded:
    fail(f"changed={changed} unrecorded={len(unrecorded)} closed={len(closed)} reopened={len(reopened)}")
print(f"CLOSED_INTACT_OK closed={len(closed)} reopened={len(reopened)}")
PY
