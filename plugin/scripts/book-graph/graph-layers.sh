#!/usr/bin/env bash
# The connectivity layers a hierarchy check and an entity-name read both miss:
# alias duplication, cross-book linking, communities, co-occurrence weights,
# relationship-label honesty, chapter order.
#
# THIS SCRIPT FAILS CLOSED. Every earlier version of it did not: with a wrong
# password every line printed blank and it still ended with LAYERS_OK, so the
# ledger box went green over a measurement that never happened. So:
#   * the Book node is resolved FIRST — a mistyped id aborts instead of
#     reporting a confident, empty "this book has no graph";
#   * every Cypher call checks its exit status and its stderr, and aborts;
#   * every query is anchored on a node known to exist and OPTIONAL-matches what
#     it counts, because `cypher-shell --format plain` prints NOTHING — not even
#     a header — when an aggregation with a grouping key matches zero rows, and
#     a literal in the RETURN does NOT save you: the literal is itself a
#     grouping key, so the WHERE must not filter rows away before the count;
#   * LAYERS_OK is printed only when every LAYER line carries a number.
# Prove any change to it the way this file prescribes: swap a relationship for
# [:NO_SUCH_REL] and confirm a 0 prints rather than nothing.
#
# Usage: graph-layers.sh <document_id>
set -uo pipefail

D="${1:?usage: graph-layers.sh <document_id>}"
case "$D" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-*-*-*-*) ;;
  *) echo "LAYERS_FAIL bad_document_id=$D"; exit 2 ;;
esac

PW=$(docker inspect neo4j --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep '^NEO4J_AUTH=' | cut -d/ -f2-)
[ -n "$PW" ] || { echo "LAYERS_FAIL neo4j_password_unreadable"; exit 2; }

ERR=$(mktemp); trap 'rm -f "$ERR"' EXIT
cy() {
  local out
  out=$(docker exec neo4j cypher-shell -u neo4j -p "$PW" --format plain "$1" 2>"$ERR")
  if [ $? -ne 0 ] || [ -s "$ERR" ]; then
    echo "LAYERS_FAIL neo4j_error: $(head -c 160 "$ERR" | tr '\n' ' ')" >&2
    return 1
  fi
  printf '%s' "$out"
}
# Pull the fields after the marker off a one-row result. Empty => the query
# returned nothing, which is never acceptable here.
row() { echo "$1" | grep "\"$2\"" | head -1 | sed 's/^[^,]*, //'; }

fail() { echo "LAYERS_FAIL $1"; exit 1; }

# --- the anchor. Everything below hangs off a Book that must exist ------------
B=$(cy "OPTIONAL MATCH (b:Book {document_id:'$D'}) RETURN 'B' AS k, count(b) AS n;") || fail neo4j_unreachable
BN=$(row "$B" B)
[ -n "$BN" ] || fail anchor_query_returned_nothing
[ "$BN" != "0" ] || fail "book_not_found document_id=$D"

MISSING=""
emit() { # emit <label> <value...>
  local label="$1"; shift
  local v="$*"
  if [ -z "${v// /}" ]; then MISSING="$MISSING $label"; echo "LAYER=$label MISSING"; else echo "LAYER=$label $v"; fi
}

# --- entity totals and type spread (a mistyped entity is visible here) --------
T=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(e:Entity)
RETURN 'T' AS k, count(e) AS entities, count(DISTINCT e.canonical_name) AS distinct_canonical;") || fail neo4j_unreachable
TV=$(row "$T" T)
TN=${TV%%,*}
[[ "$TN" =~ ^[0-9]+$ ]] || fail "entity_count_unreadable: $TV"
# An empty entity layer has no connectivity to measure. Printing zeros and
# LAYERS_OK over it ticked G7a green on a book mid-rebuild with 0 entities.
[ "$TN" != "0" ] || fail "entity_layer_empty — nothing to judge"
# The corpus figure belongs beside the book's, or the book gets blamed for a gap
# the whole graph has: G7a-read asks which of the two a number is, and without
# this line that question is answered by hand every time.
TC=$(cy "MATCH (e:Entity) RETURN 'TC' AS k, count(e) AS corpus_entities, count(DISTINCT e.canonical_name) AS corpus_canonical;") || fail neo4j_unreachable
emit canonical "$TV | corpus $(row "$TC" TC)${TV:+   <- equal numbers mean NO deduplication exists}"

TY=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(e:Entity)
RETURN 'TY' AS k, coalesce(e.entity_type,'(none)') AS t, count(e) AS n ORDER BY n DESC;") || fail neo4j_unreachable
echo "LAYER=entity_types $(echo "$TY" | grep '"TY"' | sed 's/^"TY", //' | tr '\n' ' ')"

# --- alias duplication, one class per short form. A surname matching ONE full
# --- name is a likely missing alias; a given name matching one is weaker
# --- evidence; a short form matching SEVERAL names cannot be merged on its own —
# --- `John` matched five different men in one book (Dee, Aubrey, Trithemius,
# --- Mehung, Helvetius), while `Steiner` matched two names of one man. Those are
# --- listed by name below. The tests run INSIDE the aggregation, so zero pairs
# --- still prints a row.
A=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(e:Entity) WHERE e.entity_type='person'
WITH collect(e.name) AS ns
WITH ns, [y IN ns | [
    size([x IN ns WHERE x<>y AND size(y)<size(x) AND toLower(x) ENDS WITH (' '+toLower(y))]),
    size([x IN ns WHERE x<>y AND size(y)<size(x) AND toLower(x) STARTS WITH (toLower(y)+' ')]),
    size([x IN ns WHERE x<>y AND size(y)<size(x)
        AND (toLower(x) ENDS WITH (' '+toLower(y)) OR toLower(x) STARTS WITH (toLower(y)+' '))])]] AS t
RETURN 'A' AS k, size(ns) AS persons,
    size([r IN t WHERE r[2] = 1 AND r[0] = 1]) AS surname_unique,
    size([r IN t WHERE r[2] = 1 AND r[0] = 0 AND r[1] = 1]) AS given_unique,
    size([r IN t WHERE r[2] > 1]) AS ambiguous;") || fail neo4j_unreachable
emit alias_person_short_forms "$(row "$A" A)"
echo "    (persons, surname-short unique, given-name-short unique, short forms matching several names — read those below)"
AD=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(e:Entity) WHERE e.entity_type='person'
WITH collect(e.name) AS ns
UNWIND ns AS y
WITH y, [x IN ns WHERE x<>y AND size(y)<size(x)
    AND (toLower(x) ENDS WITH (' '+toLower(y)) OR toLower(x) STARTS WITH (toLower(y)+' '))] AS longs
WHERE size(longs) > 1
RETURN 'AD' AS k, y AS short_form, size(longs) AS n, longs[0..6] AS matches ORDER BY n DESC, short_form LIMIT 20;") || fail neo4j_unreachable
echo "LAYER=alias_ambiguous_detail rows=$(echo "$AD" | grep -c '"AD"')"
echo "$AD" | grep '"AD"' | sed 's/^/    /'

# --- a short form stored under ANOTHER type escapes the person-only test above:
# --- `Lauren` typed place beside `Lauren Aletta`. A hit is a mistyped person or a
# --- word inside a longer name; the command file carries the measured counts. Read each.
AN=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(p:Entity) WHERE p.entity_type='person' AND p.name CONTAINS ' '
WITH b, collect(p.name) AS persons
OPTIONAL MATCH (b)-[:MENTIONS]->(s:Entity) WHERE coalesce(s.entity_type,'') <> 'person' AND NOT s.name CONTAINS ' '
WITH s, [x IN persons WHERE s IS NOT NULL AND (toLower(x) STARTS WITH (toLower(s.name)+' ') OR toLower(x) ENDS WITH (' '+toLower(s.name)))] AS longs
WITH collect(CASE WHEN size(longs) > 0 THEN coalesce(s.entity_type,'?') + ' ' + s.name + ' -> ' + reduce(t='', x IN longs[..4] | t + x + '; ') END) AS hits
RETURN 'AN' AS k, size(hits) AS n, hits[..20] AS detail;") || fail neo4j_unreachable
ANV=$(row "$AN" AN)
emit alias_non_person_short_forms "${ANV%%,*}"
[ -n "$ANV" ] && echo "    (short forms of a person name stored under another type: a mistyped person, or a word inside a longer name; read each) ${ANV#*, }"

# --- cross-book linking: stored edges vs the overlap that actually exists -----
S=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:SHARED_ENTITY]-(o:Book)
RETURN 'S' AS k, count(DISTINCT o) AS linked_books;") || fail neo4j_unreachable
emit shared_entity_edges "$(row "$S" S)"

R=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(o:Book) WHERE o.document_id <> '$D'
RETURN 'R' AS k, count(DISTINCT e) AS shared_entities, count(DISTINCT o) AS other_books;") || fail neo4j_unreachable
emit real_overlap "$(row "$R" R)"

# --- what each link rides on. G7b requires this to be READ, not counted ------
SD=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[s:SHARED_ENTITY]-(o:Book)
RETURN 'X' AS k, coalesce(s.shared_entity_count,0) AS n, left(coalesce(o.title,'(none)'),40) AS book,
       coalesce(s.top_entities,[]) AS on_what ORDER BY n DESC;") || fail neo4j_unreachable
echo "LAYER=shared_entity_detail rows=$(echo "$SD" | grep -c '"X"')"
echo "$SD" | grep '"X"' | sed 's/^/    /'

# --- what a link stands on. A shared name the book never prints is not a thin
# --- link, it is a false one: the extractor labelled a passage with a word from
# --- somewhere else and the label then matched another book's real entity. On
# --- cc32d8f5 three links rode on such names — `Initiationspfad` to a German
# --- alchemy book, `catastrophic thinking` to two CBT workbooks, `Water of life`
# --- to an alchemy text — and nothing in this script asked the question, so it
# --- had to be found by hand. Whole word over the content with its whitespace
# --- collapsed, since a book hard-wraps and a name breaks across lines.
CONTENT=$(mktemp); NAMES=$(mktemp); trap 'rm -f "$ERR" "$CONTENT" "$NAMES"' EXIT
docker exec pgvector psql -U scrapalot -d scrapalot -At -c "SELECT content FROM documents WHERE id='$D';" > "$CONTENT" 2>"$ERR" || fail "shared_link_names_content_query: $(head -c 120 "$ERR" | tr '\n' ' ')"
[ -s "$CONTENT" ] || fail "shared_link_names_content_empty document_id=$D"
echo "$SD" | grep '"X"' | sed 's/.*\[//;s/\].*//' | tr ',' '\n' | sed 's/^ *"//;s/" *$//' | sort -u > "$NAMES"
LN=$(python3 - "$CONTENT" "$NAMES" <<'PY'
import re, sys
def norm(v):
    return v.replace("­", "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').lower()
text = norm(" ".join(open(sys.argv[1], encoding="utf-8", errors="replace").read().split()))
names = [n.strip() for n in open(sys.argv[2], encoding="utf-8") if n.strip()]
absent = []
for name in names:
    key = norm(name).strip()
    if not key:
        continue
    pattern = r"(?<![^\W_])" + r"\s+".join(re.escape(w) for w in key.split()) + r"(?![^\W_])"
    if not re.search(pattern, text) and key not in text:
        absent.append(name)
print(f"{len(names)}, {len(absent)} absent_from_this_book")
if absent:
    print("    (each of these links stands on a name the book never prints - read the chunk behind it) " + ", ".join(sorted(absent)[:25]))
PY
) || fail shared_link_names_unreadable
emit shared_link_names "$(echo "$LN" | head -1)"
echo "$LN" | tail -n +2 | grep . || true

# --- communities, with the corpus baseline beside it -------------------------
M=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(e:Entity)
OPTIONAL MATCH (e)-[:IN_COMMUNITY]->(c:Community)
WITH e, count(c) AS hasc
RETURN 'M' AS k, count(e) AS entities, sum(CASE WHEN hasc>0 THEN 1 ELSE 0 END) AS in_community;") || fail neo4j_unreachable
G=$(cy "MATCH (b:Book {document_id:'$D'}) WITH b OPTIONAL MATCH (c:Community) RETURN 'G' AS k, count(c) AS corpus_communities;") || fail neo4j_unreachable
# How many entities the corpus has in a community at all. Without it, "6 of 708"
# reads as this book's failure when it is the corpus-wide state of the layer.
GM=$(cy "MATCH (e:Entity) WHERE (e)-[:IN_COMMUNITY]->(:Community) RETURN 'GM' AS k, count(e) AS corpus_entities_in_a_community;") || fail neo4j_unreachable
emit communities "$(row "$M" M) corpus_communities=$(row "$G" G) corpus_entities_in_a_community=$(row "$GM" GM)"

# --- co-occurrence weights. The recompute writes `document_weighted_score`
# --- (cooccurrence_weight_service.py); nothing writes `weight`, which this line
# --- counted until 2026-09-17 and so read 0 while 918 edges carried a score.
# --- Count DISTINCT on the book side: the undirected
# --- pattern visits an edge once per book-mentioned endpoint (2279 vs 1423 on
# --- one measured book), and the corpus half is single-counted, so without
# --- DISTINCT the two halves of this line are not comparable.
W=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(:Entity)-[r:CO_OCCURS_WITH]-()
RETURN 'W' AS k, count(DISTINCT r) AS edges, count(DISTINCT CASE WHEN r.document_weighted_score IS NULL THEN null ELSE r END) AS weighted;") || fail neo4j_unreachable
WC=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH ()-[r:CO_OCCURS_WITH]->()
RETURN 'WC' AS k, count(r) AS corpus_edges, count(r.document_weighted_score) AS corpus_weighted;") || fail neo4j_unreachable
emit cooccurrence "$(row "$W" W) | corpus $(row "$WC" WC)"

# --- chapter order -----------------------------------------------------------
N=$(cy "
MATCH (b:Book {document_id:'$D'}) WITH b
OPTIONAL MATCH (b)-[:HAS_CHAPTER]->(ch:Chapter)
WITH b, count(ch) AS chapters
OPTIONAL MATCH (b)-[:HAS_CHAPTER]->(:Chapter)-[n:NEXT]->(:Chapter)
RETURN 'N' AS k, chapters AS chapters, count(n) AS next_edges;") || fail neo4j_unreachable
emit chapter_chain "$(row "$N" N)"

[ -z "$MISSING" ] || fail "layers_missing_values:$MISSING"
echo "LAYERS_OK"
