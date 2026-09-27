#!/usr/bin/env python3
"""arXiv papers triaged by Jev, found without the arXiv search API.

arXiv refuses bulk and unbounded API queries, and it cools an over-eager client's
IP down for hours, longer with every retry. So nothing here searches the API.
Papers come from the two places arXiv serves to automated readers:

* the RSS feed: the latest daily announcement, every requested category in one
  request, titles and abstracts included;
* the category listings, `/list/<category>/pastweek` and `/list/<category>/<YYYY-MM>`,
  which robots.txt allows and which page with skip/show. Each category and page is
  one request, spaced by the crawl delay that `arxiv_paper.py` enforces, and an
  hour may read only so many pages. Listings carry no abstracts, so those come
  from Semantic Scholar's batch endpoint, never from arXiv. A page read after
  arXiv's latest announcement is kept until the next one, so a run that fails
  after reading it is rerun without asking arXiv again.

Jev (TypeSafe's System One judge) then answers one yes/no question per Scrapalot
interest for every paper. Only the shortlist reaches Claude, and only the few
papers Claude picks from it are fetched in full, by `arxiv_paper.py`. A paper
judged in the last two weeks is not judged again, whichever source brought it,
and a listing asks Semantic Scholar only for the papers still to be judged, so
paging back over a page already read costs no judging and no abstracts.

The engine is JEV-Paper-Radar (MIT), pinned to one commit and kept in a cache
clone outside every repository. It needs nothing beyond the standard library.
The interests live in `arxiv_profile.toml` beside this script. Run state
(decisions, runs.jsonl, the rendered page, the shortlists) lives in
`<project>/.claude/competitive-analysis/arxiv/`, never in the plugin.

    arxiv_radar.py                              the latest announcement (RSS)
    arxiv_radar.py --categories cs.IR,cs.CL     only these categories, from either source
    arxiv_radar.py --period pastweek            the past week's listing, page 1
    arxiv_radar.py --period 2026-08 --page 2    a month's listing, second page
                   --page-size 250              entries per category and page (25-2000)
    arxiv_radar.py --limit 50                   judge at most 50 papers
    arxiv_radar.py --dry-run                    collect and estimate the cost; Jev is not called
    arxiv_radar.py --shortlist                  reprint a day's shortlist from stored decisions
    arxiv_radar.py --no-jev                     no key: print the papers for title triage
    arxiv_radar.py --calibrate                  score the tracker's past verdicts with the profile

The project is --project-dir, else $CLAUDE_PROJECT_DIR, else $SCRAPALOT_ROOT,
else the working directory. The key is TYPESAFE_API_KEY or JEV_API_KEY from the
environment, else the matching line of --key-file (default: the chat deploy's
env file). Only that line is used, and the key goes to the engine, never to
stdout. Semantic Scholar is asked without a key, from a pool every keyless
client shares, and answers 429 while that pool is busy; S2_API_KEY in the
environment gives this client a rate of its own.

Exit codes: 0 done, 1 arXiv refused, a source failed or the engine failed,
2 no key, no engine or bad arguments.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from arxiv_paper import Gate, Refused, fetch

ENGINE_REPO = "https://github.com/Eliot5566/JEV-Paper-Radar"
ENGINE_SHA = "c75595386975618f64dfde4368238731dae53510"
USER_AGENT = "scrapalot-competitive-analysis/2.0 (+https://github.com/sime2408/scrapalot-claude-plugin)"
S2_BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,abstract"
LISTING = "https://arxiv.org/list/{category}/{period}?skip={skip}&show={show}"
MAX_LISTING_PAGES_PER_HOUR = 30
# A busy keyless pool stays busy for minutes, so the waits double: 15, 30, 60, 120 s.
S2_ATTEMPTS = 5
# arXiv announces at 20:00 New York time, Sunday to Thursday. An hour later the
# listings have settled; a page read after that holds until the next announcement.
ANNOUNCE_TZ = ZoneInfo("America/New_York")
ANNOUNCE_SETTLED_HOUR = 21
ANNOUNCE_WEEKDAYS = {6, 0, 1, 2, 3}

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
_CATEGORY = re.compile(r"^[a-z-]+(\.[A-Za-z-]+)?$")
_PERIOD = re.compile(r"^(pastweek|\d{4}-(0[1-9]|1[0-2]))$")
_SOURCES_BLOCK = re.compile(r"^\[\[sources\]\]\n(?:[^\[\n].*\n)*", re.MULTILINE)
_ENTRY = re.compile(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", re.S)
_ENTRY_ID = re.compile(r'href\s*=\s*"/abs/([^"]+?)"')
_TITLE = re.compile(r"<div class=.list-title[^>]*>(.*?)</div>", re.S)
_AUTHORS = re.compile(r"<div class=.list-authors.>(.*?)</div>", re.S)
_SUBJECTS = re.compile(r"<div class=.list-subjects.>(.*?)</div>", re.S)
_SUBJECT_CODE = re.compile(r"\(([a-z-]+(?:\.[A-Za-z-]+)?)\)")
_TOTAL = re.compile(r"Total of ([\d,]+) entries")
_TAGS = re.compile(r"<[^>]+>")


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

    @property
    def profile_copy(self) -> Path:
        return self.state / "radar.toml"

    def decisions(self, day: str) -> Path:
        return self.state / "data" / "decisions" / f"{day}.jsonl"

    def shortlist(self, label: str) -> Path:
        return self.state / f"shortlist-{label}.jsonl"


@dataclass
class Listed:
    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)


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


def profile_categories() -> list[str]:
    with PROFILE.open("rb") as handle:
        return list(tomllib.load(handle)["sources"][0]["categories"])


def render_profile(*, categories: list[str] | None = None, feed_file: Path | None = None) -> str:
    """The profile with its source swapped: other RSS categories, or a local feed file."""
    text = PROFILE.read_text(encoding="utf-8")
    if feed_file is not None:
        block = f'[[sources]]\ntype = "arxiv"\nfile = "{feed_file.name}"\ninclude_cross_lists = true\n'
    elif categories:
        listed = ", ".join(json.dumps(c) for c in categories)
        block = f'[[sources]]\ntype = "arxiv"\ncategories = [{listed}]\ninclude_cross_lists = true\n'
    else:
        return text
    text, count = _SOURCES_BLOCK.subn(lambda _: block, text, count=1)
    if count != 1:
        raise ValueError(f"{PROFILE} has no [[sources]] block to replace")
    return text


def run_engine(layout: Layout, engine: Path, key: str, extra: list[str], profile_text: str) -> int:
    layout.state.mkdir(parents=True, exist_ok=True)
    # Written into the state directory so the engine anchors data/ and site/ there.
    layout.profile_copy.write_text(profile_text, encoding="utf-8")
    sys.stdout.flush()  # the engine writes to the same stdout; keep the order
    env = {**os.environ, "TYPESAFE_API_KEY": key, "PYTHONPATH": str(engine)}
    command = [
        sys.executable,
        "-m",
        "paper_radar",
        "run",
        "-c",
        str(layout.profile_copy),
        "--no-notify",
        *extra,
    ]
    return subprocess.run(command, cwd=layout.state, env=env).returncode


# --------------------------------------------------------------------------- listings


def _text(fragment: str) -> str:
    return " ".join(html.unescape(_TAGS.sub(" ", fragment)).split())


def _split_authors(text: str) -> list[str]:
    """Split on commas outside parentheses: an affiliation may hold commas of its own."""
    names, current, depth = [], [], 0
    for char in text:
        depth += (char == "(") - (char == ")" and depth > 0)
        if char == "," and depth == 0:
            names.append("".join(current))
            current = []
        else:
            current.append(char)
    names.append("".join(current))
    return [name.strip() for name in names if name.strip()]


def parse_listing(page: str) -> tuple[int | None, list[Listed]]:
    """Entries of one arXiv listing page, and the listing's total entry count."""
    entries = []
    for head, body in _ENTRY.findall(page):
        found, title = _ENTRY_ID.search(head), _TITLE.search(body)
        if not found or not title:
            continue
        authors, subjects = _AUTHORS.search(body), _SUBJECTS.search(body)
        entries.append(
            Listed(
                id=base_id(found.group(1)),
                title=_text(title.group(1)).removeprefix("Title:").strip(),
                authors=_split_authors(_text(authors.group(1))) if authors else [],
                categories=_SUBJECT_CODE.findall(_text(subjects.group(1))) if subjects else [],
            )
        )
    total = _TOTAL.search(page)
    return (int(total.group(1).replace(",", "")) if total else None), entries


def latest_announcement(now: datetime) -> datetime:
    """When the latest announcement's listings had settled. A holiday without an
    announcement only makes a kept page look older than it is, never newer."""
    moment = now.astimezone(ANNOUNCE_TZ).replace(hour=ANNOUNCE_SETTLED_HOUR, minute=0, second=0, microsecond=0)
    while moment > now or moment.weekday() not in ANNOUNCE_WEEKDAYS:
        moment -= timedelta(days=1)
    return moment


def kept_listing(path: Path, wanted: dict) -> tuple[dict[str, Listed], list[tuple[str, int | None, int]]] | None:
    """The page as read since the latest announcement, or None when it has to be read again."""
    try:
        kept = json.loads(path.read_text(encoding="utf-8"))
        if datetime.fromisoformat(kept["at"]) < latest_announcement(datetime.now(timezone.utc)):
            return None
        if any(kept[name] != value for name, value in wanted.items()):
            return None
        return {p["id"]: Listed(**p) for p in kept["papers"]}, [tuple(row) for row in kept["report"]]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def collect_listing(
    layout: Layout, categories: list[str], period: str, page: int, size: int
) -> tuple[dict[str, Listed], list[tuple[str, int | None, int]]]:
    """One listing page per category, through the shared politeness gate. Raises
    Refused on the first refusal, so the remaining categories are never asked.
    A page read in full is kept and served again until the next announcement."""
    path = layout.state / f"listing-{period}-p{page}.json"
    wanted = {"categories": categories, "page_size": size}
    kept = kept_listing(path, wanted)
    if kept is not None:
        err(f"  - {period}, page {page}: read since the latest announcement; arXiv not asked again")
        return kept
    started = datetime.now(timezone.utc)
    gate = Gate(layout.state)
    papers: dict[str, Listed] = {}
    report = []
    for category in categories:
        if gate.recent("listing") >= MAX_LISTING_PAGES_PER_HOUR:
            err(
                f"  ! {MAX_LISTING_PAGES_PER_HOUR} listing pages were read in the last hour; stopping before {category}"
            )
            break
        url = LISTING.format(category=category, period=period, skip=(page - 1) * size, show=size)
        err(f"  - {category} {period}, page {page}")
        body = fetch(url, gate).decode("utf-8", errors="replace")
        gate.count("listing")
        total, entries = parse_listing(body)
        report.append((category, total, len(entries)))
        for entry in entries:
            papers.setdefault(entry.id, entry)
    if len(report) == len(categories):
        record = {"at": started.isoformat(timespec="seconds"), **wanted, "report": report}
        record["papers"] = [asdict(paper) for paper in papers.values()]
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    return papers, report


def write_feed(path: Path, papers: list[tuple[Listed, str]]) -> None:
    """Listed papers as an arXiv-shaped RSS file, so the engine reads them like the feed."""
    items = []
    for paper, abstract in papers:
        description = f"arXiv:{paper.id} Announce Type: new Abstract: {abstract}"
        items.append(
            "<item>"
            f"<title>{escape(paper.title)}</title>"
            f"<link>https://arxiv.org/abs/{escape(paper.id)}</link>"
            f"<description>{escape(description)}</description>"
            + "".join(f"<category>{escape(c)}</category>" for c in paper.categories)
            + f"<dc:creator>{escape(', '.join(paper.authors))}</dc:creator>"
            "<arxiv:announce_type>new</arxiv:announce_type>"
            "</item>"
        )
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns:dc="http://purl.org/dc/elements/1.1/">'
        "<channel>" + "".join(items) + "</channel></rss>\n",
        encoding="utf-8",
    )


def print_paging(report: list[tuple[str, int | None, int]], period: str, page: int, size: int) -> None:
    first = (page - 1) * size + 1
    for category, total, count in report:
        if not count:
            print(f"{category} {period}: nothing on page {page} (total {total})")
            continue
        last = first + count - 1
        more = f"; next: --page {page + 1}" if total and last < total else "; last page"
        print(f"{category} {period}: entries {first}-{last} of {total}{more}")


# --------------------------------------------------------------------------- shortlist


def tracked_ids(layout: Layout) -> set[str]:
    if not layout.tracker.is_file():
        return set()
    ids = set()
    for line in layout.tracker.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "|" in line:
            ids.add(base_id(line.split("|", 1)[0]))
    return ids


def judged_ids(layout: Layout, engine: Path, day: str) -> set[str]:
    """What the engine judged inside its dedupe window: it would not judge those again,
    so their abstracts are not worth a Semantic Scholar request."""
    import_engine(engine)
    from paper_radar.config import load_config
    from paper_radar.store import Store

    window = load_config(PROFILE).output.dedupe_days
    return {base_id(i) for i in Store(layout.state / "data").seen_ids(date.fromisoformat(day), window)}


def shown_ids(layout: Layout, day: str) -> set[str]:
    path = layout.decisions(day)
    if not path.is_file():
        return set()
    return {
        base_id(json.loads(line)["paper"]["id"])
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def _top_interests(interests: dict[str, float], n: int = 3, floor: float = 0.3) -> list[tuple[str, float]]:
    ranked = sorted(interests.items(), key=lambda kv: kv[1], reverse=True)
    return [(k, v) for k, v in ranked[:n] if v >= floor]


def print_shortlist(layout: Layout, day: str, label: str, skip: set[str] | None = None) -> int:
    """Print the day's must-read and maybe papers, minus tracked ones and minus `skip`
    (what earlier runs of the day already showed). Returns how many it printed.
    The label's file gains the printed papers and keeps what earlier runs put there,
    so a rerun with nothing new never empties it."""
    path = layout.decisions(day)
    if not path.is_file():
        print(f"No must-read or maybe paper stored for {day}.")
        return 0
    tracked = tracked_ids(layout)
    hidden = tracked | (skip or set())
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = sorted(
        (r for r in records if r["band"] in SHOWN_BANDS and base_id(r["paper"]["id"]) not in hidden),
        key=lambda r: r["relevance"],
        reverse=True,
    )
    fresh = [
        {
            "id": base_id(r["paper"]["id"]),
            "band": r["band"],
            "relevance": r["relevance"],
            "interests": dict(_top_interests(r["interests"])),
            "paper_type": r.get("paper_type"),
            "code": r.get("code"),
            "evidence": r.get("evidence"),
            "title": r["paper"]["title"],
            "abstract": r["paper"].get("abstract", ""),
            "url": r["paper"]["url"],
            "categories": r["paper"].get("categories", []),
        }
        for r in rows
    ]
    out = layout.shortlist(label)
    earlier = []
    if out.is_file():
        added = {record["id"] for record in fresh}
        lines = out.read_text(encoding="utf-8").splitlines()
        earlier = [json.loads(line) for line in lines if line.strip()]
        earlier = [record for record in earlier if record["id"] not in added | tracked]
    with out.open("w", encoding="utf-8") as handle:
        for record in sorted(fresh + earlier, key=lambda record: record["relevance"], reverse=True):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    must = sum(1 for r in rows if r["band"] == "must_read")
    kept = f"; {len(earlier)} from earlier runs kept in the file" if earlier else ""
    print(f"\n{label}: {must} must-read, {len(rows) - must} maybe (tracked papers left out{kept})")
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
    return len(rows)


def write_unjudged(out: Path, papers: list[dict]) -> None:
    with out.open("w", encoding="utf-8") as handle:
        for paper in papers:
            handle.write(json.dumps(paper, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- abstracts


def _s2_error(error: urllib.error.HTTPError) -> str:
    try:
        return str(json.loads(error.read() or b"{}").get("error") or "")
    except (OSError, ValueError, AttributeError):
        return ""


def s2_abstracts(ids: list[str]) -> dict[str, tuple[str, str]]:
    """Titles and abstracts from Semantic Scholar's batch endpoint, so neither a
    listing page nor a calibration run asks arXiv for them."""
    headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
    if os.environ.get("S2_API_KEY", "").strip():
        headers["x-api-key"] = os.environ["S2_API_KEY"].strip()
    found: dict[str, tuple[str, str]] = {}
    for start in range(0, len(ids), 500):
        if start:
            time.sleep(1)
        chunk = ids[start : start + 500]
        body = json.dumps({"ids": [f"ARXIV:{i}" for i in chunk]}).encode("utf-8")
        for attempt in range(S2_ATTEMPTS):
            request = urllib.request.Request(S2_BATCH, data=body, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    items = json.loads(response.read())
                break
            except urllib.error.HTTPError as error:
                # A batch in which Semantic Scholar knows no paper at all is refused with this
                # 400 rather than answered with nulls: none of them has an abstract yet.
                if error.code == 400 and _s2_error(error).startswith("No valid paper ids"):
                    items = []
                    break
                if error.code != 429 or attempt == S2_ATTEMPTS - 1:
                    raise
                hinted = (error.headers.get("Retry-After") or "").strip()
                wait = min(300, max(15 * 2**attempt, int(hinted) if hinted.isdigit() else 0))
                err(f"  Semantic Scholar is busy (429); asking again in {wait} s")
                time.sleep(wait)
        for paper_id, item in zip(chunk, items):
            if item and item.get("abstract"):
                found[paper_id] = (item.get("title") or "", item["abstract"])
    return found


# --------------------------------------------------------------------------- modes


def run_rss(args, layout: Layout, engine: Path, key: str, day: str, extra: list[str]) -> int:
    before = shown_ids(layout, day)
    if run_engine(layout, engine, key, extra, render_profile(categories=args.categories)) != 0:
        return 1
    if not args.dry_run:
        print_shortlist(layout, day, day, skip=before)
    return 0


def run_listing(args, layout: Layout, engine: Path, key: str | None, day: str, extra: list[str]) -> int:
    categories = args.categories or profile_categories()
    try:
        listed, report = collect_listing(layout, categories, args.period, args.page, args.page_size)
    except Refused as refusal:
        hint = f" (Retry-After: {refusal.retry_after})" if refusal.retry_after else ""
        err(f"error: {refusal}{hint}. Not retrying: a retry into a cooldown extends it.")
        return 1
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        err(f"error: listing request failed: {error}")
        return 1
    print_paging(report, args.period, args.page, args.page_size)

    tracked = tracked_ids(layout)
    judged = judged_ids(layout, engine, day) - tracked
    fresh = [p for p in listed.values() if p.id not in tracked and p.id not in judged]
    print(
        f"{len(listed)} listed: {sum(p.id in tracked for p in listed.values())} tracked, "
        f"{sum(p.id in judged for p in listed.values())} judged by an earlier run, {len(fresh)} to judge"
    )
    if not fresh:
        print("Nothing new on this page. `--shortlist --date <day>` reprints an earlier run's shortlist.")
        return 0
    try:
        abstracts = s2_abstracts([p.id for p in fresh])
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        err(f"error: Semantic Scholar did not return abstracts: {error}. The page is kept: a rerun does not ask arXiv.")
        return 1
    readable = [(p, abstracts[p.id][1]) for p in fresh if p.id in abstracts]
    missing = [p for p in fresh if p.id not in abstracts]
    page = f"{args.period}-p{args.page}"
    # The past week moves every day, so its outputs carry the day: a later week's run
    # must not overwrite an earlier week's shortlist. A month's page does not move.
    label = f"pastweek-{day}-p{args.page}" if args.period == "pastweek" else page
    layout.state.mkdir(parents=True, exist_ok=True)

    if key is None:  # --no-jev: hand the papers to Claude unjudged
        out = layout.state / f"feed-{label}.jsonl"
        write_unjudged(
            out,
            [{"id": p.id, "title": p.title, "abstract": a, "categories": p.categories} for p, a in readable]
            + [{"id": p.id, "title": p.title, "abstract": "", "categories": p.categories} for p in missing],
        )
        print(f"Not judged. Full records: {out}")
        for p, _ in readable:
            print(f"{p.id:<11} {p.title}")
    elif readable:
        feed = layout.state / f"listing-{page}.xml"
        write_feed(feed, readable)
        before = shown_ids(layout, day)
        if run_engine(layout, engine, key, extra, render_profile(feed_file=feed)) != 0:
            return 1
        if not args.dry_run and not print_shortlist(layout, day, label, skip=before):
            print(f"None of the {len(readable)} papers judged now reached the shortlist.")
    if missing:
        print("\nNo abstract yet (not judged; read the title, or page back later):")
        for p in missing:
            print(f"  {p.id:<11} {p.title}")
    return 0


def run_rss_unjudged(args, layout: Layout, engine: Path, day: str) -> int:
    """The RSS feed without Jev: one request, titles for Claude to triage by hand."""
    import_engine(engine)
    from paper_radar.config import load_config
    from paper_radar.sources import collect

    layout.state.mkdir(parents=True, exist_ok=True)
    layout.profile_copy.write_text(render_profile(categories=args.categories), encoding="utf-8")
    config = load_config(layout.profile_copy)
    papers = collect(config.sources, today=date.fromisoformat(day), base_dir=layout.state, log=err)
    seen = tracked_ids(layout)
    papers = [p for p in papers if base_id(p.id) not in seen]
    out = layout.state / f"feed-{day}.jsonl"
    write_unjudged(
        out,
        [
            {"id": base_id(p.id), "title": p.title, "abstract": p.abstract, "url": p.url, "categories": p.categories}
            for p in papers
        ],
    )
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


def parse_categories(value: str) -> list[str]:
    categories = [c.strip() for c in value.split(",") if c.strip()]
    bad = [c for c in categories if not _CATEGORY.match(c)]
    if not categories or bad:
        raise argparse.ArgumentTypeError(f"not arXiv categories: {', '.join(bad) or value!r} (e.g. cs.IR,cs.CL)")
    return categories


def parse_period(value: str) -> str:
    if not _PERIOD.match(value):
        raise argparse.ArgumentTypeError(f"{value!r}: use pastweek or YYYY-MM")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--key-file", type=Path, help="env file holding JEV_API_KEY or TYPESAFE_API_KEY")
    parser.add_argument("--categories", type=parse_categories, help="comma-separated arXiv categories")
    parser.add_argument("--period", type=parse_period, help="read a listing instead of the feed: pastweek or YYYY-MM")
    parser.add_argument("--page", type=int, default=1, help="listing page, from 1 (needs --period)")
    parser.add_argument("--page-size", type=int, help="entries per category and page, 25-2000 (default 250)")
    parser.add_argument("--limit", type=int, help="judge at most N papers")
    parser.add_argument("--date", help="YYYY-MM-DD label for the run and the shortlist (default: today, UTC)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="collect and estimate the cost without calling Jev")
    mode.add_argument("--shortlist", action="store_true", help="reprint a stored shortlist; no network")
    mode.add_argument("--no-jev", action="store_true", help="print the papers for title triage")
    mode.add_argument("--calibrate", action="store_true", help="measure the profile against the tracker's verdicts")
    args = parser.parse_args(argv)
    if not args.period and (args.page != 1 or args.page_size is not None):
        parser.error("--page and --page-size page a listing; add --period pastweek or --period YYYY-MM")
    args.page_size = args.page_size or 250
    if args.page < 1 or not 25 <= args.page_size <= 2000:
        parser.error("--page starts at 1 and --page-size is 25-2000")

    project = args.project_dir or Path(
        os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("SCRAPALOT_ROOT") or Path.cwd()
    )
    layout = Layout(project.resolve())
    day = args.date or datetime.now(timezone.utc).date().isoformat()

    if args.shortlist:
        print_shortlist(layout, day, day)
        return 0
    engine = ensure_engine()
    if engine is None:
        return 2
    if args.no_jev:
        if args.period:
            return run_listing(args, layout, engine, None, day, [])
        return run_rss_unjudged(args, layout, engine, day)
    key = read_key(args.key_file or layout.default_key_file)
    if not key:
        err(
            "error: no Jev key. Set TYPESAFE_API_KEY or JEV_API_KEY, or pass --key-file <env file>.\n"
            "       Without one, --no-jev prints the papers for title triage."
        )
        return 2
    if args.calibrate:
        return calibrate_profile(layout, engine, key)

    extra = ["--date", day]
    if args.limit:
        extra += ["--limit", str(args.limit)]
    if args.dry_run:
        extra.append("--dry-run")
    if args.period:
        return run_listing(args, layout, engine, key, day, extra)
    return run_rss(args, layout, engine, key, day, extra)


if __name__ == "__main__":
    raise SystemExit(main())
