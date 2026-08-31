#!/usr/bin/env bash
# PreToolUse hook for Bash. Detects "bulk dispatch" or "loop-over-dispatch"
# patterns that violate the per-doc sequential rule of /scrapalot:postprocess-parse
# (PHASE 5 in ${CLAUDE_PLUGIN_ROOT}/agents/postprocess-parse.md).
#
# Does NOT block. Emits a system-message warning so the model gets reminded
# back to the spec mid-flight.
# NOTE: deliberately does NOT use `set -e` — the false branches of the
# pattern checks are normal control flow, not errors.

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0

violations=()

# Pattern 1: more than one Celery reprocess send_task call in same command.
# `grep -c` counts MATCHING LINES; `grep -oE | wc -l` counts OCCURRENCES.
n_send=$(printf '%s' "$cmd" \
  | grep -oE 'send_task[^=]{1,40}scrapalot\.(reprocess_document|process_document|process_batch)' \
  | wc -l)
if [ "${n_send:-0}" -gt 1 ]; then
  violations+=("bulk_dispatch: $n_send Celery reprocess send_task calls in one command")
fi

# Pattern 2: for/while loop wrapping a reprocess dispatch
if printf '%s' "$cmd" | grep -qE '(for[[:space:]]+\w+[[:space:]]+in|while[[:space:]]+read)' \
   && printf '%s' "$cmd" | grep -qE 'send_task.*(reprocess|process_document)|reprocess_document_task|process_document_task'; then
  violations+=("loop_over_dispatch: a loop wraps a reprocess dispatch — must be ONE doc at a time with post-verify")
fi

# Pattern 3: explicit bulk/sweep/batch keyword alongside doc-processing call
if printf '%s' "$cmd" | grep -qiE '\b(bulk|sweep|batch[[:space:]]*dispatch)\b' \
   && printf '%s' "$cmd" | grep -qE 'reprocess|send_task|process_document'; then
  violations+=("bulk_keyword: command mentions bulk/sweep/batch alongside doc-processing")
fi

# Pattern 4: multiple distinct doc UUIDs in a command that also mentions reprocess.
# Catches scripts that hard-list UUIDs across two or more send_task calls.
n_uuids=$(printf '%s' "$cmd" \
  | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' \
  | sort -u | wc -l)
if [ "${n_uuids:-0}" -gt 1 ] \
   && printf '%s' "$cmd" | grep -qE 'reprocess|send_task|process_document'; then
  violations+=("multi_uuid_dispatch: $n_uuids distinct doc UUIDs alongside a doc-processing call in one command")
fi

# Pattern 5: mass Neo4j delete. The graph is DERIVED data, but rebuilding it
# costs LLM extraction per document — 308k entities as of 2026-07-20. A
# `DETACH DELETE` without a per-document scope wipes work that is expensive to
# recreate, and the graph has repeatedly been found INCOMPLETE rather than
# corrupt, so wiping is almost never the right first move. The only sanctioned
# delete path is `reprocess_document`, which cleans and rebuilds one document
# atomically.
if printf '%s' "$cmd" | grep -qiE 'detach[[:space:]]+delete'; then
  # Scoped to a single document/book id → allowed (that is the reprocess path).
  if printf '%s' "$cmd" | grep -qE '(document_id|book_id|doc_id)[[:space:]]*[:=]' \
     || printf '%s' "$cmd" | grep -qE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'; then
    :
  else
    violations+=("unscoped_graph_delete: DETACH DELETE with no document/book scope — this wipes derived graph data that costs LLM extraction to rebuild")
  fi
fi

# Pattern 6: whole-label or whole-database Neo4j wipe.
if printf '%s' "$cmd" | grep -qiE 'match[[:space:]]*\([a-z]*:?(Entity|Book|Chapter|Section|Chunk|Community)?[[:space:]]*\)[[:space:]]*(detach[[:space:]]+)?delete' \
   && ! printf '%s' "$cmd" | grep -qE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'; then
  violations+=("graph_label_wipe: unscoped MATCH ... DELETE over a whole node label")
fi

if [ ${#violations[@]} -eq 0 ]; then
  exit 0
fi

vlist=""
for v in "${violations[@]}"; do
  vlist="${vlist}\\n  - ${v}"
done

cat <<JSON
{
  "decision": "approve",
  "systemMessage": "🚧 /scrapalot:postprocess-parse GUARDRAIL — sideways move detected.${vlist}\\n\\nRule: process ONE document at a time, verify result, only then move to next. See PHASE 5 in ${CLAUDE_PLUGIN_ROOT}/agents/postprocess-parse.md.\\n\\nIf you are NOT inside a /scrapalot:postprocess-parse flow, this warning is informational; if you ARE, halt the bulk pattern and switch to per-doc sequential."
}
JSON
exit 0
