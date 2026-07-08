#!/usr/bin/env bash
# Real-file-copy corpus builder for eval isolation.
#
# DO NOT use symlinks: ripgrep skips them by default,
# producing silent false-negative 0-hit results. A subagent can also `readlink`
# a symlink to discover the source path and walk to forbidden siblings.
#
# DO NOT use hard links on macOS: fails with EPERM across APFS volumes
# (/tmp is on a different volume than ~/).
#
# Real `cp` is the simplest reliable option. Adjust SRC, CORPUS, CUTOFF, and
# the find filter as needed for the eval.

set -euo pipefail

# Adjust per eval:
CORPUS=/tmp/claude/eval-corpus
SRC="$HOME/.claude/projects"
CUTOFF=2026-05-25
# Filter pattern — what kinds of files belong in the corpus
FILE_PATTERN="*.jsonl"

rm -rf "$CORPUS"
mkdir -p "$CORPUS"

# `find -not -newermt $CUTOFF` keeps files modified BEFORE the cutoff date.
# Adjust the predicate if you want a different scoping rule (e.g. specific
# project dirs, specific date range).
find "$SRC" -name "$FILE_PATTERN" -not -newermt "$CUTOFF" -print0 \
| while IFS= read -r -d '' f; do
    rel="${f#$SRC/}"
    dst="$CORPUS/$rel"
    mkdir -p "$(dirname "$dst")"
    cp "$f" "$dst"
  done

echo "in_scope_files=$(find "$CORPUS" -name "$FILE_PATTERN" | wc -l | tr -d ' ')"
echo "real_files=$(find "$CORPUS" -name "$FILE_PATTERN" -type f | wc -l | tr -d ' ')"
echo "symlinks=$(find "$CORPUS" -name "$FILE_PATTERN" -type l | wc -l | tr -d ' ')"
echo "total_mb=$(du -sm "$CORPUS" | awk '{print $1}')"

# Sanity check: verify ripgrep can actually see the files.
# If this returns 0 when you know matches exist, something's wrong with
# the corpus build — likely you used symlinks somewhere.
# echo "rg_sanity_check=$(rg -l '[your-known-term-here]' "$CORPUS" 2>/dev/null | wc -l | tr -d ' ')"
