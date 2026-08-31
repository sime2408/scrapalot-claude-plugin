#!/usr/bin/env python3
"""Stop-hook brain for the corpus sweep: keep going to the next book, with no gap.

`/loop` paces the sweep with a timer, which means dead air between books — the
owner asked for the obvious alternative on 2026-08-31: *"zar ne možeš imat neki
huk koji te budi da nastavljaš kad si sa jednom knjigom gotov?"*. This is that
hook. When a sweep is active and unaudited books remain, ending the turn is
blocked and the next book is named, so the agent moves straight on.

It is armed by a marker file and is a silent no-op without one, the same shape as
every other hook in this plugin: an ordinary conversation never sees it.

  arm    : sweep-next.py arm   --session <id>
  disarm : sweep-next.py disarm
  status : sweep-next.py status

The marker records the session that armed it, and ONLY that session is ever
blocked. A sweep left armed by one session must not wall the next one — that
mistake was already made once by the gate hook, which walled unrelated sessions
behind a book audit three times on 2026-08-20/21.

Fails OPEN on every error. A hook that traps a session is worse than a hook that
does nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("SCRAPALOT_ROOT")
POSTPROCESS_DIR = Path(
    os.environ.get("SCRAPALOT_POSTPROCESS_DIR")
    or (Path(_PROJECT_DIR) / ".claude" / "postprocess" if _PROJECT_DIR else Path.cwd() / ".claude" / "postprocess")
)
MARKER = POSTPROCESS_DIR / "SWEEP_ACTIVE"
PROGRESS = POSTPROCESS_DIR / "progress.txt"
GOAL = POSTPROCESS_DIR / "GOAL.md"

# Consecutive blocks allowed without a new row in progress.txt. A book takes many
# turns, so this is generous — but it is not unbounded, because an agent stuck in
# a loop it cannot finish must be able to stop and say so.
MAX_BLOCKS_WITHOUT_PROGRESS = 25

# Hours after which an armed marker is treated as abandoned. A sweep that has not
# produced a row in this long is not a sweep any more.
STALE_HOURS = 12

# A Stop hook runs on the turn boundary, so the owner waits for it. The book
# list query measures ~8s; 25 gives it room without ever becoming a hang.
DB_TIMEOUT = 25

SQL_NEXT = """
SELECT d.id::text, replace(left(d.title, 70), E'\\n', ' '), c.collection_name
FROM documents d
JOIN collection_workspace_map c ON c.collection_id = d.collection_id
WHERE c.graph_tier = 2
  AND d.deleted_at IS NULL
  AND coalesce(d.processing_error, '') <> 'errorScannedPdfOcrDeferred'
  AND c.collection_name NOT LIKE '.test%'
ORDER BY c.collection_name, d.title;
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_marker() -> dict:
    try:
        return json.loads(MARKER.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_marker(data: dict) -> None:
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _open_ledgers() -> list[Path]:
    """Ledgers still in gates/active/, i.e. a book that is not finished."""
    try:
        gates = Path(os.environ.get("SCRAPALOT_GATES_DIR") or (POSTPROCESS_DIR.parent / "gates"))
        return [p for p in sorted((gates / "active").glob("*.md")) if p.name != "template.md"]
    except Exception:
        return []


def _progress_rows() -> int:
    try:
        return sum(1 for _ in PROGRESS.open(encoding="utf-8", errors="replace"))
    except Exception:
        return -1


def _remaining() -> tuple[int, tuple[str, str, str] | None]:
    """(books still without a ledger row, the alphabetically first of them).

    Queries the database directly rather than trusting a cached list: the corpus
    changes under the sweep, and a stale list would send the agent to a book that
    has since been deleted or re-tiered.
    """
    try:
        out = subprocess.run(
            ["docker", "exec", "pgvector", "psql", "-U", "scrapalot", "-d", "scrapalot",
             "-t", "-A", "-F", "|", "-c", SQL_NEXT],
            capture_output=True, text=True, timeout=DB_TIMEOUT,
        )
        if out.returncode != 0:
            return -1, None
        audited = PROGRESS.read_text(encoding="utf-8", errors="replace") if PROGRESS.exists() else ""
    except Exception:
        return -1, None

    remaining, first = 0, None
    for line in out.stdout.splitlines():
        parts = line.split("|")
        if len(parts) < 3:
            continue
        did, title, coll = parts[0], parts[1], parts[2]
        if did and did not in audited:
            remaining += 1
            if first is None:
                first = (did, title, coll)
    return remaining, first


def cmd_arm(session: str) -> int:
    _write_marker({"session": session, "armed_at": _now(),
                   "rows_at_arm": _progress_rows(), "blocks": 0, "rows_at_last_block": _progress_rows()})
    remaining, first = _remaining()
    where = f"{first[2]} / {first[1]}" if first else "nothing left"
    print(f"sweep armed for session {session}: {remaining} tier-2 books without a ledger row; next is {where}")
    return 0


def cmd_disarm() -> int:
    try:
        MARKER.unlink()
        print("sweep disarmed — the Stop hook will not block again")
    except FileNotFoundError:
        print("sweep was not armed")
    except Exception as e:
        print(f"could not disarm: {e}")
        return 1
    return 0


def cmd_status() -> int:
    m = _read_marker()
    if not m:
        print("sweep: not armed")
        return 0
    remaining, first = _remaining()
    print(f"sweep: armed by {m.get('session')} at {m.get('armed_at')}, "
          f"{m.get('blocks', 0)} block(s) so far, {remaining} book(s) remaining")
    if first:
        print(f"  next: {first[0][:8]}  {first[2]} / {first[1]}")
    return 0


def cmd_stop_hook() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    if os.environ.get("SCRAPALOT_SWEEP_OFF") == "1":
        return 0

    try:
        marker = _read_marker()
        if not marker:
            return 0

        # A book still in flight belongs to the gate hook, which blocks until its
        # ledger is full. Two Stop hooks pushing at once would bury the gate's
        # reason under this one's, and "start the next book" is wrong advice while
        # the current one is unfinished.
        if _open_ledgers():
            return 0

        session = str(payload.get("session_id", "unknown"))
        owner = marker.get("session")
        if owner and owner != session:
            # Never wall a session that did not arm the sweep.
            print(json.dumps({"systemMessage":
                              f"sweep: a corpus sweep is armed by another session ({owner}) — "
                              "not blocking you."}))
            return 0

        # A sweep that stopped producing rows is over, whatever the marker says.
        try:
            armed_at = datetime.fromisoformat(marker.get("armed_at", ""))
            age_h = (datetime.now(timezone.utc) - armed_at).total_seconds() / 3600
        except Exception:
            age_h = 0.0

        rows = _progress_rows()
        blocks = int(marker.get("blocks", 0))
        rows_at_last = int(marker.get("rows_at_last_block", -1))
        blocks = 1 if rows != rows_at_last else blocks + 1
        marker["blocks"] = blocks
        marker["rows_at_last_block"] = rows
        _write_marker(marker)

        if blocks > MAX_BLOCKS_WITHOUT_PROGRESS:
            cmd_disarm()
            print(json.dumps({"systemMessage":
                              f"sweep: disarmed after {MAX_BLOCKS_WITHOUT_PROGRESS} turns with no new row in "
                              "progress.txt. Say what stalled — do not re-arm it without saying so."}))
            return 0

        if age_h > STALE_HOURS:
            cmd_disarm()
            print(json.dumps({"systemMessage":
                              f"sweep: disarmed — armed {age_h:.0f}h ago and treated as abandoned."}))
            return 0

        remaining, first = _remaining()
        if remaining < 0:
            # The database could not be reached. Do NOT block on a broken query.
            print(json.dumps({"systemMessage":
                              "sweep: could not reach the database to pick the next book — not blocking."}))
            return 0
        if remaining == 0 or first is None:
            cmd_disarm()
            print(json.dumps({"systemMessage":
                              "sweep: every tier-2 book now has a ledger row. Coverage is not quality — "
                              f"check the five end-state conditions in {GOAL} before calling the goal met."}))
            return 0

        did, title, coll = first
        reason = (
            f"sweep: {remaining} tier-2 book(s) still have no ledger row. "
            f"Next is {did[:8]} — \"{title}\" in {coll}. "
            "Start it now with /scrapalot:book; do not end the turn and do not "
            "schedule a wakeup, this hook is the pacing. "
            f"The mandate and the five end-state conditions are in {GOAL}. "
            "To stop: python3 <plugin>/scripts/sweep-next.py disarm."
        )
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0
    except Exception:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stop-hook", action="store_true", help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd")
    p_arm = sub.add_parser("arm", help="arm the sweep for this session")
    p_arm.add_argument("--session", required=True)
    sub.add_parser("disarm", help="stop the sweep")
    sub.add_parser("status", help="show what the sweep is holding")
    args = ap.parse_args()

    if args.stop_hook:
        return cmd_stop_hook()
    if args.cmd == "arm":
        return cmd_arm(args.session)
    if args.cmd == "disarm":
        return cmd_disarm()
    if args.cmd == "status":
        return cmd_status()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
