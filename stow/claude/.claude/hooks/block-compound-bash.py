#!/usr/bin/env python3
"""PreToolUse hook: block Bash commands containing compound shell shapes that
the Claude Code permission matcher cannot allowlist (they produce
'Unhandled node type: string' / 'Contains while_statement' errors and force a
permission prompt every time).

Allowed: anything else. The hook exits 0 with no output for non-Bash tools and
for Bash commands that don't match any blocked pattern.
"""
import json
import re
import sys

PATTERNS = [
    (r"\bfor\s+\w+\s+in\b", "for-loop"),
    (r"\bwhile\s+", "while-loop"),
    (r";\s*do\b", "; do (loop body)"),
    (r"<\(", "process substitution <(...)"),
    (r"<<\s*['\"]?EOF", "heredoc <<EOF"),
    (r"\bif\s*\[", "if [ ... ] block"),
    (r"\bcd\s+\S+.*&&", "cd <dir> && ... (use `git -C <path>` or pass abs paths)"),
]

REASON_TEMPLATE = (
    "Blocked: this Bash command contains '{label}', a compound shell shape that "
    "Claude Code's permission matcher cannot allowlist — it produces "
    "'Unhandled node type: string' / 'Contains while_statement' errors and forces "
    "a permission prompt every time. Re-issue this work as one of: "
    "(1) ONE Grep call with `glob` and `path` to search across files/repos "
    "(e.g. Grep(pattern='tokio', glob='**/Cargo.toml', path='/Users/.../code')); "
    "(2) ONE Glob call with brace patterns (e.g. Glob(pattern='code/{{web-*,api}}/**/README.md')); "
    "(3) multiple parallel Bash calls in a single message, one per repo/target — no for/while loop; "
    "(4) `git -C <path> <cmd>` instead of `cd <path> && git ...`. "
    "If you genuinely need shell logic, write a script to /tmp/claude/<name>.sh with the Write tool and invoke it as `bash /tmp/claude/<name>.sh`."
)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # malformed input — don't block

    if data.get("tool_name") != "Bash":
        return 0

    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str):
        return 0

    for pat, label in PATTERNS:
        if re.search(pat, cmd):
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": REASON_TEMPLATE.format(label=label),
                }
            }
            json.dump(out, sys.stdout)
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
