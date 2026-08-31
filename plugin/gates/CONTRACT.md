# The gate contract — proof instead of narration

Read this once before running any command that opens a gate ledger:
`/scrapalot-book`, `/scrapalot-postprocess-parse`, `/scrapalot-postprocess-graph`,
`/scrapalot-rag-test`, `/scrapalot-competitive-impl`, `/scrapalot-devops-loop`.

It is the sibling of `postprocess/GAUNTLET.md`, and the two answer different
questions. The gauntlet answers **who judges** — a separate critic with fresh
context, never the builder. This answers **what counts as proof** — a command
whose real output matched a stated expectation, recorded before the claim was
made.

## Why it exists

Every long-running command in this tree already writes down what it did:
`postprocess/progress.txt` is 700 KB of ledger rows, `devops-loop/STATE.md` has a
timeline, `rag-test/STATE.md` has a per-question grid. All of it is **narration**
— a model writing prose about its own work. Nothing in the tree was mechanically
verifiable, so "done" was always a claim, and the claim was checked by the same
agent that made it.

Three failures in a single session on 2026-08-15/16 were caught only because
somebody happened to measure: a regression test that passed against the broken
build, a fix that would have renamed 8,226 chapter titles, a precedence change
that cut a book from 26 chapters to 2. The gauntlet fixed *who judges*. This
fixes *what a judgement is allowed to rest on*.

A gate whose `CHECK:` is `docker exec scrapalot-chat python -m pytest tests/integration/test_notes.py`
and whose `EXPECT:` is `passed` cannot be talked into being green. That is the
whole idea.

## The ledger

One file per run, in `gates/active/`, moved to `gates/done/` when the run ends.
While a ledger sits in `active/` with unmet gates, the Stop hook will not let the
turn end. Copy `template.md`, or:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py open \
    --run book-2cdd2f36 --command /scrapalot-book \
    --scope "one book, parse + graph, critic says the stored structure is the book's"
```

Format:

```markdown
- [ ] G1: integration tests for the feature pass
  CHECK: docker exec scrapalot-chat python -m pytest tests/integration/test_x.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: pending

- [ ] G2: the chapter list matches the book, judged by a critic that did not build it
  EVIDENCE: pending
```

- `EXPECT:` is a substring by default, `/regex/flags` for a pattern, and a
  leading `!` inverts it (`EXPECT: !Traceback`).
- `CWD:` per gate or in the header; defaults to `/opt/scrapalot`. Playwright
  gates need `CWD: /opt/scrapalot/scrapalot-ui`.
- `TIMEOUT:` per gate in seconds; default 600. A suite that genuinely needs
  longer says so in the gate.
- A gate with no `CHECK:` is **manual**: `EVIDENCE:` must be replaced with real
  proof — a measurement, a quoted line of output, a `file:line`, the critic's
  verdict sentence.

## A check must never wait on a human

The runner is built so a bad gate fails fast instead of stalling the run, and the
gates you write should not fight it:

- **stdin is closed.** A check that prompts — a pager, `gh auth login`, a stray
  `pdb.set_trace()`, `read` — gets EOF and fails in a second instead of hanging
  until the timeout. Never write a gate that expects to be answered.
- **The environment is non-interactive**: `PAGER=cat`, `GIT_PAGER=cat`,
  `GIT_TERMINAL_PROMPT=0`, `NO_COLOR=1`, `CI=1`.
- **A timeout kills the process group**, not just the shell — a timed-out pytest
  does not survive as an orphan holding the pipe open.
- **Never `-f` / `--follow` / `--watch` in a CHECK.** `docker logs -f` never
  ends; `docker logs --since 10m` does.
- Independent checks run concurrently (`--jobs`, default 4), and two gates whose
  `CHECK:` is byte-identical run **once** and share the result.
- **A memory-heavy build goes through `scrapalot-build`** (`scrapalot-build npm run build`),
  never bare. CI runners share this 16 GB host with every production container,
  and a gate is not a licence to skip workspace rule #14. Finish a local Gradle
  gate with `./gradlew --stop` in the same `CHECK:`.

```bash
gate-check.py run                       # everything, 4 at a time — the honest default
gate-check.py run --only G3,G7          # just these, while iterating on one fix
gate-check.py run --fast                # skip gates already met (mid-run only)
gate-check.py run --jobs 1              # serialise, when checks contend for the DB
```

`--fast` is for the middle of a run. The full `run` before `close` is the one
that counts — a gate proven an hour ago against code that has since changed is
not proof.

## Rules

1. **Gates before work.** Write the ledger before the first fix, not after. A
   checklist written at minute 2 is still sharp at minute 90, when the pull
   toward wrapping up is strongest.
2. **You never flip a `CHECK:` box by hand.** `gate-check.py run` flips it, and
   only when the output matched. Hand-flipping is the failure this file exists
   to prevent.
3. **A checked box whose `EVIDENCE:` still reads `pending` counts as UNMET.**
   So does one whose evidence starts with `FAIL`.
4. **No report until the ledger is full.** Composing a status summary while boxes
   are open is the tell. Open the ledger and pick the next unmet gate.
5. **An impossible gate is abandoned in writing, never dropped.** Add a line at
   column 0: `ABANDON: G3 <reason>`, and say it in the report. A visible
   surrender is a result; silent scope-narrowing is how a half-done run gets
   reported as done.
6. **Re-measure every number at report time.** The most reproducible failure in
   this tree is a report whose substance is right and whose numbers are invented
   from memory. Paste the ledger summary — `N/M met` — rather than a feeling.

## Provenance — a green box is not proof you did it

A ledger measures **outcomes**, and an outcome can be true because somebody else
made it true. On 2026-08-20 a `/scrapalot-book` run opened its reprocess ledger
and seven gates went green before it had done anything: another session on the
same host had already reprocessed the document. Only a timestamp check caught it.

So the **first** execution of a ledger is a baseline, not an achievement:

- `run` stamps `BASELINED:` the first time it executes, and any gate already
  passing then is written `ok PRE-EXISTING …`. The tag is sticky.
- Every summary says `N/M met (K pre-existing, not this run's work)`, and `run`
  prints a loud line when K > 0.
- That number belongs in the report. A run that reports eight green gates when
  seven were green before it started has told the truth about the state and a lie
  about itself.

This does not tell you *who* made it true — for a database-backed gate nothing
can. It tells you it was not you, which is the part a report gets wrong.

## Waiting is not quitting

The wall exists to stop the finishing reflex. It cannot see that a subagent is
still running, so a turn that ends to **wait** would burn the block budget on an
honest pause. Say so instead:

```bash
gate-check.py wait --on "parse audit agent"     # wall down, on the record, 30 min
gate-check.py resume                            # wall back up when the work lands
```

The pause names what is being waited on, appears in the hook's message every
turn, and **expires by itself** — so a forgotten `wait` cannot become a
permanent exemption. `--minutes` adjusts the life; `resume` ends it early.

## What makes a gate worth writing

A gate is an outcome a stranger could judge, not a step you intend to take.

| Bad | Why | Good |
|---|---|---|
| `G1: write tests` | an intention; satisfied by an empty file | `G1: the new suite passes` + `CHECK: … pytest … -q`, `EXPECT: /\d+ passed/` |
| `G2: the fix works` | nothing to check against | `G2: the reported error no longer appears` + `CHECK: docker logs --since 10m scrapalot-chat`, `EXPECT: !<signature>` |
| `G3: CI is fine` | vague, and green-by-default | `G3: CI green on the PR` + `CHECK: gh run list --limit 1 --json conclusion -q '.[0].conclusion'`, `EXPECT: success` |
| `G4: chapters look reasonable` | the critic invents the bar and passes everything | `G4: a critic with fresh context, given both lists unlabelled, says they are the same book` (manual, evidence = the verdict sentence) |

Four to ten gates is the working range. Two means you did not think; twenty means
you wrote a task list.

## The Stop hook

`hooks/gates_stop_guardrail.sh` runs on `Stop` and refuses to end the turn while
an active ledger has unmet gates.

- **It executes nothing.** It reads the ledger and blocks; running the checks is
  the agent's job. A hook that could launch pytest is a hook that can hang a
  session.
- **It is silent when no ledger is active** — ordinary conversation is untouched.
- **A ledger blocks only the session that opened it.** The nightly `/scrapalot-devops-loop`
  must never leave a wall standing in front of the owner's next morning session,
  and two parallel sessions must not block each other. Another session's open
  ledger is reported as an orphan to archive, never enforced.
- **A ledger is owned by the session that ran `open`** (stamped as `SESSION:` in
  its own header by `cmd_open` from `CLAUDE_CODE_SESSION_ID`) **or, for a
  hand-authored ledger, by the first session to run its checks** (`run` stamps
  one that carries no `SESSION:` line). **The Stop hook never assigns ownership.**
  An unowned ledger is reported as an orphan to everyone and walls nobody, which
  is what this document promised from the start. Before 2026-08-20 it was: a claim was
  taken by the first session whose Stop hook found the ledger unclaimed, so a
  long run that had not yet reached a Stop left its ledger unowned and an
  unrelated parallel session was walled in behind gates it had no way to meet —
  the exact opposite of the orphan rule two bullets up. A ledger with no
  `SESSION:` line (opened before this, or with the variable unset) keeps the old
  first-encounter behaviour, so nothing mid-flight changed.
- **It fails open.** Any error, any unparsable input, and it allows the stop.
- **A ledger whose header says `RESUMABLE: yes` is never blocked**, only
  reported. That is for runs driven by `/loop`, where ending the turn with work
  outstanding *is* the design and a wall would be the stall this hook exists to
  prevent. `close` still refuses while gates are open, so the run cannot end
  quietly — it can only be continued.
- **It releases after 8 consecutive blocks without ledger progress**, writes
  `RELEASED:` into the ledger, and says so. It is a wall against the finishing
  reflex, not a way to trap a run that is genuinely stuck.
- **It releases a ledger untouched for 12 hours**, so a forgotten run cannot
  block every future session.
- Escape hatches: `SCRAPALOT_GATES_OFF=1` in the environment, or
  `touch gates/.disabled`.

The hook is a wall against the **finishing reflex**, not an adversarial sandbox.
An agent with Bash can always disable it, hand-flip a box, or write its own
`RELEASED:` line. That is deliberate: every one of those leaves a mark in the
ledger or the settings, which is the point. What it removes is the frictionless
version of stopping early — deciding you are done and simply saying so.

## Closing a run

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py run      # prove what is provable
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py status   # what remains
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py close gates/active/<run>.md
```

`close` refuses while gates are unmet. `--force` closes anyway and stamps
`FORCED-CLOSE` into the archived ledger — which then belongs in the report,
stated plainly.

## Where this does not belong

A conversational reply, a one-line fix, a question. There is no ledger for a copy
tweak. Gates are for the runs that go long enough for the agent to forget what it
promised — which is exactly the set of commands listed at the top.
