#!/bin/bash
# Shallow clone a GitHub repo
# Usage: clone_repo.sh <full_name> [branch]
# Output: clone directory path

FULL_NAME=$1
BRANCH=${2:-}
CLONE_DIR="/tmp/git/$(echo "$FULL_NAME" | tr '/' '__')"

rm -rf "$CLONE_DIR"

if [ -n "$BRANCH" ]; then
  git clone --depth 1 --branch "$BRANCH" "https://github.com/$FULL_NAME" "$CLONE_DIR" 2>/dev/null
else
  git clone --depth 1 "https://github.com/$FULL_NAME" "$CLONE_DIR" 2>/dev/null
fi

if [ $? -eq 0 ]; then
  echo "$CLONE_DIR"
else
  echo "CLONE_FAILED" >&2
  exit 1
fi
