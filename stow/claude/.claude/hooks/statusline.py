#!/usr/bin/env python3
"""Claude Code status line. Shows a loud badge when autonomous mode is active
for this session (flag file /tmp/claude/autonomous-<session_id>), so it's never
invisibly on, plus the working dir and model."""
import json
import os
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

session_id = data.get("session_id", "")
cwd = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or ""
model = (data.get("model") or {}).get("display_name") or ""

parts = []
if session_id and os.path.exists(f"/tmp/claude/autonomous-{session_id}"):
    parts.append("👾 \033[1;38;2;0;255;65mA.U.T.O.N.O.M.O.U.S!\033[0m")
if cwd:
    parts.append(os.path.basename(cwd.rstrip("/")) or cwd)
if model:
    parts.append(f"\033[2m{model}\033[0m")

sys.stdout.write("  ".join(parts))
