#!/usr/bin/env bash
# Stop hook for the gate ledger (see .claude/gates/CONTRACT.md).
#
# Blocks ending the turn while a ledger in .claude/gates/active/ still has unmet
# gates. Silent no-op when no ledger is active, so ordinary conversation is
# untouched — the same "only enforce inside the run" shape as
# devops_loop_guardrail.sh.
#
# All logic lives in gate-check.py so the parser has ONE implementation; this is
# a thin wrapper kept here for discoverability alongside its sibling hooks.
#
# Fails OPEN by design: a missing interpreter, an unreadable ledger or any
# unexpected error must never trap a session. Deliberately no `set -e`.

GATE_CHECK="${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py"

command -v python3 >/dev/null 2>&1 || exit 0
[ -r "$GATE_CHECK" ] || exit 0

python3 "$GATE_CHECK" --stop-hook || exit 0
exit 0
