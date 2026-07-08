#!/bin/bash
BASE=/tmp/claude/cm-eval/iter2
printf 'full 1\nfull 2\nfull 3\nfull 4\nablated 1\nablated 2\nablated 3\nablated 4\n' | xargs -P 4 -n 2 bash "$BASE/session_runner.sh"
echo "ALL SESSIONS DONE"
