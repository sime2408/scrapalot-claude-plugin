#!/usr/bin/env python3
"""Which stored entity names the book actually prints (G4b).

Three outcomes per name, over `documents.content` with its whitespace collapsed
once:

* WHOLE_WORD       the book prints the name as a whole word, its own spaces
                   matching any whitespace run;
* VARIANT_FORM     the name appears only inside a longer word, so the book
                   prints another form of it (`eagles` for `Eagle`);
* NOT_FOUND        no occurrence at any length.

Both relaxations exist because the first hand-written version of this check got
them wrong in opposite directions, on cc32d8f5:

* its first pass was `name in text`, a plain substring test, so `Eagle` counted
  as printed because the book prints `eagles` — 22 names passed that were never
  printed as themselves;
* it ran against the text with its line breaks, and a book hard-wraps, so every
  multi-word name broken across two lines failed — `Regaining the West Bank of
  Jerusalem` and `Michael Newton` were reported missing from the book that
  prints them.

Corrected, that book reads 637 whole word, 22 variant form, 49 not found where
the first instrument said 621 / 37 / 50.

The script only SORTS. Everything outside WHOLE_WORD has to be read against
spelling variants, morphology and the chunk text behind its edges before any
verdict — a printed plural and an invented label both land in the same two
buckets. G4b-read is that reading.

Usage: name-presence.py <document_id> [--list]
"""

from __future__ import annotations

import re
import subprocess
import sys

NEO4J = "neo4j"
PGVECTOR = "pgvector"
ENV_FILE = "/opt/scrapalot/scrapalot-chat/docker-scrapalot/.env"


def fail(message: str) -> None:
    print(f"PRESENCE_FAIL {message}")
    raise SystemExit(2)


def neo4j_password() -> str:
    try:
        with open(ENV_FILE, encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("NEO4J_PASSWORD="):
                    return line.split("=", 1)[1].strip()
    except OSError as error:
        fail(f"env_unreadable {error}")
    fail("no_neo4j_password")
    return ""


def run(command: list[str], what: str) -> str:
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        fail(f"{what} rc={result.returncode} {result.stderr.strip()[:160]}")
    return result.stdout


def normalise(value: str) -> str:
    return value.replace("­", "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').lower()


def main() -> None:
    if len(sys.argv) < 2:
        fail("usage: name-presence.py <document_id> [--list]")
    document_id = sys.argv[1]
    want_list = "--list" in sys.argv[2:]

    names_out = run(
        [
            "docker", "exec", NEO4J, "cypher-shell", "-u", "neo4j", "-p", neo4j_password(), "--format", "plain",
            f"MATCH (b:Book {{document_id:'{document_id}'}})-[:MENTIONS]->(e:Entity) RETURN DISTINCT e.name AS name ORDER BY name;",
        ],
        "neo4j",
    )
    names = []
    for line in names_out.splitlines()[1:]:
        line = line.strip()
        if line.startswith('"') and line.endswith('"'):
            names.append(line[1:-1])
        elif line:
            names.append(line)
    if not names:
        fail(f"no_entity_names_for {document_id}")

    content = run(
        [
            "docker", "exec", PGVECTOR, "psql", "-U", "scrapalot", "-d", "scrapalot", "-At", "-c",
            f"SELECT content FROM documents WHERE id='{document_id}';",
        ],
        "pgvector",
    )
    text = normalise(" ".join(content.split()))
    if len(text) < 200:
        fail(f"content_too_short chars={len(text)}")

    whole, variant, absent = [], [], []
    for name in names:
        key = normalise(name).strip()
        if not key:
            absent.append(name)
            continue
        pattern = r"(?<![^\W_])" + r"\s+".join(re.escape(word) for word in key.split()) + r"(?![^\W_])"
        if re.search(pattern, text):
            whole.append(name)
        elif key in text:
            variant.append(name)
        else:
            absent.append(name)

    print(f"PRESENCE names={len(names)} whole_word={len(whole)} variant_form={len(variant)} not_found={len(absent)}")
    print("PRESENCE_READ_ME a name outside WHOLE_WORD is not yet a defect: a printed plural and an invented label")
    print("    land in the same buckets. Read each one against the chunk its edges come from (G4b-read).")
    if want_list or variant or absent:
        for name in variant:
            print(f"VARIANT_FORM {name}")
        for name in absent:
            print(f"NOT_FOUND {name}")
    print("PRESENCE_OK")


if __name__ == "__main__":
    main()
