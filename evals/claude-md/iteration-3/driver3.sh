#!/bin/bash
BASE=/tmp/claude/cm-eval/iter3
printf 'full 1\nfull 2\nfull 3\nfull 4\nfull 5\nablated 1\nablated 2\nablated 3\nablated 4\nablated 5\n' | xargs -P 5 -n 2 bash "$BASE/runner3.sh"
echo "ALL DONE"
