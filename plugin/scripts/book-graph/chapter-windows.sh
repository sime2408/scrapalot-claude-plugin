#!/usr/bin/env bash
# Are a document's chapters its own, or linear windows of chunk_index?
#
# The chapter-lock recovery in scrapalot-chat's document processor assigns
# LLM-detected chapters by `min(i // (n // k), k - 1)` and ignores the line each
# chapter starts at, so every chapter but the last holds exactly n // k chunks.
# A graph built on that layer carries the book's real chapter titles over the
# wrong chunks, the extraction context names the wrong chapter, and a
# reachability check goes green over all of it. Measured on 2026-09-17: 2835f808
# (176 chunks, 9 chapters) is 19 x 8 + 24, with 55 of its 129 body chunks under
# a neighbouring chapter; 03dad975 is 17 x 5 + 22. Four other accepted books have
# irregular sizes. Equal windows are the tell; read the flagged book's headings
# against its chunks before calling it.
#
# Figure descriptions stored beside the text chunks carry no chunk_index, so the
# recovery never placed them, and nearly all carry no chapter either. Counted, they
# formed one more "chapter" and hid the runs of two books (25 x 5 + 30 beside 91
# figure rows; 123 x 4 beside 97), so a figure row without a chunk_index is left out.
#
# Fails closed: an unreadable database or a document without chunks aborts with
# CHAPTER_WINDOWS_FAIL instead of printing OK.
#
# Usage: chapter-windows.sh <document_id>
set -uo pipefail
D="${1:?usage: chapter-windows.sh <document_id>}"
[[ "$D" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] || { echo "CHAPTER_WINDOWS_FAIL bad_document_id=$D"; exit 2; }
PG="${PG_CONTAINER:-pgvector}"
U=$(docker exec "$PG" printenv POSTGRES_USER 2>/dev/null)
[ -n "$U" ] || { echo "CHAPTER_WINDOWS_FAIL pg_user_unreadable"; exit 2; }
ERR=$(mktemp); trap 'rm -f "$ERR"' EXIT
SIZES=$(docker exec "$PG" psql -U "$U" -d scrapalot -At -c "SELECT string_agg(n::text, ',' ORDER BY first) FROM (SELECT min((cmetadata->>'chunk_index')::int) AS first, count(*) AS n FROM langchain_pg_embedding WHERE cmetadata->>'document_id' = '$D' AND NOT (coalesce((cmetadata->>'is_multimodal')::boolean, false) AND cmetadata->>'chunk_index' IS NULL) GROUP BY coalesce(cmetadata->>'chapter_title', '')) s;" 2>"$ERR")
rc=$?
{ [ $rc -eq 0 ] && [ ! -s "$ERR" ]; } || { echo "CHAPTER_WINDOWS_FAIL query_error rc=$rc: $(head -c 160 "$ERR" | tr '\n' ' ')"; exit 2; }
[ -n "$SIZES" ] || { echo "CHAPTER_WINDOWS_FAIL no_chunks"; exit 1; }
python3 - "$SIZES" <<'PY'
import sys

sizes = [int(x) for x in sys.argv[1].split(",")]
n, k = sum(sizes), len(sizes)
print(f"CHAPTER_WINDOWS chapters={k} chunks={n} sizes={sizes}")
per = n // k
if k >= 3 and per > 1 and all(s == per for s in sizes[:-1]) and sizes[-1] == n - per * (k - 1):
    print(f"CHAPTER_WINDOWS_LINEAR every chapter but the last holds exactly {n} // {k} = {per} chunks: "
          "these are windows of chunk_index, not the book's chapters")
    sys.exit(1)
print("CHAPTER_WINDOWS_OK")
PY
