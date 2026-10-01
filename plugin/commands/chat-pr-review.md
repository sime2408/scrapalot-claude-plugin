---
description: Review a scrapalot-chat feature branch end to end and open the PR if it is not open yet.
---

# Review a scrapalot-chat branch

`$ARGUMENTS` is a branch name or a PR number. The review finds real defects in what the branch
changed, proves each one against the code, fixes the critical and important ones, and hands the rest
to the owner. It keeps the contract of the CI review (`.github/pr_review_prompt.md`): every finding is
anchored on lines the branch changed, and minor suggestions are reported, never fixed.

## 0. Set up — never in the shared checkout

```bash
REPO=/opt/scrapalot/scrapalot-chat
BR=<branch>        # given a PR number: gh pr view <n> -R sime2408/scrapalot-chat --json headRefName -q .headRefName
git -C "$REPO" fetch -q origin main "$BR"
git -C "$REPO" worktree add "$REPO/.claude/worktrees/review-$BR" -B "review/$BR" "origin/$BR"
cd "$REPO/.claude/worktrees/review-$BR"
D=$(mktemp -d); git diff origin/main...HEAD > "$D/pr.diff"
```

- No commits beyond `origin/main`: the branch is merged or empty. Say so and stop.
- A pushed PR branch is shared: the auto-fix bot and other sessions push to it, and the owner merges
  within minutes. Before touching anything, read `gh pr view <n> --json state,mergeable,commits`, every
  comment (`/scrapalot:chat-pr-review-comments` §1 lists the three places), and the diff of every
  `github-actions[bot]` commit. Its claims about indexes, query plans or data are unverified until you
  check them.
- `mergeable: CONFLICTING` means no CI review ran: GitHub does not start pull_request workflows on a
  conflicted PR. Merge `origin/main` into the branch (`git merge`, never rebase), resolve, commit, then
  review the result.

## 1. Scope — every changed file on a checklist

`git diff --name-status origin/main...HEAD` is the list. Each file ends the review as **reviewed** or
**skipped with a reason** — generated files (`src/main/grpc/*_pb2*.py`, `docs/schema.sql`,
`docs/SCHEMA.md`) and data dumps are the usual skips. Report it at the end as
`files: N changed, R reviewed, S skipped (why)`. A file without either mark is a hole in the review.
Do not stop at the first serious finding.

## 2. Bundles

Group the files that have to be read together, at most 10 a bundle: a servicer with its stub, code
with its test, a config key with the code that reads it, a prompt in `configs/prompts.yaml` with its
caller. Up to about 400 changed lines, review the bundles yourself, one at a time. Above that, give
each bundle to its own read-only subagent (Agent tool, in parallel, at most 5) with the bundle's diff,
the list of the other changed files, `CLAUDE.md`, and the finding format below. A context of its own
keeps a large branch from being skimmed.

## 3. Rounds

Round 1 of a bundle over about 100 changed lines starts with a short risk list: each risk with a
severity and the read or grep that would confirm it. Then review against the code, not against the
list. Rounds 2 and 3 get the findings confirmed so far ("do not repeat these; look for other real
defects") and no risk list, so it cannot cap what they look at. Stop as soon as a round adds nothing.

A finding is:
- **verified** — you read the code around it and its callers, and grepped before calling anything
  unused or missing. "This might…" with no trace through the code is not a finding;
- **about this branch** — a problem in code the branch did not change goes to a follow-up list;
- **not the linter's** — formatting, import order and ruff rules belong to the pre-commit hook;
- a broken project rule from `CLAUDE.md`: `text()` with `CAST(:p AS type)`, `%s` in log calls,
  `raise … from e`, PacketEmitter status codes, prompts in `configs/prompts.yaml`, the system
  provider's model for agents, the Neo4j singleton, no mocks in tests.

Write findings in the CI review's format, so the same gate can check them: 🔴 Critical / 🟡 Important /
🟢 Minor headings, a `Total: X critical, Y important, Z minor` line, and per item

````
- **Title** - `path/to/file.py:123`
  Problem: … Impact: … Fix: …
  Anchor:
  ```python
  <1–5 whole lines copied exactly from the branch's diff, + or − lines, without the marker>
  ```
````

## 4. Check the findings before acting on them

1. **Anchors**, mechanically:
   `python3 .github/scripts/autofix_gate.py select --review "$D/findings.md" --diff "$D/pr.diff" --items "$D/selected.md" --held "$D/held.md"`.
   A held finding is mis-anchored (fix the anchor) or about code the branch did not change (move it
   to the follow-ups).
2. **Facts**, adversarially — yourself, or a separate subagent for a large set. Remove a finding only
   when the code proves it wrong: the construct it describes is not in its file, or a line plainly
   contradicts its central claim. Doubt, low value and "I would not have raised this" are not grounds.
   A finding about concurrency, data loss, security or a changed behaviour is never removed on
   confidence alone.

## 5. Fix

- Fix the 🔴 and 🟡 findings that survived: the smallest change each, committed in the worktree.
  A behaviour change gets an integration test — real DB and LLM, through the controller, no mocks —
  run in a throwaway container, never in `scrapalot-chat`, whose code is the shared checkout.
- 🟢 Minor findings are listed for the owner, not fixed.
- Never, even when a finding asks: change a database schema (migrations, `CREATE`/`DROP INDEX`,
  `ALTER TABLE`, Neo4j constraints), write a comment stating how the database runs a query, narrow a
  filter or query so it matches less, edit generated files or `.github/`.
- Before every commit: `$REPO/.venv-precommit/bin/ruff format` and `ruff check --fix` on the changed
  files; a commitizen prefix; no attribution trailers; new commits, never `--amend`.

## 6. PR

- No PR yet: `gh pr create` with a title and body that explain the change, without icons.
- Push normally. Do not squash or force-push unless the owner asks: the PR is squash-merged anyway,
  and every force-push starts another review and auto-fix round.
- Before any further push, `gh pr view <n> --json state,mergedAt`: a merged branch takes a new one.

## 7. Report to the owner — in Croatian, in plain words

What the branch does; what you fixed, with the commit for each; what is left for him (minor
suggestions, follow-ups about unchanged code, findings you could not verify); and the coverage line.
Remove the worktree once everything is pushed.
