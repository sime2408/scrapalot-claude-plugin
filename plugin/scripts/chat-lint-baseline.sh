#!/bin/bash
# Baseline lint snapshot for scrapalot-chat (Python)
set -euo pipefail

echo "=== SCRAPALOT-CHAT LINT BASELINE ==="
echo "Date: $(date -Iseconds)"
echo ""

echo "--- BLACK (formatting) ---"
BLACK_COUNT=$(docker exec scrapalot-chat black --check src/main/ 2>&1 | grep -c "would reformat" || echo "0")
echo "Files needing reformat: $BLACK_COUNT"

echo ""
echo "--- ISORT (import sorting) ---"
ISORT_COUNT=$(docker exec scrapalot-chat isort --check-only src/main/ 2>&1 | grep -c "would be" || echo "0")
echo "Files with import issues: $ISORT_COUNT"

echo ""
echo "--- FLAKE8 (style + complexity) ---"
FLAKE8_OUTPUT=$(docker exec scrapalot-chat flake8 src/main/ --count --statistics --max-line-length=120 --ignore=E501,W503,E402 2>&1 || true)
FLAKE8_COUNT=$(echo "$FLAKE8_OUTPUT" | tail -1 | grep -oE "^[0-9]+" || echo "0")
echo "Total errors: $FLAKE8_COUNT"
echo "Top categories:"
echo "$FLAKE8_OUTPUT" | grep -E "^[0-9]+" | sort -rn | head -10

echo ""
echo "--- PYLINT (deep analysis) ---"
PYLINT_OUTPUT=$(docker exec scrapalot-chat pylint src/main/ \
  --disable=C0114,C0115,C0116,C0103,C0301,R0903,R0913,R0914,W0511 \
  --score=y --fail-under=0 2>&1 || true)
PYLINT_SCORE=$(echo "$PYLINT_OUTPUT" | grep "Your code has been rated" | grep -oE "[0-9]+\.[0-9]+" | head -1 || echo "0.0")
echo "Score: $PYLINT_SCORE / 10"
echo "Top issues:"
echo "$PYLINT_OUTPUT" | grep -E "^[A-Z][0-9]+" | head -10

echo ""
echo "=== BASELINE SUMMARY ==="
echo "BLACK_FILES=$BLACK_COUNT"
echo "ISORT_FILES=$ISORT_COUNT"
echo "FLAKE8_ERRORS=$FLAKE8_COUNT"
echo "PYLINT_SCORE=$PYLINT_SCORE"
