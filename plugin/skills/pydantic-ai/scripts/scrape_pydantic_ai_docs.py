#!/usr/bin/env python3
"""Scrape the official Pydantic AI documentation into a single Markdown bundle.

This regenerates the reference file used by the `scrapalot:pydantic-ai` skill.
The Pydantic docs site is server-side rendered, so plain HTTP GETs are enough
(no headless browser / JS execution required).

How it works
------------
1. Fetch the overview page, whose HTML already contains the full sidebar
   navigation. Every ``href="/docs/ai/..."`` link on that page is one doc page.
2. Fetch each page politely (retries + backoff + small sleep), extract the
   article body (the element with CSS class ``main-pane``), and convert it to
   Markdown.
3. Concatenate everything into one Markdown file with a table of contents.

Dependencies (NOT in the host's stock python3 — install into a venv):
    python3 -m venv /tmp/scrape-venv
    /tmp/scrape-venv/bin/pip install requests beautifulsoup4 markdownify lxml
    /tmp/scrape-venv/bin/python scrape_pydantic_ai_docs.py

The script is idempotent: re-running it overwrites OUTPUT_PATH with a freshly
scraped bundle. Ordering follows the sidebar (first-seen link order), so the
output is deterministic across runs (network permitting).

NOTE: No timestamps/dates are emitted (the run environment has no reliable wall
clock). ``time`` is used only for polite sleeping and retry backoff.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import time

from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown
import requests

# Third-party packages this script needs (documented so a human can pip-install).
REQUIREMENTS = ["requests", "beautifulsoup4", "markdownify", "lxml"]

# --- Configuration constants (change these to retarget the scraper) ----------
BASE = "https://pydantic.dev"
START_URL = "https://pydantic.dev/docs/ai/overview"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "references" / "output-pydantic-ai_docs.md"

# Only follow links that point into the AI docs tree.
LINK_PATTERN = re.compile(r"^/docs/ai/")

# HTTP behaviour.
USER_AGENT = "Mozilla/5.0"
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
POLITE_DELAY = 0.35  # seconds between successful page fetches
BACKOFF_BASE = 1.5  # seconds, multiplied by the (1-based) attempt number

# HTML selectors, in priority order, for the article body of each page.
CONTENT_SELECTORS = [".main-pane", "main", "article"]


def make_session() -> requests.Session:
    """Return a requests session with the polite User-Agent preset."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch(session: requests.Session, url: str) -> str:
    """GET ``url`` with retries + exponential-ish backoff.

    Raises the last exception if all attempts fail.
    """
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                sleep_for = BACKOFF_BASE * attempt
                print(
                    f"  ! attempt {attempt}/{MAX_RETRIES} failed for {url}: {exc} -> retrying in {sleep_for:.1f}s",
                    file=sys.stderr,
                )
                time.sleep(sleep_for)
    assert last_exc is not None
    raise last_exc


def normalize_href(href: str) -> str:
    """Strip URL fragment/query and any trailing slash from a href path."""
    href = href.split("#", 1)[0]
    href = href.split("?", 1)[0]
    return href.rstrip("/")


def collect_doc_paths(html: str) -> list[str]:
    """Return unique, first-seen-ordered ``/docs/ai/...`` paths from the page."""
    soup = BeautifulSoup(html, "lxml")
    ordered: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not LINK_PATTERN.match(href):
            continue
        path = normalize_href(href)
        if path and path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def extract_content(html: str) -> tuple[str, str]:
    """Extract (title, markdown_body) from a doc page's HTML.

    Title = first <h1> inside the content element, else the <title> tag.
    Body  = the content element converted to Markdown (ATX headings).
    """
    soup = BeautifulSoup(html, "lxml")

    content = None
    for selector in CONTENT_SELECTORS:
        content = soup.select_one(selector)
        if content is not None:
            break
    if content is None:
        # Last resort: whole document body.
        content = soup.body or soup

    # Drop non-content noise before conversion.
    for tag in content.find_all(["script", "style", "nav"]):
        tag.decompose()

    h1 = content.find("h1")
    if h1 is not None and h1.get_text(strip=True):
        title = h1.get_text(strip=True)
    elif soup.title is not None and soup.title.get_text(strip=True):
        title = soup.title.get_text(strip=True)
    else:
        title = "Untitled"

    markdown = html_to_markdown(str(content), heading_style="ATX")
    # Collapse runs of 3+ blank lines that markdownify tends to emit.
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return title, markdown


def build_document(pages: list[dict]) -> str:
    """Assemble the final Markdown bundle from successfully scraped pages."""
    parts: list[str] = []
    parts.append("# Pydantic AI Documentation")
    parts.append("")
    parts.append(
        "_Auto-generated by `scrape_pydantic_ai_docs.py` from <https://pydantic.dev/docs/ai>. Do not edit by hand — re-run the scraper to refresh._"
    )
    parts.append("")

    # Table of contents.
    parts.append("## Table of Contents")
    parts.append("")
    for index, page in enumerate(pages, start=1):
        parts.append(f"{index}. [{page['title']}](#doc-{index})")
    parts.append("")

    # Body sections.
    for index, page in enumerate(pages, start=1):
        parts.append("---")
        parts.append("")
        parts.append(f'<a id="doc-{index}"></a>')
        parts.append("")
        parts.append(f"## {index}. {page['title']}")
        parts.append("")
        parts.append(f"> Source: {page['url']}")
        parts.append("")
        parts.append(page["body"])
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    session = make_session()

    print(f"Fetching sidebar from {START_URL} ...")
    start_html = fetch(session, START_URL)
    paths = collect_doc_paths(start_html)
    print(f"Found {len(paths)} unique /docs/ai/ links.")

    pages: list[dict] = []
    failures: list[tuple[str, str]] = []  # (url, error)

    for position, path in enumerate(paths, start=1):
        url = BASE + path
        print(f"[{position}/{len(paths)}] {url}")
        try:
            html = fetch(session, url)
            title, body = extract_content(html)
            pages.append({"title": title, "url": url, "body": body})
        except Exception as exc:
            print(f"  ! FAILED: {exc}", file=sys.stderr)
            failures.append((url, str(exc)))
        finally:
            # Be polite regardless of success/failure.
            time.sleep(POLITE_DELAY)

    document = build_document(pages)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(document, encoding="utf-8")

    byte_count = len(document.encode("utf-8"))
    line_count = document.count("\n")

    print("\n===== SUMMARY =====")
    print(f"Total links found : {len(paths)}")
    print(f"Pages succeeded   : {len(pages)}")
    print(f"Pages failed      : {len(failures)}")
    if failures:
        print("Failed URLs:")
        for url, err in failures:
            print(f"  - {url}  ({err})")
    print(f"Output file       : {OUTPUT_PATH}")
    print(f"Output size       : {byte_count} bytes, {line_count} lines")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
