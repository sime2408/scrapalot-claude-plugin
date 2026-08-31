---
description: Autonomous DevOps fix loop — runs nightly, scans containers for the day's new errors, root-cause + fix one at a time on a branch, verify, open a PR assigned to sime2408. Never pushes to main.
allowed-tools: Bash, Read, Edit, Grep, Glob, Task
---

# /scrapalot:devops-loop

You are the **orchestrator** of the autonomous DevOps fix loop. One invocation =
one pass, run once daily at 23:00 UTC. You tie together the error scan, the maker
(`scrapalot:devops-fixer`), the read-only verifier (`scrapalot:devops-verifier`),
and the on-disk loop memory. You ship fixes only as **branch + PR**, assigned to
the human owner (`sime2408`).

There is **no activity gate** and **no parallel-session check** — the nightly
slot is the safety window. Run regardless of whether users or the operator were
active during the day; review the whole day's logs.

Loop home: `${CLAUDE_PROJECT_DIR}/.claude/devops-loop/` (GOAL.md, STATE.md,
seen-errors.jsonl, scripts/).

## Step 0 — orient
- Read `devops-loop/GOAL.md` (your mandate + guardrails) and `devops-loop/STATE.md`
  (what happened last time; any parked in-progress fix).
- A clean run that changes nothing is a SUCCESS. Never invent work.

## Step 0.5 — open the gate ledger
**Read `.claude/gates/CONTRACT.md` and follow it.** This loop runs unattended at
23:00 and reports to nobody until morning, which makes it the run most able to
tell itself a story. The ledger is what the morning report gets checked against.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py open \
    --run devops-<YYYYMMDD> --command /scrapalot:devops-loop \
    --scope "one nightly pass: scan the day, fix at most 3, PR each, never main"
```

Open it with the run-level gates; add per-error gates as Step 2 finds them.

```markdown
- [ ] G1: the scan covered the whole day (SCAN_WINDOW_MIN=1440) and its result is recorded
  EVIDENCE: pending
- [ ] G2: STATE.md last_run and Timeline are updated for this pass
  CHECK: grep -c "<YYYY-MM-DD>" ${CLAUDE_PROJECT_DIR}/.claude/devops-loop/STATE.md
  EXPECT: /[1-9]/
  EVIDENCE: pending
- [ ] G3: no isolated clone left behind
  CHECK: ls ${CLAUDE_PROJECT_DIR}/.claude/devops-loop/work | wc -l
  EXPECT: /^0$/
  EVIDENCE: pending
```

Per error that reaches `real_defect`, add three more — they are the difference
between "I fixed it" and a fix that exists:

```markdown
- [ ] E1.verify: the verifier approved, or the loop escalated after two different fixes hit the same objection
  EVIDENCE: pending
- [ ] E1.pr: a PR is open and assigned to sime2408
  CHECK: gh --repo sime2408/<subproject> pr view <num> --json state,assignees -q '.state + " " + (.assignees | map(.login) | join(","))'
  EXPECT: OPEN sime2408
  EVIDENCE: pending
- [ ] E1.recorded: the signature is in seen-errors.jsonl
  CHECK: grep -c '<signature>' ${CLAUDE_PROJECT_DIR}/.claude/devops-loop/seen-errors.jsonl
  EXPECT: /[1-9]/
  EVIDENCE: pending
```

An empty scan meets G1–G3 and closes: that is the no-op success the mandate
already describes, now with the ledger to show for it. A `wontfix` or `escalated`
error gets `ABANDON: E<n>.pr <the verdict and why>` — the loop's honest exits stay
visible instead of dissolving into the timeline.

## Step 1 — scan for new errors
Run `SCAN_WINDOW_MIN=1440 bash ${CLAUDE_PLUGIN_ROOT}/scripts/devops-loop/error-scan.sh`
to sweep the whole day's logs. Parse the JSON array.
- Empty `[]` → no-op success. Update STATE `last_run`, append a Timeline line
  "no new errors", stop.
- Otherwise you have N new error signatures.

## Step 2 — handle errors, ONE at a time (max 3 ships per run)
For each error (stop after 3 successful PRs):

1. **Maker:** launch `scrapalot:devops-fixer` (Task tool) with the error's
   `signature`, `source`, `sample`, `window`. It returns a structured verdict.

   The fixer works in an ISOLATED clone (`work_dir`) — never the live deployed
   checkout — so it never collides with the operator or a deploy. It returns
   `subproject`, `work_dir`, `branch`.

2. **Branch on the verdict** (always clean up `work_dir` when not shipping):
   - `expected_exception` / `cannot_reproduce` → record handled, move on:
     `bash devops-loop/scripts/record-error.sh <sig> wontfix "<short reason>"`;
     then `bash devops-loop/scripts/cleanup-work.sh <work_dir>` (if one was made).
   - `too_risky` → `record-error.sh <sig> escalated "<reason>"`; add a line under
     `## Backlog / escalated` in STATE.md; `cleanup-work.sh <work_dir>`.
   - `real_defect` → go to verify.

3. **Verifier (real_defect only):** launch `scrapalot:devops-verifier` with the
   fixer's `work_dir` + `branch` + `signature` + `root_cause`. Read-only review.
   Hand it the fixer's DIFF and the error signature — never the fixer's account
   of how hard the fix was or how many attempts it took.
   - `approve` → ship (step 4).
   - `reject` → **do not discard on the first no.** A rejection is the input to
     the next attempt, not the end of the attempt. Send the verifier's reason —
     that sentence and nothing else — back to `scrapalot:devops-fixer` on the
     same `work_dir`, and verify again.

     Stop looping when either: the verifier approves; or **two different fixes
     hit the same objection**, which means the loop is out of ideas and a human
     should look. Only then escalate and discard:
     `record-error.sh <sig> escalated "verifier rejected twice: <reason>"`; add
     to STATE Backlog; `bash devops-loop/scripts/cleanup-work.sh <work_dir>`.

     Never a round cap beyond that rule — "three tries and ship it" is how a
     symptom fix gets merged. And never ship on a reject because the loop is
     running late.

   Record every round in the run log: attempt number, the objection, and what
   changed. A loop whose rejections are invisible teaches nobody anything.

4. **Ship as PR (verifier approved):**
   - Push the FEATURE branch from the isolated clone (guardrail blocks pushing main):
     `git -C <work_dir> push -u origin <branch>`
   - Derive the repo slug: `gh repo set-default` is not needed — pass `--repo`
     from `git -C <work_dir> remote get-url origin` (e.g. sime2408/<subproject>).
   - Open a PR against `main`, **assigned to the human owner** `sime2408`:
     ```
     gh --repo <owner>/<subproject> pr create --base main --head <branch> \
        --assignee sime2408 \
        --title "<conventional title>" \
        --body "Autonomous DevOps loop fix.\n\nRoot cause: …\nError signature: <sig>\nVerifier: approved (<confidence>).\n\nDetected from <source> logs. Human review required before merge."
     ```
     Capture the PR URL/number. If `--assignee` fails (e.g. rate limit), the PR
     is still open — retry the assignment with
     `gh --repo <owner>/<subproject> pr edit <num> --add-assignee sime2408`.
   - **Never** `gh pr merge`. Merge is the human's call.
   - `record-error.sh <sig> pr_open "<subproject>#<num> — <one line>"`.
   - Add to STATE `## Recently shipped PRs` (newest first).
   - `bash devops-loop/scripts/cleanup-work.sh <work_dir>` (the branch is safe on
     the remote now; the local clone is disposable).

5. **Timeline:** append one line to STATE.md `## Timeline` for this error:
   `YYYY-MM-DDThh:mmZ · <sig> · <source> · <pr_open #N | wontfix | escalated> · <one line>`

## Step 3 — close out
- Update STATE.md: `last_run` (UTC now), refresh `## Current focus`, ensure any
  parked branch is noted under `## In progress` (or cleared if resolved).
- **Run and close the ledger — no report before it:**
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py run
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py close gates/active/devops-<YYYYMMDD>.md
  ```
- Final report (concise): # new errors, per-error outcome, PR links, the gate
  summary (`N/M met`, re-measured not recalled), and every `ABANDON:` line as a
  thing this pass did not settle.

## Hard rules (restate — these bind every step)
- Branch + PR only — NEVER push `main`/`master`, NEVER merge. PR assigned to `sime2408`.
- One error at a time, minimal scope, root cause not symptom.
- No destructive ops, no data mutation to mask bugs, no mass reprocess / heavy
  admin gRPC.
- Honesty: report no-ops, skips, and rejects as exactly that. A fix is "done"
  only when a verifier approved it AND a PR exists.
