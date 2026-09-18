#!/usr/bin/env bash
# cheap-now.sh — exit 0 when DeepSeek is billing off-peak right now, 1 in peak.
#
# The windows are NOT restated here. `off_peak_hours_utc()` in
# scrapalot-chat/src/main/service/llm/model_pricing.py derives them from the
# price table, the Celery beat schedule already reads the same function, and a
# price change has to move all three together or none.
#
# Peak is Monday to Friday only, so a weekend hour is always cheap. That part
# the pricing module does not model — it prices every hour by the clock alone,
# deliberately over-estimating spend — so the weekday test lives here, where
# over-estimating would mean idling the loop for nothing.
set -uo pipefail

hour="$(date -u +%-H)"
dow="$(date -u +%u)"   # 1..7, Monday..Sunday

if [ "$dow" -ge 6 ]; then
  echo "cheap: weekend (UTC $(date -u +%a\ %H:%M)) — peak is Mon-Fri only"
  exit 0
fi

hours="$(docker exec scrapalot-chat python -c \
  'from src.main.service.llm.model_pricing import off_peak_hours_utc; print(",".join(map(str, off_peak_hours_utc())))' \
  2>/dev/null | tr -d '\r')"

if [ -z "$hours" ]; then
  # The container is the source of truth; without it, fall back to the windows
  # as published on 2026-09-09 and SAY that the fallback was used.
  hours="0,4,5,10,11,12,13,14,15,16,17,18,19,20,21,22,23"
  echo "warning: could not read the price table from scrapalot-chat — using the published windows" >&2
fi

case ",$hours," in
  *",$hour,"*) echo "cheap: UTC hour $hour is off-peak"; exit 0 ;;
esac

# When does it end? The next hour that is off-peak.
for ahead in 1 2 3 4 5; do
  nxt=$(( (hour + ahead) % 24 ))
  case ",$hours," in *",$nxt,"*) echo "peak: UTC hour $hour — off-peak resumes at ${nxt}:00 UTC"; exit 1 ;; esac
done
echo "peak: UTC hour $hour"
exit 1
