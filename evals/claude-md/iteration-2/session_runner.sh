#!/bin/bash
# usage: session_runner.sh <cond> <k>
cond="$1"; k="$2"
BASE=/tmp/claude/cm-eval/iter2
dir="$BASE/runs/$cond/k$k"
mkdir -p "$dir"
if [ "$cond" = "full" ]; then sp="$BASE/variants/full.txt"; else sp="$BASE/variants/ablated-min.txt"; fi
n=$(jq '.turns|length' "$BASE/turns.json")

# turn 1 (creates the session)
t=$(jq -r '.turns[0].prompt' "$BASE/turns.json")
j=$(claude -p "$t" --setting-sources "" --append-system-prompt-file "$sp" --model opus --allowedTools "Read Grep Glob" --output-format json)
echo "$j" > "$dir/turn-01.json"
sid=$(echo "$j" | jq -r '.session_id')

# turns 2..n (resume the same session; system prompt + context persist)
i=1
while [ "$i" -lt "$n" ]; do
  t=$(jq -r ".turns[$i].prompt" "$BASE/turns.json")
  num=$(printf "%02d" $((i+1)))
  out="$dir/turn-$num.json"
  [ -s "$out" ] || claude -p "$t" --resume "$sid" --model opus --allowedTools "Read Grep Glob" --output-format json > "$out"
  i=$((i+1))
done
echo "session $cond/k$k done"
