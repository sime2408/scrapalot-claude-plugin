#!/usr/bin/env bash
# install-cron.sh — idempotently register the DevOps loop in the user crontab.
#
# Default cadence: once daily at 23:00 UTC. The nightly run reviews the whole
# day's logs (SCAN_WINDOW_MIN=1440) and only spins up Claude when there are NEW
# error signatures. There is no activity gate — the late-night slot is the
# safety window.
#
# Override cadence:  CRON_EXPR='0 22 * * *' ./install-cron.sh
# Remove:            ./install-cron.sh --remove

set -euo pipefail

RUNNER="/home/scrapalot/bin/scrapalot-devops-loop.sh"
CRON_LOG="${CLAUDE_PROJECT_DIR}/.claude/devops-loop/cron.log"
CRON_EXPR="${CRON_EXPR:-0 23 * * *}"
MARKER="# scrapalot-devops-loop"
LINE="${CRON_EXPR} ${RUNNER} >> ${CRON_LOG} 2>&1 ${MARKER}"

current="$(crontab -l 2>/dev/null || true)"

if [ "${1:-}" = "--remove" ]; then
  printf '%s\n' "$current" | grep -v "$MARKER" | crontab -
  echo "removed devops-loop cron entry"
  exit 0
fi

if printf '%s\n' "$current" | grep -qF "$MARKER"; then
  # replace existing line (cadence may have changed)
  printf '%s\n' "$current" | grep -v "$MARKER" > /tmp/_cron.$$
  echo "$LINE" >> /tmp/_cron.$$
  crontab /tmp/_cron.$$ && rm -f /tmp/_cron.$$
  echo "updated devops-loop cron entry:"
else
  { printf '%s\n' "$current"; echo "$LINE"; } | crontab -
  echo "installed devops-loop cron entry:"
fi
echo "  $LINE"
echo
echo "Verify: crontab -l | grep devops-loop"
echo "Logs:   tail -f ${CLAUDE_PROJECT_DIR}/.claude/devops-loop/loop.log"
