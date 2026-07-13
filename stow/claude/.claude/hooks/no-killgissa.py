#!/usr/bin/env python3
"""Stop hook: catch "killgissa" — stating a guess as a settled cause/fact.

Three stages:
  1. Cheap deterministic prefilter — skip the turn entirely (no model call) when the
     message is too short or has no declarative/assertive content worth judging.
  2. LLM judge — a small fast model reads the last assistant message and decides
     whether it states a confident causal/factual conclusion WITHOUT citing how it
     was verified. Only an explicit KILLGISSA verdict blocks.
  3. Grounding check — runs ONLY when stage 2 flagged a killgissa. Re-reads the last
     few conversation messages and overturns the flag when the claim merely restates
     what the user just said, or points to evidence already shown in those messages.
     Re-stating the user is not a guess.

Fails open on every uncertainty (bad stdin, no transcript, judge error/timeout,
unparseable verdict) so it can never wedge a turn. The grounding check fails
"confirm" (keeps the block) on its own errors, since stage 2 already flagged.
Loops are prevented by the stop_hook_active guard.
"""
import json
import subprocess
import sys

JUDGE_MODEL = "haiku"
JUDGE_TIMEOUT_SECS = 45
MIN_CHARS = 80  # below this, not worth a model call
GROUNDING_CONTEXT_MSGS = 6  # how many trailing conversation messages the grounding check sees

RUBRIC = """You are a reviewer with ONE job: detect "killgissa" — a guess stated as a settled fact.

You are given the final message an AI assistant is about to send. Decide whether it \
asserts a CAUSAL or FACTUAL conclusion with confidence WITHOUT showing how it was \
verified.

Block (KILLGISSA) when the message states something as established fact/cause and does \
NOT, in the same message, point to the evidence (a command output, a file it read, a \
measurement, a citation) AND is not hedged as uncertain. Flat factual assertions count, \
not just "root cause" phrasing — e.g. "X is a separate account", "the hub is prod-only".

Do NOT block when: the claim is hedged (likely/probably/I think/hypothesis/may be), the \
message cites its evidence ("the jq output shows", "I read X", "the metric was 20ms"), \
the message is asking a question, or is otherwise not making a confident unbacked claim.

If the message ENDS IN A QUESTION, it is an open turn seeking direction, not a closing \
claim — do NOT block.

Do NOT block reports of the assistant's OWN in-session actions or observations. Reporting \
what it just did or saw is a status report, not a guess about the world. This includes: \
"pushed", "nothing pushed" / "I did not push", "merged", "reverted", "committed as <sha>", \
"fixed", "done", "created the PR/branch", "tests pass", "CI green", "task is RUNNING". \
Treat these as OK even when phrased flatly, UNLESS the message ALSO asserts a separate \
unbacked causal/factual claim about how the wider system works. (An offer to verify a \
claim does NOT excuse a different confident unbacked claim asserted flatly alongside it.)

Reply with EXACTLY one line:
  OK
or
  KILLGISSA: <=12 words naming the unbacked claim

The message:
---
%s
---"""

GROUNDING_RUBRIC = """You are the second reviewer. A first reviewer flagged a possible "killgissa" \
(a guess stated as settled fact) in an AI assistant's final message. Your job is to CHECK THAT \
FLAG against the recent conversation and overturn it when the message's factual claims are \
actually grounded.

The first reviewer summarized the suspect claim as: %s
But judge the ACTUAL final message (shown last in the conversation below), not that summary — \
the summary can be lossy or wrong. Consider every confident factual/causal claim the final \
message makes.

Overturn the flag (reply GROUNDED) when the final message's claims, IN ENTIRETY, are grounded. \
That is, GROUNDED when EVERY factual part of the flagged claim is either:
  - a restatement of something THE USER said in a recent message, OR
  - backed by evidence shown in the recent messages (a command output, a file that was read, a \
    measurement), even if not repeated in the final message.

Re-stating the user is never a killgissa — the assistant is repeating what it was told, not \
guessing — and this holds even if phrased flatly and even if neither party "verified" it. A \
faithful PARAPHRASE or synonym of the user's words still counts as restatement (e.g. user \
"used by X" -> assistant "used by X" or a close rewording): do NOT nitpick wording differences \
that carry the same meaning.

Keep the flag (reply CONFIRM) only when the claim asserts a NEW factual PROPERTY that the user \
did not state (explicitly or in meaning) and the conversation did not evidence — an added \
characteristic, not just different phrasing. Such an addition is the killgissa even if the rest \
of the sentence restates the user.

Worked example. User said: "main.md is used by the note shell command." \
  - Assistant "main.md is used by the note command" (or a paraphrase like "the note command \
    uses main.md") -> GROUNDED (pure restatement). \
  - Assistant "main.md is an append-only ledger used by the note command" -> CONFIRM: "used by \
    the note command" restates the user, but "append-only" is a NEW property never stated or \
    shown — that added part is the killgissa.

Also CONFIRM when the claim originates entirely from the assistant with no user source and no \
evidence anywhere in the recent messages.

Decision procedure: strip away every part of the claim that restates the user or is evidenced. \
If NOTHING factual remains, reply GROUNDED. If a factual property remains unaccounted for, reply \
CONFIRM. When the remainder is only a wording difference of equal meaning, treat it as nothing \
remaining (GROUNDED).

Reply with EXACTLY one line: GROUNDED  or  CONFIRM

Recent conversation (oldest to newest; the final assistant message is last):
---
%s
---"""


def _text_from_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(p for p in parts if p)
    return ""


def last_assistant_text(transcript_path):
    text_parts = []
    with open(transcript_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "assistant":
                continue
            content = obj.get("message", {}).get("content", [])
            parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
            if parts:
                text_parts = parts  # keep only the latest assistant message
    return "\n".join(text_parts)


def recent_messages(transcript_path, limit):
    """Return up to `limit` trailing user/assistant messages as (role, text) tuples."""
    msgs = []
    with open(transcript_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = obj.get("type")
            if role not in ("user", "assistant"):
                continue
            text = _text_from_content(obj.get("message", {}).get("content", []))
            if text.strip():
                msgs.append((role, text.strip()))
    return msgs[-limit:]


def worth_judging(text):
    if len(text.strip()) < MIN_CHARS:
        return False
    # Needs at least one sentence-ending declarative. Questions-only / list-only
    # acknowledgements aren't claims.
    return "." in text


def _run_model(prompt):
    """Return stdout string, or None on any error."""
    try:
        proc = subprocess.run(
            ["claude", "-p", "--model", JUDGE_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=JUDGE_TIMEOUT_SECS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout or ""


def judge(text):
    """Return (is_killgissa, reason). Fail open to (False, '') on any error."""
    out = _run_model(RUBRIC % text)
    if out is None:
        return (False, "")
    verdict = out.strip()
    if verdict.upper().startswith("KILLGISSA"):
        _, _, reason = verdict.partition(":")
        return (True, reason.strip())
    return (False, "")


def is_grounded(claim, msgs):
    """Stage 3: return True if the flagged claim is grounded in recent messages.

    Fails to False (keep the block) on any error — stage 2 already flagged, so a
    grounding-check failure should not silently clear a real killgissa.
    """
    if not msgs:
        return False
    convo = "\n\n".join("[%s] %s" % (role.upper(), text) for role, text in msgs)
    out = _run_model(GROUNDING_RUBRIC % (claim or "(unspecified)", convo))
    if out is None:
        return False
    return out.strip().upper().startswith("GROUNDED")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if data.get("stop_hook_active"):
        sys.exit(0)

    transcript_path = data.get("transcript_path")
    if not transcript_path:
        sys.exit(0)

    try:
        text = last_assistant_text(transcript_path)
    except OSError:
        sys.exit(0)

    if not worth_judging(text):
        sys.exit(0)

    is_killgissa, claim = judge(text)
    if not is_killgissa:
        sys.exit(0)

    # Stage 3: overturn the flag when the claim just restates the user or points to
    # evidence already shown in the recent conversation.
    try:
        msgs = recent_messages(transcript_path, GROUNDING_CONTEXT_MSGS)
    except OSError:
        msgs = []
    if is_grounded(claim, msgs):
        sys.exit(0)

    reason = (
        "A reviewer flagged a possible killgissa — a guess stated as settled fact"
        + (f': {claim}' if claim else "") + ".\n"
        "Before ending the turn: did you actually verify this?\n"
        "- If verified: state the one piece of evidence that confirms it (the command output, the file you read, the measurement).\n"
        "- If not: downgrade it to a hypothesis, name at least one competing explanation you did NOT rule out, and say what would confirm it.\n"
        "Then finish."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
