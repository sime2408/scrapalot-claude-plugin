#!/usr/bin/env python3
"""Are a document's stored chapter titles headings, or the opening words of wrapped sentences?

A chapter detector reading hard-wrapped prose can take a whole line that opens a sentence for a heading, and the next
line finishes the sentence: Ripley's Scroll (0e0dd128) stored "A notable fact is" over "that the Philosophers’ Stone
wisdom had involved", and "We can shine a" over "spotlight onto the Three-in-One leitmotif". A reprocess wrote those
chapters after its parse audit, and chapter-windows.sh passed it, because its chapter SIZES were irregular. A heading is
not followed by a line that carries on in lower case.

For each distinct stored chapter title, every line of documents.content equal to it (markdown markup and whitespace
ignored) is read with the line after it, and the title runs on when most of those lines are followed by a line opening
with a lower-case letter. A title printed nowhere as a line of its own is not judged. One run-on title is usually a
long title wrapped onto two lines ("Extending the Life Span" / "of Knowledge"): the title is incomplete, the chapter is
still real. The layer is flagged when at least 2 printed titles run on and they are at least a quarter of the printed
titles. The OK line says how many titles were judged: a document printing none of its stored titles as a line of its
own is judged on nothing, and its OK proves nothing.

Fails closed: a database that cannot be read, or a document with no content or no chunks, prints CHAPTER_TITLES_FAIL.

Usage: chapter-titles.py <document_id>
"""

import json
import re
import subprocess
import sys

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MARKUP = re.compile(r"[#*_`>]+")
MIN_RUN_ON = 2
MIN_RUN_ON_SHARE = 0.25


def fail(reason: str) -> None:
    print(f"CHAPTER_TITLES_FAIL {reason}")
    raise SystemExit(2)


def read(doc_id: str) -> tuple[str, list[str]]:
    user = subprocess.run(["docker", "exec", "pgvector", "printenv", "POSTGRES_USER"], capture_output=True, text=True).stdout.strip()
    if not user:
        fail("pg_user_unreadable")
    sql = (
        "SELECT json_build_object("
        f"'content', (SELECT content FROM documents WHERE id = '{doc_id}'), "
        "'chunks', (SELECT count(*) FROM langchain_pg_embedding "
        f"WHERE cmetadata->>'document_id' = '{doc_id}'), "
        "'titles', (SELECT coalesce(json_agg(title ORDER BY first), '[]'::json) FROM ("
        "SELECT cmetadata->>'chapter_title' AS title, min((cmetadata->>'chunk_index')::int) AS first "
        f"FROM langchain_pg_embedding WHERE cmetadata->>'document_id' = '{doc_id}' "
        "AND coalesce(cmetadata->>'chapter_title', '') <> '' GROUP BY 1) titled));"
    )
    out = subprocess.run(
        ["docker", "exec", "-i", "pgvector", "psql", "-U", user, "-d", "scrapalot", "-At", "-v", "ON_ERROR_STOP=1"],
        input=sql, capture_output=True, text=True,
    )
    if out.returncode != 0:
        fail(f"query_error: {out.stderr.strip()[:160]}")
    data = json.loads(out.stdout)
    if not data.get("content"):
        fail("no_content")
    if not data.get("chunks"):
        fail("no_chunks")
    return data["content"], data["titles"] or []


def normal(line: str) -> str:
    return " ".join(MARKUP.sub(" ", line).split())


def main() -> int:
    if len(sys.argv) != 2 or not UUID.match(sys.argv[1]):
        print("usage: chapter-titles.py <document_id>")
        return 2
    doc_id = sys.argv[1]
    content, titles = read(doc_id)
    lines = content.split("\n")
    lines_by_text: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        text = normal(line)
        if text:
            lines_by_text.setdefault(text, []).append(i)

    printed = 0
    run_on = []
    for title in titles:
        where = lines_by_text.get(normal(title), [])
        if not where:
            continue
        printed += 1
        continued = 0
        for i in where:
            following = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
            continued += bool(following) and following[0].isalpha() and following[0].islower()
        if continued * 2 > len(where):
            run_on.append((title, continued, len(where)))

    print(f"CHAPTER_TITLES titles={len(titles)} printed_as_a_line={printed} run_on={len(run_on)}")
    for title, continued, total in run_on:
        print(f"CHAPTER_TITLES_RUN_ON {title!r} is followed by a lower-case line {continued} of {total} times")
    if len(run_on) >= MIN_RUN_ON and len(run_on) >= MIN_RUN_ON_SHARE * printed:
        print(
            f"CHAPTER_TITLES_SENTENCES {len(run_on)} of {printed} printed titles open a sentence the next line finishes: "
            "the chapter layer was read out of wrapped prose, not the book's headings"
        )
        return 1
    print(f"CHAPTER_TITLES_OK judged={printed} of {len(titles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
