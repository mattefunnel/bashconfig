---
name: recap
description: Re-orient mid-work — summarize what we've done this session, in which repos/files, where we pivoted, and what the current task is. Use when the user invokes /recap, or asks "where are we", "what have we done", "what's the state of this conversation", "did we pivot", "get me my bearings", or wants to re-orient after a long or winding session.
---

# recap

Produce a timeline-style recap of the current session so the user can re-orient mid-work. Output is for a human skimming — be terse, concrete, and honest about uncertainty.

## Steps

1. **Recover earlier context from the transcript.** Some of the early conversation may have been compacted out of your context window. Read the active session transcript to recover pivots and repos you no longer hold in context:
   - **Find the live transcript by session id — never by recency or cwd.** The current session id is in the env var `CLAUDE_CODE_SESSION_ID`, and the transcript file is named exactly `<session-id>.jsonl`. So the file is `ls ~/.claude/projects/*/"$CLAUDE_CODE_SESSION_ID".jsonl` (one project folder will contain it). This is exact and unique — it picks *this* conversation even with many sessions running concurrently, and it survives a mid-session `cd` because the filename is the session id, not a path slug. Do NOT use `ls -t ... | head -1` (races against your other live sessions) and do NOT slugify cwd (breaks after `cd`).
   - Fallback if `CLAUDE_CODE_SESSION_ID` is somehow unset: `rg -l '"sessionId"' ~/.claude/projects/*/*.jsonl` and pick the file whose tail contains the `/recap` request you're servicing.
   - Pull the user's messages and the topic shifts from it. Don't dump the file — extract `"role":"user"` text and tool names. `rg '"role":"user"' <file>` then read the matches, or `rg -o '"type":"(tool_use)"[^}]*"name":"[^"]+"' <file>` for the tool/repo trail. If the file is huge, sample the first and last 200 lines.

2. **Identify repos/dirs touched.** From both context and the transcript, list every repo or directory worked in (look at file paths in Read/Edit/Write/Bash calls). Funnel checkout root is `~/code/funnel-io/<repo>`; note each distinct repo.

3. **Check git state** for each repo touched (skip if none). Use `git -C <path>` — never `cd`:
   - `git -C <path> status --short --branch` (branch, dirty files)
   - `git -C <path> log --oneline @{u}.. 2>/dev/null` (unpushed commits, if any)
   Run these as parallel Bash calls, one per repo. Keep it to repos actually touched this session.

4. **Emit the recap** in the format below.

## Output format

```
## Recap

**Goal:** <the original ask in one line>

**Timeline:**
- <chronological bullet — what happened / was decided>
- <pivot points marked explicitly: "↳ pivoted: ...">
- ...

**Repos & files:**
- `<repo>` (branch `<x>`, <N dirty / clean>) — <what we did here>
- ...

**Current task:** <what we're doing right now, one or two lines>

**Next step:** <the immediate open action, or "awaiting your call on X">

**Open questions:** <unresolved decisions, or omit if none>
```

## Rules

- Mark pivots explicitly — that's the main thing the user is asking for. If the conversation changed direction, say so and why.
- If nothing was committed/edited (advice-only session), say that plainly under Repos & files; don't invent activity.
- Distinguish done from proposed. "We decided X" ≠ "I suggested X and you haven't answered."
- No flair. Short sentences. If you're unsure whether something happened, say "unclear from transcript".
