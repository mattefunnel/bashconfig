# session-search eval — iteration 2

Dogfood of the `make-eval` skill. Bumps K=1 → K=3 vs iter-1 to get variance estimates; everything else held constant.

Date: 2026-05-27.

## Hypothesis (carried from iter-1)

Does the `session-search` playbook produce meaningfully better answers than vanilla Claude with the same tools?

## What changed from iter-1

- **K=3 per cell** (was K=1) — the headline change. Iter-1's "directional only" K=1 left us with no variance estimate; this iteration delivers one.
- Same 2 queries (VPC Lattice, actix-to-axum), same 2 conditions (vanilla, playbook), same corpus (`/tmp/claude/eval-corpus/` — real file copies, pre-2026-05-25), same prompts (`prompts/`).
- Same model (Sonnet), same toolkit (Bash/Read/Grep/Glob), same manual spot-check rubric.

## TL;DR

**New insight visible only at K=3:** the playbook produces near-zero variance in `sessions_returned` (8 in all 6 playbook runs, stdev=0) while vanilla varies substantially (13/15/17 for Q1, 7/10/12 for Q2). For Q2's token cost the difference is even more dramatic — playbook stdev is **16× lower** than vanilla's.

| metric | vanilla (mean ± stdev) | playbook (mean ± stdev) | conclusion |
|---|---|---|---|
| Q1 `sessions_returned` | 15.0 ± 2.0 | **8.0 ± 0.0** | playbook clamps to 8 via its "Cap at 8" rule; vanilla decides per run |
| Q1 `tool_uses` | 18.0 ± 3.6 | 28.7 ± 4.9 | playbook does ~60% more tool calls |
| Q1 `total_tokens` | 61,160 ± 4,768 | 64,165 ± 10,535 | similar mean; playbook variance is HIGHER |
| Q2 `sessions_returned` | 9.67 ± 2.52 | **8.0 ± 0.0** | same shape |
| Q2 `tool_uses` | 9.67 ± 1.15 | 23.7 ± 6.66 | playbook **2.4×** tool calls |
| Q2 `total_tokens` | 58,308 ± 15,992 | 56,583 ± **1,030** | playbook tokens FAR more stable (16× lower stdev) |

**Verdict (updated from iter-1):** the playbook's real value proposition is **output stabilization**, not better answers. Vanilla and playbook converge on the same top-3 canonical hits for both queries; they disagree on the tail. Playbook is much more consistent across runs (zero variance on hit count) at the cost of higher tool budget.

## What K=3 revealed that K=1 hid

**Iter-1 conclusions held but were weakly evidenced.** The "playbook ≈ vanilla" finding was correct at the mean — but it MISSED the variance story entirely:

- iter-1 said "playbook uses ~20% more tool calls (23 vs 31)". Iter-2 shows playbook uses **60-150% more** depending on query.
- iter-1 said "playbook ~20% more token-efficient". Iter-2 shows token mean is similar; the real difference is in **variance** (16× lower for playbook on Q2).
- iter-1 missed that the playbook's "Cap at 8" rule produces an unusual degenerate distribution (delta function at 8 hits) vs vanilla's roughly normal distribution.

**Two surprising findings that iter-1 might also have missed:**

1. **Coverage gap for Q1.** The playbook MISSES the canonical "AWS meeting" session (1c2cc198) that all 3 vanilla runs surface in their top 2. The playbook's hit-count-based ranking demotes it because that session has fewer total `VPC Lattice` mentions than sessions where the term appears in pasted log noise. This is a real ranking defect.

2. **Wrapper stripping ≠ noise filter for Q2.** Run 3 of the playbook surfaced 2 obviously-noise sessions (bashconfig dev-tools work, Documents-notes superpowers comparison) — both only matched because `actix-to-axum` appears in their `<system-reminder>` skill listings. The wrapper-stripping in the playbook covers OPENING prose but doesn't affect RANKING. Vanilla agents (especially run 2) caught and excluded these explicitly.

## Recommendations for iter-3

1. **Match-density ranking, not raw count.** Demote sessions where matches concentrate in single tool-output blocks. Fixes the Q1 1c2cc198 miss and reduces sensitivity to log-paste noise.
2. **Strip `<system-reminder>` before ranking, not just before showing opening prose.** Fixes the Q2 noise leakage.
3. **K=6 with a separate auto-grader** to confirm the variance findings hold at larger sample. (See review eval iter-1 for the auto-grading pattern.)
4. **Test on real session-search workload** rather than synthetic corpus queries.

## Conditions

- **A: vanilla** — `general-purpose` subagent, no playbook injection.
- **B: playbook** — `general-purpose` subagent + full body of `agent-snapshot/session-search.md` as a directive.

Both use Sonnet, same toolkit, same corpus path.

## Fixtures

Same as iter-1 — `fixtures/query-1-vpc-lattice.md`, `fixtures/query-2-actix-to-axum.md` (in iter-1; reused via reference).

## Isolation

Same corpus as iter-1: `/tmp/claude/eval-corpus/` with 941 real-file copies of `~/.claude/projects/*.jsonl` modified before 2026-05-25. Subagents have fresh contexts and the prompt forbids reads outside the corpus.

## Matrix

2 queries × 2 conditions × K=3 = **12 runs** (Sonnet only).

## Scoring (pre-declared)

Same manual spot-check rubric as iter-1, but per-metric we compute mean ± stdev across K=3 runs. Top-hit accuracy spot-checked against the same ground-truth notes in iter-1's fixtures.

## How to re-run

1. Snapshot the artifact: `cp ~/.claude/agents/session-search.md artifact-snapshot/session-search.md`.
2. Rebuild corpus if needed: `bash ../iteration-1/corpus/build_corpus.sh` (or use the make-eval skill's template).
3. Spawn 12 `general-purpose` subagents in parallel via the Agent tool, reading the prompt files at `/tmp/claude/eval-prompts/session-search-{vanilla,playbook}-{vpc,actix}.md`.
4. Save each agent's output to `runs/query-N-*/<condition>.md` (concatenate the 3 runs per cell).
5. Compute mean ± stdev per metric, update the TL;DR table.

## Layout

```
iteration-2/
├── README.md                     # this file
├── artifact-snapshot/
│   └── session-search.md
├── prompts/                      # (copied from iter-1 — same prompts)
└── runs/
    ├── query-1-vpc-lattice/
    │   ├── vanilla.md            # 3 runs + aggregate
    │   └── playbook.md
    └── query-2-actix-to-axum/
        ├── vanilla.md
        └── playbook.md
```

Iter-1 lives at `../iteration-1/` for comparison.

## Limitations

- K=3 is still small; K=6+ would tighten the variance estimates further.
- Sonnet only. Opus might behave differently (iter-1 noted Sonnet effect is bigger; Opus needs testing).
- Manual spot-check on top hits, not full auto-grading. The "playbook misses 1c2cc198 for Q1" finding is qualitative — needs auto-grading to quantify recall@8.
- The "Cap at 8" finding is somewhat artificial: it's a playbook rule, not a model behavior. Removing the cap from the playbook would change this dimension.

## Cost

12 Sonnet subagent runs, ~$1.50 total. ~3 min wall-clock parallel.
