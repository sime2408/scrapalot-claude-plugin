#!/usr/bin/env bash
# Was the book's parse_done_clean row written about the chunks stored now?
#
# The row is a claim about the chapter layer the audit read. A reprocess after it
# re-cuts the chunks and runs chapter detection again, and the row stays, so the
# precondition goes green over a layer nobody audited. Measured: Ripley's Scroll
# (0e0dd128) kept a row from 10 May while a reprocess on 21 May rewrote its chapters
# as the opening words of wrapped sentences; e4a3116f's row counts 1,374 chunks and
# 217 chapter titles, and the reprocess after it stored 1,080 chunks under 4 titles.
#
# It compares the latest parse_done_clean row's time with the latest enriched_at of
# the text chunks (figure rows without a chunk_index left out), and lists the jobs
# that wrote those chunks. enriched_at is stored as an ISO time or, in one book, as
# epoch seconds, and both are read as times. The row is stale when the chunks are
# more than 60 minutes newer: the one positive gap under an hour in the corpus is 6.5
# minutes (a row whose counts match its stored 189 chunks), and the next is 6 h 50.
# A stale row need not mean different chapters (28 stale rows still match their
# counts); it means the audit never read the stored layer.
#
#   PARSE_ROW_FRESH     no chunk was written more than an hour after the row
#   PARSE_ROW_STALE     chunks were written after the row: the stored layer is unaudited
#   PARSE_ROW_UNJUDGED  no chunk carries enriched_at, so nothing can be compared; the
#                       candidates like this are dataset imports, and their re-cut tool
#                       writes no enriched_at either
#
# The line is the verdict, not the exit code. Fails closed: a missing argument, no
# clean row, an unreadable row time, an unreadable database, no text chunks or any
# other error prints a PARSE_ROW_FAIL line and exits 2.
#
# Usage: parse-fresh.sh <document_id>
set -uo pipefail
D="${1:-}"
[ -n "$D" ] || { echo "PARSE_ROW_FAIL usage: parse-fresh.sh <document_id>"; exit 2; }
[[ "$D" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] || { echo "PARSE_ROW_FAIL bad_document_id=$D"; exit 2; }
PROGRESS="${CLAUDE_PROJECT_DIR:-/opt/scrapalot}/.claude/postprocess/progress.txt"
[ -r "$PROGRESS" ] || { echo "PARSE_ROW_FAIL progress_unreadable=$PROGRESS"; exit 2; }
# The id and status fields are trimmed the way next-book.py reads them.
ROW=$(awk -F'|' -v d="$D" '{ id = $4; gsub(/^[ \t]+|[ \t]+$/, "", id); split($6, s, ";"); gsub(/^[ \t]+|[ \t]+$/, "", s[1]); if (id == d && index(s[1], "parse_done_clean") == 1) t = $1 } END { print t }' "$PROGRESS")
[ -n "$ROW" ] || { echo "PARSE_ROW_FAIL no_parse_done_clean_row"; exit 2; }
PG="${PG_CONTAINER:-pgvector}"
U=$(docker exec "$PG" printenv POSTGRES_USER 2>/dev/null)
[ -n "$U" ] || { echo "PARSE_ROW_FAIL pg_user_unreadable"; exit 2; }
ERR=$(mktemp); trap 'rm -f "$ERR"' EXIT
WRITTEN=$(docker exec "$PG" psql -U "$U" -d scrapalot -At -F'|' -v ON_ERROR_STOP=1 -c "SELECT count(*), count(*) FILTER (WHERE cmetadata ? 'enriched_at'), coalesce(to_char(max(CASE WHEN cmetadata->>'enriched_at' ~ '^[0-9]+([.][0-9]+)?$' THEN to_timestamp((cmetadata->>'enriched_at')::double precision) WHEN cmetadata->>'enriched_at' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}' THEN (cmetadata->>'enriched_at')::timestamptz END) AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"+00:00\"'), ''), coalesce(string_agg(DISTINCT cmetadata->>'job_id', ','), '') FROM langchain_pg_embedding WHERE cmetadata->>'document_id' = '$D' AND NOT (coalesce((cmetadata->>'is_multimodal')::boolean, false) AND cmetadata->>'chunk_index' IS NULL);" 2>"$ERR")
rc=$?
{ [ $rc -eq 0 ] && [ ! -s "$ERR" ]; } || { echo "PARSE_ROW_FAIL query_error rc=$rc: $(head -c 160 "$ERR" | tr '\n' ' ')"; exit 2; }
python3 - "$ROW" "$WRITTEN" <<'PY'
import sys
from datetime import datetime, timedelta


def fail(reason):
    print(f"PARSE_ROW_FAIL {reason}")
    raise SystemExit(2)


try:
    row_text, written = sys.argv[1].strip(), sys.argv[2].strip()
    chunks, enriched, latest, jobs = written.split("|", 3)
    if int(chunks) == 0:
        fail("no_text_chunks")
    try:
        row = datetime.fromisoformat(row_text.replace("Z", "+00:00"))
    except ValueError:
        fail(f"row_time_unreadable={row_text!r}")
    if row.tzinfo is None:
        fail(f"row_time_without_offset={row_text!r}")
    print(f"PARSE_ROW row={row_text} chunks={chunks} with_enriched_at={enriched} chunks_written={latest or '-'} jobs={jobs or '-'}")
    if not latest:
        print("PARSE_ROW_UNJUDGED no chunk carries enriched_at")
        raise SystemExit(0)
    gap = datetime.fromisoformat(latest) - row
    if gap > timedelta(minutes=60):
        print(f"PARSE_ROW_STALE the chunks were written {gap} after the clean row: the stored chapter layer was never audited")
        raise SystemExit(1)
    print("PARSE_ROW_FRESH")
except SystemExit:
    raise
except Exception as error:
    fail(f"unexpected {type(error).__name__}: {error}")
PY
