#!/usr/bin/env bash
# install-cron.sh — idempotently register the book-graph sweep in the crontab,
# at DeepSeek's off-peak hours only.
#
# Two lines, because peak applies Monday to Friday: the weekday line fires on
# the off-peak hours read from the price table, the weekend line fires hourly.
# Each pass is single-flight (flock) and exits in seconds when the hour, the
# balance or the candidate list says no, so an hourly cadence costs nothing.
#
#   install:  ./install-cron.sh
#   remove:   ./install-cron.sh --remove
set -euo pipefail

MARKER="# scrapalot-book-graph"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/opt/scrapalot}"
LOG="$PROJECT_DIR/.claude/book-graph/cron.log"
WRAPPER="${WRAPPER:-$HOME/bin/scrapalot-book-graph.sh}"

current="$(crontab -l 2>/dev/null || true)"

if [ "${1:-}" = "--remove" ]; then
  printf '%s\n' "$current" | grep -v "$MARKER" | crontab -
  echo "removed book-graph cron entries"
  exit 0
fi

hours="$(docker exec scrapalot-chat python -c \
  'from src.main.service.llm.model_pricing import off_peak_hours_utc; print(",".join(map(str, off_peak_hours_utc())))' \
  2>/dev/null | tr -d '\r')"
if [ -z "$hours" ]; then
  hours="0,4,5,10,11,12,13,14,15,16,17,18,19,20,21,22,23"
  echo "warning: price table unreadable — installing the published off-peak hours" >&2
fi

mkdir -p "$(dirname "$LOG")"
weekday="0 $hours * * 1-5 $WRAPPER >> $LOG 2>&1 $MARKER"
weekend="0 * * * 6,0 $WRAPPER >> $LOG 2>&1 $MARKER"

printf '%s\n' "$current" | grep -v "$MARKER" > /tmp/_cron.$$
{ echo "$weekday"; echo "$weekend"; } >> /tmp/_cron.$$
crontab /tmp/_cron.$$ && rm -f /tmp/_cron.$$

echo "installed:"
echo "  $weekday"
echo "  $weekend"
echo
echo "Re-run this after a DeepSeek pricing change: the hours are baked into the"
echo "crontab line, while cheap-now.sh re-reads them on every pass."
