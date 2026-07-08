#!/usr/bin/env python3
"""PermissionRequest hook: in autonomous mode, auto-deny any tool call that
would otherwise trigger an interactive permission prompt.

This lets a session run unattended WITHOUT --dangerously-skip-permissions:
instead of auto-allowing everything (dangerous), it auto-denies anything that
would prompt, so the agent recomposes with allowed primitives or stops and
reports. The deny is silent to the model (PermissionRequest cannot feed a
reason back); the standing guidance in CLAUDE.md tells the agent how to react
to a bare "Permission denied by hook".

Autonomous mode is active when the per-session flag file
/tmp/claude/autonomous-<session_id> exists, toggled by typing a bare `auto` /
`noauto` prompt (see autonomous-magicword.py).

When inactive, the hook is a no-op: normal permission flow / prompt.

Tools in EXEMPT_TOOLS are never auto-denied even in autonomous mode: they fall
through to the normal interactive prompt. Workflow is exempt because it spawns
expensive multi-agent fan-outs that must stay an explicit, approved decision
rather than being silently degraded to manual Agent calls.
"""
import json
import os
import sys

EXEMPT_TOOLS = {"Workflow"}


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("tool_name", "") in EXEMPT_TOOLS:
        return 0

    session_id = data.get("session_id", "")
    flag_on = bool(session_id) and os.path.exists(
        f"/tmp/claude/autonomous-{session_id}"
    )
    if not flag_on:
        return 0

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "deny",
                "message": (
                    "Auto-denied (autonomous mode): this command would have "
                    "triggered a permission prompt. Do NOT retry it as-is. "
                    "Recompose using already-allowed tools: separate Bash calls "
                    "instead of pipes/&&/;, Read/Edit/Write (and `rg`/`fd` via Bash) instead of "
                    "cat/sed/echo, `git -C <path>` instead of `cd <path> && ...`. "
                    "If it genuinely cannot be recomposed, STOP and end your turn, "
                    "saying in your reply exactly what needs approving — do NOT try "
                    "to ask via AskUserQuestion or any prompt: the user is away in "
                    "autonomous mode, and interactive prompts are auto-denied here "
                    "too. (type noauto to turn off.)"
                ),
            },
        }
    }
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
