#!/usr/bin/env bash
# PreToolUse hook for Edit / Write / MultiEdit.
#
# A comment earns its place by explaining what is true about the code. Three
# things that keep appearing in Scrapalot comments explain nothing to the
# person reading the file, and all three have needed a corpus-wide cleanup:
#
#   1. an individual commit SHA or PR number  — the reasoning belongs in the
#      comment; the identifier sends the reader to the history for it
#   2. a date                                 — "Measured 2026-08-21: 42 rows"
#      states the finding twice over; the date only says how stale to feel
#   3. an attribution to the owner            — a decision explains itself by
#      its reason; who made it is in the history
#   4. a count of the corpus                  — "5,869 pending graphs" is true
#      for one afternoon, and the next ingest makes it a lie nobody notices
#   5. an operational runbook                 — policy and cost estimates
#      belong in the rules an agent reads, not in the file they act on
#
# Does NOT block. Emits a warning so the model catches itself before the write
# lands. Functional occurrences are deliberately exempt — see SKIP below.
# NOTE: no `set -e` — the false branches of these checks are control flow.

input=$(cat)

path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
# Everything this call would newly put in the file: Write content, Edit
# new_string, or every new_string of a MultiEdit.
added=$(printf '%s' "$input" | jq -r '
  [ .tool_input.content?,
    .tool_input.new_string?,
    (.tool_input.edits? // [] | .[].new_string?)
  ] | map(select(. != null)) | join("\n")')
[ -z "$added" ] && exit 0

case "$path" in
  # The spell-check allowlist stores SHA strings on purpose; migrations and
  # lockfiles are generated; fixtures quote dates as data.
  *_typos.toml|*.secrets.baseline|*poetry.lock|*package-lock.json) exit 0 ;;
esac

# Lines that carry a functional date/identifier rather than a narrative one.
SKIP='anthropic-version|Notion-Version|api-version|xmlns|https?://|%Y|strftime|strptime|fromisoformat|created_at|BUILD_DATE|Create Date|[0-9a-f]{8}-[0-9a-f]{4}-|claude-[a-z]+-[0-9]|gpt-[0-9]'

# Only prose lines: a comment marker, or a line inside a docstring/YAML text.
prose=$(printf '%s' "$added" | grep -E '^[[:space:]]*(#|//|\*|"""|'"'''"')|^[[:space:]]*[A-Z(`"]' | grep -vE "$SKIP")
[ -z "$prose" ] && exit 0

violations=()

# 1a. Explicit commit / PR references.
hit=$(printf '%s' "$prose" | grep -oiE '\bcommit[[:space:]]+[0-9a-f]{7,40}\b|\bPR[[:space:]]?#?[0-9]{1,4}\b|\(#[0-9]{2,4}\)' | head -3 | tr '\n' ' ')
[ -n "$hit" ] && violations+=("commit/PR reference: ${hit}")

# 1b. A bare 7-char hex token reads as a git short SHA. 8-char tokens are
#     corpus document ids in this codebase and are left alone.
hit=$(printf '%s' "$prose" | grep -oE '(^|[^0-9a-f-])[0-9a-f]{7}([^0-9a-f-]|$)' | grep -oE '[0-9a-f]{7}' | head -3 | tr '\n' ' ')
[ -n "$hit" ] && violations+=("bare short SHA: ${hit}")

# 2. Dates.
hit=$(printf '%s' "$prose" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -3 | tr '\n' ' ')
[ -n "$hit" ] && violations+=("date in a comment: ${hit}")
hit=$(printf '%s' "$prose" | grep -oiE '\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[[:space:]]+20[0-9]{2}\b' | head -2 | tr '\n' ' ')
[ -n "$hit" ] && violations+=("month/year in a comment: ${hit}")

# 3. Owner attribution — the human, not the domain concept (owner_id, the
#    workspace owner, the owner of a table).
hit=$(printf '%s' "$prose" | grep -oiE '\(owner[,)]|owner (say|said|saying|decide|decided|ask|asked|want|approved|confirmed|chose)[a-z]*|the owner'"'"'s (call|decision|choice)|per the owner|by the owner\b' | head -2 | tr '\n' ' ')
[ -n "$hit" ] && violations+=("owner attribution: ${hit}")

# 4. Corpus counts. "5,869 pending graphs" is true for one afternoon; the next
#    ingest makes the comment a lie nobody will notice.
hit=$(printf '%s' "$prose" | grep -oiE '\b[0-9][0-9,]{2,}[[:space:]]+([a-z-]+[[:space:]]+){0,2}(documents?|books?|chunks?|entities|entity|graphs?|docs?|titles?|headings?|rows?|files?|collections?|pairs?)\b' | head -3 | tr '\n' ' ')
[ -n "$hit" ] && violations+=("corpus count: ${hit}")

# 5. A runbook living in a source comment. Policy, cost estimates and "do not
#    do X" procedure belong in the rules the agent reads, not in the file.
if printf '%s' "$prose" | grep -qiE '\bDO NOT (RESUME|LIFT|ENABLE|TOUCH|REMOVE)\b|must NOT be (resumed|lifted|re-enabled)|without (the owner|an explicit decision)'; then
  n_comment_lines=$(printf '%s' "$prose" | grep -cE '^[[:space:]]*#')
  [ "${n_comment_lines:-0}" -ge 6 ] && violations+=("runbook in a comment: ${n_comment_lines} comment lines carrying operational policy")
fi

[ ${#violations[@]} -eq 0 ] && exit 0

vlist=""
for v in "${violations[@]}"; do
  vlist="${vlist}\\n  - ${v}"
done

cat <<JSON
{
  "decision": "approve",
  "systemMessage": "🧹 COMMENT HYGIENE — this write adds something a reader cannot use.${vlist}\\n\\nRewrite the comment so it states the reasoning on its own terms: keep the finding, drop the identifier. \\"Measured 2026-08-21: 42 rows\\" becomes \\"Measured: 42 rows\\"; \\"the guard PR #184 added\\" becomes \\"the guard in _inject_chapter_markers_lightweight\\".\\n\\nExempt when the token is FUNCTIONAL: an API version header, a date-filter example, a model id, a workflow's author allowlist, a git remote. If this is one of those, proceed. Full rule: ${CLAUDE_PLUGIN_ROOT}/skills/comment-hygiene/SKILL.md"
}
JSON
exit 0
