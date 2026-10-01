---
description: Read the review comments on a scrapalot-chat PR and fix the code until each one is resolved.
---

# Resolve the review comments on a scrapalot-chat PR

`$ARGUMENTS` is a branch name or a PR number.

## 0. Set up — never in the shared checkout

The worktree recipe of `/scrapalot:chat-pr-review` §0. Then read
`gh pr view <n> --json state,mergeable,commits` and the diff of every `github-actions[bot]` commit:
the auto-fix bot pushes to this branch, and what it changed is part of what you answer for.

## 1. Collect every comment — they live in three places

```bash
N=<pr>; R=sime2408/scrapalot-chat
gh api --paginate "repos/$R/pulls/$N/comments"  | jq '.[] | {id, user: .user.login, path, line, original_line, in_reply_to_id, body}'   # inline
gh api --paginate "repos/$R/issues/$N/comments" | jq '.[] | {id, user: .user.login, created_at, body}'                                   # conversation
gh api --paginate "repos/$R/pulls/$N/reviews"   | jq '.[] | {id, user: .user.login, state, body}'                                        # submitted reviews
```

- The CI review is a `claude[bot]` conversation comment, not an inline one, and only its latest
  version counts. A `github-actions[bot]` comment listing items "left for you" is the auto-fix job
  handing findings to a human: they belong to this work.
- Skip what a later commit or reply has already settled.

## 2. One comment at a time

Print `(n). From <user> on <file>:<line> — <body>`, then:

1. **Find the code by what the comment quotes**, not only by its line number: lines drift as the
   branch moves. A comment that no longer applies to the current code is reported as such.
2. **Check the claim before changing anything.** A comment can be wrong — about an index, a query
   plan, what a function returns. When the code or a read-only query proves it wrong, do not "fix" it:
   reply on the PR with the evidence.
3. **Unclear what it wants?** Do not guess; list it for the owner.
4. Otherwise make the smallest change that resolves it, before moving to the next comment.

The never-list of `/scrapalot:chat-pr-review` §5 applies here too: no schema changes, no comments
claiming how the database runs a query, no narrowed filters, no generated files, nothing under
`.github/`.

## 3. Verify, commit, push

Ruff on the changed files, an integration test in a throwaway container for any behaviour change,
new commits without attribution trailers, and a normal push. Do not squash or force-push unless the
owner asks: the PR is squash-merged anyway, and a force-push starts another review and auto-fix round.

## 4. Report — to the owner, in Croatian, in plain words

Which comments are resolved (with the commit), which you answered instead of changing code and why,
and which need him. No icons in comments or summaries.
