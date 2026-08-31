---
name: okf
description: Rules for reading, writing, and validating Open Knowledge Format (OKF v0.1) bundles in Scrapalot — the corpus collection export and the second-brain export. Use when touching anything under src/main/service/knowledge_export/, when adding a new export surface, or when a user asks whether a bundle is portable/conformant.
---

# OKF bundles in Scrapalot

Open Knowledge Format is a vendor-neutral spec (v0.1) for knowledge as markdown
files with YAML frontmatter. Scrapalot writes two bundles, and both must stay
readable by tools that have never heard of us — that is the entire point.

| Bundle | Producer | Reaches the user via |
|---|---|---|
| Collection corpus (documents / chapters / entities) | `okf_exporter.export_collection_bundle` | `ExportCollectionBundle` RPC — **no REST route or UI button exists yet** |
| Second brain (memories / insights / episodes / profiles) | `brain_okf_exporter.export_brain_bundle` | `ExportUserMemories(format="okf")` → `GET /api/v1/memory/export/okf` → panel button |

Shared markdown primitives live in `okf_markdown.py`. The conformance checker is
`okf_conformance.py`; the tests are `tests/integration/test_okf_bundle_conformance.py`.

## The three rules that make a bundle conforming

1. **Every non-reserved `.md` file has parseable YAML frontmatter.** (violation = E1)
2. **That frontmatter declares a non-empty `type`.** `type` is the ONLY required
   field and its value is a free-form string. (violation = E2)
3. **Reserved files follow their own shape.** (violation = E3)

Everything else is a warning. The spec obliges consumers to accept bundles with
missing optional fields, unknown `type` values, and broken links — so never
promote those to errors, and never reject an imported bundle for them.

## Reserved files — the rule that is easiest to get wrong

`index.md` and `log.md` are **structural, not concepts**, so they carry **no
frontmatter at all**. The single exception: a bundle root's `index.md` may
declare `okf_version` — and nothing else. Use `okf_markdown.root_index_header()`
rather than hand-writing it.

- `index.md` — a directory listing. Anything you want to say about the bundle
  goes in the body, under the `#` heading, not in frontmatter.
- `log.md` — a changelog: `## <ISO 8601 date>` sections, **newest first**.

Both of ours are generated from data we already store (document timestamps;
memory `created_at` / `valid_to` / share events), so a changelog costs no new
persistence. Keep it that way.

## Frontmatter fields

| Field | Status | Notes |
|---|---|---|
| `type` | **required** | free-form: `Document`, `Chapter`, `Entity`, `Memory`, `Insight`, `Episode`, `UserProfile` |
| `title` | recommended | display name |
| `description` | recommended | one sentence |
| `resource` | recommended | asset URI — if it is a bundle-relative path, make it correct **from that file's directory** |
| `tags`, `timestamp` | optional | `timestamp` is ISO 8601 |

Domain fields beyond the spec (`tier`, `importance`, `scope`, `in_core`,
`valid_to`, …) are fine and expected — consumers must preserve unknown fields.
Emit them through `okf_markdown.frontmatter(extra={...})`, which drops empties
rather than writing blank keys.

## Links

Relative markdown links (`./sibling.md`, `../documents/x.md`). The spec prefers
absolute (`/documents/x.md`) because those survive a file move, but our bundles
have a fixed layout generated as a unit, and relative links are what also
resolves in Obsidian, GitHub, and a plain editor. Do not "fix" this to absolute
without a reason that beats that.

A broken link is legal — it means future content, not an error. Our own exports
nonetheless resolve every link they emit; the tests assert zero `W-LINK`
warnings for the brain bundle, so keep new links pointing at files you actually
write.

## When you add or change an export

1. Emit through `okf_markdown.py` — never hand-build a `---` block.
2. Extend `tests/integration/test_okf_bundle_conformance.py`: assert
   `errors_only(validate_zip(bundle)) == []` over a **real** export, not a fixture.
3. Never fabricate data to fill a recommended field. An absent summary is an
   absent summary — `description` falls back to the title, and that is conforming.
4. Do not impose a taxonomy. `type` values follow our domain nouns; do not
   invent a hierarchy the graph does not have.

## Cross-checking against the wider ecosystem

`okflint` (PyPI, `pip install okflint`) is an independent linter for the same
spec — 18 rules, `audit` / `validate` / `index` commands. It is **not** a
dependency of this repo: our checker runs in-process with no install, and the
image stays lean. Reach for okflint on the host when you want a second opinion
on a bundle we produced, or before trusting a third-party bundle:

```bash
python -m zipfile -e bundle.zip /tmp/okf-check/ && okflint validate /tmp/okf-check/
```

If okflint and `okf_conformance.py` ever disagree, the spec wins — read it,
then fix whichever of the two is wrong.
