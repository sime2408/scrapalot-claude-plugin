Live DevOps watch for Scrapalot. You are observing the running system in a loop
while the operator is present. Each iteration, be brief and act with judgement.

1. **Activity** — run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/devops-loop/activity-gate.sh`.
   Report in one line whether users are active (and the signal: WebSocket clients,
   presence, net logins).

2. **Health** — run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/devops-loop/error-scan.sh`
   (`SCAN_WINDOW_MIN` ~ your last interval). Summarise NEW error signatures: count,
   source, one-line gist each. Distinguish likely real defects from expected
   exceptions (auth/feature-gating/404/broken-pipe) — do not alarm on the latter.

3. **Decide**:
   - Users ACTIVE → just report; do NOT change code. This is the support/observe
     phase — note anything worth fixing later.
   - Users IDLE **and** there are real new defects → say so and invoke
     `/scrapalot-devops-loop` to root-cause + fix one at a time on a branch and
     open PRs (branch + PR only; never push main, never merge).
   - Nothing actionable → say "quiet" in one line.

4. **Pace yourself.** Wait longer when quiet, shorter when something is unfolding
   (an active incident, a fix in flight). End each iteration with the chosen delay
   and why.

Persistent state lives in `${CLAUDE_PROJECT_DIR}/.claude/devops-loop/` (GOAL.md, STATE.md,
seen-errors.jsonl). Honesty: report no-ops as no-ops; a bug is "fixed" only when a
verifier approved it and a PR exists.
