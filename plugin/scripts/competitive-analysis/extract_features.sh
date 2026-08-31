#!/bin/bash
# Extract structural overview from a cloned repo
# Usage: extract_features.sh <clone_dir>

CLONE_DIR=$1

if [ ! -d "$CLONE_DIR" ]; then
  echo "ERROR: Directory $CLONE_DIR does not exist" >&2
  exit 1
fi

echo "=== REPO STRUCTURE ==="
find "$CLONE_DIR" -type f -not -path '*/.git/*' | head -300

echo ""
echo "=== KEY CONFIG FILES ==="
for f in README.md package.json requirements.txt pyproject.toml docker-compose.yml docker-compose.yaml Dockerfile Cargo.toml go.mod build.gradle pom.xml Makefile; do
  if [ -f "$CLONE_DIR/$f" ]; then
    echo "--- $f ---"
    head -100 "$CLONE_DIR/$f"
    echo ""
  fi
done

echo ""
echo "=== FILE COUNTS BY EXTENSION ==="
find "$CLONE_DIR" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20

echo ""
echo "=== DIRECTORY STRUCTURE (depth 3) ==="
find "$CLONE_DIR" -maxdepth 3 -type d -not -path '*/.git/*' -not -path '*/node_modules/*' | sort
