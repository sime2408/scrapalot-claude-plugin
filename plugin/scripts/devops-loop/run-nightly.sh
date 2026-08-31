#!/usr/bin/env bash
# scrapalot-devops-loop.sh — cron entrypoint for the autonomous DevOps fix loop.
#
# Scheduled ONCE DAILY at 23:00 UTC. There is no activity gate any more: the run
# reviews the whole day's logs regardless of whether users or the operator were
# active. The nightly slot IS the safety window.
#
#   1. error-scan.sh     — only proceed when there are NEW error signatures
#                          (scans the full day: SCAN_WINDOW_MIN=1440).
#   2. otherwise          -> headless `claude -p "/scrapalot:devops-loop"`.
#
# Exports SCRAPALOT_DEVOPS_LOOP=1 so the PreToolUse guardrail hook switches on
# (blocks push-to-main, force-push, gh pr merge, destructive ops). Fixes ship
# only as branch + PR — a human merges.
#
# Install via the cron line printed by install-cron.sh. Safe to run by hand.

set -uo pipefail

export HOME="${HOME:-/home/scrapalot}"
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

# State lives in the project; the scripts ship with the plugin and are replaced
# on every plugin update, which is why the two are not the same directory.
export CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/opt/scrapalot}"
LOOP_DIR="$CLAUDE_PROJECT_DIR/.claude/devops-loop"
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPTS/../.." && pwd)}"
mkdir -p "$LOOP_DIR"
LOG="$LOOP_DIR/loop.log"
LOCK="$LOOP_DIR/.loop.lock"

# Loop mode ON — arms the guardrail hook for this process tree.
export SCRAPALOT_DEVOPS_LOOP=1
# Tunables (override in the environment / crontab if desired).
# SCAN_WINDOW_MIN=1440 -> review the whole day's logs on the nightly run.
export SCAN_WINDOW_MIN="${SCAN_WINDOW_MIN:-1440}"
CLAUDE_MODEL="${CLAUDE_MODEL:-}"

# Prune isolated clones left by interrupted runs.
bash "$SCRIPTS/cleanup-work.sh" --prune >/dev/null 2>&1 || true

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { printf '%s %s\n' "$(ts)" "$*" >> "$LOG"; }

# Single-flight: never run two loop passes at once (one-run-per-system).
exec 9>"$LOCK" || { echo "cannot open lock $LOCK"; exit 1; }
if ! flock -n 9; then
  log "SKIP — another loop pass is already running"
  exit 0
fi

log "=== loop start (nightly, scan_window=${SCAN_WINDOW_MIN}m) ==="

# 1. error scan --------------------------------------------------------------
scan_json="$(bash "$SCRIPTS/error-scan.sh" 2>>"$LOG")"
count="$(printf '%s' "$scan_json" | jq 'length' 2>/dev/null || echo 0)"
if [ "${count:-0}" -eq 0 ]; then
  log "NO-OP — no new error signatures. Clean run."
  log "=== loop end ==="
  exit 0
fi
log "FOUND $count new error signature(s) — invoking Claude orchestrator."

# 2. headless orchestrator ---------------------------------------------------
# allowedTools auto-approves the loop's tools; the PreToolUse guardrail hook
# still runs and blocks the dangerous subset. (No --bare: we WANT CLAUDE.md,
# the /scrapalot:devops-loop command, the agents, and the hooks loaded.)
model_arg=()
[ -n "$CLAUDE_MODEL" ] && model_arg=(--model "$CLAUDE_MODEL")

cd /opt/scrapalot || exit 1
{
  echo "----- claude run $(ts) -----"
  claude -p "/scrapalot:devops-loop" \
    "${model_arg[@]}" \
    --allowedTools "Bash,Read,Edit,Grep,Glob,Task" \
    --output-format text
  echo "----- claude exit $? -----"
} >> "$LOG" 2>&1

log "=== loop end ==="
