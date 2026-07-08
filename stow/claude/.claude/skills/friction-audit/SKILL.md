---
name: friction-audit
description: Audit recent Claude Code transcripts to find sources of friction — permission prompts, deferred-tool errors, dead/buggy allowlist entries, repeatedly denied command shapes — then propose concrete fixes (settings.json edits, CLAUDE.md additions, hooks). Use whenever the user mentions excessive permission prompts, "Claude keeps asking", "this used to be more autonomous", workflow friction, "unknown type string" errors, or wants a sweep of why their setup feels slow. Triggers on phrases like "audit my friction", "why is Claude getting stuck", "fix my permissions", "what's making things slow", or `/friction-audit`. Broader than fewer-permission-prompts — that one only adds read-only allow rules; this one diagnoses root causes (compound-command shapes, dead allowlist entries, deferred tools) and proposes structural fixes including hook setup and CLAUDE.md guidance.
disable-model-invocation: true
---

# Friction audit

This skill diagnoses why Claude Code feels slow or interrupted for the user, then proposes (and optionally applies) targeted fixes. The goal is **root-cause analysis**, not just "add more allow rules".

## When to use

- User says permission prompts feel frequent, surprising, or worse than before.
- User reports cryptic tool-validation errors ("unknown type string", "expected object").
- User asks for a sweep / audit of their setup, or invokes `/friction-audit`.
- After a major Claude Code update where behavior shifted.

If the user just wants more read-only commands allowlisted (a narrower task), the `fewer-permission-prompts` skill is a better fit. This skill complements it by also looking at compound-command shapes, settings hygiene, and harness-level mechanisms (hooks, deferred tools).

## Method

### 1. Scan recent transcripts

Transcripts live in `~/.claude/projects/<sanitized-cwd>/*.jsonl`. Each line is a JSON object; assistant messages contain `message.content[]` entries with `type: "tool_use"`. For Bash, `input.command` is the shell string.

Scan across **all** project directories, not just the current one — friction shows up in whichever projects the user has been working in. Cap at ~80 most-recently-modified jsonl files so it stays fast.

Write a small Python helper to `/tmp/claude/friction_scan.py` that walks the transcripts and emits:
- Total bash invocations.
- Counts of compound shapes: `&&`, `;`, pipes, redirects, `$(...)`, heredocs `<<`, `for ... in` loops.
- Top 20 leading-token pairs (e.g. `git -C`, `grep -rn`, `cargo build`) — Counter of first non-env tokens.
- Top `git -C <path>` targets — surfaces which repos the user actually works in.
- Top `cd <target>` targets — surfaces directories the user keeps switching into.
- A handful of example commands per shape for the report.

Why a script instead of inline pipes: the harness shell-permission matcher will block long compound greps over jsonl files, defeating the very thing you're trying to debug. A self-contained Python script reads files directly and avoids that.

### 2. Read the current settings

Read `~/.claude/settings.json`, the project `.claude/settings.json`, and `.claude/settings.local.json` if they exist. Look for:

**Dead or buggy allowlist entries:**
- Auto-allowed commands that are also in the allowlist (the rule is dead — `echo`, `cat`, `ls`, `head`, `grep`, `rg`, `find` are all already auto-allowed). Don't suggest auto-allowed patterns to the user — see the `fewer-permission-prompts` skill for the full auto-allow list.
- Patterns with the wrong spacing (`cd *&& git *` won't match `cd foo && git ...` — the matcher needs the space before `&&`).
- Hyper-specific entries that match exactly one command (e.g., 9 separate `Bash(echo "specific string")` lines).
- Specific-path entries where a wildcard would do (six `Bash(git -C ~/code/<repo> *)` lines that could be one `Bash(git -C *)`).

**Missing wildcards** for paths the user actually uses — cross-reference top `git -C` and `cd` targets from step 1 against the allowlist.

**Hook configuration** — note whether SessionStart, PostToolUse, etc. hooks exist. Missing SessionStart is relevant for the deferred-tool issue.

### 3. Diagnose root causes

The Bash permission matcher is **structural**, not semantic. `Bash(grep:*)` matches `grep foo bar` but not `grep foo | head`. Any pipe / redirect / `&&` / `;` / `$(...)` / heredoc / `for` loop turns the call into a compound shape that needs its own allowlist match — and there is no syntax that allowlists "arbitrary pipelines of allowed commands". This single fact usually explains the bulk of recurring prompts.

Other recurring causes worth naming explicitly:
- `git -C <path>` whitelisted by exact path while the user works in many repos / worktrees.
- Heredoc commit messages from `/commit` and `/pr` skills — `git commit -m "$(cat <<'EOF'...)"` is a unique compound construct each time.
- `cd <path> && <cmd>` patterns where the path is allowlisted but the right-hand command isn't, or vice versa.
- "Unknown type string" errors are **not permission prompts** — they come from the harness's deferred-tools mechanism. Tools like `TaskCreate`, `TaskUpdate`, `EnterPlanMode`, `WebFetch`, `WebSearch`, `AskUserQuestion`, `Monitor`, `NotebookEdit`, MCP tools have schemas loaded only on demand via `ToolSearch select:<name>`. Calling them before `ToolSearch` produces the cryptic error.

### 4. Report findings

Present a short, structured report with these sections:

- **Pattern frequency** — table of compound shape counts (pipes, redirects, `&&`, `;`, etc.).
- **Top paths** — table of `git -C` / `cd` targets vs. what's allowlisted.
- **Pattern bugs** — specific dead, buggy, or hyper-specific entries in the allowlist.
- **Root causes** — prioritized, in plain language, with the *why* (not just the *what*).
- **Recommendations** — split into:
  - Settings changes (concrete diffs).
  - CLAUDE.md additions (workflow guidance to avoid generating prompt-triggering shapes).
  - Hook setup (e.g., SessionStart hook to pre-load deferred tool schemas).
  - What is **not fixable** via allowlist (so the user knows the limit).

Be concrete: name specific patterns to remove, specific patterns to add, specific lines to write into CLAUDE.md. Don't generalize when you can quote the actual offending entry.

### 5. Apply changes only when asked

End the report with a one-line offer: "Want me to apply (A) — rewrite the allowlist with the wildcards and drop the dead entries — and append (B) to CLAUDE.md?" If the user says yes, apply via Edit tool; preserve all other settings; validate the JSON afterward (`python3 -c "import json; json.load(open(...))"`).

For hook setup, follow the `update-config` skill's hook construction flow (pipe-test the command, validate via `jq -e`, accept that SessionStart hooks fire only on next session).

## Output structure

Use this template for the report:

```markdown
## Pattern frequency
| Shape | Count |
|---|---|
| Pipes `|` | N |
| ...

## Top `git -C` paths vs. allowlist
| Path | Calls | Allowlisted? |
| ... |

## Pattern bugs in current allowlist
- `Bash(...)` — <why it's wrong>

## Root causes (prioritized)
1. <name + one paragraph explaining the why>
2. ...

## Recommendations
**A. Settings changes** — concrete add/remove.
**B. CLAUDE.md additions** — workflow guidance.
**C. Hook setup** — when applicable.
**D. Not fixable via allowlist** — set expectations.

Want me to apply A and B?
```

## Anti-patterns to avoid

- **Don't just dump a long list of `Bash(foo:*)` rules.** That's the `fewer-permission-prompts` skill's job. This skill's value is diagnosis and structural fixes.
- **Don't suggest patterns for already-auto-allowed commands** (`cat`, `head`, `tail`, `grep`, `rg`, `find`, `ls`, `git status`, `gh pr view`, etc.). The allowlist entry is dead.
- **Don't recommend wildcards that grant arbitrary code execution** (`Bash(python3:*)`, `Bash(bash:*)`, `Bash(npx:*)`, etc.) — these are equivalent to "run any code". Skip them even if the user uses them frequently.
- **Don't promise the prompts will disappear entirely.** Compound shapes (730+ pipes in a typical scan) cannot be allowlisted by pattern. Be honest about the ceiling.
- **Don't apply changes without showing the diff first.** The user should see what's being removed and added.

## Why this skill exists

The Bash permission matcher's structural approach interacts badly with how Claude naturally writes shell commands — chained with `&&`, pipes for filtering, heredocs for multi-line strings. Over time, users accumulate dozens of hyper-specific allowlist entries that each fix one symptom, while the underlying shapes keep generating new prompts. This skill steps back, names the structural mismatch, and proposes both lower-friction prompt patterns (via CLAUDE.md) and cleaner allowlist hygiene — so the user spends less time dismissing prompts and more time getting work done.
