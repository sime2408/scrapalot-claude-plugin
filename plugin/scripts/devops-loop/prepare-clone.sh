#!/usr/bin/env bash
# prepare-clone.sh — create an ISOLATED working copy of a subproject for the fix
# loop, OUTSIDE the deployed checkout, so the loop never collides with the
# operator, other agents, or a CI deploy.
#
# Why this exists: CI/CD deploys overwrite /opt/scrapalot/<repo> in place —
# backend/gw do `sudo rm -rf` (no stash), chat/ui do `git reset --hard`. Editing
# the live checkout races every push-to-main. And the operator may have that
# checkout on a feature branch with uncommitted work (e.g. scrapalot-chat). So we
# clone a fresh, shallow copy of origin/main into a scratch dir under the loop
# home and do ALL fix work there.
#
# Usage:   prepare-clone.sh <repo-name>      # e.g. scrapalot-backend
# Output:  the absolute path of the isolated clone on stdout (logs to stderr).
# Exit:    non-zero on failure.
#
# Requires git SSH access for user `scrapalot` (same as the loop's branch push):
# a passphraseless key in ~/.ssh and github.com in known_hosts. GIT_SSH_COMMAND
# is set to BatchMode so it fails fast instead of hanging in cron.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_ROOT="$(cd "$HERE/.." && pwd)/work"
repo="${1:?repo name required (scrapalot-chat|scrapalot-backend|scrapalot-ui|scrapalot-gw)}"

case "$repo" in
  scrapalot-chat|scrapalot-backend|scrapalot-ui|scrapalot-gw) ;;
  *) echo "unknown repo: $repo" >&2; exit 2 ;;
esac

src="/opt/scrapalot/$repo"
[ -d "$src/.git" ] || { echo "no git repo at $src" >&2; exit 2; }
url="$(git -C "$src" remote get-url origin)"
[ -n "$url" ] || { echo "no origin remote for $repo" >&2; exit 2; }

mkdir -p "$WORK_ROOT"
dest="$WORK_ROOT/${repo}.$$.$(date +%s)"

export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
echo "cloning $repo origin/main -> $dest" >&2
if ! git clone --depth 1 --branch main --single-branch "$url" "$dest" >&2 2>&1; then
  # some repos may use 'master'
  if ! git clone --depth 1 --branch master --single-branch "$url" "$dest" >&2 2>&1; then
    echo "clone failed for $repo" >&2
    rm -rf "$dest"
    exit 1
  fi
fi

# Identity for commits (no Claude attribution per project rule).
git -C "$dest" config user.name  "scrapalot-devops-loop"
git -C "$dest" config user.email "devops-loop@scrapalot.local"

echo "$dest"
