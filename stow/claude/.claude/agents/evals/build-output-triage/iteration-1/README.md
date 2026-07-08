# build-output-triage eval — iteration 1

Lightweight A/B eval (made via the `make-eval` skill). Does the `build-output-triage` agent's system prompt produce a tighter, raw-dump-free build summary than vanilla Claude with the same tools and task?

Date: 2026-05-29. Model: Sonnet. **K=10** per cell.

## Conditions
- **A — vanilla:** `general-purpose` subagent, task only.
- **B — agent:** `build-output-triage` subagent (system prompt + Bash/Read/Grep/Glob), same task.

Both read the identical task file and write their verbatim report to disk. Only the agent system prompt differs.

## Fixtures (synthetic crates under `/tmp/claude/eval-crates/`)
- `fail` — `botfail` crate: 2 compile errors (E0425 missing fn, E0308 type mismatch) + 1 warning. Budget 200 words.
- `warn` — `botwarn` crate: compiles, 4 warnings. Budget 200 words.

Ground truth + scoring keys in `fixtures/`.

## Scoring (pre-declared)
Auto, via `../aggregate.py`: `word_count`, `over_budget`, `correct_status`, `raw_dump` (≥6 lines of raw rustc output — the anti-goal this agent exists to prevent). Accuracy spot-checked: did it name the right errors (fail) / report pass+warnings (warn)?

## TL;DR

| metric | vanilla (mean±stdev) | agent (mean±stdev) | read |
|---|---|---|---|
| fail `word_count` | 146.5 ± 17.37 | **63.3 ± 4.61** | agent 57% shorter, lower variance |
| warn `word_count` | 104.6 ± 8.98 | **50.3 ± 14.38** | agent 52% shorter |
| `over_budget` (200w) | 0.0 | 0.0 | both stay within budget |
| `raw_dump` (anti-goal) | 0.0 | 0.0 | **neither dumps raw rustc** — but see caveat |
| `correct_status` | 0.6 ± 0.49 | 1.0 ± 0.0 | ⚠️ **scoring artifact**, not real (see below) |

Accuracy (manual spot-check): both conditions are accurate — `fail/vanilla` names both errors (E0425, E0308) with file:line and even shows snippets; `fail/agent` names both, tighter. The `correct_status` gap is a regex false-negative: vanilla writes "failed"/"errors" (plural) which my `\bfail\b`/`\berror\b` keys miss. **Both are 100% correct on status.**

**Verdict:** Agent produces the **same accurate diagnosis in ~half the words**. The headline `raw_dump` anti-goal *did not fire for either condition* — but that's because the toy crates emit tiny output that even vanilla summarizes. On a real `mvn`/large-cargo build (the agent's actual use case) vanilla's verbosity gap would widen sharply; this fixture **understates** the agent's value. Worth keeping, but a future iteration should use a genuinely noisy build to exercise `raw_dump`.

## Limitations
- Synthetic toy crates (no deps); real builds dump far more, so the raw-dump gap is likely understated here.
- Sonnet only; K=10 single iteration.
- The agent's AWS/CodeArtifact gotcha branch is untested (no AWS-gated crate in fixtures).

## How to re-run
1. `cp ~/.claude/agents/build-output-triage.md artifact-snapshot/`
2. Recreate crates (see `/tmp/claude/eval-crates/`), re-run workflow `agent-evals-k10`.
3. `python3 /tmp/claude/agenteval/aggregate.py`.

## Cost
40 Sonnet runs (this agent's share of the 120-run batch).
