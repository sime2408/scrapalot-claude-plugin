#!/usr/bin/env bash
# notify-owner.sh "<title>" "<body>" — tell the owner the loop stopped.
#
# A cron run has nobody watching it, so "log it and hope" is not notification.
# A GitHub issue on scrapalot-chat, assigned to the owner, is what this machine
# can raise on its own and what the owner already reads; the marker file is for
# the next run, which must not start again into the same wall.
set -uo pipefail

title="${1:-scrapalot book-graph loop stopped}"
body="${2:-The book-graph loop stopped. See .claude/book-graph/loop.log.}"
LOOP_DIR="${CLAUDE_PROJECT_DIR:-/opt/scrapalot}/.claude/book-graph"
mkdir -p "$LOOP_DIR"
printf '%s %s\n%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$title" "$body" >> "$LOOP_DIR/notifications.log"

if command -v gh >/dev/null 2>&1; then
  gh issue create --repo sime2408/scrapalot-chat \
    --title "$title" --body "$body" --assignee sime2408 >/dev/null 2>&1 \
    && echo "notified: issue opened" && exit 0
fi
echo "notified: log only (gh unavailable)" >&2
exit 0
