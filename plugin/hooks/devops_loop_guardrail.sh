#!/usr/bin/env bash
# PreToolUse(Bash) hook for the autonomous DevOps fix loop.
#
# Enforces the loop's hard guardrails ONLY when the loop is running, detected via
# the env var SCRAPALOT_DEVOPS_LOOP=1 (exported by run-headless.sh). Outside the
# loop (normal interactive operator work) it is a silent no-op — it never gets in
# your way.
#
# In loop mode it DENIES (blocks) commands that would:
#   - push to main/master, force-push, or push ambiguously
#   - merge a PR (human-only decision)
#   - destroy data or containers (rm -rf, docker rm/stop/down, DROP/TRUNCATE/
#     mass DELETE, Neo4j DETACH DELETE, git reset --hard / clean -fd)
#   - mass document reprocess / heavy admin gRPC
#
# Block format: PreToolUse permissionDecision=deny (exit 0).
# Deliberately no `set -e` — failed pattern tests are normal control flow.

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0

# Only enforce inside the autonomous loop.
[ "${SCRAPALOT_DEVOPS_LOOP:-0}" = "1" ] || exit 0

deny() {
  jq -n --arg r "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: ("🚫 devops-loop guardrail: " + $r)
    }
  }'
  exit 0
}

# --- git push: branch + PR only -------------------------------------------
if printf '%s' "$cmd" | grep -qE '\bgit([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+push\b'; then
  # force-push in any form
  if printf '%s' "$cmd" | grep -qE '(--force\b|--force-with-lease\b|[[:space:]]-f\b|[[:space:]]\+[A-Za-z])'; then
    deny "force-push is not allowed; the loop uses normal feature-branch pushes only."
  fi
  # pushing main/master
  if printf '%s' "$cmd" | grep -qE '\b(main|master)\b'; then
    deny "pushing main/master is forbidden (auto-deploys to prod). Push the feature branch and open a PR."
  fi
  # ambiguous push without an explicit feature ref (could push the checked-out main)
  if ! printf '%s' "$cmd" | grep -qE 'push([[:space:]]+-u)?[[:space:]]+origin[[:space:]]+[A-Za-z0-9._/-]+'; then
    deny "ambiguous 'git push' — specify the feature branch explicitly: git push -u origin <branch>."
  fi
fi

# --- never merge a PR ------------------------------------------------------
if printf '%s' "$cmd" | grep -qE '\bgh[[:space:]]+pr[[:space:]]+merge\b'; then
  deny "merging is a human decision; the loop only opens PRs."
fi

# --- destructive filesystem / containers ----------------------------------
if printf '%s' "$cmd" | grep -qE '\brm[[:space:]]+(-[a-zA-Z]*r[a-zA-Z]*[[:space:]]+|-[a-zA-Z]*f[a-zA-Z]*[[:space:]]+).*'; then
  if printf '%s' "$cmd" | grep -qE '\brm[[:space:]]+-[a-zA-Z]*r'; then
    deny "recursive rm is blocked in loop mode."
  fi
fi
if printf '%s' "$cmd" | grep -qE '\bdocker[[:space:]]+(rm|stop|kill|restart)\b|\bdocker[[:space:]]+compose[[:space:]]+(down|rm|stop)\b|\bdocker[[:space:]]+update\b'; then
  deny "container lifecycle / docker update is blocked in loop mode."
fi

# --- destructive git -------------------------------------------------------
if printf '%s' "$cmd" | grep -qE '\bgit([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+(reset[[:space:]]+--hard|clean[[:space:]]+-[a-zA-Z]*f|push[[:space:]]+--mirror)'; then
  deny "destructive git (reset --hard / clean -f / push --mirror) is blocked in loop mode."
fi

# --- destructive DB / graph ------------------------------------------------
if printf '%s' "$cmd" | grep -qiE '\b(drop[[:space:]]+(table|database|schema|index)|truncate[[:space:]]+table|delete[[:space:]]+from)\b'; then
  deny "destructive SQL (DROP/TRUNCATE/DELETE FROM) is blocked — fix code, not data."
fi
if printf '%s' "$cmd" | grep -qiE 'detach[[:space:]]+delete'; then
  deny "Neo4j DETACH DELETE is blocked — never wipe graph data."
fi

# --- mass reprocess / heavy admin gRPC ------------------------------------
if printf '%s' "$cmd" | grep -qiE 'RecomputePageRank|RecomputeCooccurrenceWeights|ClassifyTypedRelationships|RecomputeCollectionFingerprints'; then
  deny "heavy admin gRPC recomputes are blocked in loop mode (collide with deploy window)."
fi
if printf '%s' "$cmd" | grep -qE 'send_task[^=]{1,40}scrapalot\.(reprocess_document|process_document|process_batch)'; then
  deny "document reprocess dispatch is out of scope for the fix loop."
fi

exit 0
