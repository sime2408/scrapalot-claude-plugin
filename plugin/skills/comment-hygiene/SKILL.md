---
name: comment-hygiene
description: The rule for what a Scrapalot code comment may contain, and the procedure for cleaning up when it does not. Use when writing or reviewing comments and docstrings, or when sweeping a repo for commit/PR references, dates, owner attributions, corpus counts, or variable external data such as model names. Encodes what the corpus-wide cleanups learned, including the mistakes.
---

# A comment says what is true, not when someone learned it

Several kinds of content keep appearing in comments across the Scrapalot repos.
None of them tells a reader of the file anything they can act on, and each has
already cost a corpus-wide cleanup.

## The rule

**No individual commit SHA or PR number.** Keep the reasoning, drop the
identifier. The reader is in the file because they want to understand the code;
sending them to `git show` for the explanation defeats the comment.

```python
# before
# Strip TOC dot-leader runs (Tier 3.5 parity, commit 39f58ce).
# after
# Strip TOC dot-leader runs (Tier 3.5 parity).

# before
# Gate mirrors the `_numbered_space_headings` guard PR #184 added to
# after
# Gate mirrors the `_numbered_space_headings` guard in
```

**No dates.** A measurement either still holds — in which case the date is
noise — or it no longer holds, in which case the date is a false reassurance
that someone checked. Neither earns the space.

```python
# before
# Measured 2026-08-21 on doc 2c5a432f (Alchemy Journal Vol 2 no 6): "By Lynn
# after
# Measured on doc 2c5a432f (Alchemy Journal Vol 2 no 6): "By Lynn
```

**No owner attribution.** A decision explains itself by its reason. Who made it
is in the history, and naming them invites a reader to treat the comment as
somebody's opinion rather than the system's contract.

```python
# before
# Currently ON (owner, 2026-08-16): parse before graph.
# DO NOT resume without the owner saying so.
# after
# Currently ON: parse before graph.
# DO NOT resume without an explicit decision to.
```

**No count of the corpus.** "draining 5,869 pending graphs", "1,555 of the
5,597 documents", "162 documents carry such lines" — every one of these is true
for an afternoon. The next ingest makes the comment a lie, and nothing will
flag it. State the shape of the finding, not its size, and let the reader run
the query if they need the number.

```python
# before
# so draining 5,869 pending graphs ahead of the corpus-wide parse sweep
# after
# so draining the pending graphs ahead of the corpus-wide parse sweep

# before
# Measured: 1,555 of the 5,597 documents holding more than 5,000 characters
# after
# Measured: most documents holding more than 5,000 characters
```

**No variable external data — model names above all.** Which model a
provider serves, what its `/models` endpoint lists, which alias routes where,
when a model retires, how long one call takes, how large a context window is,
which version of a tool is current: all of it runs on somebody else's release
schedule. Today it is one model, tomorrow another, and a comment that names it
turns into a confident lie the day the provider moves — nothing flags it, and
the reader trusts it because it sounds measured. State the contract the code
relies on, and let the value live where it is meant to change: the config
value, the database row, the provider's own listing.

```yaml
# before
# (deepseek-flash for both tiers). Measured against the live API on
# 2026-09-12: /models lists only `deepseek-flash` and `deepseek-v4-pro`,
# and every legacy alias — `deepseek-chat`, `deepseek-v4-flash` — comes
# back served by `deepseek-flash`. `deepseek-v4-pro` is retired on
# 2026-09-14 12:00 Beijing (04:00 UTC), after which it routes to Flash.
# after
# The running model is whatever that row names; which ids the provider
# serves is the provider's own /models listing, not something a comment
# can keep current.

# before
      # tool-calling tier (deepseek-flash) — reliable structured/tool calls
# after
      # tool-calling tier — reliable structured/tool calls
```

The config value carrying a model id is not the problem — it is the one place
the id is supposed to be, and where the next change will be made. The problem
is the comment beside it repeating the value, or narrating what the provider
did last week. A format example is no exception:
`model_name="claude-opus-4-5-20251101"` in a comment goes stale just as fast —
write `model_name="<the provider's model id>"`.

**No operational runbook.** Policy — "DO NOT RESUME without…", what a flag
costs to lift, what happened the last time someone lifted it — is not something
the file's reader acts on while reading the file. It is something the *agent*
needs before it touches the system, so it belongs where the agent reads its
rules: the subproject `CLAUDE.md`, the relevant `docs/README_*.md`, or this
plugin. Leave the code carrying the flag and one line of reason, and point at
the rule.

```yaml
# before: twelve lines of policy, incident history and cost estimate in the workflow
# after
          # Graph backfill stays paused while the parse sweep owns the box: a
          # graph built on a badly parsed book is torn down and rebuilt once
          # the parse defect is fixed. Lifting it is a deliberate decision —
          # see docs/README_BACKGROUND_JOBS.md.
          GRAPH_BACKFILL_PAUSED=true
```

## What is exempt

These are *functional* — deleting them breaks or opens something:

- API version headers: `anthropic-version`, `Notion-Version`, XMP namespaces
- Date-filter syntax examples in prompts (`created_at: "2025-01-01"`)
- Model ids that embed a date, where the id is a **value** the code sends
  (`claude-haiku-4-5-20251001` as a config default or a request field) — the
  date rule does not strip it. In a narrative comment the same id is variable
  external data and goes (see above).
- Real filenames (`libgen_2025-06-03.rar`), `BUILD_DATE` defaults
- A workflow's author allowlist, PR assignee, or git remote — the GitHub
  username there is authorization and routing, not attribution
- Synthetic SHAs that are **test fixture data**: the regex-grep suite asks
  "where does the doc mention `7f3a9c1`?" to exercise the SHA-shaped-query
  routing rule. Deleting those breaks the tests.
- `_typos.toml` allowlist entries, which exist precisely because a SHA string
  appears somewhere the spell-checker reads

## Cleaning up: what the sweeps learned

**Resolve hex tokens against the object database, never by shape.** In
scrapalot-chat a 7-character hex token in a comment is a git short SHA and an
8-character one is a corpus document id — `b23120b2` is *World Without Cancer*.
Deleting by pattern destroys the parser evidence the comments exist to record.

```bash
grep -rIoh -E '\b[0-9a-f]{7,40}\b' src tests scripts | sort -u > tokens.txt
git cat-file --batch-check < tokens.txt      # "commit" = real, "missing" = not ours
```

**Do not regex-strip dates.** This was tried and reverted. A rule wide enough
to catch the 300-odd shapes produced `Observed on:`, `The default was "true"
until, which made`, `#/24`, `// Last Updated:` and `# worker.` — comments worse
than the dates they removed. Two rules are narrow enough to be safe:

- a parenthetical holding *only* a date, and not at the start of a line
- a measurement verb whose date sits between it and its object:
  `Measured 2026-08-21 on doc X` → `Measured on doc X`, `Measured 2026-08-31:`
  → `Measured:`

Everything else — `until <date>`, `oldest <date>`, `opened <date>`, a date that
*is* the sentence subject — needs the sentence rewritten by hand. Budget for
that rather than automating it.

**Model names: keep the value, rewrite the narration.** Grep comments for
provider and model-family names, then read every hit. A config default or a
request field carrying the id stays — it is the value. A comment repeating it
beside the value, narrating what a provider's listing held, or stamping a
retirement date or a call latency gets rewritten to the contract the code
relies on.

```bash
grep -rnE '#.*(deepseek|gpt-|claude-|llama|qwen|gemini|mistral|glm|kimi)' \
  configs src scripts .github docker-scrapalot
```

**Fix the generator, not only the output.** Alembic's `script.py.mako`,
`migration_template.py.mako` and `create_migration.py` each stamped
`Create Date:` into every migration, so stripping the 104 existing headers
without touching the templates would have regressed on the next migration.
Removing the field also orphaned a `timestamp` variable and its `datetime`
import — check for those.

**Re-wrap what you shorten.** Removing a clause mid-paragraph leaves a ragged
line. Check that no line you touched exceeds the width of the paragraph around
it, and that a docstring's first line still reads as a summary.

## Sweep every directory, including the ones that are not code

`.github/` is the one that gets missed, and it is full of exactly this material:
workflow files carry long explanatory comment blocks about outages, deploys and
runners. A sweep that greps `src tests scripts configs` and stops leaves them
untouched and still reports clean. `alembic/`, `docker-scrapalot/` and the repo
root's loose `*.py` / `*.toml` are the same trap.

Two mechanical reasons the miss is easy to make: a shell glob listing
directories will not expand a dotted one, and an `--exclude-dir=.git` sitting in
the same command reads as "skip anything git-ish" to whoever skims it later.
Name `.github` explicitly, then verify by grepping it on its own.

Re-run the whole sweep after merging the base branch, too. Work that landed
while the branch sat brings its own dates and counts, and a branch claiming
"no narrative dates remain" stops being true the moment it merges with a base
that has some.

## Verifying a sweep

```bash
python3 -m compileall -q $(git diff --name-only | grep '\.py$')
python3 -c "import yaml,glob;[yaml.safe_load(open(f)) for f in glob.glob('configs/*.yaml')]"
docker run --rm --name scrapalot-ruff-<topic> --network none \
  -v "$PWD":/w:ro -w /w scrapalot-chat:latest ruff check --no-cache src tests scripts
```

The pre-commit hook rewrites `.secrets.baseline` whenever line numbers shift,
which a comment sweep always does. Expect the first commit to fail with
"files were modified by this hook", `git add .secrets.baseline`, and commit again.
