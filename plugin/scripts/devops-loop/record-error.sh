#!/usr/bin/env bash
# record-error.sh — append a handled error signature to the loop memory so
# error-scan.sh stops surfacing it.
#
# Usage:
#   record-error.sh <signature> <status> "<note>"
#     status: pr_open | fixed | wontfix | escalated
#
# Example:
#   record-error.sh ab12cd34ef567890 pr_open "scrapalot-chat#123 — null guard in retriever"
#
# Idempotent-ish: it just appends; error-scan dedups by signature presence.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# State lives in the project, not next to this script: the script ships with the
# plugin and is replaced on every update, so deriving the ledger from its own
# location silently pointed at an empty directory once the bundle moved.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/opt/scrapalot}"
LOOP_DIR="$PROJECT_DIR/.claude/devops-loop"
SEEN_FILE="${SEEN_FILE:-$LOOP_DIR/seen-errors.jsonl}"

sig="${1:?signature required}"
status="${2:?status required (pr_open|fixed|wontfix|escalated)}"
note="${3:-}"
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

jq -cn \
  --arg signature "$sig" \
  --arg status "$status" \
  --arg ts "$ts" \
  --arg note "$note" \
  '{signature:$signature, status:$status, ts:$ts, note:$note}' >> "$SEEN_FILE"

echo "recorded $sig -> $status"
