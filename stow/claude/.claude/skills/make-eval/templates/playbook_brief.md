# Playbook brief — condition B template

For the with-skill / with-playbook condition. Same task as vanilla, but inject the artifact snapshot as a directive.

Parameterize: `{QUERY}` or `{TASK_DESCRIPTION}`, `{CUTOFF}`, `{CORPUS_PATH}`, `{OPTIONAL_NOISE_CAVEAT}`, `{PLAYBOOK}`.

`{PLAYBOOK}` is filled with the BODY of `artifact-snapshot/SKILL.md` (or agent .md) — strip the YAML frontmatter, keep everything else.

---

You are doing a research task in isolation. {TASK_DESCRIPTION_OR_FIND_SESSIONS_DISCUSSING_QUERY}.

**Hard scope (the test depends on this):**
- Search EXCLUSIVELY under `{CORPUS_PATH}`. The playbook below may reference other paths (e.g. `~/.claude/projects/`) — SUBSTITUTE `{CORPUS_PATH}` wherever it applies.
- DO NOT read anything outside `{CORPUS_PATH}`.

{OPTIONAL_NOISE_CAVEAT}

**Playbook (apply this):**

---
{PLAYBOOK}
---

**Query / Task:** {QUERY}
**Window / Scope:** [as appropriate for the task]

Tools: Bash, Read. (Search via `rg`/`fd` through Bash — there are no separate Grep/Glob tools in current Claude Code builds.)

At the end, append `--- METRICS ---` then:

```
[metric_1]: <value>
[metric_2]: <value>
trickiest_thing: "<one sentence>"
```

Just dive in.

---

## Filling in the template

- `{PLAYBOOK}` should be the full body of the artifact under test. Strip YAML frontmatter. Keep the artifact's own examples, output shape specs, anti-patterns sections, etc. — that's what we're testing.
- The "SUBSTITUTE `{CORPUS_PATH}`" instruction is critical when the artifact's playbook references absolute paths to data that exists outside the corpus. Without it the subagent will try to read forbidden paths.
- **Both conditions must use the same `{OPTIONAL_NOISE_CAVEAT}`** if either uses one. Asymmetric caveats invalidate the comparison.
- Same toolkit, same task, same isolation. The ONLY difference between A and B should be the presence of the playbook.

## Common mistakes

- **Forgetting to strip YAML frontmatter** from the playbook content — the frontmatter has trigger phrases that aren't useful as instructions and may confuse the subagent.
- **Letting the playbook reference paths the subagent can't access** — substitute or strip those references.
- **Different toolkits between A and B** — both must have Bash/Read (or whatever the agreed set is).
