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
    (r"<<-?\s*(['\"]?)[A-Za-z_]\w*\1", "heredoc <<WORD (any delimiter) / here-string"),
    (r"\bif\s*\[", "if [ ... ] block"),
    (r"\bcd\s+\S+.*&&", "cd <dir> && ... (use `git -C <path>` or pass abs paths)"),
]


def has_unquoted_semicolon_chain(cmd: str) -> bool:
    """True iff `cmd` contains `; <cmd>` outside any quoted region."""
    in_single = False
    in_double = False
    i = 0
    n = len(cmd)
    while i < n:
        c = cmd[i]
        if c == "\\" and i + 1 < n:
            i += 2
            continue
        if not in_double and c == "'":
            in_single = not in_single
        elif not in_single and c == '"':
            in_double = not in_double
        elif not in_single and not in_double and c == ";":
            rest = cmd[i + 1 :]
            if re.match(r"\s+(?:\\)?[a-zA-Z_/]", rest):
                return True
        i += 1
    return False


SEMICOLON_LABEL = (
    "; cmd2 (command-chain via semicolon — use parallel Bash calls in one message, "
    "or N parallel Read tool calls for multi-file inspection)"
)

# The short flag `rg -r` substitutes matches with the given text. `rg` is already
# recursive by default, so `rg -rn` does NOT mean "recursive + line numbers" —
# it replaces every match with the literal `n`. Catch a short-flag cluster
# containing `r` (no ripgrep short flag uses the letter `r` except replace).
# Only the short form is the trap: `--replace` is explicit and never confused for
# recursion, so it is allowed. The gap before the flag must not cross a shell
# separator (`|`, `&`, `;`); otherwise a `-r` from a piped command (e.g.
# `rg ... | sort -rn`) is wrongly blamed on `rg`.
RG_REPLACE_PATTERN = re.compile(
    r"\brg\b[^|&;]*?\s-[A-Za-z]*r[A-Za-z]*(?=[\s=]|$)"
)

RG_REPLACE_REASON = (
    "Blocked: this command uses `rg -r`. In ripgrep `-r` means "
    "REPLACE (substitute each match with the given text), NOT recursive — `rg` is "
    "already recursive by default. So `rg -rn pattern` replaces every match with "
    "the literal `n` instead of showing recursive numbered results. "
    "Drop the `-r`: use `rg -n pattern path` for line numbers, plain `rg pattern path` "
    "for a recursive search. If you genuinely want text substitution, use `--replace` "
    "(the long form is allowed)."
)

REASON_TEMPLATE = (
    "Blocked: this Bash command contains '{label}', a compound shell shape that "
    "Claude Code's permission matcher cannot allowlist — it produces "
    "'Unhandled node type: string' / 'Contains while_statement' errors and forces "
    "a permission prompt every time. Re-issue this work as one of: "
    "(1) ONE Bash `rg` call to search across files/repos "
    "(e.g. rg -l actix-web -g '**/Cargo.toml' /Users/.../funnel-io); "
    "(2) ONE Bash `fd` / `rg --files` call with brace patterns (e.g. fd CODEOWNERS ~/code/funnel-io); "
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

    def deny(label: str) -> int:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON_TEMPLATE.format(label=label),
            }
        }
        json.dump(out, sys.stdout)
        return 0

    if RG_REPLACE_PATTERN.search(cmd):
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": RG_REPLACE_REASON,
            }
        }
        json.dump(out, sys.stdout)
        return 0

    for pat, label in PATTERNS:
        if re.search(pat, cmd):
            return deny(label)

    if has_unquoted_semicolon_chain(cmd):
        return deny(SEMICOLON_LABEL)

    return 0


if __name__ == "__main__":
    sys.exit(main())
