---
description: Implement the next feature from the research backlog — repairs misnamed research files, verifies the PRD against real code, interviews the owner in plain Croatian one feature at a time, then builds it on a branch with a PR. Multi-agent.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent, Task, AskUserQuestion, WebFetch, TaskCreate, TaskUpdate, TaskList
user-invocable: true
---

# /scrapalot:competitive-impl

You are the **orchestrator** that turns research documents into shipped features. The
analysis commands write plans; this one spends them.

**Read first — it is the law, and this file deliberately does not restate it:**
`${CLAUDE_PLUGIN_ROOT}/skills/competitive-impl/SKILL.md`

Home: `${CLAUDE_PROJECT_DIR}/.claude/competitive-impl/` (`STATE.md`, and `INVENTORY.md` which the
cartographer regenerates).

Your five agents:

| Agent | Role |
|---|---|
| `scrapalot:prd-cartographer` | Read-only. Finds every research artifact in the workspace, checks it against the naming law, returns the queue and the strays. |
| `scrapalot:prd-auditor` | Read-only. Checks one group of features against the actual code and returns evidence-backed state. Runs 2–5 in parallel. |
| `scrapalot:prd-explainer` | Writes the plain-Croatian card for ONE feature from the auditor's findings. You present it verbatim. |
| `scrapalot:prd-builder` | Maker. Implements ONE approved feature in a worktree, writes tests, commits. Never pushes. |
| `scrapalot:prd-reviewer` | Read-only. Reviews the builder's diff against the approved scope and votes APPROVE / REJECT. |

`$ARGUMENTS` may be: empty (pick per §3), a slug or product name, a category number, a
plain description of a feature, or one of the sub-commands below.

| Sub-command | Effect |
|---|---|
| `inventory` | Phase 1 only — map + repair the research files, print the queue, stop. |
| `status` | Print `STATE.md` and the open queue in plain language. Nothing else. |
| `resume` | Skip selection, continue whatever `STATE.md` has in flight. |
| `build` | Skip the interview, build the already-approved features of the in-flight item. |

---

## Phase 0 — orient

Read `STATE.md`. Check for other live sessions (`ps aux | grep -c '[c]laude'`) and any CI
run in flight (`gh -R sime2408/<repo> run list --limit 1`) before touching a repo — both
change how you work, neither stops you.

A run that changes nothing because the queue is decided and merged is a **success**. Say
so and stop. Never invent work.

---

## Phase 1 — map and repair the research files

Launch `scrapalot:prd-cartographer`. It returns: the open queue, the half-open items, the
strays, and the dead links.

**Then repair, in this pass, not later:**

- Rename every stray to its canonical path and fix every link that pointed at the old name.
- Rescue anything that exists only inside `.claude/worktrees/*` — CI deletes those.
- Delete strays confirmed to be duplicates of a canonical file.
- Fix dead links in the two `README.md` indexes.

Repairs to files inside a repo follow §7 — worktree, branch, PR, never a push to `main`.
Repairs under `${CLAUDE_PROJECT_DIR}/.claude/` are direct; that tree is not a git repository.

Report the repair in one plain sentence per file. If nothing was misplaced, say that — it
is the outcome we want, and stating it is how we learn the law is holding.

With `inventory`, stop here.

---

## Phase 2 — pick the item

Follow SKILL §3. When it comes down to the owner's choice, this is **two turns, not one**,
and you write neither of them yourself:

1. Launch `scrapalot:prd-explainer` for a **context turn + choice card** (SKILL §5.0, §5.2c).
   It must say where these candidates came from without naming a document or a date, what is
   actually true in that area today, and why the choice is in front of the owner now. Present
   it verbatim and **end the turn**.
2. Next turn only: one `AskUserQuestion` whose stem and options the explainer also wrote.
   Recommendation marked `(Preporuka)`.

Never hand-write this question. The one time it was improvised it referenced a decision the
owner did not remember and offered "fix the broken things" without saying what was broken;
it was rejected outright.

Write the pick into `STATE.md` before going on.

---

## Phase 3 — verify against the code

Split the item's features into 2–5 disjoint groups and launch one `scrapalot:prd-auditor`
per group, in parallel, in a single message. Every claim comes back with evidence
(SKILL §4).

Then:

- Mark features that already ship as done **in the document**, with their evidence. They
  never reach the owner as a question — one line each in your report: "this already
  exists, here is where."
- Order what remains: the cheapest thing that gives a visible result first.

Report the shape of it in plain Croatian before any question — via the explainer, as a
context turn (SKILL §5.0): where this came from, what is genuinely true in that area today,
what turned out to be already built, and what is actually left. Counts are not a report:
"deset stvari" tells the owner nothing, "danas ovo radi ovako, a ovo se ne može" does.

---

## Phase 4 — the interview, one feature at a time

For each undecided feature, in order:

1. **Explanation turn.** Launch `scrapalot:prd-explainer` with that feature's audit
   findings. Present its card **verbatim** — do not "improve" it, that is where the jargon
   leaks back in. End the turn with *"Javi kad si spreman za odluku."* **No question tool
   in this turn.**
2. **Decision turn.** After the owner replies: one `AskUserQuestion`, self-contained,
   options per SKILL §5.3, recommendation marked.
   - Asked to explain it differently → back to step 1 with a different frame (an everyday
     metaphor, not a second technical pass). No limit on how often.
   - Accepted with a change → restate the change in one sentence and confirm it before it
     becomes scope.
3. **Branch drilling.** For an accepted feature, walk SKILL §5.4's branch table one
   question per turn, each with your recommended answer. **Answer from the codebase
   whenever the codebase can answer** and say so in one line instead of asking. Stop when
   nothing undecided would change a line of code.
4. **Record it** — Decision Log row in the document, and `STATE.md`. Immediately, before
   the next feature.

Never bundle features. Never bundle explanation and question. Never carry a decision only
in the conversation.

---

## Phase 5 — build

**Defects first, and explained the same way.** A defect the audit surfaced is fixed under
the fix-immediately rule without waiting for approval — but the owner still gets a
`scrapalot:prd-explainer` **defect card** (SKILL §5.2b) telling them what happens on screen,
what should happen, and how we know. Fixing something and reporting only that it is fixed is
the same failure as asking a question with no context. Anything that is a product decision
rather than a plain defect — deleting a button versus building what it promises — goes
through the full interview, never decided unilaterally.

### The gate ledger — one per feature, opened before the builder starts

**Read `.claude/gates/CONTRACT.md` and follow it.** "No tests, not done" and
"Chrome before Playwright" are in the hard rules below and have been since the
command was written; they were still only sentences. This is where they become a
thing a command settles.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py open \
    --run feat-<slug> --command /scrapalot:competitive-impl \
    --scope "<feature as the owner approved it, one line>"
```

Fill in the real paths — a placeholder left in a `CHECK:` is a gate that proves
nothing:

```markdown
- [ ] G1: integration tests for this feature pass
  CHECK: docker exec scrapalot-chat python -m pytest tests/integration/<test_file>.py -q
  EXPECT: /\d+ passed/
  TIMEOUT: 1200
  EVIDENCE: pending
- [ ] G2: the E2E spec for this feature passes
  CHECK: npx playwright test tests/e2e/<spec>.spec.ts --reporter=line
  CWD: /opt/scrapalot/scrapalot-ui
  EXPECT: /\d+ passed/
  TIMEOUT: 1800
  EVIDENCE: pending
- [ ] G3: types check and the UI build is clean
  CHECK: npx tsc -p tsconfig.app.json --noEmit && scrapalot-build npm run build
  CWD: /opt/scrapalot/scrapalot-ui
  EXPECT: /built in/
  TIMEOUT: 1200
  EVIDENCE: pending
- [ ] G4: the feature was driven in Chrome and the screenshot shows the promised behaviour
  EVIDENCE: pending
- [ ] G5: the reviewer approved this diff against the approved scope
  EVIDENCE: pending
- [ ] G6: the PR is open against main and assigned to sime2408
  CHECK: gh --repo sime2408/<subproject> pr view <num> --json state,baseRefName,assignees -q '.state + " " + .baseRefName + " " + (.assignees | map(.login) | join(","))'
  EXPECT: OPEN main sime2408
  EVIDENCE: pending
- [ ] G7: CI is green on that PR
  CHECK: gh --repo sime2408/<subproject> run list --branch <branch> --limit 1 --json conclusion -q '.[0].conclusion'
  EXPECT: success
  TIMEOUT: 1200
  EVIDENCE: pending
- [ ] G8: the Decision Log row carries the PR number, and STATE.md is updated
  EVIDENCE: pending
```

G1–G3 are the ones that cannot be argued with, and they are the reason this
ledger exists: a feature whose suites were never run has no green box to show,
whatever the builder reported. G2 is skipped only for work with no UI surface at
all, and then it is `ABANDON: G2 backend-only change, no UI surface` — written
down, not assumed. G4 stays manual because pixels are the proof and the evidence
line carries the screenshot path.

While iterating, check one gate at a time (`--only G1`) rather than re-running
the whole suite set; the full `run` before the report is the one that counts.

Then, per approved feature, smallest first (SKILL §7):

1. Worktree + feature branch in the right subproject.
2. `scrapalot:prd-builder` — implement, test, commit. Hand it the **approved scope as the
   owner agreed it**, including every branch answer from Phase 4.3.
3. `scrapalot:prd-reviewer` — diff review, APPROVE or REJECT. Give it the diff and the
   approved scope, never the builder's account of the work.
4. `REJECT` → the objection alone goes back to the builder. Approve, or two different
   attempts hitting the same objection → stop and bring it to the owner.
5. `APPROVE` → push the branch, open the PR against `main` assigned to `sime2408`, poll CI
   inline until green, verify UI work in the browser.
6. Update the Decision Log row with the PR number and `STATE.md`.
7. Run the feature's ledger and close it — a feature is not finished while a gate is open:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py run gates/active/feat-<slug>.md
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py close gates/active/feat-<slug>.md
   ```

Between features, tell the owner what landed in one plain sentence and go on. Ask before
starting a feature only if its answer would change what you build.

---

## Phase 6 — close out

When every feature of the item is decided and every accepted one is merged, run SKILL §8
in full: record → document → delete the artifact → fix the index → update the tracker →
update `PRD_STATUS.md` → clear `STATE.md`. One PR.

Then report, in plain Croatian: what the owner now has that they did not have before, what
was skipped and why, what is still open. No file paths, no PR numbers as the main content —
those go at the bottom if at all.

---

## Hard rules (they bind every phase)

- Plain Croatian to the owner. The banned vocabulary in SKILL §5.1 is a list, not a hint.
- The context turn (SKILL §5.0) precedes every question, including the item choice.
- The explainer writes every user-facing word, options included. You present it verbatim.
- Never appeal to a date, a past decision or a document the owner has not read this minute.
- Never call something broken without the symptom in clicks and the proof.
- Explanation and question are separate turns. Always.
- One feature at a time. One PR at a time. Smallest step first.
- Branch + PR only — never push `main`, never merge, PRs assigned to `sime2408`.
- Worktree from the first edit, in every `/opt/scrapalot` repo.
- No tests, not done. Chrome before Playwright. Both are gates in the feature
  ledger (`.claude/gates/CONTRACT.md`), and the ledger — not a summary — is what
  says a feature is finished.
- Never ask about something that already ships. Check, then say it exists.
- Never claim a gap without a grep.
- Never delete an artifact before its record is written and its knowledge relocated.
- A run that finds nothing to do is a success. Report it as one.
