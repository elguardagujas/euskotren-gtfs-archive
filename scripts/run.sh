#!/usr/bin/env bash
# -*- coding: utf-8 -*-

set -euo pipefail

REPO_URL="${1:?Usage: $0 <repo-url>}"
UPDATE_TXT="data/update.txt"
TIMESTAMP=$(date -u "+%Y-%m-%d %H:%M")
WORKDIR=$(mktemp -d)

trap 'if [[ -n "$WORKDIR" && "$WORKDIR" == /tmp/* && -d "$WORKDIR" ]]; then echo "Cleaning up $WORKDIR..."; rm -rf "$WORKDIR"; fi' EXIT

echo "Cloning $REPO_URL into $WORKDIR..."
git clone "$REPO_URL" "$WORKDIR"
cd "$WORKDIR"

echo "Running update..."
./tools/update.py

# Any new (untracked) zip files in data/?
NEW_FILES=$(git status --porcelain data/ | awk '/^\?\?/ {print $2}')

if [[ -n "$NEW_FILES" ]]; then
  echo "New files produced:"
  echo "$NEW_FILES"
  echo "$TIMESTAMP" > "$UPDATE_TXT"
  git add data/
  git commit -m "data: update $TIMESTAMP"
  git push origin master

else
  echo "No new files."

  # Check if update.txt is missing or older than 1 day
  NEEDS_BUMP=0
  if [[ ! -f "$UPDATE_TXT" ]]; then
    NEEDS_BUMP=1
  else
    LAST=$(cat "$UPDATE_TXT")
    LAST_EPOCH=$(date -ud "$LAST" "+%s" 2>/dev/null || date -ujf "%Y-%m-%d %H:%M" "$LAST" "+%s")
    NOW_EPOCH=$(date -u "+%s")
    if (( NOW_EPOCH - LAST_EPOCH > 86400 )); then
      NEEDS_BUMP=1
    fi
  fi

  if [[ "$NEEDS_BUMP" -eq 1 ]]; then
    echo "Bumping $UPDATE_TXT to $TIMESTAMP"
    echo "$TIMESTAMP" > "$UPDATE_TXT"
    git add "$UPDATE_TXT"
    git commit -m "data: heartbeat $TIMESTAMP"
    git push origin master
  else
    echo "update.txt is fresh, nothing to do."
  fi
fi


