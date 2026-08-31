#!/usr/bin/env python3
"""manual_coverage_sweep.py — drive RAG-technique COVERAGE through the REAL chat
path (gateway), one DISTINCT technique per question, proving each of the ~30
strategies/orchestrators actually executes. Mechanism B of /scrapalot-rag-test
--manual: PIN each technique via the admin's `settings_general`
(`use_agentic_routing=false` + `rag_strategy`/`rag_orchestrator`), ask one
catalogue-shaped question, read back which strategy ACTUALLY ran, ledger it.

Why not the in-process verify_all_techniques harness: in a standalone process its
`llm_manager.get_llm(provider_type="system")` can't resolve the system DeepSeek
provider (falls back to the config.yaml openai stub → "Failed to get LLM"). The
gateway path uses the fully-initialised server, so technique execution is real.

Restores the original settings on exit (even on crash). Writes a JSON ledger +
prints a coverage grid. Run from this dir; reuses rag_chat_driver.py via subprocess.

Full catalogue by default. `--only` narrows it — that is how a `focus=` from
/scrapalot-rag-test reaches this sweep (e.g. `--only graph,entity`). A narrowed
run says so in the header, the ledger and the summary, so a subset is never
mistaken for full coverage.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, "rag_chat_driver.py")
LEDGER = os.path.join(os.path.dirname(HERE), "runs", "manual_coverage_ledger.json")
ADMIN = "ad93054b-635b-47b0-b6f4-7c7e06989c4c"
WS = "0ebf2e09-7198-4b7a-a100-87b6dc969387"
COL = "5eeec701-511d-4f85-b8b5-6cbcd64e4467"  # anthropology (rich corpus)

# Catalogue → catalogue-shaped question. Orchestrators (name ends 'Orchestrator')
# pin via rag_orchestrator+use_orchestrator=true; the rest via rag_strategy.
CATALOGUE = {
    "RAGSimilaritySearch": "What does the corpus say about kinship in early societies?",
    "RAGSparseSearch": "Define the exact term 'matrilineal descent' as used in these books.",
    "RAGRegexGrep": "Quote the exact sentence where these books define 'kinship'.",
    "RAGHyDE": "How do families pass down belonging across generations here?",
    "RAGMultiQuery": "What are the benefits, the criticisms, and the methods of kinship analysis?",
    "RAGDecomposition": "What is kinship, how is it structured, and why does it change over time?",
    "RAGStepBack": "What general principle of social organization underlies kinship systems?",
    "RAGRewriteRetrieveRead": "kinship stuff?",
    "RAGGraphSearch": "How is descent related to marriage in these kinship systems?",
    "RAGEntityExpanded": "What links lineage, clan, and household across these books?",
    "RAGParentDocument": "Explain the full context around how lineages form.",
    "RAGSectionExpansion": "Give the complete passage on the definition of kinship.",
    "RAGAgenticContextNavigator": "In the part about descent systems, what is described?",
    "RAGSelfQuery": "In the chapters specifically about marriage, what is said about alliance?",
    "RAGHybridSelfQuery": "Find the rare term 'cross-cousin marriage' and explain it.",
    "RAGFusion": "Cover everything these books say about kinship and social structure.",
    "RAGGenerativeFeedbackLoop": "Refine and deepen: what is the most important point about kinship here?",
    "RAGQueryChain": "Trace how descent leads to lineage leads to clan organization.",
    "RAGHybridSummarySearch": "Give an overview of what these books cover about kinship.",
    "RAGTwoPhaseContext": "What is a lineage, and what surrounds that idea in the text?",
    "RAGAgenticExpansion": "Explore everything the corpus covers on social structure.",
    "RAGAdaptiveOrchestrator": "Analyze kinship and social structure across these books.",
    "RAGKnowledgeIntensiveOrchestrator": "Reason across the books: how do kinship, economy, and ritual interrelate?",
    "RAGDocumentHierarchyOrchestrator": "Walk the structure of how these books present kinship.",
    "RAGQueryRefinementOrchestrator": "Tell me about the structure stuff in early societies.",
    "RAGBalancedOrchestrator": "Summarize kinship and social organization evenly across sources.",
    "RAGContextEnhancedOrchestrator": "Explain kinship with rich surrounding context.",
    "RAGFeedbackLoopOrchestrator": "Iteratively answer: what defines a kinship system?",
    "RAGPrecisionOrchestrator": "Precisely, what is the anthropological definition of descent?",
    "EnhancedTriModalOrchestrator": "What do these books say about kinship and social structure?",
}


def _sql(stmt: str) -> str:
    return subprocess.run(
        ["docker", "exec", "-i", "pgvector", "psql", "-U", "scrapalot", "-d", "scrapalot", "-tA"],
        input=stmt, capture_output=True, text=True,
    ).stdout.strip()


def _get_settings() -> str:
    return _sql(
        f"SELECT setting_value FROM user_settings WHERE user_id='{ADMIN}' "
        "AND setting_key='settings_general';"
    )


def _restore(original: str) -> None:
    if not original:
        return
    # write the verbatim original JSON back
    js = original.replace("'", "''")
    _sql(
        f"UPDATE user_settings SET setting_value='{js}'::json "
        f"WHERE user_id='{ADMIN}' AND setting_key='settings_general';"
    )


def _pin(technique: str) -> None:
    is_orch = technique.endswith("Orchestrator")
    key = "rag_orchestrator" if is_orch else "rag_strategy"
    use_orch = "true" if is_orch else "false"
    stmt = (
        "UPDATE user_settings SET setting_value = (jsonb_set(jsonb_set(jsonb_set("
        "setting_value::jsonb,'{use_agentic_routing}','false'),"
        f"'{{use_orchestrator}}','{use_orch}'),"
        f"'{{{key}}}','\"{technique}\"'))::json "
        f"WHERE user_id='{ADMIN}' AND setting_key='settings_general';"
    )
    _sql(stmt)


def _ask(technique: str, question: str, collection: str, workspace: str) -> dict:
    sid = json.loads(subprocess.run(
        [sys.executable, DRIVER, "create-session", "--collection", collection,
         "--name", f"cov-{technique}"],
        capture_output=True, text=True).stdout)["session_id"]
    # No --mode: Engine A must run the strategy pinned above, not agentic routing.
    out = subprocess.run(
        [sys.executable, DRIVER, "ask", "--session", sid, "--question", question,
         "--workspace", workspace, "--collection", collection],
        capture_output=True, text=True, timeout=400)
    try:
        v = json.loads(out.stdout)
    except Exception:
        return {"session_id": sid, "ok": False, "error": "driver_parse_fail",
                "executed": None, "answer_len": 0}
    return {"session_id": sid, "ok": v.get("ok"), "error": v.get("error"),
            "executed": v.get("strategy_name"), "answer_len": v.get("answer_len", 0),
            "ttfb_ms": v.get("ttfb_ms"), "ttft_ms": v.get("ttft_ms"),
            "total_ms": v.get("total_ms"), "timeline": v.get("timeline")}


def _select(only: str) -> dict:
    """Resolve --only tokens (exact technique names or substrings) into a subset."""
    if not only:
        return dict(CATALOGUE)
    tokens = [t.strip().lower() for t in only.split(",") if t.strip()]
    return {k: v for k, v in CATALOGUE.items()
            if any(t == k.lower() or t in k.lower() for t in tokens)}


def main():
    ap = argparse.ArgumentParser(
        description="Pin + ask + read-back every RAG technique through the real gateway.")
    ap.add_argument("--only", help="comma-separated technique names or substrings "
                                   "(e.g. 'graph,entity') — narrows the catalogue; "
                                   "this is how a focus= reaches the sweep")
    ap.add_argument("--collection", default=COL, help="collection id to ask against")
    ap.add_argument("--workspace", default=WS, help="workspace id")
    ap.add_argument("--limit", type=int, help="stop after N techniques")
    ap.add_argument("--ledger", default=LEDGER, help="where to write the JSON ledger")
    ap.add_argument("--list", action="store_true",
                    help="print the catalogue and exit (no chat, no pinning)")
    a = ap.parse_args()

    if a.list:
        for tech, q in CATALOGUE.items():
            print(f"{tech:34} {q}")
        return

    selected = _select(a.only)
    if not selected:
        raise SystemExit(f"ERROR: --only '{a.only}' matched none of the "
                         f"{len(CATALOGUE)} techniques. Run --list to see them.")
    if a.limit:
        selected = dict(list(selected.items())[:a.limit])
    subset = len(selected) < len(CATALOGUE)
    skipped = [t for t in CATALOGUE if t not in selected]

    original = _get_settings()
    if not original:
        print("ERROR: could not read admin settings_general; aborting (no restore needed)")
        return
    rows = []
    meta = {"selected": len(selected), "catalogue": len(CATALOGUE), "subset": subset,
            "only": a.only, "limit": a.limit, "skipped": skipped,
            "collection": a.collection, "workspace": a.workspace}
    scope = (f"SUBSET {len(selected)}/{len(CATALOGUE)} (only={a.only or 'n/a'}, limit={a.limit})"
             if subset else f"FULL {len(CATALOGUE)}")
    print(f"Coverage sweep: {scope} techniques via gateway pin. Original settings backed up.")
    try:
        for i, (tech, q) in enumerate(selected.items(), 1):
            _pin(tech)
            t0 = time.time()
            try:
                r = _ask(tech, q, a.collection, a.workspace)
            except subprocess.TimeoutExpired:
                r = {"ok": False, "error": "timeout", "executed": None, "answer_len": 0}
            ran = (r.get("executed") == tech)
            row = {"technique": tech, "executed": r.get("executed"), "ran_as_intended": ran,
                   "answer_len": r.get("answer_len", 0), "ok": bool(r.get("ok")),
                   "error": r.get("error"), "ms": int((time.time() - t0) * 1000),
                   # Latency profile: ms above includes session setup; these are the
                   # numbers a user actually feels.
                   "ttfb_ms": r.get("ttfb_ms"), "ttft_ms": r.get("ttft_ms"),
                   "total_ms": r.get("total_ms"), "timeline": r.get("timeline")}
            rows.append(row)
            with open(a.ledger, "w") as f:
                json.dump({"meta": meta, "rows": rows}, f, indent=2)
            mark = "✅" if (ran and row["answer_len"] > 40) else ("⚠️" if r.get("ok") else "❌")
            print(f"[{i:2}/{len(selected)}] {mark} {tech:34} executed={r.get('executed')} "
                  f"len={row['answer_len']} ttft={r.get('ttft_ms')}ms total={r.get('total_ms')}ms "
                  f"{('ERR:'+str(r.get('error'))[:40]) if r.get('error') else ''}",
                  flush=True)
    finally:
        _restore(original)
        print("Restored original admin settings_general.")

    ran = sum(1 for r in rows if r["ran_as_intended"] and r["answer_len"] > 40)
    mismatch = sum(1 for r in rows if r["executed"] and not r["ran_as_intended"])
    fail = sum(1 for r in rows if not r["ok"])
    print(f"\nCOVERAGE: {ran}/{len(selected)} ran-as-intended+answered | "
          f"{mismatch} executed-but-mismatched | {fail} failed | ledger: {a.ledger}")
    if subset:
        # Never let a narrowed sweep read as full coverage.
        print(f"SUBSET RUN — {len(skipped)} techniques NOT tested: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
