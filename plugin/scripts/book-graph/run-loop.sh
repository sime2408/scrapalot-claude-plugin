#!/usr/bin/env bash
# run-loop.sh — cron entrypoint for the unattended book-graph sweep.
#
# One pass = one Claude session that audits and builds the graph of ONE book and
# then, while the hour stays cheap and the account has money, moves to the next.
# The session does that itself (see the "Unattended mode" section of
# /scrapalot:book-graph); this script only decides whether a pass may start, and
# kills it before the next peak window opens.
#
#   cheap hour?  -> cheap-now.sh      (DeepSeek bills peak at double)
#   room?        -> disk-check.sh     (a full volume takes Neo4j and pgvector down together)
#   money?       -> balance-check.sh  (402 stops the sweep and tells the owner)
#   a book?      -> next-book.py      (parse-clean, tier 2, no graph row yet)
#
# The disk is the one gate that also runs DURING a pass: cron cannot see a
# volume that fills between two starts, and a book finished onto a wedged
# database is worth nothing.
#
# Install with install-cron.sh. Safe to run by hand; FORCE=1 ignores a stop
# marker, SCRAPALOT_ALLOW_PEAK=1 ignores the hour.
set -uo pipefail

export HOME="${HOME:-/home/scrapalot}"
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"
export CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/opt/scrapalot}"

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPTS/../.." && pwd)}"
LOOP_DIR="$CLAUDE_PROJECT_DIR/.claude/book-graph"
LOG="$LOOP_DIR/loop.log"
LOCK="$LOOP_DIR/.loop.lock"
STOPPED_BALANCE="$LOOP_DIR/STOPPED-no-balance"
STOPPED_DISK="$LOOP_DIR/STOPPED-disk-full"
mkdir -p "$LOOP_DIR"

# The goal is read at the start of every iteration, so it has to exist.
[ -f "$LOOP_DIR/GOAL.md" ] || cp "$SCRIPTS/GOAL.template.md" "$LOOP_DIR/GOAL.md"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { printf '%s %s\n' "$(ts)" "$*" >> "$LOG"; }

exec 9>"$LOCK" || { echo "cannot open lock $LOCK"; exit 1; }
if ! flock -n 9; then
  log "SKIP — a pass is already running"
  exit 0
fi

# A spent account fails every call; a nearly full volume takes the database with
# it. Starting again into either wall only fills the log, so the marker survives
# until the owner clears it (or FORCE=1).
for marker in "$STOPPED_BALANCE" "$STOPPED_DISK"; do
  if [ -f "$marker" ] && [ "${FORCE:-0}" != "1" ]; then
    log "SKIP — stopped: $(head -1 "$marker" 2>/dev/null). Clear $marker to resume."
    exit 0
  fi
done

if [ "${SCRAPALOT_ALLOW_PEAK:-0}" != "1" ]; then
  if ! hour_msg="$(bash "$SCRIPTS/cheap-now.sh")"; then
    log "SKIP — $hour_msg"
    exit 0
  fi
else
  hour_msg="peak override"
fi

# Free before cheap: this gate costs nothing and guards more than money.
disk_msg="$(bash "$SCRIPTS/disk-check.sh" 2>&1)"; disk_rc=$?
if [ "$disk_rc" -eq 2 ]; then
  printf '%s %s\n' "$(ts)" "$disk_msg" > "$STOPPED_DISK"
  log "STOP — $disk_msg"
  bash "$SCRIPTS/notify-owner.sh" \
    "Disk nearly full — book-graph sweep stopped" \
    "The unattended graph sweep did not start a pass at $(ts): $disk_msg. Neo4j and the pgvector data directory share that volume, so a graph build writes into a disk that is about to fill, and Neo4j meeting a full volume stops accepting writes — its store can then need recovery. Free space (docker image prune, old backups, .claude/postprocess dumps), delete $STOPPED_DISK, and the next cheap hour resumes. The loop's own state is in $LOOP_DIR/STATE.md."
  exit 0
fi
if [ "$disk_rc" -ne 0 ]; then
  log "SKIP — $disk_msg"
  exit 0
fi

balance_msg="$(bash "$SCRIPTS/balance-check.sh" 2>&1)"; balance_rc=$?
if [ "$balance_rc" -eq 2 ]; then
  printf '%s no balance\n' "$(ts)" > "$STOPPED_BALANCE"
  log "STOP — $balance_msg"
  bash "$SCRIPTS/notify-owner.sh" \
    "DeepSeek balance empty — book-graph sweep stopped" \
    "The unattended graph sweep stopped at $(ts): the DeepSeek account returns 402 Insufficient Balance, so every call fails. Top the account up, delete $STOPPED_BALANCE, and the next cheap hour picks the sweep up where it left off. Progress so far is in .claude/postprocess/progress.txt; the loop's own state is in $LOOP_DIR/STATE.md."
  exit 0
fi
if [ "$balance_rc" -ne 0 ]; then
  log "SKIP — $balance_msg"
  exit 0
fi

pick_err="$(mktemp)"
book="$(python3 "$SCRIPTS/next-book.py" 2>"$pick_err")"; pick_rc=$?
cat "$pick_err" >> "$LOG"
if [ "$pick_rc" -eq 3 ]; then
  log "DONE — no candidate books left"
  # The picker skips books that fail a Phase 0 check, so "nothing left" can still leave books without a graph.
  bash "$SCRIPTS/notify-owner.sh" "Book-graph sweep finished" \
    "No parse-clean book in a tier-2 collection is left to pick at $(ts). The picker said: $(tr '\n' ' ' < "$pick_err")"
  rm -f "$pick_err"
  exit 0
fi
rm -f "$pick_err"
[ "$pick_rc" -eq 0 ] && [ -n "$book" ] || { log "SKIP — could not pick a book (rc=$pick_rc)"; exit 0; }

doc_id="${book%%|*}"
rest="${book#*|}"
title="${rest%%|*}"

# Never run into a peak window: stop the pass a minute before the next one
# opens. A build already in flight is not killed by the hour, but a session that
# would START new work in peak is.
budget=$(python3 - <<'PY'
from datetime import UTC, datetime, timedelta
now = datetime.now(UTC)
peak = ((1, 4), (6, 10))
def is_peak(dt):
    return dt.weekday() < 5 and any(s <= dt.hour < e for s, e in peak)
edge = now
for _ in range(24 * 60):
    edge += timedelta(minutes=1)
    if is_peak(edge):
        break
print(max(int((edge - now).total_seconds()) - 60, 300))
PY
)

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "dry run: would start /scrapalot:book-graph $doc_id ($title) — $hour_msg, $disk_msg, budget ${budget}s"
  log "DRY RUN — would start $doc_id $title (budget ${budget}s)"
  exit 0
fi

export SCRAPALOT_BOOK_GRAPH_LOOP=1
# `claude -p` waits at most 600 s for background tasks and then terminates the
# session. This loop is built on background work — sub-agents, corpus scans, a
# review that takes minutes — so that ceiling cut pass 1 off mid-measurement
# ("Background tasks still running after 600s; terminating", 2026-09-12). The
# budget below is the real bound; the ceiling only truncated the thinking.
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0
log "=== pass start ($hour_msg; $disk_msg; budget ${budget}s) — $doc_id $title"

cd "$CLAUDE_PROJECT_DIR" || exit 1
echo "----- claude run $(ts) -----" >> "$LOG"
timeout --signal=INT "${budget}s" claude -p "/scrapalot:book-graph $doc_id" \
  --allowedTools "Bash,Read,Edit,Write,Grep,Glob,Task,Agent" \
  --output-format text >> "$LOG" 2>&1 9>&- &
run_pid=$!

# The gates above ran once. The disk is the one that turns against us mid-pass —
# entity extraction writes to Neo4j and pgvector for as long as the book lasts —
# so it is watched while the pass runs and the pass is interrupted the moment it
# crosses. The owner is told BEFORE the kill, so a failure to interrupt cleanly
# still leaves them informed. INT first: the session gets to write STATE.md and
# park its ledger.
(
  # Drop the lock fd: a `sleep` in here outlives the kill below, and an
  # inherited fd 9 would hold the flock after this pass is over, so the next
  # cron hour would report "a pass is already running" over nothing.
  exec 9>&-
  while kill -0 "$run_pid" 2>/dev/null; do
    sleep "${DISK_WATCH_SECONDS:-180}"
    kill -0 "$run_pid" 2>/dev/null || break
    watch_msg="$(bash "$SCRIPTS/disk-check.sh" 2>&1)"; watch_rc=$?
    [ "$watch_rc" -eq 2 ] || continue
    printf '%s %s (mid-pass, on %s)\n' "$(ts)" "$watch_msg" "$title" > "$STOPPED_DISK"
    log "STOP — $watch_msg — interrupting the pass on $title"
    bash "$SCRIPTS/notify-owner.sh" \
      "Disk nearly full — book-graph sweep interrupted mid-pass" \
      "The graph sweep was building $title ($doc_id) at $(ts) when the disk crossed the limit: $watch_msg. The pass was interrupted rather than finished — Neo4j and pgvector share that volume and a full one stops accepting writes, which can leave the store needing recovery. The book's ledger is in .claude/gates/, the loop's state in $LOOP_DIR/STATE.md. Free space, delete $STOPPED_DISK, and the next cheap hour resumes from that book."
    pkill -INT -P "$run_pid" 2>/dev/null
    kill -INT "$run_pid" 2>/dev/null
    sleep 30
    if kill -0 "$run_pid" 2>/dev/null; then
      pkill -TERM -P "$run_pid" 2>/dev/null
      kill -TERM "$run_pid" 2>/dev/null
    fi
    break
  done
) &
watch_pid=$!

wait "$run_pid"; run_rc=$?
kill "$watch_pid" 2>/dev/null
echo "----- claude exit $run_rc -----" >> "$LOG"

if tail -400 "$LOG" | grep -q "Insufficient Balance"; then
  printf '%s no balance (seen mid-pass)\n' "$(ts)" > "$STOPPED_BALANCE"
  log "STOP — the account ran out during the pass"
  bash "$SCRIPTS/notify-owner.sh" \
    "DeepSeek balance ran out mid-pass — book-graph sweep stopped" \
    "The graph sweep hit 402 Insufficient Balance while working on $title ($doc_id) at $(ts). Top up, delete $STOPPED_BALANCE, and the next cheap hour resumes."
fi

log "=== pass end ==="
