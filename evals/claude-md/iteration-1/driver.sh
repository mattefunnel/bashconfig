#!/bin/bash
BASE=/tmp/claude/cm-eval/iter1
xargs -P 5 -n 3 bash "$BASE/runner.sh" < "$BASE/tuples.txt"
echo "ALL CELLS DONE"
