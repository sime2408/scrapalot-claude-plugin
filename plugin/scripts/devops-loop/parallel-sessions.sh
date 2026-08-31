#!/usr/bin/env bash
# parallel-sessions.sh — report OTHER active work on the host so the loop does
# not step on anyone's toes: live Claude Code sessions, in-flight CI deploys, and
# dirty subproject working trees.
#
# Output (stdout): a JSON object:
#   {
#     "claude_sessions":[{"pid","name","cwd","status","updatedAt"}],
#     "busy_sessions": <int>,        # claude sessions with status=busy
#     "deploy_in_flight": <bool>,    # Runner.Worker / gradlew / docker build|compose
#     "dirty_repos":[{"repo","changes"}],
#     "any_dev_activity": <bool>     # busy_sessions>0 || deploy_in_flight || dirty_repos>0
#   }
#
# Self-exclusion: pass the PID to ignore (the loop's own claude) as $1, or set
# SELF_PID. The pre-launch gate in run-headless.sh runs BEFORE the loop's claude
# starts, so it needs no exclusion; the orchestrator should pass its own pid.
#
# Read-only.

set -uo pipefail

SELF_PID="${1:-${SELF_PID:-0}}"
SESS_DIR="${CLAUDE_SESS_DIR:-/home/scrapalot/.claude/sessions}"

# --- live Claude sessions from session lock files --------------------------
sessions_json='[]'
if [ -d "$SESS_DIR" ]; then
  sessions_json="$(
    for f in "$SESS_DIR"/*.json; do
      [ -e "$f" ] || continue
      jq -c --argjson self "$SELF_PID" '
        {pid: (.pid // (input_filename|gsub(".*/";"")|gsub("\\.json$";"")|tonumber? // 0)),
         name: (.name // ""),
         cwd: (.cwd // ""),
         status: (.status // "unknown"),
         updatedAt: (.updatedAt // "")}
        | select(.pid != $self)
      ' "$f" 2>/dev/null
    done | jq -sc '.'
  )"
  [ -z "$sessions_json" ] && sessions_json='[]'
fi
busy=$(printf '%s' "$sessions_json" | jq '[.[] | select(.status=="busy")] | length')

# --- in-flight CI deploy ---------------------------------------------------
deploy=false
if pgrep -af 'Runner.Worker|[g]radlew|docker[[:space:]]+build|docker[[:space:]]+compose|docker-compose' >/dev/null 2>&1; then
  deploy=true
fi

# --- dirty subproject working trees ----------------------------------------
dirty_json='[]'
for repo in scrapalot-chat scrapalot-backend scrapalot-ui scrapalot-gw; do
  d="/opt/scrapalot/$repo"
  [ -d "$d/.git" ] || continue
  n=$(git -C "$d" status --porcelain 2>/dev/null | grep -c . || true)
  if [ "${n:-0}" -gt 0 ]; then
    dirty_json="$(printf '%s' "$dirty_json" | jq -c --arg r "$repo" --argjson n "$n" '. + [{repo:$r, changes:$n}]')"
  fi
done

dirty_count=$(printf '%s' "$dirty_json" | jq 'length')
any=false
if [ "${busy:-0}" -gt 0 ] || [ "$deploy" = true ] || [ "${dirty_count:-0}" -gt 0 ]; then
  any=true
fi

jq -cn \
  --argjson sessions "$sessions_json" \
  --argjson busy "${busy:-0}" \
  --argjson deploy "$deploy" \
  --argjson dirty "$dirty_json" \
  --argjson any "$any" \
  '{claude_sessions:$sessions, busy_sessions:$busy, deploy_in_flight:$deploy, dirty_repos:$dirty, any_dev_activity:$any}'
