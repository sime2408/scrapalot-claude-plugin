#!/usr/bin/env bash
# Stop hook for the corpus sweep (see .claude/postprocess/GOAL.md).
#
# While a sweep is armed and tier-2 books still have no ledger row, this blocks
# ending the turn and names the next book, so the agent moves straight from one
# book to the next with no timer in between. Armed by a marker file and a silent
# no-op without one, so ordinary conversation is untouched — the same shape as
# gates_stop_guardrail.sh beside it.
#
# All logic lives in sweep-next.py so there is ONE implementation; this is a thin
# wrapper kept here for discoverability alongside its sibling hooks.
#
# Fails OPEN by design: a missing interpreter, an unreachable database or any
# unexpected error must never trap a session. Deliberately no `set -e`.

SWEEP="${CLAUDE_PLUGIN_ROOT}/scripts/sweep-next.py"

command -v python3 >/dev/null 2>&1 || exit 0
[ -r "$SWEEP" ] || exit 0

python3 "$SWEEP" --stop-hook || exit 0
exit 0
