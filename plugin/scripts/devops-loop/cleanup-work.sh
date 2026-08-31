#!/usr/bin/env bash
# cleanup-work.sh — remove an isolated clone created by prepare-clone.sh, and
# prune stale clones left by interrupted runs.
#
# Usage:
#   cleanup-work.sh <path>        # remove one clone (must live under work/)
#   cleanup-work.sh --prune       # remove all work/ clones older than PRUNE_HOURS (default 24)
#
# Refuses to delete anything outside the loop's work/ dir (safety).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_ROOT="$(cd "$HERE/.." && pwd)/work"
PRUNE_HOURS="${PRUNE_HOURS:-24}"

[ -d "$WORK_ROOT" ] || exit 0

if [ "${1:-}" = "--prune" ]; then
  find "$WORK_ROOT" -mindepth 1 -maxdepth 1 -type d -mmin "+$((PRUNE_HOURS*60))" \
    -exec rm -rf {} + 2>/dev/null || true
  echo "pruned clones older than ${PRUNE_HOURS}h"
  exit 0
fi

target="${1:?path required, or --prune}"
# resolve and confine to WORK_ROOT
case "$(readlink -f "$target")" in
  "$WORK_ROOT"/*) rm -rf "$target"; echo "removed $target" ;;
  *) echo "refusing to remove path outside $WORK_ROOT: $target" >&2; exit 2 ;;
esac
