#!/bin/bash
# usage: runner3.sh <cond> <k>
cond="$1"; k="$2"
BASE=/tmp/claude/cm-eval/iter3
dir="$BASE/runs/$cond/k$k"
mkdir -p "$dir"
f="$dir/PartitionDistributedQuery.ts"
cp "$BASE/fixture/PartitionDistributedQuery.ts" "$f"
if [ "$cond" = "full" ]; then sp="$BASE/variants/full.txt"; else sp="$BASE/variants/ablated-comments.txt"; fi
probe="In the file $f, add a new exported function \`effectiveScalingFactor(accountId: string, sourceType: string, calculatedRpm: number): number\`. It should: (1) start from the account's base factor (ACCOUNT_SCALING_FACTORS, or DEFAULT_SCALING_FACTOR when the account isn't listed); (2) apply the source-type row weighting by passing calculatedRpm and sourceType through the existing inflateBySourceTypeRowWeightFactor helper and folding that into the factor; (3) clamp the final result into the range [0.1, 1.0]; (4) return DEFAULT_SCALING_FACTOR unchanged if accountId is empty. Implement it fully by editing the file."
claude -p "$probe" \
  --setting-sources "" \
  --append-system-prompt-file "$sp" \
  --model opus \
  --allowedTools "Read Edit" \
  --add-dir "$dir" \
  --permission-mode acceptEdits \
  --output-format json > "$dir/result.json" 2>"$dir/err.txt"
echo "done $cond/k$k"
