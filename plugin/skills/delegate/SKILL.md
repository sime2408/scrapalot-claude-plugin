---
name: delegate
description: Hand a self-contained, verifiable task to a cheaper subscription instead of spending Claude Max quota — Codex on a ChatGPT plan, or a flat coding plan (GLM, Qwen and the like) through its Claude Code profile. Use when the work is mechanical and the result can be checked by a command or a diff: bulk renames, boilerplate tests, i18n key sync, doc formatting, log triage, dependency bumps, repetitive edits across many files. Not for architecture, cross-service debugging, production data, or anything that needs project judgment.
---

# Delegate the mechanical half of the work

Claude Max is usually the scarce resource. Other subscriptions — a ChatGPT plan,
flat coding plans — are separate pools that often sit idle. Any task a cheaper
model can finish correctly, and whose result can be verified by running
something, belongs on one of them.

Quality is not traded away here: **the delegate produces a proposal, you own the
result.** You read the diff, you run the check, you commit. A delegate never
commits, never pushes, never merges, and never touches production.

## Pick the backend

| Task | Backend | Why |
|---|---|---|
| Planning, code review, architecture, a bug spanning services, anything touching production | Keep it on Claude — Opus, or Sonnet with `/advisor opus` | This is the judgment the plan is paid for. Delegating costs more than it saves once the result has to be redone |
| Well-specified implementation that still needs project context — repo conventions, earlier decisions | `codex exec` with the mid tier at `medium` effort | Codex keeps project context when it is set up to read the same instructions and memory as Claude Code, for example `~/.codex/AGENTS.md` pointing at your `CLAUDE.md` and the same memory directory or MCP server. Where it is not, the brief has to carry that context |
| Repetitive execution — running scripts, log sweeps, boilerplate tests, mass mechanical edits | `codex exec` with the cheapest tier at `low` effort, raised to `high` only if it comes back wrong | On a ChatGPT Plus plan the cheapest tier allows roughly twenty-five times as many messages per 5-hour window as the top tier |
| Bulk work whose whole context fits in the brief, or overflow once the ChatGPT window is spent | A Claude Code profile on a flat coding plan: `${CLAUDE_PROJECT_DIR}/.claude/settings.local.<vendor>.json`, run with `claude --settings <profile>` or an alias for it | Same harness and tools, billed to that plan instead of Max |

Which vendors are set up changes as plans are bought and dropped, so list the
profiles before choosing one instead of assuming a vendor is still there.

## The order

Delegated work goes down this ladder, and only moves a rung when the rung above
refuses:

1. **Codex on the ChatGPT plan** takes every simple task first.
2. **The flat coding-plan profiles**, in the order the project's `CLAUDE.md`
   names. If it names none, ask the owner once rather than picking. A profile
   takes over only when the rung above answers with a usage or rate limit, not a
   problem with the task, and it gets the same brief, unchanged.
3. **Nobody.** When every rung is spent, say so and stop delegating. Do not
   quietly move the work back onto Claude Max, and never reach for the expensive
   Codex tiers as a substitute — that is the spend this ladder exists to avoid.

A refusal that is about the task, not the quota, means the brief was wrong. Fix
the brief rather than moving down a rung. Note the rung in the log line, so the
record shows how often each plan runs out.

Never send delegated work to the top Codex tiers. A working day on the largest
model can use up a week of a ChatGPT Plus plan, which is the whole reason the
task is leaving Claude. Current tiers, their per-plan message limits and their
credit cost: https://developers.openai.com/codex/pricing.

Reasoning effort on Codex is `none`, `low`, `medium`, `high` or `xhigh`, passed
as `-c model_reasoning_effort=…`. Start low and raise it rather than the other
way round; a cheap model at high effort is usually still cheaper than the next
tier up.

Check the profile is on a flat plan and not a pay-per-token key before using it.
A subscription and the vendor's pay-per-token API usually live on different
endpoints, and only one of them is covered by the plan. If you cannot tell which
the profile holds, ask instead of spending someone's money. A profile whose key
has expired fails with an authentication error on the first call — report it,
do not fall back to Claude silently.

## Run it

Always inside a git worktree, never in a checkout that other sessions share: a
delegate that edits a shared tree can land its changes in someone else's commit.

```bash
# Codex on the ChatGPT plan
codex exec -m <model> -c model_reasoning_effort=low -s workspace-write \
  -C <worktree> "<brief>" < /dev/null

# Claude Code on a flat coding plan
(cd <worktree> && claude --settings "${CLAUDE_PROJECT_DIR}/.claude/settings.local.<vendor>.json" \
   -p "<brief>" --permission-mode acceptEdits)
```

`codex exec` reads stdin when it is not redirected, so a call without
`< /dev/null` hangs. Outside a git repository it also needs
`--skip-git-repo-check`. Codex opens a smaller context window than the model's
advertised maximum unless it is raised in its config, so keep briefs
self-contained rather than pointing it at a large tree.

## Write the brief

A delegate knows nothing about this conversation. Every brief carries five
things:

1. The exact files or directories, as paths.
2. What "done" means, as a command it can run: a test file, a build, a `grep`
   that has to come back empty.
3. The constraints it must not break — the rules from the CLAUDE.md that governs
   those files, named explicitly, because a different model will not weigh them
   the way you do.
4. What to report back: the diff and the output of the check, nothing else.
5. The sentence "You are a delegate: do this task yourself and do not hand it to
   another agent or subscription." A delegate reads the same `CLAUDE.md` files,
   including any rule that tells a Max session to delegate, and without this
   line it can pass the task on to itself.

A task you cannot state in points 1 to 4 is not ready to delegate. That is the
signal it still needs judgment.

## Never delegate

- Anything that writes to production: databases, caches, the running services,
  or copying files into a live container.
- Database migrations, secrets, deletions, gate state under `.claude/gates/`,
  and another person's documents.
- Committing, pushing, opening or merging a PR.
- Work whose acceptance criteria you cannot express as a command.

## Close the loop

Read the diff yourself and run the check yourself. If the delegate needs more
than one correction round, take the task back: a second round usually costs more
than doing it yourself would have.

Append one line per delegated task to
`${CLAUDE_PROJECT_DIR}/.claude/delegate-log.tsv` — date, backend, task, outcome
(accepted, corrected, or taken back). That log is the evidence for which task
classes are safe to delegate and whether delegation is paying for itself.
