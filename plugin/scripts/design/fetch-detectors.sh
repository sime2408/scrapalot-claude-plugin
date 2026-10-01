#!/usr/bin/env bash
# Fetch the two detectors the design review injects into each page, pinned to
# one release and checked against its SHA-256, into the project's state
# directory (never into the plugin: an update would delete them).
#
#   Impeccable's in-page anti-pattern detector (Apache-2.0, pbakaus/impeccable)
#   axe-core, the accessibility rule engine (MPL-2.0, Deque Systems)
#
# Prints the two `export` lines the capture reads. To move to a newer release,
# change the ref or version AND its checksum together.
set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
DIR="${SCRAPALOT_DESIGN_VENDOR:-$ROOT/.claude/design/vendor}"

IMPECCABLE_REF=9d715cc4f5564a990ca8345abfdd5df6dc9b41c8
IMPECCABLE_SHA256=a632dbcaf74de772d702627b543d4557e28a6aed675cf8b3da79cf0500cae54b
AXE_VERSION=4.13.0
AXE_SHA256=c24f097bd2f451d4f933e8bc7d8d539f8672a2ebcb5cc9f9f3eec8ca9470a0c1

fetch() {
  local url=$1 file=$2 sum=$3 tmp
  if [[ -f $file ]] && echo "$sum  $file" | sha256sum -c --quiet 2>/dev/null; then
    return 0
  fi
  tmp=$(mktemp "$DIR/.fetch.XXXXXX")
  if ! curl -fsSL --retry 2 --max-time 120 "$url" -o "$tmp"; then
    rm -f "$tmp"
    echo "fetch-detectors: could not download $url" >&2
    return 1
  fi
  if ! echo "$sum  $tmp" | sha256sum -c --quiet 2>/dev/null; then
    rm -f "$tmp"
    echo "fetch-detectors: checksum mismatch for $url (expected $sum)" >&2
    return 1
  fi
  mv "$tmp" "$file"
}

mkdir -p "$DIR"
fetch "https://raw.githubusercontent.com/pbakaus/impeccable/$IMPECCABLE_REF/crates/live/assets/detect-antipatterns-browser.js" \
  "$DIR/impeccable-detector.js" "$IMPECCABLE_SHA256"
fetch "https://cdn.jsdelivr.net/npm/axe-core@$AXE_VERSION/axe.min.js" \
  "$DIR/axe.min.js" "$AXE_SHA256"

echo "export DESIGN_IMPECCABLE_JS=$DIR/impeccable-detector.js"
echo "export DESIGN_AXE_JS=$DIR/axe.min.js"
