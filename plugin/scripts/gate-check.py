#!/usr/bin/env python3
"""Gate ledger runner + Stop-hook for the long-running Scrapalot commands.

A gate ledger is a markdown file whose checkboxes are flipped by THIS script,
never by the agent's opinion. A gate with a `CHECK:` line is proven by running
that command and matching its output against `EXPECT:`; a gate without one is
manual and needs a real `EVIDENCE:` line before it counts.

Why it exists: `postprocess/progress.txt`, `devops-loop/STATE.md` and the run
reports are narration — a model writing prose about itself. Nothing in the tree
was mechanically verifiable, so "done" was always a claim. This is the ledger
that claim gets checked against. See `CONTRACT.md`.

Subcommands
-----------
  open   --run SLUG --command /name [--scope TEXT]   create active/SLUG.md
  run    [LEDGER...]                                 execute CHECKs, flip boxes
  status [LEDGER...]                                 report only, execute nothing
  close  LEDGER [--force]                            archive to done/ when full
  --stop-hook                                        Claude Code Stop hook mode

Exit codes: 0 = every gate met (or abandoned), 1 = gates outstanding, 2 = error.
Stdlib only, Python 3.8+.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ledgers are workspace state and must outlive a plugin update, so they live in
# the project, not next to this script (which sits in the plugin's install cache
# and is replaced wholesale on every update). SCRAPALOT_GATES_DIR overrides;
# otherwise the project root wins, and only a bare checkout falls back to $CWD.
_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("SCRAPALOT_ROOT")
GATES_DIR = Path(
    os.environ.get("SCRAPALOT_GATES_DIR")
    or (Path(_PROJECT_DIR) / ".claude" / "gates" if _PROJECT_DIR else Path.cwd() / ".claude" / "gates")
)
ACTIVE_DIR = GATES_DIR / "active"
DONE_DIR = GATES_DIR / "done"
# The template ships with the plugin; a project-local copy still wins if present.
TEMPLATE = GATES_DIR / "template.md"
if not TEMPLATE.exists():
    TEMPLATE = _PLUGIN_ROOT / "gates" / "template.md"
STOP_STATE = GATES_DIR / ".stop-state.json"
DISABLED_FLAG = GATES_DIR / ".disabled"

DEFAULT_CWD = str(_PROJECT_DIR) if _PROJECT_DIR else str(Path.cwd())
DEFAULT_TIMEOUT = 600           # a check that needs longer says so with TIMEOUT:
DEFAULT_JOBS = 4                # independent checks run concurrently by default
EVIDENCE_TAIL = 240             # deciding lines only — a ledger is not a log store
MAX_BLOCKS = 8                  # consecutive Stop blocks without ledger progress
STALE_HOURS = 12                # an untouched ledger stops blocking future sessions
WAIT_MINUTES = 30               # default life of a WAITING pause
PENDING = {"", "pending", "-", "tbd", "todo", "n/a"}

# Checks must never wait on a human: no pager, no colour codes, no git credential
# prompt. Combined with stdin=DEVNULL this turns "hangs for the whole timeout"
# into "fails in a second with a readable reason".
NONINTERACTIVE_ENV = {
    "PAGER": "cat",
    "GIT_PAGER": "cat",
    "GIT_TERMINAL_PROMPT": "0",
    "NO_COLOR": "1",
    "CI": "1",
    "DEBIAN_FRONTEND": "noninteractive",
    "PYTHONUNBUFFERED": "1",
}

GATE_RE = re.compile(r"^(\s*)- \[( |x|X)\] ([A-Za-z0-9_.-]+):\s*(.*)$")
FIELD_RE = re.compile(r"^\s+(CHECK|EXPECT|EVIDENCE|CWD|TIMEOUT):\s*(.*)$")
ABANDON_RE = re.compile(r"^ABANDON:\s*([A-Za-z0-9_.-]+)\s*(.*)$")
HEADER_RE = re.compile(r"^(RUN|COMMAND|SCOPE|OPENED|CWD|RESUMABLE):\s*(.*)$")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #

class Gate:
    def __init__(self, gid: str, title: str, box_line: int) -> None:
        self.id = gid
        self.title = title
        self.box_line = box_line
        self.checked = False
        self.check = ""
        self.expect = ""
        self.evidence = ""
        self.evidence_line = -1
        self.cwd = ""
        self.timeout = 0
        self.abandoned = ""
        self.took = 0.0

    @property
    def unmet(self) -> bool:
        if self.abandoned:
            return False
        if not self.checked:
            return True
        ev = self.evidence.strip()
        if ev.lower() in PENDING:
            return True
        return ev.upper().startswith("FAIL")

    def label(self) -> str:
        return f"{self.id}: {self.title}".strip()


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines()
        self.header: dict[str, str] = {}
        self.gates: list[Gate] = []
        self._parse()

    def _parse(self) -> None:
        current: Gate | None = None
        for i, line in enumerate(self.lines):
            m = GATE_RE.match(line)
            if m:
                current = Gate(m.group(3), m.group(4).strip(), i)
                current.checked = m.group(2).lower() == "x"
                self.gates.append(current)
                continue
            m = FIELD_RE.match(line)
            if m and current is not None:
                key, val = m.group(1), m.group(2).strip()
                if key == "CHECK":
                    current.check = val
                elif key == "EXPECT":
                    current.expect = val
                elif key == "EVIDENCE":
                    current.evidence = val
                    current.evidence_line = i
                elif key == "CWD":
                    current.cwd = val
                elif key == "TIMEOUT":
                    current.timeout = int(val) if val.isdigit() else 0
                continue
            m = ABANDON_RE.match(line)
            if m:
                reason = m.group(2).strip() or "(no reason given)"
                for g in self.gates:
                    if g.id == m.group(1):
                        g.abandoned = reason
                continue
            m = HEADER_RE.match(line)
            if m and not self.gates:
                self.header[m.group(1)] = m.group(2).strip()

    # -- state ------------------------------------------------------------- #

    @property
    def unmet(self) -> list[Gate]:
        return [g for g in self.gates if g.unmet]

    @property
    def abandoned(self) -> list[Gate]:
        return [g for g in self.gates if g.abandoned]

    def summary(self) -> str:
        met = len(self.gates) - len(self.unmet) - len(self.abandoned)
        out = f"{met}/{len(self.gates)} met"
        pre = sum(1 for g in self.gates if "PRE-EXISTING" in g.evidence and not g.unmet)
        if pre:
            out += f" ({pre} pre-existing, not this run's work)"
        if self.abandoned:
            out += f", {len(self.abandoned)} abandoned"
        if self.unmet:
            out += f", {len(self.unmet)} OUTSTANDING"
        return out

    # -- mutation ---------------------------------------------------------- #

    def set_box(self, gate: Gate, checked: bool) -> None:
        m = GATE_RE.match(self.lines[gate.box_line])
        if not m:
            return
        indent, _, gid, title = m.groups()
        self.lines[gate.box_line] = f"{indent}- [{'x' if checked else ' '}] {gid}: {title}"
        gate.checked = checked

    def set_evidence(self, gate: Gate, text: str) -> None:
        text = " ".join(text.split())
        if gate.evidence_line >= 0:
            indent = re.match(r"^(\s*)", self.lines[gate.evidence_line]).group(1)
            self.lines[gate.evidence_line] = f"{indent}EVIDENCE: {text}"
        else:
            self.lines.insert(gate.box_line + 1, f"  EVIDENCE: {text}")
            for g in self.gates:
                if g.box_line > gate.box_line:
                    g.box_line += 1
                if g.evidence_line > gate.box_line:
                    g.evidence_line += 1
            gate.evidence_line = gate.box_line + 1
        gate.evidence = text

    def append(self, text: str) -> None:
        self.lines.append(text)

    def save(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)


# --------------------------------------------------------------------------- #
# checking
# --------------------------------------------------------------------------- #

def expect_matches(expect: str, output: str) -> bool:
    """Substring by default; `/re/flags` for regex; a leading `!` inverts."""
    expect = expect.strip()
    if not expect:
        return True
    negate = expect.startswith("!")
    if negate:
        expect = expect[1:].strip()
    m = re.match(r"^/(.*)/([imsx]*)$", expect, re.DOTALL)
    if m:
        flags = 0
        for ch in m.group(2):
            flags |= {"i": re.I, "m": re.M, "s": re.S, "x": re.X}[ch]
        hit = re.search(m.group(1), output, flags) is not None
    else:
        hit = expect in output
    return not hit if negate else hit


def kill_tree(proc: subprocess.Popen) -> None:
    """Kill the whole process group, not just the shell we spawned.

    `shell=True` means our direct child is /bin/sh; a timed-out pytest or
    playwright lives in its grandchildren. Killing the shell alone leaves them
    running AND holding the output pipe open, which is how a "timeout" turns
    into a hang.
    """
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(os.getpgid(proc.pid), sig)
        except (ProcessLookupError, PermissionError, OSError):
            return
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def run_gate(gate: Gate, default_cwd: str) -> tuple[bool, str]:
    cwd = gate.cwd or default_cwd
    timeout = gate.timeout or DEFAULT_TIMEOUT
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.Popen(
            gate.check, shell=True, cwd=cwd, env={**os.environ, **NONINTERACTIVE_ENV},
            # stdin closed: a check that asks a question (a pager, `gh auth`, a
            # pdb breakpoint, `read`) must fail fast instead of blocking the run
            # until the timeout. This was the single likeliest way to stall.
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace", start_new_session=True,
        )
    except OSError as exc:
        return False, f"could not run: {exc}"
    try:
        output = proc.communicate(timeout=timeout)[0] or ""
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        try:
            output = proc.communicate(timeout=10)[0] or ""
        except Exception:
            output = ""
        tail = " ".join(output.split())[-EVIDENCE_TAIL:] or "(no output)"
        return False, f"timeout after {timeout}s, process group killed | {tail}"
    took = (datetime.now(timezone.utc) - started).total_seconds()
    proc.returncode = proc.returncode if proc.returncode is not None else -1
    gate.took = took
    tail = " ".join(output.split())[-EVIDENCE_TAIL:] or "(no output)"
    ok = expect_matches(gate.expect, output)
    # A negated EXPECT ("must not contain X") is trivially satisfied by a command
    # that never ran. rc 126/127 is "not executable" / "not found" — proof of
    # nothing. Other non-zero codes stay legal: `grep` exits 1 on no match, which
    # is precisely the success case for a negated check.
    if ok and gate.expect.strip().startswith("!") and proc.returncode in (126, 127):
        return False, f"rc={proc.returncode} | command not runnable, negated EXPECT proves nothing | {tail}"
    return ok, f"rc={proc.returncode} in {took:.0f}s | {tail}"


# --------------------------------------------------------------------------- #
# ledger discovery
# --------------------------------------------------------------------------- #

def resolve(paths: list[str]) -> list[Path]:
    if paths:
        out = []
        for p in paths:
            path = Path(p)
            if not path.is_absolute() or not path.exists():
                # Accept every shape a command or a person might type:
                # a path relative to cwd, one relative to the gates dir, a bare
                # ledger name, or that name without the .md.
                name = Path(p).name
                for cand in (Path.cwd() / p, ACTIVE_DIR / p, GATES_DIR / p,
                             ACTIVE_DIR / name, ACTIVE_DIR / f"{name}.md",
                             DONE_DIR / name):
                    if cand.exists():
                        path = cand
                        break
            out.append(path)
        return out
    return sorted(f for f in ACTIVE_DIR.glob("*.md") if f.name != "template.md")


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #

def cmd_open(args) -> int:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", args.run).strip("-")
    dest = ACTIVE_DIR / f"{slug}.md"
    if dest.exists():
        print(f"ledger already open: {dest}", file=sys.stderr)
        return 2
    body = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else (
        "# Gates — <title>\nRUN: \nCOMMAND: \nSCOPE: \nOPENED: \n\n"
        "- [ ] G1: <outcome>\n  EVIDENCE: pending\n"
    )
    body = body.replace("<run-slug>", slug)
    body = body.replace("<command>", args.command or "")
    # Stamp the OPENING session. Ownership used to be decided by whichever
    # session's Stop hook first found the ledger unclaimed — so a long run that
    # had not yet reached a Stop left its ledger unowned, and an unrelated
    # parallel session picked it up and got walled in behind gates it had no
    # way to meet. CONTRACT.md already promised the opposite ("another session's
    # open ledger is reported as an orphan, never enforced"); this is what makes
    # that true. Absent (older ledgers, or no env var) falls back to the old
    # first-encounter behaviour, so nothing mid-flight changes.
    body = body.replace("<session-id>", os.environ.get("CLAUDE_CODE_SESSION_ID", ""))
    body = body.replace("<one line: what this run must deliver>", args.scope or "")
    body = body.replace("<UTC timestamp>", utc_now())
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    print(f"opened {dest}")
    print("Fill in the gates BEFORE starting work, then: gate-check.py run")
    return 0


def cmd_run(args) -> int:
    ledgers = resolve(args.ledgers)
    if not ledgers:
        print("no active ledger — nothing to check")
        return 0
    # Stamp ownership on the session that actually WORKS the ledger. `cmd_open`
    # stamps too, but only for ledgers created through it — a hand-authored one
    # (the contract allows those) carries no SESSION line, and then the Stop hook
    # falls back to claiming it for whichever session reaches a Stop first. That
    # is how an unrelated session got walled behind a book audit twice on
    # 2026-08-20/21. Running the checks is a far better proxy for ownership than
    # arriving first: the bystander never calls this.
    _sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if _sid:
        for _p in ledgers:
            try:
                _blob = _p.read_text(encoding="utf-8")
                if re.search(r"^SESSION:\s*\S", _blob, re.M):
                    continue
                _lines = _blob.splitlines()
                _at = next((i for i, ln in enumerate(_lines) if ln.startswith("COMMAND:")), 0)
                _lines.insert(_at + 1, f"SESSION: {_sid}")
                _p.write_text("\n".join(_lines) + "\n", encoding="utf-8")
                print(f"stamped {_p.name} as owned by this session")
            except Exception:
                pass
    only = {s.strip() for s in args.only.split(",") if s.strip()} if args.only else set()
    jobs = max(1, args.jobs)
    outstanding = 0
    for path in ledgers:
        if not path.exists():
            print(f"missing ledger: {path}", file=sys.stderr)
            return 2
        led = Ledger(path)
        default_cwd = led.header.get("CWD", DEFAULT_CWD)
        first_run = not any(line.startswith("BASELINED:") for line in led.lines)
        print(f"\n=== {path.name} ===")

        # Decide what actually needs executing, then run those concurrently.
        # Identical CHECK+CWD+TIMEOUT triples run ONCE and share their result —
        # a whole-ledger re-verify should not rebuild the same suite five times.
        todo = [g for g in led.gates
                if g.check and not g.abandoned
                and (not only or g.id in only)
                and not (args.fast and not g.unmet)]
        results: dict[str, tuple[bool, str]] = {}
        if todo:
            uniq: dict[tuple, Gate] = {}
            for g in todo:
                uniq.setdefault((g.check, g.cwd or default_cwd, g.timeout), g)
            with ThreadPoolExecutor(max_workers=min(jobs, len(uniq))) as pool:
                futures = {key: pool.submit(run_gate, g, default_cwd)
                           for key, g in uniq.items()}
                for key, fut in futures.items():
                    results[key] = fut.result()

        for g in led.gates:
            if g.abandoned:
                print(f"  ~ {g.id}  ABANDONED — {g.abandoned}")
                continue
            if not g.check:
                if not g.unmet:
                    print(f"  ✔ {g.id}  MANUAL, evidence recorded — {g.title}")
                elif g.checked:
                    print(f"  ☐ {g.id}  MANUAL, box ticked but EVIDENCE is still "
                          f"'{g.evidence or 'empty'}' — {g.title}")
                elif g.evidence.strip().lower() not in PENDING:
                    print(f"  ☐ {g.id}  MANUAL, evidence recorded — tick the box to "
                          f"assert it — {g.title}")
                else:
                    print(f"  ☐ {g.id}  MANUAL, no evidence yet — {g.title}")
                continue
            key = (g.check, g.cwd or default_cwd, g.timeout)
            if key not in results:
                mark = "✔" if not g.unmet else "☐"
                why = "already met, skipped" if args.fast and not g.unmet else "not selected"
                print(f"  {mark} {g.id}  {why} — {g.title}")
                continue
            ok, detail = results[key]
            # PROVENANCE. A ledger measures outcomes, and an outcome can be true
            # because somebody else made it true. On 2026-08-20 seven gates went
            # green before the run had done anything — another session had
            # reprocessed the document — and only a timestamp check caught it.
            # So the FIRST execution of a gate is a baseline, not an achievement:
            # anything already passing then is marked PRE-EXISTING and stays
            # marked, and `close` reports the count so a report cannot quietly
            # take the credit.
            pre = ok and first_run and not g.evidence.strip().lower().startswith(("ok", "fail"))
            tag = " PRE-EXISTING" if pre or (ok and "PRE-EXISTING" in g.evidence) else ""
            led.set_box(g, ok)
            led.set_evidence(g, f"{'ok' if ok else 'FAIL'}{tag} {utc_now()} | {detail}")
            print(f"  {'✔' if ok else '✘'} {g.id} {'(pre-existing)' if tag else ''} {g.title}")
            if not ok:
                print(f"      {detail}")
        if first_run and todo:
            led.append(f"\nBASELINED: {utc_now()} — first execution of this ledger. "
                       f"Gates passing here were already true before the run acted; "
                       f"they carry PRE-EXISTING and are not this run's work.")
        led.save()
        pre_count = sum(1 for g in led.gates if "PRE-EXISTING" in g.evidence and not g.unmet)
        if pre_count:
            print(f"  !! {pre_count} gate(s) were ALREADY GREEN at baseline — "
                  f"not this run's doing. Say so in the report.")
        print(f"  -> {led.summary()}")
        for g in led.unmet:
            print(f"     outstanding: {g.label()}")
        outstanding += len(led.unmet)
    print(f"\n{outstanding} gate(s) outstanding" if outstanding else "\nall gates met")
    return 1 if outstanding else 0


def cmd_status(args) -> int:
    ledgers = resolve(args.ledgers)
    if not ledgers:
        print("no active ledger")
        return 0
    outstanding = 0
    payload = []
    for path in ledgers:
        if not path.exists():
            continue
        led = Ledger(path)
        outstanding += len(led.unmet)
        payload.append({
            "ledger": str(path),
            "run": led.header.get("RUN", path.stem),
            "command": led.header.get("COMMAND", ""),
            "total": len(led.gates),
            "unmet": [g.label() for g in led.unmet],
            "abandoned": [f"{g.id}: {g.abandoned}" for g in led.abandoned],
        })
        if not args.json:
            print(f"=== {path.name} === {led.summary()}")
            for g in led.gates:
                mark = "~" if g.abandoned else ("✔" if not g.unmet else "☐")
                print(f"  {mark} {g.label()}")
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 1 if outstanding else 0


def cmd_wait(args) -> int:
    """Declare that the turn is ending to WAIT, not to quit.

    The wall exists to stop the finishing reflex. It cannot see that a subagent
    is still running, so without this it blocks a turn that ends for an honest
    reason and burns its block budget on nothing. The pause is short-lived and
    on the record: it names what is being waited on and expires by itself.
    """
    ledgers = resolve(args.ledgers)
    if not ledgers:
        print("no active ledger — nothing to pause")
        return 0
    for path in ledgers:
        led = Ledger(path)
        led.lines = [ln for ln in led.lines if not ln.startswith("WAITING:")]
        led.append(f"WAITING: {utc_now()} +{args.minutes}m — {args.on}")
        led.save()
        print(f"paused {path.name} for {args.minutes}m — {args.on}")
    print("The wall is down until it expires. Clear it when the work lands: "
          f"python3 {Path(__file__).resolve()} resume")
    return 0


def cmd_resume(args) -> int:
    ledgers = resolve(args.ledgers)
    for path in ledgers:
        led = Ledger(path)
        before = len(led.lines)
        led.lines = [ln for ln in led.lines if not ln.startswith("WAITING:")]
        if len(led.lines) != before:
            led.save()
            print(f"resumed {path.name} — the wall is back up")
    return 0


def waiting_active(blob: str) -> str:
    """Return the reason if a fresh WAITING marker is present, else ""."""
    m = re.search(r"^WAITING:\s*(\S+)\s*\+(\d+)m\s*—?\s*(.*)$", blob, re.M)
    if not m:
        return ""
    try:
        stamped = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return ""
    if datetime.now(timezone.utc) - stamped > timedelta(minutes=int(m.group(2))):
        return ""
    return m.group(3) or "background work"


def cmd_close(args) -> int:
    path = resolve([args.ledger])[0]
    if not path.exists():
        print(f"missing ledger: {path}", file=sys.stderr)
        return 2
    led = Ledger(path)
    if led.unmet and not args.force:
        print(f"refusing to close — {led.summary()}", file=sys.stderr)
        for g in led.unmet:
            print(f"  outstanding: {g.label()}", file=sys.stderr)
        print("Finish them, or record `ABANDON: <id> <reason>` and say so in the report.",
              file=sys.stderr)
        return 1
    if led.unmet and args.force:
        led.append(f"\nFORCED-CLOSE: {utc_now()} — {len(led.unmet)} gate(s) still unmet: "
                   + ", ".join(g.id for g in led.unmet))
        led.save()
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = DONE_DIR / f"{stamp}-{path.stem}.md"
    os.replace(path, dest)
    print(f"closed -> {dest}")
    print(f"summary: {led.summary()}")
    return 0


# --------------------------------------------------------------------------- #
# Stop hook
# --------------------------------------------------------------------------- #

def load_stop_state() -> dict:
    try:
        return json.loads(STOP_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_stop_state(state: dict) -> None:
    """Persist hook state, pruning entries older than a week.

    Shape: {"claims": {ledger-name: {session, ts}}, "sessions": {sid: {hash, blocks, ts}}}
    A claim is dropped once its ledger is gone, so a closed run frees its name.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    pruned = {
        "claims": {k: v for k, v in state.get("claims", {}).items()
                   if v.get("ts", "9999") >= cutoff and (ACTIVE_DIR / k).exists()},
        "sessions": {k: v for k, v in state.get("sessions", {}).items()
                     if v.get("ts", "9999") >= cutoff},
    }
    try:
        tmp = STOP_STATE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(pruned), encoding="utf-8")
        os.replace(tmp, STOP_STATE)
    except Exception:
        pass


def cmd_stop_hook() -> int:
    """Block ending the turn while an active ledger has outstanding gates.

    Fails open on every error: a broken hook must never trap a session. It reads
    state only — it NEVER executes a CHECK command. Running the checks is the
    agent's job, through `gate-check.py run`.
    """
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    if os.environ.get("SCRAPALOT_GATES_OFF") == "1" or DISABLED_FLAG.exists():
        return 0

    try:
        ledgers = [p for p in sorted(ACTIVE_DIR.glob("*.md")) if p.name != "template.md"]
        if not ledgers:
            return 0

        session = str(payload.get("session_id", "unknown"))
        state = load_stop_state()
        claims = state.setdefault("claims", {})

        blobs, unmet, released, foreign, resumable, paused, mine = [], [], [], [], [], [], []
        newest = 0.0
        for path in ledgers:
            blob = path.read_text(encoding="utf-8")
            led = Ledger(path)
            # A ledger already marked RELEASED/FORCED-CLOSE has had its wall lifted
            # once, on the record. Re-blocking it just churns; the unmet gates stay
            # in the file and belong in the report either way.
            if re.search(r"^(RELEASED|FORCED-CLOSE):", blob, re.M):
                if led.unmet:
                    released.append((path.name, len(led.unmet)))
                continue
            if not led.unmet:
                continue
            waiting = waiting_active(blob)
            if waiting:
                paused.append((path.name, len(led.unmet), waiting))
                continue
            # A `/loop`-driven run ends its turn on purpose every tick and resumes
            # on the next one. Walling that in would be the stall this hook exists
            # to prevent, so a RESUMABLE ledger reports instead of blocking. It
            # still refuses to `close` with gates open.
            if re.search(r"^RESUMABLE:\s*(yes|true)\s*$", blob, re.M | re.I):
                resumable.append((path.name, len(led.unmet)))
                continue
            # A ledger belongs to the session that opened it. The nightly loop must
            # never leave a wall standing in front of tomorrow's interactive session,
            # and two parallel sessions must not block each other.
            # A ledger that names its opener owns itself — the state file cannot
            # override it, and a session that did not open it never becomes the
            # owner by arriving first.
            stamped = re.search(r"^SESSION:\s*(\S+)\s*$", blob, re.M)
            owner = stamped.group(1) if stamped else claims.get(path.name, {}).get("session")
            if owner is None:
                # Ownership is assigned by `open` (which stamps SESSION) and by
                # `run` (which stamps a hand-authored ledger the first time its
                # checks are executed). It is NOT assigned here, because "the
                # first session to reach a Stop" is not a claim to anyone's work:
                # on 2026-08-20/21 that rule walled an unrelated session behind a
                # book audit three separate times, while the session actually
                # doing the work had simply not reached a Stop yet. An unowned
                # ledger is reported as an orphan to everyone — which is what
                # CONTRACT.md promised all along — and becomes owned the moment
                # somebody runs its checks.
                foreign.append((path.name, len(led.unmet)))
                continue
            if owner != session:
                foreign.append((path.name, len(led.unmet)))
                continue
            mine.append(path)
            blobs.append(blob)
            newest = max(newest, path.stat().st_mtime)
            unmet += [(path.name, g.label()) for g in led.unmet]

        if not unmet:
            notes = []
            full = [p.name for p in ledgers
                    if not Ledger(p).unmet
                    and not re.search(r"^(RELEASED|FORCED-CLOSE):",
                                      p.read_text(encoding="utf-8"), re.M)]
            if full:
                notes.append(f"every gate met in {', '.join(full)} — close it: "
                             f"python3 {Path(__file__).resolve()} close <ledger>")
            if released:
                notes.append("released but still unmet: "
                             + ", ".join(f"{n} ({c})" for n, c in released))
            if paused:
                notes.append("paused while waiting: "
                             + ", ".join(f"{n} ({c} unmet, on {w})" for n, c, w in paused)
                             + " — clear it with `gate-check.py resume` once that lands")
            if resumable:
                notes.append("resumable ledger(s) mid-run: "
                             + ", ".join(f"{n} ({c} unmet)" for n, c in resumable)
                             + " — the next tick continues there, do not call it done")
            if foreign:
                notes.append("open ledger(s) from another session: "
                             + ", ".join(f"{n} ({c} unmet)" for n, c in foreign)
                             + " — archive or finish them, they are not blocking you")
            save_stop_state(state)
            if notes:
                print(json.dumps({"systemMessage": "gates: " + "; ".join(notes) + "."}))
            return 0
            names = ", ".join(p.name for p in ledgers)
            print(json.dumps({"systemMessage":
                              f"gates: every gate met in {names}. Close the ledger: "
                              f"python3 {Path(__file__).resolve()} close <ledger>"}))
            return 0

        age_h = (datetime.now(timezone.utc).timestamp() - newest) / 3600
        if age_h > STALE_HOURS:
            save_stop_state(state)
            print(json.dumps({"systemMessage":
                              f"gates: {len(unmet)} gate(s) still unmet but the ledger has "
                              f"not been touched in {age_h:.0f}h — releasing. Archive or "
                              f"finish it: python3 {Path(__file__).resolve()} status"}))
            return 0

        digest = hashlib.sha256("".join(blobs).encode("utf-8")).hexdigest()
        sessions = state.setdefault("sessions", {})
        entry = sessions.get(session, {})
        blocks = 0 if entry.get("hash") != digest else int(entry.get("blocks", 0))
        blocks += 1
        sessions[session] = {"hash": digest, "blocks": blocks,
                             "ts": datetime.now(timezone.utc).isoformat()}
        save_stop_state(state)

        if blocks > MAX_BLOCKS:
            for path in mine:
                try:
                    led = Ledger(path)
                    if led.unmet:
                        led.append(f"\nRELEASED: {utc_now()} — Stop hook released after "
                                   f"{MAX_BLOCKS} blocks without ledger progress; "
                                   f"{len(led.unmet)} gate(s) unmet.")
                        led.save()
                except Exception:
                    pass
            print(json.dumps({"systemMessage":
                              f"gates: releasing after {MAX_BLOCKS} blocks without progress. "
                              f"{len(unmet)} gate(s) remain unmet and the release is recorded "
                              f"in the ledger — say so in the report, do not call this done."}))
            return 0

        listed = "; ".join(f"{name} → {label}" for name, label in unmet[:5])
        more = f" (+{len(unmet) - 5} more)" if len(unmet) > 5 else ""
        reason = (
            f"gates: {len(unmet)} gate(s) unmet — {listed}{more}. "
            "No report until the ledger is full. Work the next unmet gate, then prove it: "
            f"python3 {Path(__file__).resolve()} run. "
            "A gate that has become genuinely impossible is not dropped silently — write "
            "`ABANDON: <id> <reason>` into the ledger and say so in the report."
        )
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0
    except Exception:
        return 0


# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stop-hook", action="store_true", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd")

    p_open = sub.add_parser("open", help="create a ledger in active/")
    p_open.add_argument("--run", required=True, help="short slug, e.g. book-2cdd2f36")
    p_open.add_argument("--command", default="", help="the slash command this run belongs to")
    p_open.add_argument("--scope", default="", help="one line: what this run must deliver")

    p_run = sub.add_parser("run", help="execute CHECKs and flip boxes")
    p_run.add_argument("ledgers", nargs="*")
    p_run.add_argument("--only", default="",
                       help="comma-separated gate ids — check just these (G3,G7)")
    p_run.add_argument("--jobs", type=int, default=DEFAULT_JOBS,
                       help=f"concurrent checks (default {DEFAULT_JOBS}; 1 to serialise)")
    p_run.add_argument("--fast", action="store_true",
                       help="skip gates already met — for mid-run iteration. The full "
                            "run before `close` is the one that counts.")

    p_status = sub.add_parser("status", help="report only, execute nothing")
    p_status.add_argument("ledgers", nargs="*")
    p_status.add_argument("--json", action="store_true")

    p_wait = sub.add_parser("wait", help="pause the wall while background work runs")
    p_wait.add_argument("--on", required=True,
                        help="what is being waited on, e.g. 'parse audit agent'")
    p_wait.add_argument("--minutes", type=int, default=WAIT_MINUTES,
                        help=f"how long the pause stays valid (default {WAIT_MINUTES})")
    p_wait.add_argument("ledgers", nargs="*")

    p_resume = sub.add_parser("resume", help="clear the pause, the wall is back up")
    p_resume.add_argument("ledgers", nargs="*")

    p_close = sub.add_parser("close", help="archive a full ledger to done/")
    p_close.add_argument("ledger")
    p_close.add_argument("--force", action="store_true",
                         help="close with gates unmet; records FORCED-CLOSE in the ledger")

    args = parser.parse_args()
    if args.stop_hook:
        return cmd_stop_hook()
    if args.cmd == "open":
        return cmd_open(args)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "wait":
        return cmd_wait(args)
    if args.cmd == "resume":
        return cmd_resume(args)
    if args.cmd == "close":
        return cmd_close(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
