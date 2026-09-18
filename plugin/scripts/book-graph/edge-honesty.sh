#!/usr/bin/env bash
# Does each chunk->entity edge point at a chunk that actually names the entity?
#
# An edge to a chunk that never writes the thing's name is wrong whatever the
# label is supposed to mean, and this needs no model, no critic and no round.
# It is a POINTER, never a score, and it errs in BOTH directions: it cannot see an
# edge whose name IS present but whose label is wrong (a bare mention stored as
# DEFINES reads as correct here), and it wrongly flags every edge whose stored
# name is a normalised spelling of what the text writes — one book wrote
# `Uroboros` and the extractor stored `Ouroboros`, which this check called absent.
# So: read the offenders. Never report the percentage as a defect rate, and never
# conclude contamination from it — absence of a string is not absence of a thing.
#
# EDGE_HONESTY_SPLIT sorts the flags: a variant spelling inside the chunk, the name in a
# chunk within two of this one (still wrong, and mostly a merged extraction unit
# giving each of its entities an edge to every source chunk), elsewhere in the book,
# or nowhere.
#
# FAILS CLOSED. An earlier version swallowed Cypher errors and then announced
# "the entity layer is empty" — an unreachable database reported as a fact about
# the book. It now aborts instead, and prints the unresolvable-id count BEFORE
# any early exit, because a total Neo4j<->pgvector join failure shows up there
# and nowhere else.
#
# Usage: edge-honesty.sh <document_id>
set -uo pipefail

D="${1:?usage: edge-honesty.sh <document_id>}"
case "$D" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-*-*-*-*) ;;
  *) echo "EDGE_HONESTY_FAIL bad_document_id=$D"; exit 2 ;;
esac

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
PW=$(docker inspect neo4j --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep '^NEO4J_AUTH=' | cut -d/ -f2-)
[ -n "$PW" ] || { echo "EDGE_HONESTY_FAIL neo4j_password_unreadable"; exit 2; }

# Chunk nodes carry `id`, NOT `chunk_id`, and no text at all — the text lives in
# pgvector only. A wrong property name returns NULL for every row, which reads
# exactly like "the field is never populated".
if ! docker exec neo4j cypher-shell -u neo4j -p "$PW" --format plain "
MATCH (c:Chunk {document_id:'$D'})-[r]->(e:Entity)
RETURN type(r)+'\t'+c.id+'\t'+e.name AS row;" > "$TMP/edges.raw" 2>"$TMP/err"; then
  echo "EDGE_HONESTY_FAIL neo4j_error: $(head -c 160 "$TMP/err" | tr '\n' ' ')"; exit 1
fi
[ -s "$TMP/err" ] && { echo "EDGE_HONESTY_FAIL neo4j_error: $(head -c 160 "$TMP/err" | tr '\n' ' ')"; exit 1; }
tail -n +2 "$TMP/edges.raw" | tr -d '"' > "$TMP/edges.tsv"

# \r is stripped as well as \n and \t: Python reads universal newlines, so a lone
# carriage return splits one chunk's text in two, truncating it — the entity name
# then reads as absent and silently inflates the count instead of failing.
if ! docker exec pgvector psql -U scrapalot -d scrapalot -At -F$'\t' -c "
SELECT id, coalesce(cmetadata->>'chunk_index', ''), replace(replace(replace(lower(document), E'\n', ' '), E'\r', ' '), E'\t', ' ')
FROM langchain_pg_embedding WHERE cmetadata->>'document_id'='$D';" > "$TMP/chunks.tsv" 2>"$TMP/perr"; then
  echo "EDGE_HONESTY_FAIL pgvector_error: $(head -c 160 "$TMP/perr" | tr '\n' ' ')"; exit 1
fi

python3 - "$TMP" <<'PY'
import collections, re, sys
t = sys.argv[1]
chunks, index = {}, {}
for line in open(f"{t}/chunks.tsv", encoding="utf-8", errors="replace"):
    p = line.rstrip("\n").split("\t", 2)
    if len(p) == 3:
        chunks[p[0]] = p[2]
        index[p[0]] = p[1]
# Reading order for the neighbour class, only when every chunk carries a numeric
# chunk_index; otherwise that class is reported as unavailable.
ordered = bool(index) and all(v.isdigit() for v in index.values())
order = sorted(chunks, key=lambda c: int(index[c])) if ordered else []
rank = {c: n for n, c in enumerate(order)}
book_text = "\n".join(chunks.values())

tot, bad, unresolved = collections.Counter(), collections.Counter(), 0
worst = collections.defaultdict(set)
split = collections.Counter()


def classify(cid, low, text):
    words = [w for w in re.findall(r"[^\W\d_]+", low) if len(w) >= 4]
    if words and all(w[:max(4, len(w) - 3)] in text for w in words):
        return "variant"
    if ordered:
        n = rank[cid]
        if any(low in chunks[order[n + k]] for k in (-2, -1, 1, 2) if 0 <= n + k < len(order)):
            return "neighbour"
    return "elsewhere" if low in book_text else "nowhere"


edges_seen = 0
for line in open(f"{t}/edges.tsv", encoding="utf-8", errors="replace"):
    f = line.rstrip("\n").split("\t")
    if len(f) != 3:
        continue
    edges_seen += 1
    rel, cid, name = f
    text = chunks.get(cid)
    if text is None:
        unresolved += 1
        continue
    tot[rel] += 1
    low = name.lower()
    if low not in text:
        bad[rel] += 1
        worst[rel].add(name)
        split[classify(cid, low, text)] += 1

# Printed BEFORE any early exit: if every edge failed to resolve, this is the
# only place it shows, and the old version suppressed it in exactly that case.
print(f"EDGE_HONESTY chunk_texts={len(chunks)} edges={edges_seen} unresolvable_chunk_ids={unresolved}")
if unresolved and unresolved == edges_seen:
    print("EDGE_HONESTY_FAIL every edge's chunk id is unknown to pgvector — join broken, not a fact about the book")
    raise SystemExit(1)
if not tot:
    # An empty layer is nothing to judge, and exiting 0 with digits that match the
    # EXPECT ticked G7c green on a book mid-rebuild with 0 entities.
    print("EDGE_HONESTY_FAIL entity_layer_empty — nothing to judge")
    raise SystemExit(1)
for rel in sorted(tot, key=lambda r: -tot[r]):
    pct = 100 * bad[rel] / tot[rel]
    ex = ", ".join(sorted(worst[rel])[:3])          # deduplicated: 3 offenders, not one name thrice
    print(f"  {rel:<12} edges={tot[rel]:<5} name_absent={bad[rel]:<4} ({pct:4.1f}%)  distinct_offenders={len(worst[rel])}  e.g. {ex}")
n, b = sum(tot.values()), sum(bad.values())
print(f"EDGE_HONESTY_TOTAL edges={n} name_absent={b} ({100*b/n:.1f}%) — a POINTER to read, not a defect rate; spelling normalisation inflates it")
nb = f"neighbour={split['neighbour']}" if ordered else "neighbour=unavailable(no_chunk_index)"
print(f"EDGE_HONESTY_SPLIT name_absent={b} variant={split['variant']} {nb} elsewhere={split['elsewhere']} nowhere={split['nowhere']}")
print("EDGE_HONESTY_READ_ME variant is a normalised spelling. neighbour edges are still wrong edges, mostly from one cause: "
      "a merged extraction unit gives each of its entities an edge to every source chunk, so the name sits next door. "
      "Read elsewhere and nowhere first, then a sample of neighbour, and look for a name printed in a chunk that carries no edge to it.")
PY
