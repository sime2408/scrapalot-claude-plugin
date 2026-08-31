#!/usr/bin/env bash
# activity-gate.sh — decide whether it is SAFE for the autonomous DevOps loop to
# act. The loop must wait for the right time: act ONLY when no end-user is using
# the app AND the operator is not doing direct-API / dev work.
#
# FAIL-SAFE: if any signal says active, or a probe errors, we treat the system as
# ACTIVE and hold off.
#
# Exit codes:
#   0  -> IDLE       — safe to act
#   10 -> ACTIVE     — hold off
#   20 -> INDETERM   — could not determine; treated as ACTIVE (fail-safe)
#
# Two tiers of signal:
#
#   END-USER (always checked) — web + Android app users. They hold a STOMP
#   WebSocket open for the whole session, so live STOMP connections are the
#   real-time presence signal. Corroborated by workspace_chat_presence and net
#   logins. Client type (web vs android vs api) is classified from the per-login
#   `user_agent` stored in Redis DB 1 for reporting.
#
#   DEV / PARALLEL (checked only when GATE_CHECK_DEV=1, i.e. the pre-launch gate
#   in run-headless.sh) — the operator working directly via the API / Claude Code,
#   another agent session, an in-flight CI deploy, or a dirty working tree. We do
#   NOT fix during development: those errors are work-in-progress, not defects.
#   Direct-API / scp-key / curl traffic does NOT open a STOMP socket, so it never
#   trips the end-user tier — this dev tier is how we catch it.
#
# Tunables (env): IDLE_WINDOW_MIN (15), REDIS_FRESH_HOURS (6), GATE_CHECK_DEV (0)

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IDLE_WINDOW_MIN="${IDLE_WINDOW_MIN:-15}"
REDIS_FRESH_HOURS="${REDIS_FRESH_HOURS:-6}"
GATE_CHECK_DEV="${GATE_CHECK_DEV:-0}"
SINCE="${IDLE_WINDOW_MIN}m"
VERBOSE="${ACTIVITY_GATE_VERBOSE:-1}"

log() { [ "$VERBOSE" = "1" ] && printf '[activity-gate] %s\n' "$*" >&2; }
dlogs() { docker logs --since "$SINCE" "$1" 2>&1 || true; }
ccount() { grep -cE "$1" || true; }

reasons=()
indeterminate=0

have_pg=0; docker ps --format '{{.Names}}' | grep -q '^pgvector$' && have_pg=1
have_redis=0; docker ps --format '{{.Names}}' | grep -q '^redis$' && have_redis=1

# --- classify active sessions from Redis DB 1 user_agent (reporting) --------
web=0; android=0; api=0; imp=0; unknown=0
if [ "$have_redis" = 1 ]; then
  fresh_cutoff_ms=$(( ( $(date +%s) - REDIS_FRESH_HOURS*3600 ) * 1000 ))
  # redis-cli runs INSIDE the container using its own $REDIS_PASSWORD env — we
  # never handle the secret ourselves. -a warns on stderr, so swallow it.
  classified="$(docker exec redis sh -c '
    RC="redis-cli ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} -n 1"
    $RC --scan --pattern "scrapalot:auth:refresh:*" 2>/dev/null | while read -r k; do
      ua=$($RC HGET "$k" user_agent 2>/dev/null)
      lu=$($RC HGET "$k" last_used_at 2>/dev/null)
      printf "%s\t%s\n" "${lu:-0}" "$ua"
    done' 2>/dev/null || true)"
  if [ -n "$classified" ]; then
    while IFS=$'\t' read -r lu ua; do
      [ -z "${lu:-}" ] && continue
      # keep only sessions used within the freshness window
      [ "${lu%%.*}" -lt "$fresh_cutoff_ms" ] 2>/dev/null && continue
      case "$ua" in
        impersonation-by-*) imp=$((imp+1)) ;;
        *"; wv)"*|*Android*wv*) android=$((android+1)) ;;
        curl/*|*python-httpx*|*python-requests*|Go-http-client*|PostmanRuntime*|*okhttp*|*axios*|Java/*|*Claude*|unknown) api=$((api+1)) ;;
        *Mozilla/5.0*) web=$((web+1)) ;;
        *) unknown=$((unknown+1)) ;;
      esac
    done <<< "$classified"
  fi
else
  indeterminate=1; log "redis not found — cannot classify sessions"
fi

# --- END-USER tier: real-time presence -------------------------------------
chat_logs="$(dlogs scrapalot-chat)"
stomp_conn=$(printf '%s' "$chat_logs" | ccount 'STOMP client .* (WebSocket connected|authenticated as user)')
stomp_disc=$(printf '%s' "$chat_logs" | ccount 'STOMP client .* (disconnected|WebSocket disconnected)')
stomp_net=$(( stomp_conn - stomp_disc ))

presence_online="?"
if [ "$have_pg" = 1 ]; then
  presence_online=$(docker exec pgvector psql -U scrapalot -d scrapalot_backend -tAc \
    "SELECT count(*) FROM scrapalot.workspace_chat_presence WHERE is_online = true;" 2>/dev/null | tr -d '[:space:]')
  [[ "$presence_online" =~ ^[0-9]+$ ]] || { presence_online="?"; indeterminate=1; }
else
  indeterminate=1
fi

be_logs="$(dlogs scrapalot-backend)"
logins=$(printf '%s' "$be_logs" | ccount 'logged in:|Login successful|OAuth login successful')
logouts=$(printf '%s' "$be_logs" | ccount 'Logout.*revoked|revoked all families')
login_net=$(( logins - logouts ))

[ "$stomp_net" -gt 0 ] && reasons+=("live STOMP clients net=$stomp_net (web/android)")
{ [ "$presence_online" != "?" ] && [ "$presence_online" -gt 0 ]; } && reasons+=("workspace presence online=$presence_online")
[ "$login_net" -gt 0 ] && reasons+=("net logins=$login_net")
[ "$api" -gt 0 ] && reasons+=("$api active API/dev session(s) in Redis (fresh<${REDIS_FRESH_HOURS}h)")

# --- DEV / PARALLEL tier (pre-launch only) ---------------------------------
dev_summary="(not checked)"
if [ "$GATE_CHECK_DEV" = "1" ]; then
  ps_json="$(bash "$HERE/parallel-sessions.sh" "${SELF_PID:-0}" 2>/dev/null || echo '{}')"
  busy=$(printf '%s' "$ps_json" | jq -r '.busy_sessions // 0')
  deploy=$(printf '%s' "$ps_json" | jq -r '.deploy_in_flight // false')
  dirty=$(printf '%s' "$ps_json" | jq -r '(.dirty_repos // []) | length')
  dev_summary="busy_claude=$busy deploy=$deploy dirty_repos=$dirty"
  [ "${busy:-0}" -gt 0 ] && reasons+=("$busy other Claude session(s) busy — operator/agent working")
  [ "$deploy" = "true" ] && reasons+=("CI deploy in flight")
  [ "${dirty:-0}" -gt 0 ] && reasons+=("$dirty subproject working tree(s) dirty — work in progress")
fi

# --- decide ----------------------------------------------------------------
log "window=$SINCE classify[web=$web android=$android api=$api imp=$imp unk=$unknown] presence=$presence_online stomp_net=$stomp_net login_net=$login_net dev[$dev_summary] indet=$indeterminate"

if [ "${#reasons[@]}" -gt 0 ]; then
  log "ACTIVE — $(IFS='; '; echo "${reasons[*]}")"
  echo "ACTIVE"; exit 10
fi
if [ "$indeterminate" = "1" ]; then
  log "INDETERMINATE — treating as ACTIVE (fail-safe)"
  echo "INDETERMINATE"; exit 20
fi
log "IDLE — no end-users, no dev activity; safe to act"
echo "IDLE"; exit 0
