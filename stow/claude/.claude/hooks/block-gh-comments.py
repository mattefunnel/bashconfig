#!/usr/bin/env python3
"""PreToolUse hook: block Bash commands that POST comments or reviews to GitHub.

Matte does not want the assistant posting to PR/issue comment threads or review
threads — triage belongs in chat, code fixes belong in commits. Reading
(gh pr view, gh api GET) and opening PRs (gh pr create) stay allowed.

Blocks:
  - gh pr comment / gh issue comment
  - gh pr review            (any form — posting a review body/approval)
  - gh api ...              targeting a /comments, /replies, or /reviews endpoint
                            with a write (POST/PATCH, or a body/input flag)

Matches both `gh` and the escaped `\\gh` Matte uses. Exits 0 with no output for
non-Bash tools and for commands that don't match — same contract as the other
PreToolUse hooks.

Override mechanism (mirrors check-code-rules.py): when Matte explicitly asks for
a comment to be posted, the model writes a JSON file to
/tmp/claude/pending-gh-comment-override-<session_id>.json with shape:
    {"reason": "<>= 40 chars — who asked and for what>"}
Re-issuing the same command then succeeds once. The override is single-use,
expires after 10 minutes, and is logged to
~/.claude/debug/gh-comment-overrides.jsonl for post-hoc review.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

GH = r"(?:\\)?gh\b"

HOME = Path.home()
PENDING_OVERRIDE_DIR = Path("/tmp/claude")
AUDIT_LOG = HOME / ".claude" / "debug" / "gh-comment-overrides.jsonl"
OVERRIDE_TTL_SECONDS = 600  # 10 minutes
MIN_REASON_CHARS = 40

# gh pr comment / gh issue comment / gh pr review — always a post.
VERB_PATTERNS = [
    (re.compile(GH + r"\s+pr\s+comment\b"), "gh pr comment"),
    (re.compile(GH + r"\s+issue\s+comment\b"), "gh issue comment"),
    (re.compile(GH + r"\s+pr\s+review\b"), "gh pr review"),
]

# gh api against a comment/review endpoint. Only block writes: an explicit
# POST/PATCH method, a body/input flag, or a /replies path (replies are POST).
API_CALL = re.compile(GH + r"\s+api\b")
API_COMMENT_PATH = re.compile(r"/(?:comments|replies|reviews)\b")
API_WRITE = re.compile(
    r"(?:-X\s+(?:POST|PATCH|PUT)\b"
    r"|--method\s+(?:POST|PATCH|PUT)\b"
    r"|-f\s+body|-F\s+body|--field\s+body|--raw-field\s+body"
    r"|--input\b"
    r"|/replies\b)"
)

REASON = (
    "Blocked: this command posts to a GitHub comment or review thread, which "
    "Matte has asked the assistant not to do. Report review triage (what you "
    "fixed / declined and why) directly in chat instead, and land code changes "
    "as commits. Reading (gh pr view, gh api GET) and opening PRs (gh pr create) "
    "are still allowed."
)


def pending_override_path(session_id: str) -> Path:
    suffix = (session_id or "").strip() or "no-session"
    return PENDING_OVERRIDE_DIR / f"pending-gh-comment-override-{suffix}.json"


def load_override(session_id: str) -> dict | None:
    path = pending_override_path(session_id)
    if not path.exists():
        return None
    try:
        if time.time() - path.stat().st_mtime > OVERRIDE_TTL_SECONDS:
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


def blocked_label(cmd: str) -> str | None:
    for pat, label in VERB_PATTERNS:
        if pat.search(cmd):
            return label
    if API_CALL.search(cmd) and API_COMMENT_PATH.search(cmd) and API_WRITE.search(cmd):
        return "gh api (comment/review write)"
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("tool_name") != "Bash":
        return 0

    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str):
        return 0

    label = blocked_label(cmd)
    if label is None:
        return 0

    session_id = (data.get("session_id") or "").strip()

    override = load_override(session_id)
    if override:
        reason = (override.get("reason") or "").strip()
        if len(reason) >= MIN_REASON_CHARS:
            consume_override(session_id, {
                "ts": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "command": cmd,
                "blocked_as": label,
                "reason": reason,
            })
            return 0

    pending_path = pending_override_path(session_id)
    example = json.dumps({
        "reason": "REPLACE — who explicitly asked for this comment and for what; >= 40 chars.",
    })
    msg = REASON + (
        f"\n\nIf Matte explicitly asked you to post this, override it: write to "
        f"`{pending_path}` (use the Write tool) with JSON like:\n  {example}\n"
        f"Then re-issue the same command. The override is single-use, expires in "
        f"10 minutes, scoped to this session (session_id={session_id or 'unknown'}), "
        f"and logged to `{AUDIT_LOG}` for review. Do NOT override on your own "
        f"initiative — only when the user directly requested the post."
    )
    if override:
        reason = (override.get("reason") or "").strip()
        msg += (
            f"\n\nNOTE: pending override file found but not accepted: reason is "
            f"{len(reason)} chars; must be >= {MIN_REASON_CHARS}."
        )
    return deny(msg)


if __name__ == "__main__":
    sys.exit(main())
