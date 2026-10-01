#!/usr/bin/env python3
"""Summarise a design review run, optionally against an earlier one.

    summarize.py <run-dir> [--against <earlier-run-dir>] [--json]

A run directory is what the scrapalot-ui design capture writes (report.json,
findings/, shots/, aria/). The summary groups what the detectors found by rule
across every screen, width, theme and accent, so one defect seen in twelve
captures reads as one line, and lists what a screen tried to save when it
opened (the capture blocks every write).

With --against, each rule shows its count before and after, and rules that
appeared or disappeared are called out. Compare runs of the same screens,
widths, themes and accents; anything else compares different pages.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3, None: 4}


def load_run(run: Path) -> dict:
    report_path = run / "report.json"
    if not report_path.is_file():
        sys.exit(f"summarize: {run} has no report.json")
    report = json.loads(report_path.read_text())
    findings = []
    for capture in report.get("captures", []):
        if not capture.get("findings"):
            continue
        path = run / capture["findings"]
        if path.is_file():
            findings.append((capture, json.loads(path.read_text())))
    return {"report": report, "findings": findings}


def combo(capture: dict) -> str:
    return f"{capture['surface']} {capture['viewport']} {capture['theme']} {capture['accent']}"


def aggregate(run: dict) -> dict:
    axe: dict[str, dict] = {}
    impeccable: dict[str, dict] = {}
    overflow, errors, writes = [], defaultdict(set), defaultdict(set)
    detector_errors = []
    for capture, data in run["findings"]:
        where = combo(capture)
        for v in data.get("axe") or []:
            entry = axe.setdefault(
                v["id"],
                {"impact": v.get("impact"), "help": v.get("help"), "count": 0, "captures": set(), "examples": []},
            )
            entry["count"] += v.get("count", 0)
            entry["captures"].add(where)
            for ex in v.get("examples", [])[:2]:
                if len(entry["examples"]) < 3:
                    target = " ".join(str(t) for t in ex.get("target", []))
                    entry["examples"].append(f"{target}: {(ex.get('summary') or '').splitlines()[-1][:160]}")
        imp = data.get("impeccable")
        if isinstance(imp, dict) and imp.get("error"):
            detector_errors.append(f"{where}: {imp['error']}")
        for group in imp if isinstance(imp, list) else []:
            for f in group.get("findings", []):
                key = f.get("type") or f.get("id") or "unknown"
                entry = impeccable.setdefault(
                    key,
                    {
                        "name": f.get("name"),
                        "category": f.get("category"),
                        "advisory": f.get("advisory", False),
                        "count": 0,
                        "captures": set(),
                        "examples": [],
                    },
                )
                entry["count"] += 1
                entry["captures"].add(where)
                example = f"{(f.get('detail') or '')[:140]} @ {group.get('selector', '?')[:90]}"
                if len(entry["examples"]) < 3 and example not in entry["examples"]:
                    entry["examples"].append(example)
        metrics = data.get("metrics") or {}
        if metrics.get("overflowX"):
            overflow.append(
                f"{where}: page {metrics.get('pageWidth')} px wide in a {metrics.get('viewportWidth')} px window;"
                f" past the edge: {', '.join(metrics.get('pastRightEdge') or []) or '?'}"
            )
        for e in data.get("consoleErrors") or []:
            errors[e.splitlines()[0][:200]].add(where)
        for w in data.get("blockedWrites") or []:
            writes[w].add(where)
    return {
        "axe": axe,
        "impeccable": impeccable,
        "overflow": overflow,
        "errors": errors,
        "writes": writes,
        "detector_errors": detector_errors,
    }


def spread(captures: set, total: int) -> str:
    return f"{len(captures)}/{total} captures"


def print_summary(run_dir: Path, run: dict, agg: dict, before: dict | None) -> None:
    report = run["report"]
    total = len(run["findings"]) or 1
    served = f"local build {report['localDist']}" if report.get("localDist") else "deployed build"
    print(f"Design review {run_dir}")
    print(
        f"screens {', '.join(report['surfaces'])} | widths {', '.join(report['viewports'])} |"
        f" themes {', '.join(report['themes'])} | accents {', '.join(report['accents'])} | {report['lang']} | {served}"
    )
    detectors = [name for name, on in report.get("detectors", {}).items() if on]
    print(
        f"{len(report['captures'])} captures, {len(report['problems'])} problems,"
        f" detectors: {', '.join(detectors) or 'none'}"
    )

    def delta(section: str, key: str, now: int) -> str:
        if before is None:
            return ""
        was = before[section].get(key, {}).get("count", 0)
        return f"  (was {was})" if was != now else "  (unchanged)"

    print("\n## Accessibility (axe, WCAG 2.2 AA + best practice)")
    if not agg["axe"]:
        print("none" if report["detectors"].get("axe") else "not run")
    for rule, e in sorted(agg["axe"].items(), key=lambda kv: (IMPACT_ORDER.get(kv[1]["impact"], 4), -kv[1]["count"])):
        print(f"- {e['impact'] or '?'} {rule}: {e['count']} elements, {spread(e['captures'], total)} - {e['help']}{delta('axe', rule, e['count'])}")
        for ex in e["examples"]:
            print(f"    {ex}")

    print("\n## Anti-patterns and quality (Impeccable)")
    if not agg["impeccable"]:
        print("none" if report["detectors"].get("impeccable") else "not run")
    for rule, e in sorted(agg["impeccable"].items(), key=lambda kv: (kv[1]["advisory"], kv[1]["category"] != "quality", -kv[1]["count"])):
        flag = " (advisory)" if e["advisory"] else ""
        print(f"- {e['category']} {rule}{flag}: {e['count']}, {spread(e['captures'], total)} - {e['name']}{delta('impeccable', rule, e['count'])}")
        for ex in e["examples"]:
            print(f"    {ex}")

    if before is not None:
        gone = [
            f"{section} {rule}"
            for section in ("axe", "impeccable")
            for rule in before[section]
            if rule not in agg[section]
        ]
        new = [
            f"{section} {rule}"
            for section in ("axe", "impeccable")
            for rule in agg[section]
            if rule not in before[section]
        ]
        print("\n## Against the earlier run")
        print(f"resolved: {', '.join(gone) or 'none'}")
        print(f"new: {', '.join(new) or 'none'}")

    print("\n## Horizontal overflow")
    print("\n".join(f"- {o}" for o in agg["overflow"]) or "none")

    print("\n## Saved on open (blocked by the capture; a screen that writes when it is only looked at)")
    print("\n".join(f"- {w}  [{', '.join(sorted(c))}]" for w, c in sorted(agg["writes"].items())) or "none")

    print("\n## Console errors")
    print("\n".join(f"- {e}  [{len(c)} captures]" for e, c in sorted(agg["errors"].items(), key=lambda kv: -len(kv[1]))) or "none")

    if agg["detector_errors"] or report["problems"]:
        print("\n## Capture problems")
        for p in report["problems"] + agg["detector_errors"]:
            print(f"- {p}")

    print("\n## Shots")
    for capture in report["captures"]:
        shots = capture.get("shots", [])
        more = f" (+{len(shots) - 1} more slices)" if len(shots) > 1 else ""
        if shots:
            print(f"- {run_dir / shots[0]}{more}")


def to_json(agg: dict) -> dict:
    def plain(section: dict) -> dict:
        return {k: {**v, "captures": sorted(v["captures"])} for k, v in section.items()}

    return {
        "axe": plain(agg["axe"]),
        "impeccable": plain(agg["impeccable"]),
        "overflow": agg["overflow"],
        "errors": {k: sorted(v) for k, v in agg["errors"].items()},
        "writes": {k: sorted(v) for k, v in agg["writes"].items()},
        "detector_errors": agg["detector_errors"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    parser.add_argument("--against", type=Path, help="an earlier run of the same screens")
    parser.add_argument("--json", action="store_true", help="print the aggregate as JSON")
    args = parser.parse_args()

    run = load_run(args.run)
    agg = aggregate(run)
    before = aggregate(load_run(args.against)) if args.against else None
    if args.json:
        print(json.dumps(to_json(agg), indent=2))
    else:
        print_summary(args.run, run, agg, before)


if __name__ == "__main__":
    main()
