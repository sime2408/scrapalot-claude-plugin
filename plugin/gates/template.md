# Gates — <run-slug>
RUN: <run-slug>
COMMAND: <command>
SESSION: <session-id>
SCOPE: <one line: what this run must deliver>
OPENED: <UTC timestamp>
CWD: /opt/scrapalot

<!--
Format (full rules in ../CONTRACT.md — read it once, it is short):
  - one checkbox per outcome, stated so a stranger could judge it
  - CHECK: a shell command that proves the outcome
    EXPECT: substring the output must contain, /regex/flags, or !negated
    (optional) CWD: <dir>   TIMEOUT: <seconds>
  - a gate with no possible command is manual: no CHECK, and EVIDENCE must be
    replaced by real proof — a measurement, a quoted line, a file:line
  - `gate-check.py run` flips the boxes; you never flip a CHECK box by hand
  - a checked box whose EVIDENCE still reads "pending" counts as UNMET
  - impossible gate → add a line at column 0: ABANDON: G<n> <reason>, and say so
    in the report. Visible surrender is honest; silent narrowing is not.
-->

- [ ] G1: <observable outcome>
  CHECK: <shell command that proves it>
  EXPECT: <substring or /regex/>
  EVIDENCE: pending

- [ ] G2: <another runnable outcome>
  CHECK: <command>
  EXPECT: <substring or /regex/>
  EVIDENCE: pending

- [ ] G3: <manual outcome — no command can prove it>
  EVIDENCE: pending
