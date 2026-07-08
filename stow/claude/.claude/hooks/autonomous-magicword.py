#!/usr/bin/env python3
"""UserPromptSubmit hook: a bare `auto` / `noauto` prompt instantly toggles
autonomous mode. It touches/removes the per-session flag and blocks the prompt
so it never reaches the model (no model turn). Submitting fires a status-line
refresh, so the 👾 badge flips instantly — no polling needed."""
import json
import os
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

prompt = (data.get("prompt") or "").strip()
session_id = data.get("session_id", "")
if not session_id or prompt not in ("auto", "noauto"):
    sys.exit(0)

flag = f"/tmp/claude/autonomous-{session_id}"
if prompt == "auto":
    open(flag, "a").close()
    msg = "👾 autonomous mode ON — anything that would prompt is auto-denied. Type noauto to turn off."
else:
    try:
        os.remove(flag)
    except FileNotFoundError:
        pass
    msg = "autonomous mode OFF — normal permission prompts restored."

print(json.dumps({"decision": "block", "reason": msg}))
