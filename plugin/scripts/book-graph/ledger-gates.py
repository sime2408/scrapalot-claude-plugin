#!/usr/bin/env python3
"""Does this gate ledger carry every starter gate of /scrapalot:book-graph?

A ledger opened by copying an older book's ledger carries the gates of the
command as it was then: one opened after G3b joined the starter gates still
lacked it, and the gap surfaced only when that gate's evidence had nowhere to
go. Run from the ledger at baseline, this names the missing gate before any
build. It compares gate ids only: an abandoned gate keeps its line, so it
counts as present, and the placeholders in each CHECK are the book's to fill. Gates
the book added beyond the starter set are allowed. It reads the live command,
so a starter gate another session lands mid-run fails the next run: add it.

Usage: ledger-gates.py <ledger.md>
"""

import re
import sys
from pathlib import Path

COMMAND = Path(__file__).resolve().parents[2] / "commands" / "book-graph.md"
# gate-check.py's GATE_RE, so every line it treats as a gate counts here too.
GATE = re.compile(r"^(\s*)- \[( |x|X)\] ([A-Za-z0-9_.-]+):\s*(.*)$")


def gate_ids(text: str) -> list[str]:
    return [m.group(3) for m in map(GATE.match, text.splitlines()) if m]


def starter_ids(text: str) -> list[str]:
    start = text.find("Starter gates.")
    if start < 0:
        return []
    block = text.find("```markdown", start)
    end = text.find("```", block + len("```markdown"))
    if block < 0 or end < 0:
        return []
    return gate_ids(text[block:end])


def main() -> int:
    if len(sys.argv) != 2:
        print("LEDGER_GATES_FAIL usage: ledger-gates.py <ledger.md>")
        return 1
    ledger = Path(sys.argv[1])
    if not ledger.is_file():
        print(f"LEDGER_GATES_FAIL ledger_not_found {ledger}")
        return 1
    wanted = starter_ids(COMMAND.read_text(encoding="utf-8"))
    if not wanted:
        print(f"LEDGER_GATES_FAIL starter_block_not_found {COMMAND}")
        return 1
    have = set(gate_ids(ledger.read_text(encoding="utf-8")))
    missing = [g for g in wanted if g not in have]
    if missing:
        print(f"LEDGER_GATES_MISSING starter={len(wanted)} ledger={len(have)} missing={','.join(missing)}")
        return 1
    print(f"LEDGER_GATES_OK starter={len(wanted)} ledger={len(have)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
