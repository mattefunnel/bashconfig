# pr-watcher eval — iteration 1

Lightweight A/B eval (made via the `make-eval` skill). Does the `pr-watcher` agent's system prompt produce a more compact, structured, accurate PR-status report than vanilla Claude with the same tools and task?

Date: 2026-05-29. Model: Sonnet (agent's declared model). **K=10** per cell.

## Conditions
- **A — vanilla:** `general-purpose` subagent, task only, no agent system prompt.
- **B — agent:** `pr-watcher` subagent (its system prompt + Bash/Read tools), same task.

Both read the identical task file and write their verbatim report to disk. The ONLY difference is the agent system prompt.

## Fixtures (real `\gh`, funnel-io/transform)
- `multi` — sweep 4 PRs (#766 open, #762 merged, #753 closed, #752 merged). Budget 150 words.
- `single` — detail on PR #766. Budget 200 words.

Ground truth + scoring keys in `fixtures/`.

## Scoring (pre-declared)
Auto, from disk output via `../aggregate.py`: `word_count`, `over_budget`, `has_table`/`has_structure`, `raw_json` (leaks raw gh JSON — the anti-goal). Accuracy spot-checked manually against `fixtures/*.md` ground truth.

## TL;DR

| metric | vanilla (mean±stdev) | agent (mean±stdev) | read |
|---|---|---|---|
| multi `word_count` | 276.2 ± 38.44 | **96.5 ± 1.28** | agent **65% shorter**, ~30× lower variance |
| multi `over_budget` (150w) | **1.0** ± 0.0 | 0.0 ± 0.0 | vanilla busts the 150-word budget every single run |
| single `word_count` | 177.7 ± 20.92 | **63.9 ± 6.86** | agent 64% shorter |
| `has_table` | 1.0 | 1.0 | both always produce a table/structured block |
| `raw_json` (anti-goal) | 0.0 | 0.0 | **neither leaks raw gh JSON** |

Accuracy (manual spot-check): both report all 4 PR states correctly (open/merged/closed/merged), CI passing, mergeability right.

**Verdict:** The agent delivers the **same accuracy in ~⅓ the words** with near-zero length variance. (Vanilla's 276-word multi-PR sweep exceeds the agent's 150w cap, but absolute cap-compliance is not treated as a quality gate — the meaningful signal is the brevity *delta*, which is large.) Its value prop is **brevity + consistency**, not better answers. Note the two explicit guards in the agent spec — "produce a table" and "don't show raw JSON" — turn out to be belt-and-suspenders: vanilla already does both. The agent earns its keep purely as a context-saver.

## Limitations
- Sonnet only; K=10 single iteration.
- #766 is a live PR — its state could drift; the merged/closed PRs are stable anchors.
- Accuracy is manual spot-check, not auto-graded against a planted key.

## How to re-run
1. `cp ~/.claude/agents/pr-watcher.md artifact-snapshot/`
2. Re-run the workflow `agent-evals-k10` (script under the session's workflows/scripts/).
3. `python3 /tmp/claude/agenteval/aggregate.py` and copy results back here.

## Cost
40 Sonnet runs (this agent's share of the 120-run batch). ~$3-4 for the agent's slice.
