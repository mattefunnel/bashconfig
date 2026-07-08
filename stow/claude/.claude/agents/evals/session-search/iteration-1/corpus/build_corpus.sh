#!/usr/bin/env bash
set -euo pipefail

CORPUS=/tmp/claude/eval-corpus
SRC="$HOME/.claude/projects"
CUTOFF=2026-05-25

rm -rf "$CORPUS"
mkdir -p "$CORPUS"

# Real file copies — no symlinks (so no readlink leak, no rg --follow trap),
# hard links don't work across APFS volumes on macOS. 377 MB total.
find "$SRC" -name "*.jsonl" -not -newermt "$CUTOFF" -print0 \
| while IFS= read -r -d '' f; do
    rel="${f#$SRC/}"
    dst="$CORPUS/$rel"
    mkdir -p "$(dirname "$dst")"
    cp "$f" "$dst"
  done

echo "in_scope_files=$(find "$CORPUS" -name '*.jsonl' | wc -l | tr -d ' ')"
echo "real_files=$(find "$CORPUS" -name '*.jsonl' -type f | wc -l | tr -d ' ')"
echo "symlinks=$(find "$CORPUS" -name '*.jsonl' -type l | wc -l | tr -d ' ')"
echo "total_mb=$(du -sm "$CORPUS" | awk '{print $1}')"
echo "vpc_lattice_files=$(find "$CORPUS" -name '*.jsonl' -exec grep -l 'VPC Lattice' {} + | wc -l | tr -d ' ')"
echo "actix_to_axum_files=$(find "$CORPUS" -name '*.jsonl' -exec grep -l 'actix-to-axum' {} + | wc -l | tr -d ' ')"
echo "rg_vpc_lattice_files=$(rg -l 'VPC Lattice' "$CORPUS" 2>/dev/null | wc -l | tr -d ' ')"
