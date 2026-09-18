#!/usr/bin/env bash
# Parse damage that reaches the graph as an entity NAME.
#
# A blind critic found two such classes on a German book after every other gate
# had passed, so they became a check:
#
#   1. FUSED WORDS. A line break lost its hyphen and two words ran together:
#      ArgonautenSage, JohannesBuch, SaturnEntwicklung.
#   2. ONE-OFF SPELLINGS. A name occurring exactly once as a WORD in
#      documents.content while a close variant occurs more often is usually the
#      damaged copy: `Sulfiir` once against `Sulfur` 21 times; `JohannesBuch`
#      once against `Johannes-Buch` five times.
#
# **THIS OUTPUT MUST BE READ, NOT COUNTED.** Measured over 11,937 corpus
# entities, roughly 59% of what the fusion rule flags are correct forms a book
# legitimately writes — LinkedIn, iPhone, CrossFit, WordPress, Lady GaGa,
# DiDonato, LaPorte, DeAngelo. Gaelic and Scottish surnames are excluded by
# name, but no rule can separate `HodgkinHuxley equations` from `SoundCloud`
# without someone looking. A count on its own is worth nothing here.
#
# **It is PARSE damage, not extraction.** The extractor stored faithfully what
# the text already held: `ArgonautenSage` occurs once in documents.content and
# `Argonauten-Sage` never. A book can carry all of it while its ledger row reads
# `parse_done_clean` — that row promises the CHAPTER LAYER, not clean text.
# Report it; never delete; the fix is upstream and is the owner's call.
#
# FAILS CLOSED, like its siblings: an unreachable database, an empty entity layer
# and a missing Book all abort. An earlier draft of THIS script sent the second
# query's stderr to /dev/null and announced "the entity layer is empty" — an
# infrastructure failure reported as a fact about the book, which is the exact
# bug edge-honesty.sh's header records as already fixed. Do not reintroduce it.
#
# Usage: name-damage.sh <document_id>
set -uo pipefail
D="${1:?usage: name-damage.sh <document_id>}"
case "$D" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-*-*-*-*) ;;
  *) echo "NAME_DAMAGE_FAIL bad_document_id=$D"; exit 2 ;;
esac
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
PW=$(docker inspect neo4j --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep '^NEO4J_AUTH=' | cut -d/ -f2-)
[ -n "$PW" ] || { echo "NAME_DAMAGE_FAIL neo4j_password_unreadable"; exit 2; }

B=$(docker exec neo4j cypher-shell -u neo4j -p "$PW" --format plain "MATCH (b:Book {document_id:'$D'}) RETURN count(b);" 2>&1 | tail -1 | tr -d ' ')
case "$B" in 1) ;; 0) echo "NAME_DAMAGE_FAIL book_not_found"; exit 1;; *) echo "NAME_DAMAGE_FAIL neo4j_error: $B"; exit 1;; esac

docker exec neo4j cypher-shell -u neo4j -p "$PW" --format plain "
MATCH (:Book {document_id:'$D'})-[:MENTIONS]->(e:Entity) RETURN e.name;" >"$TMP/raw" 2>"$TMP/err"
rc=$?
[ $rc -eq 0 ] && [ ! -s "$TMP/err" ] || { echo "NAME_DAMAGE_FAIL neo4j_error: $(head -c 150 "$TMP/err" | tr '\n' ' ')"; exit 1; }
tail -n +2 "$TMP/raw" | sed 's/^"//; s/"$//' > "$TMP/names.txt"
# An empty entity layer is not a clean sheet — it is nothing to judge, and it
# must not be reported in the shape of a pass.
[ -s "$TMP/names.txt" ] || { echo "NAME_DAMAGE_FAIL entity_layer_empty — nothing to judge"; exit 1; }

docker exec pgvector psql -U scrapalot -d scrapalot -At -c "SELECT content FROM documents WHERE id='$D';" >"$TMP/text.txt" 2>"$TMP/perr"
[ -s "$TMP/text.txt" ] || { echo "NAME_DAMAGE_FAIL document_content_empty: $(head -c 120 "$TMP/perr" | tr '\n' ' ')"; exit 1; }

python3 - "$TMP" <<'PY'
import re, sys
t = sys.argv[1]
names = [l.strip() for l in open(f"{t}/names.txt", encoding="utf-8", errors="replace") if l.strip()]
raw = open(f"{t}/text.txt", encoding="utf-8", errors="replace").read()
norm = raw.replace("­", "").replace("’", "'").replace("‘", "'")
low = norm.lower()

# Unicode-aware, not Latin-1: a Croatian, Czech, Polish or Greek book must not
# come back a confident zero because its letters fell outside a byte range.
def fusion_sites(s: str):
    return [i for i in range(1, len(s)) if s[i-1].islower() and s[i].isupper()]

# Gaelic and Scottish surnames carry an internal capital by right.
NATIVE = re.compile(r"\b(Ma?c|O')(?=[^\W\da-z])", re.UNICODE)
def mask(s: str) -> str:
    return NATIVE.sub(lambda m: "_" * len(m.group(0)), s)

fused = [n for n in names if fusion_sites(mask(n))]

def word_count(term: str) -> int:
    """Occurrences of `term` as a whole word.

    The boundary must treat `_` as punctuation, not as a letter. Markdown
    emphasis wraps words in underscores — the text prints `_Sal, Mercur,
    Sulfiir_` — and a plain \b boundary therefore counts `Sulfiir` zero times
    and drops the one name this class exists to catch.
    """
    b = r"(?<![^\W_])" + re.escape(term.lower()) + r"(?![^\W_])"
    return len(re.findall(b, low))

# The one-off class is defined by the text, NOT by fusion: `Sulfiir` has no
# internal capital and is the textbook case. Counting must be word-bounded —
# a substring count calls `Astra` 30 and hides it.
# --- the one-off class, kept to what is actually reliable -------------------
# A first attempt hunted near-variants for every token against the book's whole
# vocabulary. It returned 46 hits on a 645-name book, nearly all nonsense:
# Faust->fast, Kiel->viel, John->johann, Gnosis->genesis. Fuzzy matching arbitrary
# words against a large vocabulary cannot carry a gate, so it is gone.
#
# What remains has evidence behind each hit:
#   SEAM   — a fused name whose hyphenated or spaced form the book actually uses.
#   NEAR   — a single-token name occurring once, against a variant sharing a
#            4-character prefix, within edit distance 2, and at least 5x as
#            frequent. `Sulfiir` vs `Sulfur` (1 vs 21) is the case this exists for.
#
# WHAT THIS CANNOT SEE, and the critic still must: OCR mangling with no seam and
# no close neighbour — `Gäblr ibn Hayyän`, `Mvlaprakrti`, `al-Färäbl`, `ar-RäzI`.
# Those were found by a human-style read of the name list and nothing here
# replaces that. Nor a fusion with no internal capital: `Godconsciousness` is
# printed once and `God consciousness` never, so it has no seam and no neighbour.
# Nor `vibeshifting mist`: two words, and its damaged token is printed exactly as
# often as the intact `vibe-shifting` (1 against 1), so NEAR's 5x rule cannot fire
# even per token.
#
# NOR `King Solotmn`, OCR rot for Solomon. The name occurs once, but it has two
# words and NEAR only tests single-token names; its damaged token `Solotmn`
# occurs twice, so a per-token NEAR would not call it a one-off either. That
# variant was measured over five books and left out: 28 flags, 0 of them damage
# (Medici~medical, Frances~francis, Splendor~splendour).
#
# NEAR is weak evidence even where it applies: over the same five books it
# flagged 5 names and 1 was damage (`Sulfiir`); the other four were real words
# beside similar ones (Trier~tried, Urinal~urine, Sophia~sophic,
# Symbolists~symbolism).
import difflib
VOCAB = {w for w in re.findall(r"\w{4,}", low)}

def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n

oneoff = []
for n in names:
    if word_count(n) != 1:
        continue
    best = None
    for i in fusion_sites(mask(n)):
        for c in (n[:i] + "-" + n[i:], n[:i] + " " + n[i:]):
            k = word_count(c)
            if k > 1 and (best is None or k > best[1]):
                best = (c, k, "SEAM")
    if best is None and len(n.split()) == 1 and len(n) >= 5:
        nl = n.lower()
        for c in difflib.get_close_matches(nl, VOCAB, n=5, cutoff=0.70):
            if c == nl or c in nl or nl in c:
                continue
            if common_prefix(c, nl) < 4 or edit_distance(c, nl) > 2:
                continue
            k = word_count(c)
            if k >= 5 and (best is None or k > best[1]):
                best = (c, k, "NEAR")
    if best:
        oneoff.append((n, best[0], best[1], best[2]))

print(f"NAME_DAMAGE names={len(names)} fused={len(fused)} oneoff={len(oneoff)}")
for n in fused:
    print(f"    fused   {n}")
for n, better, c, kind in oneoff:
    print(f"    oneoff[{kind}]  {n!r} occurs once as a word; {better!r} occurs {c} times")
print("NAME_DAMAGE_BLIND OCR damage with no seam and no close neighbour (Gäblr ibn Hayyän, Mvlaprakrti), and a two-word name whose damaged word repeats elsewhere (King Solotmn), a fusion with no internal capital (Godconsciousness), and a two-word name whose damaged token is no rarer than its hyphenated form (vibeshifting mist), are NOT detectable here — the critic still has to read the list.")
print("NAME_DAMAGE_READ_ME ~59% of `fused` corpus-wide are correct forms (LinkedIn, iPhone, DiDonato), and NEAR was damage 1 time in 5 over five books. Read each one; a count proves nothing.")
PY
rc=$?
[ $rc -eq 0 ] || { echo "NAME_DAMAGE_FAIL analysis_failed rc=$rc"; exit 1; }
echo "NAME_DAMAGE_OK"
