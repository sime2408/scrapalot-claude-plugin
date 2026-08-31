#!/usr/bin/env python3
"""
rag_chat_driver.py — canonical harness that drives a real Scrapalot chat turn
end-to-end (login -> session -> SSE chat/completions -> verdict) exactly the way
the React UI does, so /scrapalot-rag-test can ask a book question, watch the live
stream, and HALT the moment the backend emits a streaming error.

Stdlib only (urllib + json + subprocess). Runs on the HOST; reaches the Gateway
at http://localhost:8080/api/v1 and the DB via `docker exec pgvector psql`.

Subcommands
-----------
  login                          -> {access_token}
  pick-book   --workspace <id>   -> {workspace_id, collection_id, collection_name,
                                      document_id, document_title}
  create-session [--collection]  -> {session_id}
  ask         --session <id> --question <q> [--mode auto|manual|web_search|...]
              [--collection <id>...] [--workspace <id>] [--document <id>...]
                                 -> verdict JSON (ok / error / strategy / citations
                                    / graph / answer) + full packet log on disk
              The two RAG-agent modes of /scrapalot-rag-test map onto the API here:
              `auto` (alias `agentic`) sends mode=agentic so the agent routes
              itself; `manual` sends NO mode, so the strategy pinned in
              user_settings runs. Other modes (web_search, deep_research, tutor,
              thought_partner) pass through untouched.
  analyze     --session <id>     -> per-message persisted quality signals from DB
  del-message --message <id>     -> delete one chat message (retry-after-fix path)

Prompt-calibration verbs (the --tune loop):
  harvest-sessions [--user u] [--days N]
                                 -> every assistant turn REAL users got, with the
                                    question, routing/citation facts, thumbs
                                    feedback, and reask_overlap (did the user
                                    immediately ask the same thing again?)
  prompt-get  --key a.b          -> read one prompt from configs/prompts.yaml
  prompt-set  --key a.b --file f -> replace it atomically, keeping a backup
  prompt-reload [--off]          -> toggle the live watcher (no restart needed)
  busy-check                     -> is a real user mid-conversation right now?

Every `ask` writes the raw packet stream to runs/<session>__<ts>.jsonl so a failed
turn can be inspected after the fact.

Auth: admin creds come from env TEST_EMAIL / TEST_PASSWORD, the same pair the
Playwright suite uses. Both are required — never hard-code secrets.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("RAG_TEST_BASE", "http://localhost:8080/api/v1")
USER = os.environ.get("TEST_EMAIL", "admin")
PW = os.environ.get("TEST_PASSWORD")
if not PW:
    # No baked-in default: this driver logs into a real deployment as admin, and
    # this file is published in a public plugin. Set it in the project's
    # .claude/settings.local.json env block, which stays off git.
    sys.exit("TEST_PASSWORD is not set — export it (or add it to .claude/settings.local.json env) before running the driver.")
HERE = os.path.dirname(os.path.abspath(__file__))
# Run artefacts belong to the project and must survive a plugin update.
PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", "/opt/scrapalot")
RUNS = os.path.join(PROJECT_DIR, ".claude", "rag-test", "runs")
ADMIN_ID = os.environ.get("RAG_TEST_USER_ID", "ad93054b-635b-47b0-b6f4-7c7e06989c4c")

# Status codes the UI renders as a hard turn failure (chat-message.tsx KNOWN_STATUS_CODES).
ERROR_STATUS_CODES = {"streamingError", "errorGeneratingResponse", "errorTimeout",
                      "errorRateLimited", "errorModelUnavailable"}


def _emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _post(path, body, token=None, timeout=60):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw.strip() else {}


def login():
    r = _post("/auth/login", {"username_or_email": USER, "password": PW})
    tok = r.get("access_token") or r.get("accessToken")
    if not tok:
        raise SystemExit("login failed: no access_token in response")
    return tok


def _psql(db, sql):
    out = subprocess.run(
        ["docker", "exec", "pgvector", "psql", "-U", "scrapalot", "-d", db,
         "-tA", "-F", "\x1f", "-c", sql],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("psql error: " + out.stderr.strip())
    return [line.split("\x1f") for line in out.stdout.splitlines() if line.strip()]


# ---------------------------------------------------------------- pick-book
def pick_book(workspace_id=None, collection_hint=None):
    """Pick a collection+book the admin owns. Prefers a mid-size book (>=8 chunks)
    so retrieval/hierarchy/graph signals are actually exercisable."""
    where_ws = "AND cwm.workspace_id = '%s'" % workspace_id if workspace_id else ""
    where_col = "AND cwm.collection_name ILIKE '%%%s%%'" % collection_hint if collection_hint else ""
    rows = _psql("scrapalot", f"""
        SELECT cwm.workspace_id::text, cwm.collection_id::text, cwm.collection_name,
               d.id::text, d.title,
               COALESCE((d.processing_stats->>'chunk_count')::int, 0) AS chunks
          FROM collection_workspace_map cwm
          JOIN documents d ON d.collection_id = cwm.collection_id
         WHERE d.deleted_at IS NULL
           AND d.processing_status = 'completed'
           AND COALESCE((d.processing_stats->>'chunk_count')::int, 0) >= 8
           {where_ws} {where_col}
         ORDER BY cwm.collection_name ASC, d.title ASC
         LIMIT 1
    """)
    if not rows:
        raise SystemExit("pick-book: no completed book with >=8 chunks found for filter")
    ws, cid, cname, did, title, chunks = rows[0]
    return {"workspace_id": ws, "collection_id": cid, "collection_name": cname,
            "document_id": did, "document_title": title, "chunks": int(chunks)}


# -------------------------------------------------------------- list-books
def list_books(workspace_id=None, per_collection=2, limit=20, min_chunks=8):
    """Spread a sample of real books across the user's collections.

    Question generation must be grounded in material the system actually has,
    and spread across collections so the corpus covers more than one subject.
    Ranked by chunk count so retrieval, hierarchy and graph signals are
    exercisable rather than trivially thin."""
    where_ws = "AND cwm.workspace_id = '%s'" % workspace_id if workspace_id else ""
    rows = _psql("scrapalot", f"""
        WITH ranked AS (
          SELECT cwm.workspace_id::text AS ws, cwm.collection_id::text AS cid,
                 cwm.collection_name AS cname, d.id::text AS did, d.title,
                 COALESCE((d.processing_stats->>'chunk_count')::int, 0) AS chunks,
                 row_number() OVER (PARTITION BY cwm.collection_id
                                    ORDER BY COALESCE((d.processing_stats->>'chunk_count')::int,0) DESC) AS rn
            FROM collection_workspace_map cwm
            JOIN documents d ON d.collection_id = cwm.collection_id
           WHERE d.deleted_at IS NULL
             AND d.processing_status = 'completed'
             AND COALESCE((d.processing_stats->>'chunk_count')::int, 0) >= {int(min_chunks)}
             {where_ws}
        )
        SELECT ws, cid, cname, did, title, chunks FROM ranked
         WHERE rn <= {int(per_collection)}
         ORDER BY cname ASC, chunks DESC
         LIMIT {int(limit)}
    """)
    books = [{"workspace_id": r[0], "collection_id": r[1], "collection_name": r[2],
              "document_id": r[3], "document_title": r[4], "chunks": int(r[5])} for r in rows]
    return {"n_books": len(books), "n_collections": len({b["collection_id"] for b in books}),
            "books": books}


# ------------------------------------------------------------ sample-chunks
def sample_chunks(document_id, n=5, chars=600):
    """Real text from a real book — the raw material a question is written from.

    Spread across the document rather than taken from the front matter, so
    generated questions probe actual content instead of the title page."""
    rows = _psql("scrapalot", f"""
        WITH c AS (
          SELECT document, row_number() OVER () AS rn, count(*) OVER () AS total
            FROM langchain_pg_embedding
           WHERE cmetadata->>'document_id' = '{document_id}'
        )
        SELECT replace(replace(left(document, {int(chars)}), chr(10), ' '), chr(13), ' ')
          FROM c
         WHERE rn % GREATEST(total / {int(n)}, 1) = 0
         LIMIT {int(n)}
    """)
    return {"document_id": document_id, "n_chunks": len(rows),
            "chunks": [r[0] for r in rows]}


# ------------------------------------------------------------- create-session
def create_session(token, collection_id=None, name=None):
    body = {}
    if collection_id:
        body["collection_id"] = collection_id
    if name:
        body["conversation_name"] = name
    r = _post("/sessions", body, token=token)
    sid = r.get("id")
    if not sid:
        raise SystemExit("create-session failed: " + json.dumps(r))
    return sid


# ----------------------------------------------------------------------- ask
# The test surface speaks two RAG-agent modes; the API speaks one flag.
# auto -> `agentic` (the agent routes itself, Engine B).
# manual -> no mode at all, so the strategy pinned in user_settings runs (Engine A).
# Anything else (web_search, deep_research, tutor, thought_partner) is sent verbatim.
MODE_ALIASES = {"auto": "agentic", "agentic": "agentic",
                "manual": None, "off": None, "none": None}


def resolve_mode(mode):
    """Map a command-surface mode onto the API's `scrapalot.mode` value."""
    if not mode:
        return None
    return MODE_ALIASES.get(mode.strip().lower(), mode)


def ask(token, session_id, question, mode=None, collection_ids=None,
        workspace_id=None, document_ids=None, model="scrapalot:default",
        timeout=600, language=None, provider_type=None, model_name_pick=None):
    mode_requested, mode = mode, resolve_mode(mode)
    scrapalot = {"session_id": session_id}
    if mode:
        scrapalot["mode"] = mode
    if language:
        scrapalot["language"] = language
    if provider_type:
        scrapalot["provider_type"] = provider_type
    if model_name_pick:
        scrapalot["model_name"] = model_name_pick
    if workspace_id:
        scrapalot["workspace_id"] = workspace_id
    if collection_ids:
        scrapalot["collection_ids"] = collection_ids
    if document_ids:
        scrapalot["document_ids"] = document_ids
    body = {"model": model, "stream": True,
            "messages": [{"role": "user", "content": question}],
            "scrapalot": scrapalot}

    req = urllib.request.Request(BASE + "/chat/completions",
                                 data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "text/event-stream")
    req.add_header("Authorization", "Bearer " + token)

    os.makedirs(RUNS, exist_ok=True)
    log_path = os.path.join(RUNS, "%s__%s.jsonl" % (session_id[:8], int(time.time())))

    verdict = {
        "ok": False, "error": None, "error_packet": None,
        "strategy_name": None, "rationale": None, "sources_queried": None,
        "sub_queries": None, "filters_applied": None,
        "n_citations": 0, "citations": [], "n_graph_packets": 0,
        "answer_len": 0, "answer_preview": "", "packet_types": {},
        "stream_end_reason": None, "session_id": session_id,
        "question": question, "mode": mode, "mode_requested": mode_requested,
        "log": log_path,
        # Latency instrumentation. ttfb = first byte of any packet (when the UI
        # first shows life); ttft = first answer token (what a user calls "it
        # started answering"); timeline = first/last arrival per packet type, so
        # the pre-token time can be attributed to a phase instead of guessed at.
        "ttfb_ms": None, "ttft_ms": None, "total_ms": None, "timeline": {},
    }
    answer = []
    logf = open(log_path, "w")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                try:
                    frame = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                logf.write(payload + "\n")
                pkt = _unwrap(frame)
                if pkt is None:
                    continue
                el = int((time.time() - t0) * 1000)
                if verdict["ttfb_ms"] is None:
                    verdict["ttfb_ms"] = el
                ptype = pkt.get("type", "unknown")
                if ptype == "message_delta" and verdict["ttft_ms"] is None:
                    verdict["ttft_ms"] = el
                slot = verdict["timeline"].setdefault(ptype, {"first_ms": el, "last_ms": el, "n": 0})
                slot["last_ms"] = el
                slot["n"] += 1
                _absorb(pkt, verdict, answer)
                if verdict["error"]:
                    # HALT immediately on first hard error — the whole point.
                    break
    except urllib.error.HTTPError as e:
        verdict["error"] = "http_%s" % e.code
        verdict["error_packet"] = e.read().decode("utf-8", "replace")[:2000]
    except Exception as e:  # noqa: BLE001 - surface transport death as an error verdict
        verdict["error"] = "transport_error"
        verdict["error_packet"] = repr(e)
    finally:
        logf.close()
        verdict["total_ms"] = int((time.time() - t0) * 1000)

    verdict["answer_len"] = sum(len(a) for a in answer)
    verdict["answer_preview"] = ("".join(answer))[:600]
    # An EMPTY stream (no frames at all — e.g. the container restarted and gRPC
    # was not ready yet) leaves error=None, stream_end_reason=None, answer_len=0;
    # that is NOT a success. Require a real completion or some answer text.
    verdict["ok"] = verdict["error"] is None and (
        verdict["stream_end_reason"] == "completed" or verdict["answer_len"] > 0
    )
    return verdict


def _unwrap(frame):
    """Map an OpenAI chat.completion.chunk frame to a native Scrapalot packet."""
    try:
        delta = frame["choices"][0]["delta"]
    except (KeyError, IndexError, TypeError):
        return None
    if isinstance(delta, dict) and delta.get("scrapalot"):
        return delta["scrapalot"]
    if isinstance(delta, dict) and delta.get("content"):
        return {"type": "message_delta", "content": delta["content"]}
    fr = (frame.get("choices") or [{}])[0].get("finish_reason")
    if fr == "stop":
        return {"type": "stream_end", "reason": "completed"}
    return None


def _absorb(pkt, v, answer):
    t = pkt.get("type", "unknown")
    v["packet_types"][t] = v["packet_types"].get(t, 0) + 1
    if t == "message_delta":
        answer.append(pkt.get("content", ""))
    elif t == "strategy_transparency":
        v["strategy_name"] = pkt.get("strategy_name") or v["strategy_name"]
        v["rationale"] = pkt.get("rationale") or v["rationale"]
        v["sources_queried"] = pkt.get("sources_queried") or v["sources_queried"]
        v["sub_queries"] = pkt.get("sub_queries") or v["sub_queries"]
        v["filters_applied"] = pkt.get("filters_applied") or v["filters_applied"]
    elif t in ("citation_info", "citation_delta", "citation_start"):
        v["n_citations"] += 1
        v["citations"].append({k: pkt.get(k) for k in
                               ("citation_num", "document_title", "page", "score", "url")})
    elif t == "graph_expansion":
        v["n_graph_packets"] += 1
    elif t == "error":
        v["error"] = pkt.get("error_code") or "error"
        v["error_packet"] = pkt
    elif t == "status":
        if pkt.get("content") in ERROR_STATUS_CODES:
            v["error"] = pkt.get("content")
            v["error_packet"] = pkt
    elif t == "stream_end":
        v["stream_end_reason"] = pkt.get("reason")
        if pkt.get("reason") == "error":
            v["error"] = v["error"] or "stream_end_error"
            v["error_packet"] = v["error_packet"] or pkt


# ------------------------------------------------------------------- analyze
def analyze(session_id):
    """Pull persisted per-message quality signals straight from the messages
    table — the ground truth the UI shows (search_strategy, citations, graph)."""
    rows = _psql("scrapalot_backend", f"""
        SELECT role,
               left(content, 80),
               COALESCE(metadata->'search_strategy'->>'strategy_name',''),
               COALESCE(metadata->'search_strategy'->>'sources_queried',''),
               -- citations live in metadata->'citations' (the standalone `citations`
               -- column is vestigial/unmapped, dropped by Liquibase changeset 119).
               jsonb_array_length(COALESCE(metadata->'citations','[]'::jsonb)),
               jsonb_array_length(COALESCE(used_graph_element_ids,'[]'::jsonb)),
               (metadata ? 'retrieval_results')::text,
               id::text
          FROM messages
         WHERE session_id = '{session_id}'
         ORDER BY created_at ASC
    """)
    msgs = [{"role": r[0], "content": r[1], "strategy": r[2], "sources": r[3],
             "n_citations": int(r[4]), "n_graph": int(r[5]),
             "has_retrieval": r[6] == "true", "message_id": r[7]} for r in rows]
    summ = _psql("scrapalot", f"""
        SELECT left(summary, 200) FROM conversation_summaries
         WHERE session_id = '{session_id}'""")
    return {"session_id": session_id, "n_messages": len(msgs), "messages": msgs,
            "memory_summary": (summ[0][0] if summ else None)}


# -------------------------------------------------------- harvest-sessions
def _tokens(text):
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split() if len(w) > 2}


def _overlap(a, b):
    """Jaccard overlap of two messages. Deliberately mechanical: a high score
    between one question and the user's NEXT question means they re-asked the
    same thing, which is the strongest evidence an answer failed. No keyword
    list — the LLM judges WHY, this only flags WHERE to look."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return round(len(ta & tb) / len(ta | tb), 3)


def harvest_sessions(username=None, days=None, limit=200, min_answer_chars=0):
    """Read real conversations users had with Scrapalot AI and return every
    assistant turn with the signals needed to judge it: the question that
    produced it, the routing/citation/graph facts persisted for it, the user's
    explicit feedback, and whether the user immediately re-asked.

    This is the corpus the prompt tuner calibrates against — real questions in
    the users' own words, not questions the harness invented."""
    where = []
    if username:
        where.append("u.username = '%s'" % username.replace("'", "''"))
    if days:
        where.append("m.created_at > now() - interval '%d days'" % int(days))
    where_sql = ("AND " + " AND ".join(where)) if where else ""

    rows = _psql("scrapalot_backend", f"""
        SELECT m.session_id::text, u.username, m.created_at::text, m.role,
               replace(replace(m.content, chr(10), ' '), chr(13), ' '),
               COALESCE(m.metadata->'search_strategy'->>'strategy_name',''),
               COALESCE(m.metadata->'search_strategy'->>'sources_queried',''),
               jsonb_array_length(COALESCE(m.metadata->'citations','[]'::jsonb)),
               jsonb_array_length(COALESCE(m.used_graph_element_ids,'[]'::jsonb)),
               COALESCE(m.feedback::text,''), m.id::text,
               COALESCE(s.conversation_name,''), COALESCE(s.collection_id::text,'')
          FROM messages m
          JOIN sessions s ON s.id = m.session_id
          JOIN users u ON u.id = s.user_id
         WHERE 1=1 {where_sql}
         ORDER BY m.session_id, m.created_at ASC
        LIMIT {int(limit)}
    """)

    # Walk each session in order so every assistant turn keeps the question that
    # produced it and the question that followed it.
    by_session = {}
    for r in rows:
        by_session.setdefault(r[0], []).append(r)

    turns = []
    for sid, msgs in by_session.items():
        for i, r in enumerate(msgs):
            if r[3] != "assistant":
                continue
            prev_user = next((msgs[j][4] for j in range(i - 1, -1, -1) if msgs[j][3] == "user"), "")
            next_user = next((msgs[j][4] for j in range(i + 1, len(msgs)) if msgs[j][3] == "user"), "")
            answer = r[4]
            if len(answer) < min_answer_chars:
                continue
            turns.append({
                "session_id": sid, "user": r[1], "created_at": r[2],
                "conversation_name": r[11], "collection_id": r[12] or None,
                "question": prev_user, "answer": answer, "answer_len": len(answer),
                "strategy": r[5], "sources": r[6], "n_citations": int(r[7]),
                "n_graph": int(r[8]),
                "feedback": (int(r[9]) if r[9] else None),
                "message_id": r[10],
                "next_user_message": next_user,
                # High overlap => the user asked the same thing again => this answer failed them.
                "reask_overlap": _overlap(prev_user, next_user) if (prev_user and next_user) else 0.0,
            })

    turns.sort(key=lambda t: t["reask_overlap"], reverse=True)
    return {
        "n_sessions": len(by_session), "n_turns": len(turns),
        "suspect_turns": sum(1 for t in turns if t["reask_overlap"] >= 0.5 or t["feedback"] == -1),
        "turns": turns,
    }


# ------------------------------------------------------------ prompt access
def _prompts_path():
    return os.environ.get("RAG_TEST_PROMPTS", "/opt/scrapalot/scrapalot-chat/configs/prompts.yaml")


def prompt_get(dotted_key):
    """Read one prompt by dotted key (e.g. rag_agent.system_prompt)."""
    import yaml
    with open(_prompts_path(), encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    node = data
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise SystemExit(f"prompt-get: key not found: {dotted_key}")
        node = node[part]
    return {"key": dotted_key, "value": node, "path": _prompts_path()}


def _indent_of(line):
    return len(line) - len(line.lstrip(" "))


def _find_block(lines, dotted_key):
    """Locate a dotted key's block-scalar body by walking indentation.

    Text-level on purpose. A yaml load/dump round-trip would reformat all 4700
    lines and drop every comment and block style in the file, turning a one-prompt
    edit into an unreviewable diff. This touches only the target block."""
    parts = dotted_key.split(".")
    start, parent_indent = 0, -1
    key_line = None

    for depth, part in enumerate(parts):
        key_line = None
        for i in range(start, len(lines)):
            line = lines[i]
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = _indent_of(line)
            # Left the parent's block without a match.
            if indent <= parent_indent and i > start:
                break
            if indent > parent_indent and line.lstrip().startswith(part + ":"):
                key_line = i
                break
        if key_line is None:
            raise SystemExit(f"prompt-set: key not found: {dotted_key} (missing '{part}')")
        parent_indent = _indent_of(lines[key_line])
        start = key_line + 1
        if depth == len(parts) - 1:
            break

    header = lines[key_line]
    marker = header.split(":", 1)[1].strip()
    if marker not in ("|", "|-", "|+", ">", ">-"):
        raise SystemExit(
            f"prompt-set: {dotted_key} is not a block scalar (found '{marker[:20]}'). "
            "Only block-scalar prompts are editable by this harness.")

    body_end = key_line + 1
    for i in range(key_line + 1, len(lines)):
        if not lines[i].strip():
            body_end = i + 1
            continue
        if _indent_of(lines[i]) <= parent_indent:
            break
        body_end = i + 1

    # Trailing blank lines belong to the file, not the block.
    while body_end - 1 > key_line and not lines[body_end - 1].strip():
        body_end -= 1

    body_indent = next((_indent_of(lines[i]) for i in range(key_line + 1, body_end) if lines[i].strip()),
                       parent_indent + 2)
    return key_line, body_end, body_indent


def prompt_set(dotted_key, value_file, note=None):
    """Replace one prompt's block-scalar body, atomically, keeping a backup.

    Atomic temp+rename matters: the running service watches this file, so a
    half-written read would otherwise land as a broken prompt set."""
    import shutil
    path = _prompts_path()
    with open(value_file, encoding="utf-8") as fh:
        new_value = fh.read().rstrip("\n")

    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    key_line, body_end, body_indent = _find_block(lines, dotted_key)
    old_body = "\n".join(lines[key_line + 1:body_end])
    pad = " " * body_indent
    new_body = [pad + ln if ln.strip() else "" for ln in new_value.split("\n")]
    if "\n".join(new_body) == old_body:
        return {"key": dotted_key, "changed": False, "reason": "value identical"}

    backups = os.path.join(os.path.dirname(HERE), "prompt_backups")
    os.makedirs(backups, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(backups, f"prompts__{stamp}.yaml")
    shutil.copy2(path, backup)

    updated = lines[:key_line + 1] + new_body + lines[body_end:]
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(updated))

    # Never hand the running service a file that does not parse.
    import yaml
    with open(tmp, encoding="utf-8") as fh:
        try:
            yaml.safe_load(fh)
        except yaml.YAMLError as e:
            os.remove(tmp)
            raise SystemExit(f"prompt-set: edit would produce invalid YAML, aborted: {e}") from e
    os.replace(tmp, path)

    return {"key": dotted_key, "changed": True, "backup": backup, "note": note,
            "old_lines": body_end - key_line - 1, "new_lines": len(new_body),
            "old_len": len(old_body), "new_len": len(new_value)}


def prompt_reload(enable=True):
    """Turn the live prompt watcher on/off via its sentinel and report the state.

    The service reloads within ~5s of a change while the sentinel exists."""
    sentinel = os.path.join(os.path.dirname(_prompts_path()), ".prompts_autoreload")
    if enable:
        with open(sentinel, "w", encoding="utf-8") as fh:
            fh.write("enabled by rag_chat_driver for prompt tuning\n")
    elif os.path.exists(sentinel):
        os.remove(sentinel)
    return {"sentinel": sentinel, "auto_reload": os.path.exists(sentinel)}


def busy_check(idle_minutes=20):
    """Are real users mid-conversation right now? The tuner edits a shared
    production prompt, so it must not do that under someone's live session."""
    rows = _psql("scrapalot_backend", f"""
        SELECT u.username, max(m.created_at)::text,
               EXTRACT(EPOCH FROM (now() - max(m.created_at)))/60
          FROM messages m
          JOIN sessions s ON s.id = m.session_id
          JOIN users u ON u.id = s.user_id
         WHERE u.username <> '{USER}'
         GROUP BY u.username
        HAVING EXTRACT(EPOCH FROM (now() - max(m.created_at)))/60 < {int(idle_minutes)}
    """)
    active = [{"user": r[0], "last_msg": r[1], "minutes_ago": round(float(r[2]), 1)} for r in rows]
    return {"safe_to_tune": not active, "idle_window_minutes": idle_minutes, "active_users": active}


# --------------------------------------------------------------- del-message
def del_message(token, message_id):
    req = urllib.request.Request(BASE + "/messages/" + message_id, method="DELETE")
    req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"deleted": message_id, "status": r.status}
    except urllib.error.HTTPError as e:
        return {"deleted": None, "status": e.code, "error": e.read().decode()[:500]}


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    p = sub.add_parser("pick-book")
    p.add_argument("--workspace")
    p.add_argument("--collection")
    p = sub.add_parser("create-session")
    p.add_argument("--collection")
    p.add_argument("--name")
    p = sub.add_parser("ask")
    p.add_argument("--session", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--mode", help="auto (=agentic routing) | manual (=pinned strategy, "
                                  "sends no mode) | web_search | deep_research | tutor | "
                                  "thought_partner")
    p.add_argument("--collection", action="append", default=[])
    p.add_argument("--workspace")
    p.add_argument("--document", action="append", default=[])
    p.add_argument("--language")
    p.add_argument("--provider")
    p.add_argument("--model")
    p = sub.add_parser("analyze")
    p.add_argument("--session", required=True)
    p = sub.add_parser("del-message")
    p.add_argument("--message", required=True)
    p = sub.add_parser("list-books")
    p.add_argument("--workspace")
    p.add_argument("--per-collection", type=int, default=2)
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("sample-chunks")
    p.add_argument("--document", required=True)
    p.add_argument("--n", type=int, default=5)
    p = sub.add_parser("harvest-sessions")
    p.add_argument("--user", help="only this username (default: every real user)")
    p.add_argument("--days", type=int, help="only turns newer than N days")
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--min-answer-chars", type=int, default=0)
    p = sub.add_parser("prompt-get")
    p.add_argument("--key", required=True, help="dotted key, e.g. rag_agent.system_prompt")
    p = sub.add_parser("prompt-set")
    p.add_argument("--key", required=True)
    p.add_argument("--file", required=True, help="file holding the new prompt text")
    p.add_argument("--note")
    p = sub.add_parser("prompt-reload")
    p.add_argument("--off", action="store_true", help="disable the live watcher")
    p = sub.add_parser("busy-check")
    p.add_argument("--idle-minutes", type=int, default=20)
    a = ap.parse_args()

    if a.cmd == "login":
        _emit({"access_token": login()})
    elif a.cmd == "pick-book":
        _emit(pick_book(a.workspace, a.collection))
    elif a.cmd == "create-session":
        _emit({"session_id": create_session(login(), a.collection, a.name)})
    elif a.cmd == "ask":
        _emit(ask(login(), a.session, a.question, a.mode,
                  a.collection or None, a.workspace, a.document or None,
                  language=a.language, provider_type=a.provider, model_name_pick=a.model))
    elif a.cmd == "analyze":
        _emit(analyze(a.session))
    elif a.cmd == "del-message":
        _emit(del_message(login(), a.message))
    elif a.cmd == "list-books":
        _emit(list_books(a.workspace, a.per_collection, a.limit))
    elif a.cmd == "sample-chunks":
        _emit(sample_chunks(a.document, a.n))
    elif a.cmd == "harvest-sessions":
        _emit(harvest_sessions(a.user, a.days, a.limit, a.min_answer_chars))
    elif a.cmd == "prompt-get":
        _emit(prompt_get(a.key))
    elif a.cmd == "prompt-set":
        _emit(prompt_set(a.key, a.file, a.note))
    elif a.cmd == "prompt-reload":
        _emit(prompt_reload(not a.off))
    elif a.cmd == "busy-check":
        _emit(busy_check(a.idle_minutes))


if __name__ == "__main__":
    main()
