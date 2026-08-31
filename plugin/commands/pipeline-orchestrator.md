---
description: "End-to-end document processing orchestrator with OOM protection"
allowed-tools: Agent, Bash, Read, Edit, Grep, Glob, Write, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__resize_window, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__computer, mcp__claude-in-chrome__find, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__javascript_tool, mcp__claude-in-chrome__gif_creator
---

Launch the `scrapalot:pipeline-orchestrator` agent to handle the user's request.

The pipeline orchestrator monitors: upload → parse → chunk → embed → Neo4j graph → RAG quality.
It tracks logs across ALL containers (gw, backend, chat, workers), detects OOM kills, disk pressure, and adapts processing.

## When to use

- Document upload and processing verification
- Full pipeline debugging (parse → embed → graph → RAG)
- Neo4j graph hierarchy validation (Book → Chapter → Section → Chunk → Entity)
- RAG quality benchmarking on a collection
- Container health monitoring and OOM recovery
- After changes to chunking, embedding, or graph code

## Bug Fix Strategy

When errors occur during processing:
1. **Fix immediately** — edit source code as soon as an error is detected
2. **DO NOT commit** — let the pipeline keep running while you fix
3. **After pipeline finishes** — commit all fixes in one batch, push to git
4. **Report to user** — list completed docs, failed docs (with reasons), and whether re-upload is needed

## Permissions

Auto-handled by the orchestrator (no user round-trip required):
- Read-only log tailing across containers (`docker logs -f scrapalot-gw`,
  `scrapalot-backend`, `scrapalot-chat`, `scrapalot-workers`).
- pgvector / Neo4j read queries for progress and topology inspection.
- Flower (`:5555`) task-status reads.
- Edit source files for bug fixes detected during the run (commit + push deferred
  to the end-of-pipeline batch per "Bug Fix Strategy" above).
- Browser inspection via Chrome MCP for UI verification (read_page, get_page_text,
  find — read-only DOM inspection).

Forbidden without explicit user approval (see Human Gates):
- `docker restart <container>` — container restart drops in-flight requests and
  invalidates uploads-in-progress.
- `docker update --cpus=N <container>` — runtime CPU re-allocation. Mass
  recomputes can starve user-facing containers (`feedback_cpu_isolation_not_automatic`).
- Worker scale-down or pause (`docker exec scrapalot-workers celery control
  cancel_consumer`).
- Mass document delete / `DELETE FROM langchain_pg_embedding ...` rollbacks.
- Bulk Celery dispatch (>5 docs in one loop) — PreToolUse guardrail at
  `${CLAUDE_PLUGIN_ROOT}/hooks/postprocess_guardrail.sh` will block; re-route
  through `/scrapalot:postprocess-parse` (TWO docs per invocation).
- `git push --force` or branch deletion. End-of-pipeline batch commit uses
  standard push only.
- Modifying production `.env` files (`scrapalot-chat/docker-scrapalot/.env`)
  during a run — restart-only change, will interrupt processing.

Tools (frontmatter `allowed-tools`): Agent, Bash, Read, Edit, Grep, Glob, Write,
plus chrome MCP (read-only DOM inspection for UI verification).

## Human Gates

| Trigger | Question shape | Options minimum |
|---|---|---|
| OOM kill detected (`docker logs` shows `OOMKilled`) | "OOM on `<container>` — restart now or wait for current batch to drain?" | restart now / drain then restart / abort pipeline |
| Disk pressure (`/mnt/volume-nbg1-1` > 90%) | "Disk at `<X>%` — pause uploads + free space?" | pause + cleanup / continue at risk / abort |
| Worker zombie (task age > `time_limit`) | "Zombie `<task_id>` for `<duration>` — revoke + reset?" | revoke + reset / wait `<N>` more min / abort |
| CPU starvation (gw RTT > 5s during batch) | "GW slow under load — lower batch parallelism from `<N>` to `<N/2>`?" | reduce / pause / continue |
| Re-upload required after fix | "Doc `<title>` needs re-upload (parse fix invalidated existing chunks). Do it now?" | yes (Cat-F dispatch) / log + defer (next invocation) |
| End-of-pipeline batch commit | "Pipeline done. `<N>` source fixes ready. Commit + push as one batch?" | yes / show diff first / split into N commits |
| Production container restart of `nginx-proxy-manager` | "Restart NPM (will drop ALL inbound traffic for ~5s) — confirm?" | yes / no (find alternative) |

Bundling rule: OOM + disk-pressure during the SAME drain cycle may be combined
into one multi-select question. Container restarts must remain single-question
(each one is a separate operational decision).

## Verification

Pre-pipeline (run BEFORE dispatching the first doc):
- All containers reachable: `docker ps` shows `scrapalot-gw`, `scrapalot-backend`,
  `scrapalot-chat`, `scrapalot-workers`, `pgvector`, `neo4j`, `redis` all Up.
- Free disk on `/mnt/volume-nbg1-1` > 5 GB (the 30 GB volume hosts Docker data).
- Free RAM > 2 GB (`free -m | awk '/^Mem:/{print $7}'`).
- CI deploy not in progress (`gh run list --limit 1 --json status`). If
  `in_progress` on a workflow that touches backend or chat, postpone the
  pipeline start by 12 min (`feedback_no_heavy_admin_grpc_during_ci_deploy`).
- No `gh run` queued for the next 30 min that would `git reset --hard origin/main`
  the runner workspace (CI runners regularly wipe — defer mass operations to
  off-peak windows).
- Optional but recommended: `scrapalot-chat` heap and CPU settings match expected
  values for the planned batch size.

Mid-pipeline (monitored every drain cycle):
- OOM watch: `docker events --filter event=oom --since 1m` shows nothing OR
  triggers the matching Human Gate.
- Disk watch: `df -h /mnt/volume-nbg1-1 | tail -1 | awk '{print $5}'` < 90%.
- Worker liveness: Flower's "Active" + "Reserved" counts non-zero AND no task in
  "Started" state older than its `time_limit`.
- Per-doc progress: `progress.txt` getting `parse_*` and `graph_*` rows at the
  expected cadence (no silent stall for > 10 min).

Post-pipeline:
- All targeted docs landed in terminal status (`completed` | `failed` |
  `deferred`); no `processing` left over.
- `/scrapalot:postprocess-parse` audit re-runs on the docs that finished, to
  catch chunker pollution invisible from surface metrics
  (`feedback_postprocess_methodology`).
- End-of-batch source fixes committed in ONE commit per logical group; pushed
  to remote. Run `gh run list --limit 1` and wait for CI green before declaring
  done (`feedback_cicd_before_next_phase`).
- Final report: completed docs (with chunk counts), failed docs (with reasons +
  whether re-upload is needed), source patches applied (with commit SHAs),
  any `systemic_blockers` opened during the run.

Failure-mode rule: if Verification finds anything inconsistent (e.g. docs stuck
in `processing`, missing chunks, broken hierarchy), do NOT auto-retry — surface
to user with explicit Cat-F / Cat-H recommendation. Auto-retry hides root
causes (`feedback_fix_culture`).

## Instructions

Use the Agent tool with `subagent_type: "scrapalot:pipeline-orchestrator"` to launch the orchestrator agent. Pass the user's request as the prompt, including any specific details they mentioned (document names, collection names, error symptoms, etc.).

If the user provided arguments with the slash command (e.g., `/pipeline-orchestrator check graph health`), include those as context in the agent prompt.
