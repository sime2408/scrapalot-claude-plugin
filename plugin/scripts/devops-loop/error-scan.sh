#!/usr/bin/env bash
# error-scan.sh — harvest application errors from all Scrapalot containers,
# collapse them into stable signatures, drop the ones already handled, and
# print the NEW ones as a JSON array on stdout.
#
# This is the loop's "discovery" step. The orchestrator (/scrapalot-devops-loop)
# reads this JSON, then deep-investigates each NEW signature.
#
# Loop-memory:
#   seen-errors.jsonl  (one JSON obj per line: {"signature","status","ts","note"})
#   A signature listed there (any status) is considered handled and is filtered
#   out of the output so the loop never re-fixes the same thing. The orchestrator
#   appends to it via record-error.sh.
#
# Output (stdout): JSON array, e.g.
#   [{"signature":"ab12..","source":"scrapalot-chat","count":4,"sample":"..."}]
#   Empty array [] means "nothing new" — the loop then no-ops (a clean run).
#
# Tunables (env): SCAN_WINDOW_MIN (default 60)
#
# Read-only against the system; only reads the local seen-errors ledger.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# State lives in the project, not next to this script: the script ships with the
# plugin and is replaced on every update, so deriving the ledger from its own
# location silently pointed at an empty directory once the bundle moved.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/opt/scrapalot}"
LOOP_DIR="$PROJECT_DIR/.claude/devops-loop"
SEEN_FILE="${SEEN_FILE:-$LOOP_DIR/seen-errors.jsonl}"
SCAN_WINDOW_MIN="${SCAN_WINDOW_MIN:-60}"
SINCE="${SCAN_WINDOW_MIN}m"

dlogs() { docker logs --since "$SINCE" "$1" 2>&1 || true; }

# Normalize a log line into a structural skeleton so cosmetic differences
# (timestamps, ids, line numbers, ports) collapse to ONE signature.
normalize() {
  sed -E \
    -e 's/\x1b\[[0-9;]*m//g' \
    -e 's/[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9:.,]+Z?//g' \
    -e 's/\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b/<uuid>/g' \
    -e 's/0x[0-9a-fA-F]+/<hex>/g' \
    -e 's/:[0-9]+\)/:<n>)/g' \
    -e 's/\b[0-9]+\b/<n>/g' \
    -e 's/[[:space:]]+/ /g' \
    -e 's/^ +//; s/ +$//'
}

declare -A CNT SAMPLE SRC
ingest() {
  local source="$1" line norm sig
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    norm="$(printf '%s' "$line" | normalize)"
    [ -z "$norm" ] && continue
    sig="$(printf '%s|%s' "$source" "$norm" | sha1sum | cut -c1-16)"
    CNT["$sig"]=$(( ${CNT["$sig"]:-0} + 1 ))
    if [ -z "${SAMPLE[$sig]:-}" ]; then
      # trim sample to a sane length
      SAMPLE["$sig"]="$(printf '%s' "$line" | sed -E 's/\x1b\[[0-9;]*m//g' | cut -c1-300)"
      SRC["$sig"]="$source"
    fi
  done
}

# --- harvest per container with source-appropriate patterns ----------------

# Python AI + Celery workers (same image). gRPC handlers + tracebacks.
# NOTE: feed ingest via process substitution, NOT a pipe — a piped `| ingest`
# runs the function in a subshell and the harvested arrays are lost.
#
# We capture only the HEAD of each error (the log-level line or the top-level
# exception), never individual stack frames — one traceback = one signature.
# DROP_FRAMES strips continuation lines (`at ...`, `File "..."`, `...`).
DROP_FRAMES='^[[:space:]]*(at [A-Za-z]|File "|\.\.\.|Caused by:.*\$)'

# Python AI + Celery workers: bracketed log-level + gRPC/service heads.
# Match the LEVEL FIELD `[ERROR ]`, not a bare "ERROR" substring (which appears
# inside DEBUG request bodies and produces false positives).
PY_PAT='\[(ERROR|CRITICAL)|Error in .*Service|gRPC .* failed|^[A-Za-z][A-Za-z0-9_.]*(Error|Exception): '
for c in scrapalot-chat scrapalot-workers scrapalot-workers-graph; do
  docker ps --format '{{.Names}}' | grep -q "^${c}$" || continue
  ingest "$c" < <(dlogs "$c" | grep -aE "$PY_PAT" | grep -avE "$DROP_FRAMES")
done

# Kotlin backend — ERROR log lines + top-level exception type lines only.
if docker ps --format '{{.Names}}' | grep -q '^scrapalot-backend$'; then
  ingest scrapalot-backend \
    < <(dlogs scrapalot-backend | grep -aE '\[(ERROR|CRITICAL)|^[A-Za-z][A-Za-z0-9_.]*Exception:|StatusRuntimeException' \
        | grep -avE "$DROP_FRAMES")
fi

# Gateway — 5xx, circuit-breaker fallbacks, gRPC deadlines (already head-only).
if docker ps --format '{{.Names}}' | grep -q '^scrapalot-gw$'; then
  ingest scrapalot-gw \
    < <(dlogs scrapalot-gw | grep -aE '<<<.* - 5[0-9][0-9] |fallback triggered|DEADLINE_EXCEEDED|UNAVAILABLE|CircuitBreaker')
fi

# --- load already-handled signatures --------------------------------------
declare -A SEEN
# A missing ledger is not an empty one. Reading it as "nothing handled yet"
# reports every known signature as new, which is how a loop re-opens PRs for
# errors it already marked wontfix.
if [ ! -f "$SEEN_FILE" ]; then
  echo "error-scan: seen-errors ledger not found at $SEEN_FILE" >&2
  echo "error-scan: refusing to report every signature as new; set CLAUDE_PROJECT_DIR or SEEN_FILE" >&2
  exit 2
fi
if [ -f "$SEEN_FILE" ]; then
  while IFS= read -r s; do
    [ -n "$s" ] && SEEN["$s"]=1
  done < <(grep -oE '"signature"[[:space:]]*:[[:space:]]*"[0-9a-f]+"' "$SEEN_FILE" \
             | grep -oE '[0-9a-f]{8,}' || true)
fi

# --- emit NEW signatures as JSON ------------------------------------------
first=1
printf '['
for sig in "${!CNT[@]}"; do
  [ -n "${SEEN[$sig]:-}" ] && continue
  [ "$first" = 1 ] && first=0 || printf ','
  jq -cn \
    --arg sig "$sig" \
    --arg source "${SRC[$sig]}" \
    --argjson count "${CNT[$sig]}" \
    --arg sample "${SAMPLE[$sig]}" \
    '{signature:$sig, source:$source, count:$count, sample:$sample}'
done
printf ']\n'
