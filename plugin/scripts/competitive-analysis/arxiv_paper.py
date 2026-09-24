#!/usr/bin/env python3
"""One arXiv paper, read politely: metadata, full text, and the evidence a PRD needs.

arXiv's robots.txt allows /abs, /html and /pdf with a crawl delay and forbids
indiscriminate automated downloads. So this reads one paper per call. It waits
the crawl delay between any two arXiv requests, across calls and processes,
through a lock and a timestamp file. It caps how many papers one hour may
fetch, and caches every paper it has read so none is downloaded twice. A
refusal (403, 406, 429, 503) ends the call without a retry, because retrying
into a cooldown is what extends it.

    arxiv_paper.py 2609.27009                  metadata + HTML full text
    arxiv_paper.py https://arxiv.org/abs/2609.27009v2
    arxiv_paper.py 2609.27009 --pdf            no HTML version: save the PDF for the Read tool

Writes `<project>/.claude/competitive-analysis/arxiv/papers/<id>/`: `meta.json`
from the abstract page's citation tags, then `fulltext.md` (headings, paragraphs,
tables as pipe rows, captions, math as its LaTeX source; the bibliography is
dropped) or `paper.pdf`. The summary puts first what the three-pillar check
needs: whether the paper reports tables of results, and which code, data or model
links it gives.

The project is --project-dir, else $CLAUDE_PROJECT_DIR, else $SCRAPALOT_ROOT,
else the working directory.

Exit codes: 0 done, 1 arXiv refused or the request failed, 2 not an arXiv id,
3 the hourly cap is reached.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ARXIV = "https://arxiv.org"
USER_AGENT = "scrapalot-competitive-analysis/2.0 (+https://github.com/sime2408/scrapalot-claude-plugin)"
CRAWL_DELAY = 15.0  # robots.txt Crawl-delay for arxiv.org, in seconds
MAX_PAPERS_PER_HOUR = 6
ID_RE = re.compile(r"^(\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?$")
ARTEFACT_HOSTS = (
    "github.com",
    "gitlab.com",
    "huggingface.co",
    "zenodo.org",
    "bitbucket.org",
    "codeberg.org",
    "anonymous.4open.science",
)
# arXiv's own HTML renderer links these from every page; they are not the paper's.
RENDERER_LINKS = ("github.com/arXiv/", "github.com/brucemiller/LaTeXML")


_ARTEFACT_URL = re.compile(
    r"https?://(?:www\.)?(?:" + "|".join(re.escape(h) for h in ARTEFACT_HOSTS) + r")/[^\s)\]}>,;\"'`]+"
)


# A clone URL's ".git", or text the HTML rendering glued straight onto it
# ("…/Repo.gitGitHub"), is not part of the repository's address.
_GIT_SUFFIX = re.compile(r"\.git(?:[A-Z][\w-]*)?$")


def _clean_link(url: str) -> str:
    return _GIT_SUFFIX.sub("", url.rstrip(".,"))


def artefact_links(*texts: str, seed: list[str] | None = None) -> list[str]:
    """Code, data and model links, whether the paper made them hyperlinks or plain text."""
    links: list[str] = []
    seen: set[str] = set()
    candidates = list(seed or []) + [url for text in texts for url in _ARTEFACT_URL.findall(text or "")]
    for url in map(_clean_link, candidates):
        if url.lower() not in seen and not any(r in url for r in RENDERER_LINKS):
            seen.add(url.lower())
            links.append(url)
    return links


class Refused(Exception):
    def __init__(self, url: str, status: int, retry_after: str | None):
        super().__init__(f"arXiv answered {status} for {url}")
        self.status = status
        self.retry_after = retry_after


def parse_id(raw: str) -> str | None:
    value = re.sub(r"^arxiv:", "", raw.strip(), flags=re.IGNORECASE)
    value = re.sub(r"^https?://(?:www\.|export\.)?arxiv\.org/(?:abs|pdf|html)/", "", value)
    value = value.removesuffix(".pdf").strip("/")
    match = ID_RE.match(value)
    return match.group(1) if match else None


# --------------------------------------------------------------------------- politeness


class Gate:
    """Spaces arXiv requests by the crawl delay and counts, per hour, the papers and
    listing pages read, shared by every process through one lock file."""

    def __init__(self, state: Path):
        state.mkdir(parents=True, exist_ok=True)
        self.path = state / ".arxiv-gate.json"
        self.lock_path = state / ".arxiv-gate.lock"

    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        data.setdefault("last_request", 0.0)
        data.setdefault("events", {})
        return data

    def _save(self, data: dict) -> None:
        self.path.write_text(json.dumps(data), encoding="utf-8")

    @contextlib.contextmanager
    def turn(self):
        with self.lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                wait = self._load()["last_request"] + CRAWL_DELAY - time.time()
                if wait > 0:
                    time.sleep(wait)
                yield
            finally:
                data = self._load()
                data["last_request"] = time.time()
                self._save(data)
                fcntl.flock(lock, fcntl.LOCK_UN)

    def recent(self, kind: str) -> int:
        cutoff = time.time() - 3600
        return sum(1 for t in self._load()["events"].get(kind, []) if t >= cutoff)

    def count(self, kind: str) -> None:
        with self.lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = self._load()
            cutoff = time.time() - 3600
            data["events"][kind] = [t for t in data["events"].get(kind, []) if t >= cutoff] + [time.time()]
            self._save(data)
            fcntl.flock(lock, fcntl.LOCK_UN)


def fetch(url: str, gate: Gate) -> bytes:
    with gate.turn():
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            raise Refused(url, error.code, error.headers.get("Retry-After")) from None


# --------------------------------------------------------------------------- parsing


class CitationMeta(HTMLParser):
    """The `citation_*` meta tags arXiv puts on every abstract page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, list[str]] = {}

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        attributes = dict(attrs)
        name = attributes.get("name") or ""
        if name.startswith("citation_"):
            self.meta.setdefault(name, []).append((attributes.get("content") or "").strip())


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIPPED_TAGS = {"script", "style", "nav", "header", "footer", "button", "noscript", "svg"}
SKIPPED_CLASSES = ("ltx_bibliography", "ltx_page_footer", "ltx_page_navbar", "ltx_TOC", "ltx_authors", "ltx_dates")
BLOCKS = {"p", "div", "section", "article", "li", "figcaption", "blockquote", "dd", "dt", "caption", "table"}


class FullText(HTMLParser):
    """arXiv's LaTeXML HTML as plain markdown: enough to judge results and methods,
    small enough to read whole."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.text: list[str] = []
        self.stack: list[tuple[str, bool]] = []  # (tag, skips its subtree)
        self.in_document = False  # only article.ltx_document is the paper; the rest is page chrome
        self.skip_depth = 0
        self.heading = 0
        self.table_depth = 0
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.rows: list[str] = []
        self.tables = 0
        self.sections: list[str] = []
        self.links: list[str] = []

    # -- helpers
    def _flush(self) -> None:
        text = " ".join("".join(self.text).split())
        self.text = []
        if not text:
            return
        if self.heading:
            self.blocks.append("#" * min(self.heading, 4) + " " + text)
            if self.heading == 2:
                self.sections.append(text)
        else:
            self.blocks.append(text)

    def _write(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)
        else:
            self.text.append(data)

    # -- parser hooks
    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if not self.in_document:
            if tag == "article" and "ltx_document" in classes:
                self.in_document = True
                self.stack.append((tag, False))
            return
        if tag == "a" and not self.skip_depth:
            href = attributes.get("href") or ""
            if any(host in href for host in ARTEFACT_HOSTS) and not any(r in href for r in RENDERER_LINKS):
                if href not in self.links:
                    self.links.append(href)
        if tag in VOID:
            if tag == "br" and not self.skip_depth:
                self._write(" ")
            return
        skips = tag in SKIPPED_TAGS or not classes.isdisjoint(SKIPPED_CLASSES) or tag == "math"
        self.stack.append((tag, skips))
        if self.skip_depth:
            if skips:
                self.skip_depth += 1
            return
        if tag == "math":
            source = attributes.get("alttext") or ""
            if source:
                self._write(f" ${source}$ ")
            self.skip_depth += 1
            return
        if skips:
            self.skip_depth += 1
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self.heading = int(tag[1])
        elif tag == "table" and "ltx_tabular" in classes:
            self._flush()
            self.table_depth += 1
            if self.table_depth == 1:
                self.tables += 1
                self.rows = []
        elif tag == "tr" and self.table_depth:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag in BLOCKS and not self.table_depth:
            self._flush()

    def handle_endtag(self, tag):
        # A stray end tag must not unwind the whole stack.
        if not self.in_document or tag in VOID or all(open_tag != tag for open_tag, _ in self.stack):
            return
        while self.stack:
            open_tag, skips = self.stack.pop()
            if skips and self.skip_depth:
                self.skip_depth -= 1
            elif not self.skip_depth:
                self._close(open_tag)
            if open_tag == tag:
                break
        if not self.stack:
            self.in_document = False

    def _close(self, tag: str) -> None:
        if re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self.heading = 0
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if any(self.row):
                self.rows.append("| " + " | ".join(self.row) + " |")
            self.row = None
        elif tag == "table" and self.table_depth:
            self.table_depth -= 1
            if not self.table_depth and self.rows:
                self.blocks.append("\n".join(self.rows))
                self.rows = []
        elif tag in BLOCKS and not self.table_depth:
            self._flush()

    def handle_data(self, data):
        if self.in_document and not self.skip_depth:
            self._write(data)

    def markdown(self) -> str:
        self._flush()
        return "\n\n".join(self.blocks) + "\n"


# --------------------------------------------------------------------------- main


def abstract_page(paper_id: str, gate: Gate) -> dict:
    parser = CitationMeta()
    parser.feed(fetch(f"{ARXIV}/abs/{paper_id}", gate).decode("utf-8", errors="replace"))
    m = parser.meta
    return {
        "id": paper_id,
        "title": " ".join((m.get("citation_title") or [""])[0].split()),
        "authors": m.get("citation_author", []),
        "date": (m.get("citation_date") or [""])[0],
        "online_date": (m.get("citation_online_date") or [""])[0],
        "abstract": " ".join((m.get("citation_abstract") or [""])[0].split()),
        "abs_url": f"{ARXIV}/abs/{paper_id}",
        "html_url": f"{ARXIV}/html/{paper_id}",
        "pdf_url": (m.get("citation_pdf_url") or [f"{ARXIV}/pdf/{paper_id}"])[0],
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def read_paper(paper_id: str, folder: Path, gate: Gate, want_pdf: bool) -> int:
    meta_path, text_path, pdf_path = folder / "meta.json", folder / "fulltext.md", folder / "paper.pdf"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        meta = None
    need_meta = meta is None
    # `has_html` is recorded once the HTML page was asked for, found or not.
    need_text = meta is None or "has_html" not in meta or (meta["has_html"] and not text_path.is_file())
    need_pdf = want_pdf and not pdf_path.is_file()
    if (need_meta or need_text or need_pdf) and gate.recent("paper") >= MAX_PAPERS_PER_HOUR:
        print(
            f"error: {MAX_PAPERS_PER_HOUR} papers were already fetched from arXiv in the last hour. "
            "Stop here and continue with what is cached.",
            file=sys.stderr,
        )
        return 3

    folder.mkdir(parents=True, exist_ok=True)
    touched_network = False
    try:
        if need_meta:
            touched_network = True
            meta = abstract_page(paper_id, gate)
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        if need_text:
            touched_network = True
            try:
                page = fetch(meta["html_url"], gate).decode("utf-8", errors="replace")
            except Refused as refusal:
                if refusal.status != 404:
                    raise
                page = ""
            meta["has_html"] = "ltx_document" in page
            text, hrefs = "", []
            if meta["has_html"]:
                full = FullText()
                full.feed(page)
                text, hrefs = full.markdown(), full.links
                text_path.write_text(
                    text if text.startswith("# ") else f"# {meta['title']}\n\n{text}", encoding="utf-8"
                )
                meta.update(tables=full.tables, sections=full.sections)
            meta["links"] = artefact_links(meta["abstract"], text, seed=hrefs)
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        if need_pdf:
            touched_network = True
            pdf_path.write_bytes(fetch(meta["pdf_url"], gate))
    except Refused as refusal:
        hint = f" (Retry-After: {refusal.retry_after})" if refusal.retry_after else ""
        print(f"error: {refusal}{hint}. Not retrying: a retry into a cooldown extends it.", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        print(f"error: request failed: {error}", file=sys.stderr)
        return 1
    finally:
        if touched_network:
            gate.count("paper")

    print_summary(meta, text_path, pdf_path)
    return 0


def print_summary(meta: dict, text_path: Path, pdf_path: Path) -> None:
    authors = meta.get("authors") or []
    shown = ", ".join(authors[:5]) + (f" (+{len(authors) - 5} more)" if len(authors) > 5 else "")
    print(f"arXiv:{meta['id']} — {meta['title']}")
    print(f"authors: {shown or '-'} · submitted {meta.get('date') or '-'}")
    if text_path.is_file():
        words = len(text_path.read_text(encoding="utf-8").split())
        print(
            f"full text: {text_path} ({words:,} words, {len(meta.get('sections', []))} sections, "
            f"{meta.get('tables', 0)} data tables)"
        )
    elif meta.get("has_html") is False:
        print("full text: arXiv has no HTML version of this paper; run again with --pdf and read the PDF")
    if pdf_path.is_file():
        print(f'pdf: {pdf_path} ({pdf_path.stat().st_size // 1024:,} KB) — read it with the Read tool, pages="1-20"')
    links = meta.get("links") or []
    print("code/data/model links: " + (" · ".join(links) if links else "none in the text"))
    if meta.get("sections"):
        print("sections: " + " · ".join(meta["sections"]))
    print(f"\nabstract: {meta.get('abstract') or '-'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paper", help="an arXiv id or an arxiv.org abs/pdf/html URL")
    parser.add_argument("--pdf", action="store_true", help="also save the PDF (for papers without an HTML version)")
    parser.add_argument("--project-dir", type=Path)
    args = parser.parse_args(argv)

    paper_id = parse_id(args.paper)
    if not paper_id:
        print(f"error: {args.paper!r} is not an arXiv id or URL", file=sys.stderr)
        return 2
    project = args.project_dir or Path(
        os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("SCRAPALOT_ROOT") or Path.cwd()
    )
    state = project.resolve() / ".claude" / "competitive-analysis" / "arxiv"
    folder = state / "papers" / paper_id.replace("/", "_")
    return read_paper(paper_id, folder, Gate(state), args.pdf)


if __name__ == "__main__":
    raise SystemExit(main())
