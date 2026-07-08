#!/usr/bin/env python3
"""PreToolUse hook: block Edit/Write/MultiEdit calls that introduce content
matching CLAUDE.md "Code Standard Hotspots" — speculative defensive flare,
default logging, rationale comments, stale-cross-reference comments, ignored
TODO test stubs.

Override mechanism: the model writes a JSON file to
/tmp/claude/pending-code-rule-override.json with shape:
    {"rule": "<rule-id>", "reason": "<>= 40 chars explaining the exception>"}
Re-issuing the same Edit/Write then succeeds — the override is single-use,
its rule must match the violation, and it's logged to
~/.claude/code-rule-overrides.jsonl for post-hoc review.

Stays silent for non-code files (config, docs, notes, tmp).
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
PENDING_OVERRIDE_DIR = Path("/tmp/claude")
AUDIT_LOG = HOME / ".claude" / "debug" / "code-rule-overrides.jsonl"
OVERRIDE_TTL_SECONDS = 600  # 10 minutes
MIN_REASON_CHARS = 40


def pending_override_path(session_id: str) -> Path:
    suffix = (session_id or "").strip() or "no-session"
    return PENDING_OVERRIDE_DIR / f"pending-code-rule-override-{suffix}.json"

# Extensions where these rules apply. Non-source files (docs, configs, notes)
# are ignored entirely.
CODE_EXTENSIONS = {
    ".rs", ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".java", ".scala", ".kt", ".swift",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".rb",
}

# Skip files under these prefixes regardless of extension. Note `.worktrees/` is NOT skipped:
# real feature work lives in `.worktrees/<name>/src/...` and must stay in scope. A `.claude/`
# dir inside a worktree is still skipped by the `/.claude/` entry above.
SKIP_PATH_SUBSTRINGS = (
    "/.claude/",
    "/Documents/notes/",
    "/tmp/",
)

# Rule definitions. Each rule:
#   id      — short slug used in override file
#   pattern — regex to find in added content (multiline-aware)
#   summary — one-line description shown when blocking
#   ref     — pointer back to CLAUDE.md section
RULES = [
    {
        "id": "no-default-tracing",
        "pattern": re.compile(r"\btracing::(info|warn|debug|trace)!\s*\("),
        "summary": (
            "Adds `tracing::{info|warn|debug|trace}!` call. "
            "Per CLAUDE.md: logging defaults to none. Keep only at external IO "
            "boundaries (with elapsed/status), genuine decision points, "
            "or error paths that don't throw."
        ),
        "ref": "Logging: default to none",
    },
    {
        "id": "no-default-log",
        "pattern": re.compile(r"\b(log|logger|console)\.(info|debug|log|warn)\s*\("),
        "summary": (
            "Adds default-logging call (log.* / console.*). "
            "Per CLAUDE.md: logging defaults to none. Only IO boundaries, "
            "decision points, or non-throwing error paths."
        ),
        "ref": "Logging: default to none",
    },
    {
        "id": "no-ignored-todo-test",
        "pattern": re.compile(r"#\[ignore[^\]]*\][\s\S]{0,400}\btodo!\s*\("),
        "summary": (
            "Adds `#[ignore]` test whose body is `todo!()`. "
            "Per CLAUDE.md: no ignored tests or TODO placeholders. "
            "If the test can't be made to work yet, don't write it at all."
        ),
        "ref": "No ignored tests or TODO placeholders",
    },
]


def added_content(tool_name: str, tool_input: dict) -> list[tuple[str, str]]:
    """Return list of (label, content) pieces this tool call wants to write."""
    if tool_name == "Write":
        return [("content", tool_input.get("content", "") or "")]
    if tool_name == "Edit":
        return [("new_string", tool_input.get("new_string", "") or "")]
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits") or []
        return [
            (f"edits[{i}].new_string", (e or {}).get("new_string", "") or "")
            for i, e in enumerate(edits)
        ]
    return []


def file_path_in_scope(file_path: str) -> bool:
    if not file_path:
        return False
    if any(s in file_path for s in SKIP_PATH_SUBSTRINGS):
        return False
    ext = os.path.splitext(file_path)[1].lower()
    return ext in CODE_EXTENSIONS


def find_violations(pieces: list[tuple[str, str]]) -> list[tuple[str, str, str]]:
    """Return list of (rule_id, label, matched_snippet)."""
    hits = []
    for label, content in pieces:
        if not content:
            continue
        for rule in RULES:
            m = rule["pattern"].search(content)
            if m:
                snippet = m.group(0)
                if len(snippet) > 120:
                    snippet = snippet[:117] + "..."
                hits.append((rule["id"], label, snippet))
    return hits


HASH_COMMENT_EXTS = {".py", ".rb"}
TODO_NOTE_RE = re.compile(r"^(?://+|#)\s*(?:TODO|FIXME)\b", re.IGNORECASE)

NEW_COMMENT_RULE = {
    "id": "no-new-comment",
    "summary": (
        "Adds a new code comment line. Per CLAUDE.md comments default to ZERO: "
        "only add one a reviewer would INSIST on (would block the PR if it were missing). "
        "Rationale -> commit message; invariants -> a test name. "
        "Override only for a genuine landmine, with that justification. "
        "(TODO/FIXME working notes are allowed and not blocked.)"
    ),
    "ref": "Comments: default to ZERO",
}


def leading_comment_lines(text: str, ext: str) -> set[str]:
    prefixes = ("//", "#") if ext in HASH_COMMENT_EXTS else ("//",)
    return {
        s
        for s in (line.strip() for line in (text or "").splitlines())
        if s.startswith(prefixes) and not TODO_NOTE_RE.match(s)
    }


def comment_diff_hits(tool_name: str, tool_input: dict, ext: str) -> list[tuple[str, str, str]]:
    """Flag leading comment lines present in the new content but not the old
    (net-new comments), so editing code near existing comments doesn't trip it."""
    pairs = []  # (label, old, new)
    if tool_name == "Write":
        old = ""
        try:
            old = Path(tool_input.get("file_path", "") or "").read_text()
        except Exception:
            old = ""
        pairs.append(("content", old, tool_input.get("content", "") or ""))
    elif tool_name == "Edit":
        pairs.append(
            ("new_string", tool_input.get("old_string", "") or "", tool_input.get("new_string", "") or "")
        )
    elif tool_name == "MultiEdit":
        for i, e in enumerate(tool_input.get("edits") or []):
            e = e or {}
            pairs.append(
                (f"edits[{i}].new_string", e.get("old_string", "") or "", e.get("new_string", "") or "")
            )

    hits = []
    for label, old, new in pairs:
        for c in sorted(leading_comment_lines(new, ext) - leading_comment_lines(old, ext)):
            snippet = c if len(c) <= 120 else c[:117] + "..."
            hits.append(("no-new-comment", label, snippet))
    return hits


def load_override(session_id: str) -> dict | None:
    path = pending_override_path(session_id)
    if not path.exists():
        return None
    try:
        age = time.time() - path.stat().st_mtime
        if age > OVERRIDE_TTL_SECONDS:
            return None
        return json.loads(path.read_text())
    except Exception:
        return None


def consume_override(session_id: str, record: dict) -> None:
    """Atomically claim the per-session override and append to audit log.

    Uses os.rename to a unique claim path so two hook subprocesses racing on
    the same session's override file cannot both succeed."""
    src = pending_override_path(session_id)
    claim = src.with_suffix(f".claimed-{os.getpid()}-{int(time.time() * 1e6)}.json")
    try:
        os.rename(src, claim)
    except OSError:
        return  # already consumed by a racing subprocess
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a") as f:
            f.write(json.dumps(record) + "\n")
    finally:
        try:
            claim.unlink()
        except FileNotFoundError:
            pass


def rule_by_id(rule_id: str) -> dict | None:
    for r in RULES + [NEW_COMMENT_RULE]:
        if r["id"] == rule_id:
            return r
    return None


def deny(reason: str) -> int:
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(out, sys.stdout)
    return 0


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = data.get("tool_name") or ""
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return 0

    session_id = (data.get("session_id") or "").strip()
    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "") or ""
    if not file_path_in_scope(file_path):
        return 0

    ext = os.path.splitext(file_path)[1].lower()
    pieces = added_content(tool_name, tool_input)
    hits = find_violations(pieces) + comment_diff_hits(tool_name, tool_input, ext)
    if not hits:
        return 0

    rule_ids_hit = sorted({h[0] for h in hits})

    override = load_override(session_id)
    if override:
        ov_rule = (override.get("rule") or "").strip()
        ov_reason = (override.get("reason") or "").strip()
        ov_file = (override.get("file_path") or "").strip()
        file_ok = (not ov_file) or ov_file == file_path
        if ov_rule in rule_ids_hit and len(ov_reason) >= MIN_REASON_CHARS and file_ok:
            consume_override(session_id, {
                "ts": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "tool": tool_name,
                "file": file_path,
                "rule": ov_rule,
                "reason": ov_reason,
                "override_file_path": ov_file or None,
                "other_rules_hit": [r for r in rule_ids_hit if r != ov_rule],
            })
            remaining = [r for r in rule_ids_hit if r != ov_rule]
            if remaining:
                return deny(
                    f"Override accepted for `{ov_rule}` but additional rules also hit: "
                    f"{remaining}. Add a separate override for each rule violation."
                )
            return 0
        # Override exists but doesn't match — fall through to deny with explanation.

    # Build deny message
    bullets = []
    for rid in rule_ids_hit:
        rule = rule_by_id(rid)
        if rule is None:
            continue
        bullets.append(f"  - `{rid}` ({rule['ref']}): {rule['summary']}")
    rules_list = "\n".join(bullets)

    primary_rule = rule_ids_hit[0]
    example_override = json.dumps({
        "rule": primary_rule,
        "file_path": file_path,
        "reason": "REPLACE — for a comment: why would a reviewer INSIST on it (block the PR if missing)? Else: why this case is the exception. >= 40 chars.",
    })
    pending_path = pending_override_path(session_id)

    msg = (
        f"BLOCKED by check-code-rules on {tool_name} of `{file_path}`.\n"
        f"Violations found:\n{rules_list}\n\n"
        f"If you genuinely need this exception, override it: write to "
        f"`{pending_path}` (use the Write tool) with JSON like:\n"
        f"  {example_override}\n"
        f"Then re-issue the same {tool_name} call. The override is single-use, "
        f"scoped to this session (session_id={session_id or 'unknown'}), and logged to "
        f"`{AUDIT_LOG}` for the user to review. The `file_path` field is optional "
        f"but recommended — it binds the override to this exact file so a concurrent "
        f"Edit elsewhere in this session cannot consume it.\n"
        f"Otherwise: revise the code to remove the flagged pattern. "
        f"For most cases the right answer is to drop the comment/log/stub, "
        f"not to override."
    )
    if override:
        ov_rule = (override.get("rule") or "").strip()
        ov_reason = (override.get("reason") or "").strip()
        ov_file = (override.get("file_path") or "").strip()
        problems = []
        if ov_rule not in rule_ids_hit:
            problems.append(
                f"override rule `{ov_rule}` does not match any violation in this edit "
                f"(actual rules hit: {rule_ids_hit})"
            )
        if ov_file and ov_file != file_path:
            problems.append(
                f"override `file_path` is `{ov_file}` but this edit targets `{file_path}`"
            )
        if len(ov_reason) < MIN_REASON_CHARS:
            problems.append(
                f"override reason is {len(ov_reason)} chars; "
                f"must be >= {MIN_REASON_CHARS} to prove deliberate intent"
            )
        msg += (
            f"\n\nNOTE: pending override file found but not accepted because: "
            f"{'; '.join(problems)}."
        )
    return deny(msg)


if __name__ == "__main__":
    sys.exit(main())
