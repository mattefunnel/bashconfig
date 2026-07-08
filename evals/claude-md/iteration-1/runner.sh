#!/bin/bash
# usage: runner.sh <id> <cond> <k>
id="$1"; cond="$2"; k="$3"
BASE=/tmp/claude/cm-eval/iter1
dir="$BASE/runs/$id/$cond"
mkdir -p "$dir"
out="$dir/run-$k.json"
[ -s "$out" ] && exit 0   # idempotent: skip already-completed cells
probe=$(jq -r --arg id "$id" '.rules[]|select(.id==$id)|.probe' "$BASE/rules.json")
if [ "$cond" = "full" ]; then
  sp="$BASE/variants/full.txt"
else
  sp="$BASE/variants/ablated-$id.txt"
fi
claude -p "$probe" \
  --setting-sources "" \
  --append-system-prompt-file "$sp" \
  --model opus \
  --allowedTools "Read Grep Glob" \
  --output-format json > "$out" 2>"$dir/run-$k.err"
