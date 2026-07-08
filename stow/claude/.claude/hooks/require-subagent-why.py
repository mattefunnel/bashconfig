#!/usr/bin/env python3
"""PreToolUse hook for the Agent tool: deny a subagent spawn whose prompt lacks a
WHY: rationale trace. The trace must come from the spawning model's context — a hook
can only enforce presence, not author it."""
import json
import sys

data = json.load(sys.stdin)
prompt = data.get("tool_input", {}).get("prompt", "")

if "WHY:" in prompt:
    sys.exit(0)

reason = (
    "Subagent prompt is missing a WHY: rationale trace. Prepend a line like:\n"
    "  WHY: <end goal> <- <what consumes this> <- this task.\n"
    "State the dependency chain (why this task exists, what depends on its result) "
    "so the subagent can judge relevance and self-correct, not just pattern-match. "
    "Re-spawn with WHY: included."
)
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
}))
sys.exit(0)
