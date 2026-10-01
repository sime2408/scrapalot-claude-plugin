#!/usr/bin/env python3
"""Check scrapalot-ui source against the house design rules a browser cannot see.

    design-lint.py [--scope auto|app|public] [--json] <file-or-dir>...

The rendered checks (contrast, overflow, anti-patterns in the page) come from
the design review capture. This reads the source for the rules that live in
class names and style props: semantic colour tokens only, no tinted fills or
side stripes in the product, sharp corners and borders over shadows, and the
Radix traps that have already cost a bug hunt.

Scope decides which rules apply. The product ("app") is held to the restrained
system; public marketing pages are exempt from the shape and surface rules
because they are allowed a louder voice. "auto" decides per file by path.

Findings are advice with a line to look at, not a gate: the exit code is 0
unless --strict is given and something at severity P1 or P2 was found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PUBLIC_PAGES = {
    "home", "Index", "about", "contact", "pricing", "buy-license", "desktop", "shop",
    "blog", "blog-post", "privacy", "terms", "delete-account", "login", "sign-up",
    "invite", "team-invite", "NotFound",
}

CHROMATIC = (
    "red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose"
)
TOKENS = "primary|secondary|accent|info|success|warning|destructive|danger"


@dataclass
class Rule:
    id: str
    severity: str
    scope: str  # "app", "public" or "all"
    pattern: re.Pattern
    message: str


RULES = [
    Rule(
        "raw-palette-color",
        "P2",
        "app",
        re.compile(rf"(?<![\w-])(?:[a-z-]+:)*(?:bg|text|border|ring|fill|stroke|from|via|to|outline|decoration|divide|placeholder)-(?:{CHROMATIC})-\d{{2,3}}(?:/\d+)?\b"),
        "raw Tailwind palette colour; use a semantic token (bg-primary, text-destructive, ...) so accents and themes follow",
    ),
    Rule(
        "hex-color",
        "P2",
        "app",
        re.compile(r"(?:\[#[0-9a-fA-F]{3,8}\]|(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['\"]#[0-9a-fA-F]{3,8}['\"])"),
        "literal colour; use a semantic token or hsl(var(--token))",
    ),
    Rule(
        "tinted-fill",
        "P2",
        "app",
        re.compile(rf"(?<![\w:/-])bg-(?:{TOKENS})/(?:5|10|15|20|25|30)\b"),
        "tinted background fill; in the product colour lives in text, icons and borders (border-*/40), surfaces stay bg-card or bg-muted/30",
    ),
    Rule(
        "side-stripe",
        "P2",
        "all",
        re.compile(r"(?<![\w-])border-[lr]-(?:2|4|8|\[\d+px\])(?![\w-])"),
        "thick one-sided border as an accent stripe; the item's name, icon or avatar already carries that, remove it",
    ),
    Rule(
        "gradient-text",
        "P3",
        "all",
        re.compile(r"bg-clip-text[^\"'`]*text-transparent|text-transparent[^\"'`]*bg-clip-text|background-clip:\s*text"),
        "gradient-filled text; emphasis should come from weight or size",
    ),
    Rule(
        "rounded-drift",
        "P3",
        "app",
        re.compile(r"(?<![\w-])(?:[a-z-]+:)*rounded-(?:sm|md|lg|xl|2xl|3xl)(?![\w-])"),
        "rounded corner in the product; the system is sharp (rounded-full only for circles)",
    ),
    Rule(
        "heavy-shadow",
        "P3",
        "app",
        re.compile(r"(?<![\w-])(?:[a-z-]+:)*shadow-(?:md|lg|xl|2xl)(?![\w-])"),
        "drop shadow for elevation; the product uses border border-border",
    ),
    Rule(
        "decorative-loop",
        "P3",
        "all",
        re.compile(r"(?<![\w-])animate-(?:pulse|bounce|ping)(?![\w-])"),
        "looping animation; keep it only where it shows something live (a recording, a running job), never as decoration",
    ),
    Rule(
        "popover-offset-hack",
        "P1",
        "all",
        re.compile(r"!(?:left|right|top|bottom)-\["),
        "forced position on a floating element; use Radix collisionPadding / side / align",
    ),
    Rule(
        "scrollarea-in-flex",
        "P1",
        "all",
        re.compile(r"<ScrollArea[^>]*\bflex-1\b"),
        "Radix ScrollArea inside a flex column does not get the parent's height and wheel scrolling dies; use a native flex-1 min-h-0 overflow-y-auto div",
    ),
    Rule(
        "tiny-text",
        "P2",
        "all",
        re.compile(r"(?<![\w-])text-\[(?:[0-9]|10)px\]"),
        "text under 11 px; functional text needs 11 px or more, body 14 px or more",
    ),
    Rule(
        "outline-none-without-ring",
        "P1",
        "all",
        re.compile(r"(?<![\w:-])(?:outline-none|focus:outline-none)(?![\w-])(?![^\"'`]*focus-visible:ring)"),
        "focus outline removed with no focus-visible ring in the same class list; keyboard users lose their place",
    ),
    Rule(
        "zoom-disabled",
        "P1",
        "all",
        re.compile(r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1(?:\.0)?\b"),
        "pinch zoom disabled; WCAG 1.4.4 requires text to scale to 200 %",
    ),
]

EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
# Emoji in developer logs are not on screen.
LOG_LINE = re.compile(r"console\.|logger\.|\blog\(|debugLog|throw new")
SKIP_DIRS = {"node_modules", "dist", ".git", "test-results", "coverage"}
EXTENSIONS = {".tsx", ".ts", ".jsx", ".css", ".html"}


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    message: str
    snippet: str


def file_scope(path: Path) -> str:
    parts = path.parts
    if "landing" in parts or path.name == "landing.css":
        return "public"
    if "pages" in parts and path.stem in PUBLIC_PAGES:
        return "public"
    return "app"


def iter_files(paths: list[Path]):
    for root in paths:
        if root.is_file():
            yield root
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix in EXTENSIONS and not SKIP_DIRS.intersection(path.parts) and path.is_file():
                if ".test." in path.name or ".spec." in path.name:
                    continue
                yield path


def strip_comment(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith(("//", "*", "/*")):
        return ""
    return line


def lint(path: Path, scope_arg: str) -> list[Finding]:
    scope = file_scope(path) if scope_arg == "auto" else scope_arg
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError as exc:
        print(f"design-lint: cannot read {path}: {exc}", file=sys.stderr)
        return []
    found = []
    for number, raw in enumerate(lines, 1):
        line = strip_comment(raw)
        if not line or "design-lint: ignore" in raw:
            continue
        for rule in RULES:
            if rule.scope not in ("all", scope):
                continue
            for match in rule.pattern.finditer(line):
                found.append(Finding(str(path), number, rule.id, rule.severity, rule.message, match.group(0)[:80]))
        if path.suffix in {".tsx", ".jsx"} and EMOJI.search(line) and not LOG_LINE.search(line):
            found.append(
                Finding(str(path), number, "emoji-as-icon", "P3", "emoji in markup; icons come from lucide-react", line.strip()[:80])
            )
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--scope", choices=["auto", "app", "public"], default="auto")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="exit 1 on any P1 or P2 finding")
    args = parser.parse_args()

    findings = [f for path in iter_files(args.paths) for f in lint(path, args.scope)]
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        by_rule: dict[str, int] = {}
        for f in findings:
            by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
            print(f"{f.file}:{f.line}  {f.severity} {f.rule}  {f.snippet}")
        if findings:
            print()
            for rule, n in sorted(by_rule.items(), key=lambda kv: -kv[1]):
                message = next(r.message for r in RULES if r.id == rule) if rule != "emoji-as-icon" else "emoji in markup"
                print(f"{n:5d}  {rule}: {message}")
        else:
            print("design-lint: nothing found")
    if args.strict and any(f.severity in ("P1", "P2") for f in findings):
        sys.exit(1)


if __name__ == "__main__":
    main()
