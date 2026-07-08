# Vanilla brief — condition A template

For the no-skill / no-playbook condition. The subagent gets task description + tools + isolation scope, with NO injected artifact content.

Parameterize: `{QUERY}` (or `{TASK_DESCRIPTION}`), `{CUTOFF}`, `{CORPUS_PATH}`, `{OPTIONAL_NOISE_CAVEAT}`.

---

You are doing a research task in isolation. {TASK_DESCRIPTION_OR_FIND_SESSIONS_DISCUSSING_QUERY}.

**Background:** [Brief domain context the subagent needs to understand the task — e.g. "Claude Code stores conversation transcripts as .jsonl files (one JSON event per line). Each file is one session. Events have .type, .message.role, .message.content..."]

**Hard scope (the test depends on this):**
- Search EXCLUSIVELY under `{CORPUS_PATH}`. This is a curated corpus of pre-{CUTOFF} [DATA_DESCRIPTION], with the original directory structure preserved. The files are real copies — all tools work normally.
- DO NOT read anything outside `{CORPUS_PATH}`. The corpus has everything you need.

**Task:** [What the subagent must produce. Be specific about output shape: ranked list, table, key-value, etc.]

{OPTIONAL_NOISE_CAVEAT}

Tools: Bash, Read. (Search via `rg`/`fd` through Bash — there are no separate Grep/Glob tools in current Claude Code builds.)

**Output:** concise, ≤250 words. [Format expectation — e.g. tabular preferred.]

At the end, append `--- METRICS ---` then:

```
[metric_1]: <value>
[metric_2]: <value>
trickiest_thing: "<one sentence on the trickiest part>"
```

Just dive in. No clarifying questions.

---

## Filling in the template

- `{TASK_DESCRIPTION_OR_FIND_SESSIONS_DISCUSSING_QUERY}` — the actual task. Be concrete: not "do code review", but "Review the diff at fixtures/fixture-1.patch and flag CLAUDE.md violations".
- `{OPTIONAL_NOISE_CAVEAT}` — used only when the fixture has known noise that must be filtered (e.g. "term X is also a skill name and appears in every system-reminder"). If used, document the asymmetry in the README. Both conditions get the same caveat — otherwise the test is unfair.
- Self-reported metrics should match what the rubric scores on. Don't ask for `sessions_returned` if scoring on `accuracy`.
- "Just dive in" prevents the subagent from asking clarifying questions and wasting tool budget.
