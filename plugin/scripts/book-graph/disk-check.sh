#!/usr/bin/env bash
# disk-check.sh — exit 0 when there is room to build a graph, 2 when a disk this
# work writes to is nearly full, 1 when it cannot be measured.
#
# Two filesystems can wedge a graph pass, so both are measured:
#
#   * the volume Neo4j's /data sits on — asked INSIDE the container, which is
#     the database's own view of the disk it writes to and the only view that
#     needs no root on the host (the docker volume directory is 0700, so `df`
#     on it from the scrapalot user answers "Permission denied"). On this host
#     that same volume carries the pgvector data directory and every other
#     docker volume, so the one measurement covers the whole store.
#   * the filesystem carrying CLAUDE_PROJECT_DIR — the checkout, the worktree a
#     fix is built in, the ledgers, this loop's own logs.
#
# The limit is 88 and not 90 because a pass keeps writing between two checks,
# and Neo4j meeting a full volume does not fail cleanly: it stops accepting
# writes and the store can need recovery. DISK_STOP_PCT overrides it.
set -uo pipefail

limit="${DISK_STOP_PCT:-88}"
project="${CLAUDE_PROJECT_DIR:-/opt/scrapalot}"

worst=-1
parts=()

# add <label> <df -P output> — `-P` is what guarantees one line per filesystem.
add() {
  local label="$1" last pct avail mount
  last="$(printf '%s\n' "$2" | tail -1)"
  pct="$(awk '{print $5}' <<<"$last" | tr -dc '0-9')"
  avail="$(awk '{print $4}' <<<"$last" | tr -dc '0-9')"
  mount="$(awk '{print $6}' <<<"$last")"
  [ -n "$pct" ] && [ -n "$avail" ] || return 1
  parts+=("$label ${pct}% used, $((avail / 1024 / 1024))G free (${mount:-?})")
  [ "$pct" -gt "$worst" ] && worst="$pct"
  return 0
}

if ! add "neo4j /data" "$(docker exec neo4j df -P /data 2>/dev/null)"; then
  # Without the container, find the mount point holding docker's root by
  # matching the mount table — that needs no access to the volume itself.
  dockerroot="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null)"
  [ -n "$dockerroot" ] || dockerroot=/var/lib/docker
  add "docker root" "$(df -P | awk -v p="$dockerroot/" '
    NR > 1 { t = $6; s = (t == "/") ? t : t "/"
             if (index(p, s) == 1 && length(t) >= n) { n = length(t); best = $0 } }
    END { print best }')" || true
fi

add "project" "$(df -P "$project" 2>/dev/null)" || true

if [ "${#parts[@]}" -eq 0 ]; then
  echo "disk: could not measure — neither the neo4j container nor df answered" >&2
  exit 1
fi

msg="$(printf '%s; ' "${parts[@]}")"; msg="${msg%; }"
if [ "$worst" -ge "$limit" ]; then
  echo "disk FULL at ${worst}% (limit ${limit}%) — $msg"
  exit 2
fi
echo "disk ok at ${worst}% (limit ${limit}%) — $msg"
exit 0
