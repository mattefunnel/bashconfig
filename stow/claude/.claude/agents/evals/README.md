# /Users/mattias.johansson/.claude/agents/evals/

Empirical evaluations of the custom subagents in `~/.claude/agents/`. One subdir per agent, with versioned `iteration-N/` subdirs inside. Layout mirrors `~/.claude/skills/review/evals/` so the same conventions and tooling apply.

## Agents with evals

- `session-search/iteration-1/` — does the `session-search.md` playbook produce meaningfully better answers than vanilla Claude with the same tools and same query?

## Adding a new eval

1. `mkdir ~/.claude/agents/evals/<agent-name>/iteration-1/`
2. Write a `README.md` with: TL;DR + verdict, conditions, fixtures, matrix, scoring, layout, cost.
3. Snapshot the agent file at the time of evaluation under `agent-snapshot/`.
4. Capture fixtures, prompt templates, and per-run outputs.
5. For multi-iteration evals, copy `prompts/` and `fixtures/` to `iteration-2/` and update.

## Methodology notes — read before designing a new eval

**The "vanilla" baseline must be truly bare, not another elaborate prompt.** The realistic alternative to invoking an agent/skill is "type a 1-3 line prompt and hope Claude figures it out," not "type a 20-30 line briefing that already prescribes plants/controls/K/isolation/rubric." If the vanilla condition shares the skill's structure, you've smuggled the skill's contribution into the control and will measure a near-zero advantage even when the skill is genuinely valuable.

Concrete trigger: the make-eval skill's iter-4 K=10 result reported "skill loses to vanilla by -0.81 overall, recommend deprecation." iter-5 (same skill, same fixtures, same grader) replaced the 30-line "vanilla" with a 4-line bare prompt. Result flipped to **skill wins +0.48 with 95% CI [+0.15, +0.81]**, with adversarial fixtures at +1.23. The earlier negative verdict was an artifact of a strawman baseline.

Full write-up: `~/.claude/skills/make-eval/evals/iteration-5/README.md`. The general anti-pattern is captured as #23 in `~/.claude/skills/make-eval/references/anti-patterns.md`.

If you want to ALSO compare against an elaborate alternative prompt, set up a three-arm eval (bare / elaborate-alternative / skill) — don't conflate the alternative-prompt comparison with the user-facing value question.

**Grader-validity caveat (also applies to skill evals).** A single LLM-as-judge grader scores eval-design idiomaticity (does this match the answer key's expected elements?), not whether the design would produce a correct outcome if executed. Findings are robust within the grader's idiom but should not be confused with outcome validity. See iter-5 README for a longer discussion.
