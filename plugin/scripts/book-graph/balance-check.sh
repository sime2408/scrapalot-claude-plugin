#!/usr/bin/env bash
# balance-check.sh — is there money on the DeepSeek account?
#
#   exit 0  the account answers
#   exit 2  insufficient balance (HTTP 402) — the caller must STOP, not retry
#   exit 1  anything else (no key, no network, some other HTTP error)
#
# One-token probe against the model the system provider actually runs. It costs
# a fraction of a cent and is the only way to know: a spent account fails every
# call with 402 while the logs fill with what looks like a model problem. That
# is how three days of silent failure went unnoticed on 2026-09-09..12.
set -uo pipefail

model="${DEEPSEEK_PROBE_MODEL:-deepseek-flash}"
key="$(docker exec pgvector psql -U scrapalot -d scrapalot -At -c \
  "SELECT api_key FROM model_providers WHERE provider_type ILIKE '%deepseek%' OR name ILIKE '%deep%' LIMIT 1" 2>/dev/null | tr -d '\r')"
[ -n "$key" ] || { echo "balance: no DeepSeek key in model_providers" >&2; exit 1; }

body="$(printf '{"model":"%s","messages":[{"role":"user","content":"ping"}],"max_tokens":1,"thinking":{"type":"disabled"}}' "$model")"
code="$(curl -s --max-time 60 -o /tmp/.ds_probe.$$ -w '%{http_code}' \
  -H "Authorization: Bearer ${key}" -H 'Content-Type: application/json' \
  -d "$body" https://api.deepseek.com/chat/completions 2>/dev/null)"
out="$(cat /tmp/.ds_probe.$$ 2>/dev/null)"; rm -f /tmp/.ds_probe.$$

case "$code" in
  200) echo "balance: ok"; exit 0 ;;
  402) echo "balance: INSUFFICIENT (402)"; exit 2 ;;
  *)   echo "balance: HTTP $code — ${out:0:120}" >&2; exit 1 ;;
esac
