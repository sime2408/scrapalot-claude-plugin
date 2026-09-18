#!/usr/bin/env bash
# Whether a book's STORED chunks lost words the book prints, to the chunker's old running-header rule.
#
# `_filter_headers_footers` used to delete every line under 40 characters that
# repeats 3+ times. Where a book puts a short string on a line of its own inside a
# sentence — an EPUB converter does this with every italic run — that deleted the
# sentence's own words: cc32d8f5's chunk stored "Dreams in which suicide is
# highlighted are encouraging…" where the book prints "are not encouraging", and
# its italic heading line `Themes` vanished into the entity `strong emotional
# dreams`. The live rule keeps an occurrence the sentence runs through, but only
# for NEW chunking; every chunk stored before it still carries the cut.
#
# Method, offline and read-only:
#   * run the live filter over documents.content twice — as it is, and with the
#     sentence rescue switched off (the old rule, exactly);
#   * the occurrences the first keeps and the second drops are the words the old
#     rule cut from inside sentences;
#   * each one is then looked for in the book's stored chunks, joined in order:
#     "missing" means the phrase WITHOUT the word is there and the phrase WITH it
#     is not — the stored text really lacks it. That is the number that matters;
#     the first is only what the old rule would cut.
# A count proves nothing on its own: read the strings. `not` missing from one
# sentence can invert a book's meaning, `context` missing from nineteen costs
# little.
#
# Usage: chunk-text-loss.sh <document_id>
set -uo pipefail
D="${1:?usage: chunk-text-loss.sh <document_id>}"
case "$D" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-*-*-*-*) ;;
  *) echo "CHUNK_TEXT_LOSS_FAIL bad_document_id=$D"; exit 2 ;;
esac
OUT=$(docker exec -i scrapalot-chat python - "$D" 2>/dev/null <<'PY'
import collections, os, re, sys

import psycopg2

from src.main.service.rag.chunking.chunking_enhanced_markdown import EnhancedMarkdownChunkingStrategy as S

doc = sys.argv[1]
conn = psycopg2.connect(host="pgvector", port=5432, dbname="scrapalot", user="scrapalot", password=os.environ["POSTGRES_PASSWORD"])
cur = conn.cursor()
cur.execute("SELECT content FROM documents WHERE id = %s AND deleted_at IS NULL", (doc,))
row = cur.fetchone()
if not row or not row[0]:
    print("CHUNK_TEXT_LOSS_FAIL no_live_content")
    raise SystemExit(0)
text = row[0]
cur.execute(
    "SELECT document FROM langchain_pg_embedding WHERE cmetadata->>'document_id' = %s "
    "AND coalesce(cmetadata->>'is_multimodal','false') <> 'true' "
    "ORDER BY (cmetadata->>'chunk_index')::int NULLS LAST",
    (doc,),
)
stored = " ".join(" ".join((r[0] or "").split()) for r in cur.fetchall())
if not stored:
    print("CHUNK_TEXT_LOSS_FAIL no_stored_chunks")
    raise SystemExit(0)

chunker = S()
live = chunker._filter_headers_footers(text).split("\n")
rescue = S._text_runs_through
S._text_runs_through = staticmethod(lambda previous, following, stripped: False)
try:
    old = chunker._filter_headers_footers(text).split("\n")
finally:
    S._text_runs_through = rescue

live_count = collections.Counter(line.strip() for line in live if line.strip())
old_count = collections.Counter(line.strip() for line in old if line.strip())
cut = {s: live_count[s] - old_count[s] for s in live_count if live_count[s] > old_count[s]}
cut_total = sum(cut.values())

# Read each cut occurrence back against the stored chunks.
lines = [line.strip() for line in text.split("\n")]
nonempty = [(i, s) for i, s in enumerate(lines) if s]
where = collections.defaultdict(list)
for k, (_i, s) in enumerate(nonempty):
    if s in cut:
        where[s].append(k)


def edge(words, n, tail):
    parts = words.split()
    return " ".join(parts[-n:] if tail else parts[:n])


missing = collections.Counter()
examples = []
for s, positions in where.items():
    for k in positions:
        before = nonempty[k - 1][1] if k > 0 else ""
        after = nonempty[k + 1][1] if k + 1 < len(nonempty) else ""
        # Only the occurrences the live rule keeps: the others are margins both rules
        # delete, and their absence from the chunks is the filter working.
        if not before or not after or not S._text_runs_through(before, after, s):
            continue
        a, b = edge(before, 4, True), edge(after, 4, False)
        with_it = " ".join(f"{a} {s} {b}".split())
        without = " ".join(f"{a} {b}".split())
        if with_it not in stored and without in stored:
            missing[s] += 1
            examples.append((s, f"…{a} [{s}] {b}…"))

# The live rescue also re-admits some margins — a title running head where a page
# broke mid-sentence and no folio line sits beside it (4fb26145 kept "The
# Experience of Eternity" 54 times), and index rows whose neighbours are index
# rows (c54b5060, "hotline numbers, 192"). Their absence from the chunks is the
# old rule being RIGHT. A word that opens in lower case and carries no digit is
# neither a title nor an index row, so only those count as lost words.
def sentence_word(s):
    return s[:1].islower() and not any(ch.isdigit() for ch in s)


lost = collections.Counter({s: n for s, n in missing.items() if sentence_word(s)})
lost_total = sum(lost.values())
missing_total = sum(missing.values())
print(f"CHUNK_TEXT_LOSS lines={len(lines)} old_rule_cuts_from_sentences={cut_total} missing_from_stored_chunks={missing_total} sentence_words_lost={lost_total} distinct_lost={len(lost)}")
if lost:
    print("    lost words: " + ", ".join(f"{s!r}x{n}" for s, n in lost.most_common(20)))
other = [(s, n) for s, n in missing.most_common() if not sentence_word(s)]
if other:
    print("    missing but not a sentence word (margins or index rows the old rule rightly cut): " + ", ".join(f"{s[:40]!r}x{n}" for s, n in other[:10]))
for e in [shown for word, shown in examples if sentence_word(word)][:4]:
    print("    e.g. " + e)
print("CHUNK_TEXT_LOSS_NONE" if lost_total == 0 else "CHUNK_TEXT_LOSS_FOUND")
PY
)
# The container's own logging writes to stdout too; keep only this script's lines.
OUT=$(echo "$OUT" | grep -E '^(CHUNK_TEXT_LOSS|    )')
[ -n "$OUT" ] || { echo "CHUNK_TEXT_LOSS_FAIL container_run_printed_nothing"; exit 2; }
echo "$OUT"
