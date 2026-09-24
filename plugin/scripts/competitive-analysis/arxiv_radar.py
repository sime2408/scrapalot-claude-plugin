#!/usr/bin/env python3
"""The day's arXiv announcement, triaged by Jev, without touching the arXiv search API.

arXiv refuses bulk and unbounded API queries, and it cools an over-eager client's
IP down for hours, longer with every retry. So discovery here never searches. It
reads the official RSS feed, which carries every requested category in one
request and the whole daily announcement with titles and abstracts. Jev
(TypeSafe's System One judge) then answers one yes/no question per Scrapalot
interest for every paper. Only the shortlist reaches Claude, and only the few
papers Claude picks from it are ever fetched in full, by `arxiv_paper.py`.

The engine is JEV-Paper-Radar (MIT), pinned to one commit and kept in a cache
clone outside every repository. It needs nothing beyond the standard library.
The interests live in `arxiv_profile.toml` beside this script. Run state
(decisions, runs.jsonl, the rendered page, the shortlists) lives in
`<project>/.claude/competitive-analysis/arxiv/`, never in the plugin.

    arxiv_radar.py                 judge the announcement, print the shortlist
    arxiv_radar.py --limit 50      judge at most 50 papers (a cheap first look)
    arxiv_radar.py --dry-run       fetch and estimate the cost; Jev is not called
    arxiv_radar.py --shortlist     reprint a day's shortlist from stored decisions
    arxiv_radar.py --no-jev        no key: print the raw feed for title triage
    arxiv_radar.py --calibrate     score the tracker's past verdicts with the profile
                                   and print how well it separates them

The project is --project-dir, else $CLAUDE_PROJECT_DIR, else $SCRAPALOT_ROOT,
else the working directory. The key is TYPESAFE_API_KEY or JEV_API_KEY from the
environment, else the matching line of --key-file (default: the chat deploy's
env file). Only that line is used, and the key goes to the engine, never to
stdout.

Exit codes: 0 done, 1 the engine or a source failed, 2 no key or no engine.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

ENGINE_REPO = "https://github.com/Eliot5566/JEV-Paper-Radar"
ENGINE_SHA = "c75595386975618f64dfde4368238731dae53510"
USER_AGENT = "scrapalot-competitive-analysis/2.0 (+https://github.com/sime2408/scrapalot-claude-plugin)"
S2_BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,abstract"

PROFILE = Path(__file__).resolve().parent / "arxiv_profile.toml"
ENGINE = (
    Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    / "scrapalot-plugin"
    / f"paper-radar-{ENGINE_SHA[:12]}"
)
KEY_NAMES = ("TYPESAFE_API_KEY", "JEV_API_KEY")
SHOWN_BANDS = ("must_read", "maybe")
# Tracker verdicts that mean "passed abstract triage" (see the tracker's header).
POSITIVE_VERDICTS = {"relevant", "skipped", "accepted"}
NEGATIVE_VERDICTS = {"irrelevant"}
_VERSION = re.compile(r"v\d+$")


@dataclass(frozen=True)
class Layout:
    project: Path

    @property
    def state(self) -> Path:
        return self.project / ".claude" / "competitive-analysis" / "arxiv"

    @property
    def tracker(self) -> Path:
        return self.project / ".claude" / "competitive-analysis" / "analyzed_arxiv_papers.txt"

    @property
    def default_key_file(self) -> Path:
        return self.project / "scrapalot-chat" / "docker-scrapalot" / ".env"

    def decisions(self, day: str) -> Path:
        return self.state / "data" / "decisions" / f"{day}.jsonl"

    def shortlist(self, day: str) -> Path:
        return self.state / f"shortlist-{day}.jsonl"


def base_id(raw: str) -> str:
    return _VERSION.sub("", raw.strip().removeprefix("arxiv:"))


def err(message: str) -> None:
    print(message, file=sys.stderr)


# --------------------------------------------------------------------------- engine


def ensure_engine() -> Path | None:
    """Clone the pinned engine commit once; later runs reuse the cache."""
    if (ENGINE / "paper_radar" / "__init__.py").is_file():
        return ENGINE
    partial = ENGINE.with_name(ENGINE.name + ".partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.parent.mkdir(parents=True, exist_ok=True)
    steps = (
        ["git", "init", "-q", str(partial)],
        ["git", "-C", str(partial), "fetch", "-q", "--depth", "1", ENGINE_REPO, ENGINE_SHA],
        ["git", "-C", str(partial), "checkout", "-q", "FETCH_HEAD"],
    )
    try:
        for step in steps:
            subprocess.run(step, check=True, stdout=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as error:
        err(f"error: could not fetch the radar engine {ENGINE_REPO}@{ENGINE_SHA[:12]}: {error}")
        return None
    partial.rename(ENGINE)
    return ENGINE


def import_engine(engine: Path) -> None:
    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))


def read_key(key_file: Path) -> str | None:
    for name in KEY_NAMES:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    try:
        lines = key_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        name, sep, value = line.strip().partition("=")
        if sep and name.strip() in KEY_NAMES:
            value = value.strip().strip('"').strip("'")
            if value:
                return value
    return None


def run_engine(layout: Layout, engine: Path, key: str, extra: list[str]) -> int:
    layout.state.mkdir(parents=True, exist_ok=True)
    # A copy, so the engine anchors data/ and site/ in the state directory.
    shutil.copyfile(PROFILE, layout.state / "radar.toml")
    env = {**os.environ, "TYPESAFE_API_KEY": key, "PYTHONPATH": str(engine)}
    command = [
        sys.executable,
        "-m",
        "paper_radar",
        "run",
        "-c",
        str(layout.state / "radar.toml"),
        "--no-notify",
        *extra,
    ]
    return subprocess.run(command, cwd=layout.state, env=env).returncode


# --------------------------------------------------------------------------- shortlist


def tracked_ids(layout: Layout) -> set[str]:
    if not layout.tracker.is_file():
        return set()
    ids = set()
    for line in layout.tracker.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "|" in line:
            ids.add(base_id(line.split("|", 1)[0]))
    return ids


def _top_interests(interests: dict[str, float], n: int = 3, floor: float = 0.3) -> list[tuple[str, float]]:
    ranked = sorted(interests.items(), key=lambda kv: kv[1], reverse=True)
    return [(k, v) for k, v in ranked[:n] if v >= floor]


def print_shortlist(layout: Layout, day: str) -> int:
    path = layout.decisions(day)
    if not path.is_file():
        print(f"No decisions stored for {day} (nothing announced, or the radar has not run).")
        return 0
    seen = tracked_ids(layout)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = sorted(
        (r for r in records if r["band"] in SHOWN_BANDS and base_id(r["paper"]["id"]) not in seen),
        key=lambda r: r["relevance"],
        reverse=True,
    )
    out = layout.shortlist(day)
    with out.open("w", encoding="utf-8") as handle:
        for r in rows:
            paper = r["paper"]
            handle.write(
                json.dumps(
                    {
                        "id": base_id(paper["id"]),
                        "band": r["band"],
                        "relevance": r["relevance"],
                        "interests": dict(_top_interests(r["interests"])),
                        "paper_type": r.get("paper_type"),
                        "code": r.get("code"),
                        "evidence": r.get("evidence"),
                        "title": paper["title"],
                        "abstract": paper.get("abstract", ""),
                        "url": paper["url"],
                        "categories": paper.get("categories", []),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    must = sum(1 for r in rows if r["band"] == "must_read")
    print(f"\n{day}: {must} must-read, {len(rows) - must} maybe (already tracked papers left out)")
    print(f"Full records with abstracts: {out}")
    for r in rows:
        top = _top_interests(r["interests"], n=1, floor=0.0)
        interest = f"{top[0][0]}={top[0][1]:.2f}" if top else "-"
        code = f"{r['code']:.2f}" if isinstance(r.get("code"), (int, float)) else "-"
        print(
            f"{'must ' if r['band'] == 'must_read' else 'maybe'} {r['relevance']:.2f} "
            f"{base_id(r['paper']['id']):<11} {(r.get('paper_type') or '-'):<15} code={code} "
            f"{interest} | {r['paper']['title']}"
        )
    return 0


# --------------------------------------------------------------------------- no key


def print_feed(layout: Layout, engine: Path, day: str) -> int:
    """The feed without Jev: one RSS request, titles for Claude to triage by hand."""
    import_engine(engine)
    from paper_radar.config import load_config
    from paper_radar.sources import collect

    config = load_config(PROFILE)
    papers = collect(config.sources, today=date.fromisoformat(day), base_dir=PROFILE.parent, log=err)
    seen = tracked_ids(layout)
    papers = [p for p in papers if base_id(p.id) not in seen]
    layout.state.mkdir(parents=True, exist_ok=True)
    out = layout.state / f"feed-{day}.jsonl"
    with out.open("w", encoding="utf-8") as handle:
        for p in papers:
            record = {
                "id": base_id(p.id),
                "title": p.title,
                "abstract": p.abstract,
                "url": p.url,
                "categories": p.categories,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{len(papers)} papers in the feed, not judged. Full records: {out}")
    for p in papers:
        print(f"{base_id(p.id):<11} {p.title}")
    return 0


# --------------------------------------------------------------------------- calibration


def tracker_labels(layout: Layout) -> dict[str, bool]:
    labels: dict[str, bool] = {}
    if not layout.tracker.is_file():
        return labels
    for line in layout.tracker.read_text(encoding="utf-8").splitlines():
        parts = line.split("|")
        if line.startswith("#") or len(parts) < 3:
            continue
        verdict = parts[2].strip()
        if verdict in POSITIVE_VERDICTS or verdict in NEGATIVE_VERDICTS:
            labels[base_id(parts[0])] = verdict in POSITIVE_VERDICTS
    return labels


def s2_abstracts(ids: list[str]) -> dict[str, tuple[str, str]]:
    """Titles and abstracts from Semantic Scholar's batch endpoint, so a calibration
    run costs arXiv nothing."""
    found: dict[str, tuple[str, str]] = {}
    for start in range(0, len(ids), 500):
        chunk = ids[start : start + 500]
        body = json.dumps({"ids": [f"ARXIV:{i}" for i in chunk]}).encode("utf-8")
        for attempt in range(3):
            request = urllib.request.Request(
                S2_BATCH,
                data=body,
                method="POST",
                headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            )
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    items = json.loads(response.read())
                break
            except urllib.error.HTTPError as error:
                if error.code != 429 or attempt == 2:
                    raise
                time.sleep(20)
        for paper_id, item in zip(chunk, items):
            if item and item.get("abstract"):
                found[paper_id] = (item.get("title") or "", item["abstract"])
    return found


def calibrate_profile(layout: Layout, engine: Path, key: str) -> int:
    labels = tracker_labels(layout)
    if sum(labels.values()) < 5 or len(labels) < 30:
        err("error: the tracker needs at least 30 verdicts, 5 of them positive, to say anything.")
        return 1
    abstracts = s2_abstracts(sorted(labels))
    import_engine(engine)
    from paper_radar.calibrate import calibrate, format_report
    from paper_radar.config import load_config
    from paper_radar.jev import make_backend
    from paper_radar.models import Paper
    from paper_radar.pipeline import judge_all
    from paper_radar.questions import build_questions

    config = load_config(PROFILE)
    papers = [
        Paper(id=f"arxiv:{pid}", source="arxiv", title=title, abstract=abstract, url=f"https://arxiv.org/abs/{pid}")
        for pid, (title, abstract) in abstracts.items()
    ]
    backend = make_backend(config.jev, env={"TYPESAFE_API_KEY": key})
    decisions, failures = judge_all(backend, papers, build_questions(config), config, log=err)
    score = {d.paper.id: (0.0 if d.band == "excluded" else d.relevance) for d in decisions}
    truth = {f"arxiv:{pid}": labels[pid] for pid in abstracts}
    positives = [score[k] for k, v in truth.items() if v and k in score]
    negatives = [score[k] for k, v in truth.items() if not v and k in score]
    auc = sum((p > n) + 0.5 * (p == n) for p in positives for n in negatives) / max(1, len(positives) * len(negatives))

    t = config.thresholds
    print(f"Profile: {PROFILE}")
    print(f"Tracker verdicts: {len(labels)} ({sum(labels.values())} passed triage); abstracts found: {len(abstracts)}")
    print(f"Judged {len(decisions)}, failed {len(failures)}, cost ≈${sum(d.cost for d in decisions):.4f}")
    print(f"AUC, passed-triage vs irrelevant: {auc:.3f}   (0.5 is chance, 1.0 separates them perfectly)")
    print(f"Current thresholds: must_read {t.must_read:.2f}, maybe {t.maybe:.2f}\n")
    print(format_report(calibrate(score, truth, target_precision=0.6, target_recall=0.9), 0.6, 0.9))
    missed = sorted((k for k, v in truth.items() if v and k in score and score[k] < t.maybe), key=lambda k: score[k])
    if missed:
        print("\nPassed triage but would fall below `maybe`:")
        for k in missed:
            print(f"  {score[k]:.2f} {k.removeprefix('arxiv:')} {abstracts[k.removeprefix('arxiv:')][0]}")
    return 0


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--key-file", type=Path, help="env file holding JEV_API_KEY or TYPESAFE_API_KEY")
    parser.add_argument("--limit", type=int, help="judge at most N papers")
    parser.add_argument("--date", help="YYYY-MM-DD label for the run and the shortlist (default: today, UTC)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="fetch and estimate the cost without calling Jev")
    mode.add_argument("--shortlist", action="store_true", help="reprint a stored shortlist; no network")
    mode.add_argument("--no-jev", action="store_true", help="print the raw feed for title triage")
    mode.add_argument("--calibrate", action="store_true", help="measure the profile against the tracker's verdicts")
    args = parser.parse_args(argv)

    project = args.project_dir or Path(
        os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("SCRAPALOT_ROOT") or Path.cwd()
    )
    layout = Layout(project.resolve())
    day = args.date or datetime.now(timezone.utc).date().isoformat()

    if args.shortlist:
        return print_shortlist(layout, day)
    engine = ensure_engine()
    if engine is None:
        return 2
    if args.no_jev:
        return print_feed(layout, engine, day)
    key = read_key(args.key_file or layout.default_key_file)
    if not key:
        err(
            "error: no Jev key. Set TYPESAFE_API_KEY or JEV_API_KEY, or pass --key-file <env file>.\n"
            "       Without one, --no-jev prints the raw feed for title triage."
        )
        return 2
    if args.calibrate:
        return calibrate_profile(layout, engine, key)

    extra = ["--date", day]
    if args.limit:
        extra += ["--limit", str(args.limit)]
    if args.dry_run:
        extra.append("--dry-run")
    if run_engine(layout, engine, key, extra) != 0:
        return 1
    return 0 if args.dry_run else print_shortlist(layout, day)


if __name__ == "__main__":
    raise SystemExit(main())
