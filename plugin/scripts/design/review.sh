#!/usr/bin/env bash
# Run the design review capture and print its summary.
#
#   review.sh <label> <surfaces> [viewports] [themes] [accents]
#
#   label      names the run directory: <project>/.claude/design/runs/<time>-<label>
#   surfaces   comma list: names from scrapalot-ui tests/e2e/design/surfaces.ts or paths
#   viewports  laptop, panel, desktop, tablet, phone or WxH   (default laptop,phone)
#   themes     light, dark, hybrid                             (default light,dark)
#   accents    gray, blue, green, red, violet, orange or all  (default blue)
#
# Environment:
#   SCRAPALOT_UI_DIR  checkout to run from: a worktree whose change is under
#                     review, or the shared one (default <project>/scrapalot-ui)
#   E2E_DIST          a local build to serve instead of the deployed one
#   DESIGN_LANG, DESIGN_SLICES, DESIGN_EMULATE   passed through to the capture
#
# Exit 2 when the host is too short of memory to start a browser safely.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
  exit 64
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
UI="${SCRAPALOT_UI_DIR:-$ROOT/scrapalot-ui}"
LABEL=$(echo "$1" | tr -c 'A-Za-z0-9_.-' '-' | sed 's/-*$//')

if [[ ! -f $UI/playwright.design.config.ts ]]; then
  echo "review: $UI has no playwright.design.config.ts; point SCRAPALOT_UI_DIR at a scrapalot-ui checkout that has the capture" >&2
  exit 1
fi

# One headless browser is ~0.5 GB, and this host shares its memory with production.
avail_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
if (( avail_kb < 1500000 )); then
  echo "review: only $((avail_kb / 1024)) MB available; not starting a browser next to production (need 1500 MB)" >&2
  exit 2
fi

eval "$("$HERE/fetch-detectors.sh")"

OUT="$ROOT/.claude/design/runs/$(date +%Y%m%d-%H%M%S)-$LABEL"
mkdir -p "$OUT"

export DESIGN_OUT="$OUT" DESIGN_SURFACES="$2"
[[ -n ${3:-} ]] && export DESIGN_VIEWPORTS="$3"
[[ -n ${4:-} ]] && export DESIGN_THEMES="$4"
[[ -n ${5:-} ]] && export DESIGN_ACCENTS="$5"

status=0
(cd "$UI" && npx playwright test --config=playwright.design.config.ts) > "$OUT/playwright.log" 2>&1 || status=$?
tail -3 "$OUT/playwright.log"

if [[ -f $OUT/report.json ]]; then
  python3 "$HERE/summarize.py" "$OUT"
else
  echo "review: the capture wrote no report; see $OUT/playwright.log" >&2
fi
exit "$status"
