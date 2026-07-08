---
name: review-habits
description: Audit how the user works with Claude Code and produce prioritized workflow recommendations. Inventories current settings/hooks/skills/plugins, analyzes recent conversation logs for tool-usage and friction signals, cross-references the latest Claude Code CHANGELOG and best-practices docs to surface unused features. Use when the user asks to "review my habits", "audit my Claude Code workflow", "find workflow improvements", "what should I change about how I use Claude Code", invokes /review-habits, or wants recommendations about settings, skills, or plugins they could adopt or drop.
disable-model-invocation: true
---

# Review Habits

Audit the user's Claude Code usage and produce a prioritized list of workflow improvements.

Accepts optional `<days>` argument (default `14`) for how far back to scan conversation logs.

## Workflow

### 1. Inventory current config (parallel batch)

In one assistant message, in parallel:
- Read `~/.claude/settings.json` (permissions, hooks, sandbox, enabled plugins, model, effort)
- `ls ~/.claude/hooks/ ~/.claude/skills/ ~/.claude/plugins/cache/`
- Read `~/.claude/plugins/installed_plugins.json`
- Read `~/.claude/CLAUDE.md` and the nearest project `CLAUDE.md`
- Check for `~/.claude/keybindings.json`

### 2. Analyze conversation logs (one Explore agent)

Spawn `subagent_type: Explore` with a self-contained prompt covering:
- Logs are JSONL under `~/.claude/projects/*/`, mtime within the last `<days>` days. The largest files (>500KB) are the most active sessions — focus there.
- **Tool usage breakdown**: count Bash, Read, Edit, Write, Agent, Skill, Monitor, EnterPlanMode, AskUserQuestion, TaskCreate, TaskUpdate, ScheduleWakeup, WebFetch.
- **Skill invocation counts**: from `Skill` tool calls + `<command-name>` tags in user messages.
- **Slash commands invoked**: grep for `<command-name>` tags and `/[a-z-]+` at message start.
- **Friction signals**: `InputValidationError`, `unknown type string`, `permission denied`, `user denied`, `<user-interrupted>`, plus user-message phrases like "no, don't", "stop", "wait", "actually", "not that". Count + a few representative file:line examples.
- **Repeated user corrections**: instructions the user gives often (signals missing automation/memory).
- **Agent fan-out**: parallel (multiple Agent calls in one assistant message) vs sequential.
- **Plan mode / Monitor / background tasks**: how often used; in which sessions.
- **Skills available but unused**: cross-reference `ls ~/.claude/skills/` and plugin skills against invocation counts.

Instruct the agent to use `rg -c`, `jq`, `grep`, `head` — not full reads. Cap report at 600 words with file:line evidence where useful.

### 3. Fetch latest docs (parallel WebFetch, single message)

In one assistant message, in parallel:
- `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` — summarize last 6 months grouped by theme (new tools, hooks, settings, slash commands, MCP/plugins, perf/UX, memory/agents).
- `https://code.claude.com/docs/en/best-practices` — extract tips and best-practices.
- `https://code.claude.com/docs/en/overview` — surface "Pro tip" / "Tip" callouts. Follow redirects from `docs.claude.com` to `code.claude.com` if needed.

### 4. Synthesize recommendations

Organize the report as these sections, each tied to **specific evidence** (invocation count, friction occurrences, log file paths):

1. **What you're doing well** (don't change)
2. **Highest-leverage changes** (do these first)
3. **Settings to add to `~/.claude/settings.json`**
4. **Skills/commands you have but don't use** — consider pruning or starting
5. **Workflow changes worth trying**
6. **Things to NOT bother with**

End with a one-line summary of the top 5.

### 5. Save the report to notes

Write the full report to `~/Documents/notes/YYYY-MM-DD-review-habits-report.md`:
- Use today's date (`date +%Y-%m-%d`).
- If that file already exists, suffix `-r2.md`, then `-r3.md`, etc. — check with `ls ~/Documents/notes/YYYY-MM-DD-review-habits-report*.md` first.
- Include the same six sections shown to the user plus the evidence (counts, file paths).

### 6. Offer to apply config changes

After presenting, ask whether to apply the concrete `settings.json` edits identified. Do not modify any files until the user has approved.

## Guardrails

- Use `subagent_type: Explore` (read-only) for log scanning — never `general-purpose`.
- Fan out parallel work in **one assistant message**; sequential calls block.
- Report must be specific. "Use plan mode more" is bad. "You used `EnterPlanMode` 35× but `/loop` 0× despite a polling pattern in 4 sessions" is good.
- Do not modify any file before synthesis is complete and user has approved.
- "Recommend something the user has" — before recommending a skill or slash command exists, verify it actually appears in the inventory or the changelog.
