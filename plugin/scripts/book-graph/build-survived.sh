#!/usr/bin/env bash
# Did a dispatched graph build run to completion without a deploy killing it?
#
# A deploy restarts the worker containers, and a build killed that way reports
# nothing: no error, no failed task, a checkpoint left at entity_running. Measured
# twice: a build dispatched 18:53:06Z died in the 19:21 restart, and a rebuild
# dispatched 02:50:46Z died in the 03:11:38 restart.
#
# What shaped this check, each measured:
#   * StartedAt is a container's LAST start only: a restart 43 min after a build
#     finished made a StartedAt-vs-dispatch check go red over that finished build.
#     Restarts are read from the workers' own "<name>@<host> ready." log lines.
#   * Rotated logs hold restarts too (celery_worker_*.log.1-3 held 16 matching
#     lines; documents.log rotated three times in 7 days), so the glob is *.log*.
#   * An unreadable log is not "no restarts": every read must succeed or the check
#     aborts with BUILD_FAIL.
#   * A success line proves THIS build only when its task was received after the
#     dispatch and received exactly once; a second receipt is a broker redelivery.
#
# Survival = the sync row completed after the dispatch with entities; no worker
# became "ready." between the dispatch and completed_at; and one extract_entities
# task, received once after the dispatch, succeeded within 5 s of completed_at
# storing exactly the recorded entities.
#
# Usage: build-survived.sh <document_id> <dispatched_at, e.g. 2026-09-13T03:16:09Z>
set -uo pipefail
D="${1:?usage: build-survived.sh <document_id> <dispatched_at>}"
AT="${2:?usage: build-survived.sh <document_id> <dispatched_at>}"
WORKERS="${WORKERS_CONTAINER:-scrapalot-workers}"
GRAPH="${GRAPH_WORKER_CONTAINER:-scrapalot-workers-graph}"
PG="${PG_CONTAINER:-pgvector}"
[[ "$D" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] || { echo "BUILD_FAIL bad_document_id=$D"; exit 2; }
[[ "$AT" =~ ^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] || { echo "BUILD_FAIL dispatch_time_unreadable=$AT"; exit 2; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
# An unreadable sync row is a failure to measure, not an unfinished build.
ROW=$(docker exec "$PG" psql -U scrapalot -d scrapalot -At -F' ' -c "SELECT status, entities_extracted, to_char(completed_at AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') FROM graph_sync_status WHERE document_id='$D';" 2>"$TMP/perr")
rc=$?; { [ $rc -eq 0 ] && [ ! -s "$TMP/perr" ]; } || { echo "BUILD_FAIL sync_row_unreadable rc=$rc: $(head -c 120 "$TMP/perr" | tr '\n' ' ')"; exit 2; }
read -r ST EN DONE <<<"$ROW"
echo "graph_sync_status: ${ROW:-(no row)} | dispatched=$AT"
if [ "${ST:-}" != completed ] || ! [[ "${EN:-}" =~ ^[0-9]+$ ]] || [ "${EN:-0}" -eq 0 ] || ! [[ "${DONE:-}" > "$AT" ]]; then
  echo "BUILD_NOT_PROVEN — not completed with entities after the dispatch"; exit 1
fi
docker exec "$WORKERS" sh -c 'ls /app/data/logs/celery_worker_*.log* >/dev/null' 2>"$TMP/err" || { echo "BUILD_FAIL log_unreadable $WORKERS: $(head -c 120 "$TMP/err" | tr '\n' ' ')"; exit 2; }
# grep exits 1 for "no match" and 2 for an error; only 2 is a failure.
docker exec "$WORKERS" sh -c "grep -a -h -E '\] [A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+ ready\.|extract_entities\[[0-9a-f-]+\] (received|succeeded)' /app/data/logs/celery_worker_*.log*" > "$TMP/files" 2>"$TMP/err"
# docker exec also exits 1 on a daemon error, so a no-match rc of 1 counts only with empty stderr.
rc=$?; { [ $rc -eq 0 ] || { [ $rc -eq 1 ] && [ ! -s "$TMP/err" ]; }; } || { echo "BUILD_FAIL log_unreadable $WORKERS rc=$rc: $(head -c 120 "$TMP/err" | tr '\n' ' ')"; exit 2; }
# The whole log, not --since the dispatch: a first receipt before the dispatch must still count.
docker logs "$GRAPH" > "$TMP/graph_raw" 2>&1 || { echo "BUILD_FAIL log_unreadable $GRAPH: $(head -c 120 "$TMP/graph_raw" | tr '\n' ' ')"; exit 2; }
python3 - "$AT" "$DONE" "$EN" "$TMP/files" "$TMP/graph_raw" <<'PY'
import collections, datetime, re, sys
at, done, en, files, graph = sys.argv[1:6]
iso = lambda s: datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
logt = lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
t_at, t_done = iso(at), iso(done)
lines = open(files, encoding="utf-8", errors="replace").read().splitlines() + open(graph, encoding="utf-8", errors="replace").read().splitlines()
restarts, received, success = set(), collections.defaultdict(list), []
for line in lines:
    ts = re.search(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+:", line)
    if not ts:
        continue
    t = logt(ts.group(1))
    m = re.search(r"\] ([A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+) ready\.", line)
    if m and t_at < t < t_done:
        restarts.add(f"{m.group(1)} at {ts.group(1)}")
    m = re.search(r"extract_entities\[([0-9a-f-]+)\] received", line)
    if m and t.isoformat() not in received[m.group(1)]:
        received[m.group(1)].append(t.isoformat())
    m = re.search(r"extract_entities\[([0-9a-f-]+)\] succeeded.*entities_stored.: (\d+)", line)
    if m and m.group(2) == en and abs((t - t_done).total_seconds()) <= 5:
        success.append((m.group(1), ts.group(1)))
bound = []
for tid, when in success:
    receipts = sorted(set(received.get(tid, [])))
    if len(receipts) == 1 and datetime.datetime.fromisoformat(receipts[0]) > t_at:
        bound.append(f"task {tid} received once at {receipts[0]}, succeeded at {when} storing {en}")
    else:
        print(f"success of task {tid} at {when} is not bound to this dispatch: receipts={receipts}")
for r in sorted(restarts):
    print(f"RESTARTED_DURING_BUILD {r}")
print("success: " + bound[0] if bound else f"no success line bound to this dispatch within 5 s of {done} storing {en}")
ok = bool(bound) and not restarts
print("BUILD_SURVIVED" if ok else "BUILD_NOT_PROVEN")
sys.exit(0 if ok else 1)
PY
