# /review skill evals

Empirical evaluation of how the **Code Standard Hotspots** section of `SKILL.md` affects review quality. The question was: since `~/.claude/CLAUDE.md` is already in the system prompt every turn, does duplicating the same rules in this skill add signal, or just tokens?

Iterations 1–2 test the Hotspots section. **Iteration 3** (`iteration-3/`) tests a different change — the **Regression Scoping** rule (block only on issues the diff introduces, not pre-existing problems). Verdict there: ship it. Recall on introduced items stays at 1.00; pre-existing false positives drop sharply (Opus 7→0 hard FPs, silence 0.58→1.00; Sonnet a smaller 8→6). See `iteration-3/README.md`.

## TL;DR — iteration 1

| Cell (n=12) | TP rate | Silence rate | Hard FPs |
|---|---|---|---|
| **with Hotspots** × opus | 0.82 ± 0.06 | 0.67 ± 0.24 | 10 |
| **with Hotspots** × sonnet | 0.78 ± 0.06 | 0.90 ± 0.11 | 1 |
| **no Hotspots** × opus | 0.64 ± 0.21 | 0.60 ± 0.31 | 14 |
| **no Hotspots** × sonnet | **0.23 ± 0.17** | 0.85 ± 0.17 | 5 |

**Verdict: keep the Hotspots section.** It's load-bearing for Sonnet (TP drops 55 pp without it) and a meaningful uplift for Opus (TP drops 18 pp, variance triples).

Full numbers and per-item breakdown in `iteration-1/benchmark.json` (regenerable from `aggregate.py`).

## How the eval is set up

### Conditions tested

- **A: with Hotspots** — current `~/.claude/skills/review/SKILL.md`, includes the **Code Standard Hotspots** section enumerating speculative-defense / excessive-comments / placeholder-test / etc. patterns to flag.
- **B: no Hotspots** — same skill with that section stripped. CLAUDE.md is still referenced and loaded into every turn.

Both snapshots live under `iteration-1/skill-snapshots/{skill-A,skill-B}/SKILL.md`.

### Fixtures

Two ~800-line synthetic Rust diffs, designed so each planted CLAUDE.md violation is camouflaged among legitimate code of the same shape:

- **`fixture-1-comment-heavy.patch`** — 25–40 comments throughout (mostly legitimate workaround docs); the bloated `Why:`/`Note:` docstring has to be picked out of that noise.
- **`fixture-2-defense-heavy.patch`** — 10–15 defensive patterns (size caps, retries, fail-fast panics on misconfig); the speculative cap is placed *adjacent* to the legitimate public-upload cap so they look identical at a glance.

Each fixture has:
- **5 planted items (P1–P5)** that the reviewer SHOULD flag as `Blocking`.
- **3 controls (C1–C3)** that look flag-worthy but are intentional — these come from real conversation pushback ("trust the upstream API → drop the `model_name` guard", "Makefile tab-IFS continuation works", "`expect()` on env at startup is fail-fast on misconfig, idiomatic Funnel"). The fixtures themselves are synthetic but the control patterns are battle-tested in real PRs.

Ground truth tables: `iteration-1/fixtures/fixture-{1,2}-ground-truth.md`.

### Matrix

2 fixtures × 2 conditions × 2 models (Opus 4.7, Sonnet 4.6) × **K=6 runs per cell** = 48 reviews. Each review was graded by a separate Sonnet 4.6 grader = 48 grading.json files.

The reviewer brief and grader brief used by all 96 subagents are in `iteration-1/prompts/`.

## Scoring

For each **planted** item, the grader assigns:

- `tp` (1.0): flagged as `Blocking` with substantively the same concern
- `tp_partial` (0.5): mentioned in `Good To Know` only, OR flagged at the same location with a different concern
- `missing` (0.0): not mentioned at all

For each **control** item, the grader assigns:

- `correct_silence` (1.0): not flagged
- `fp_soft` (0.5): raised in `Good To Know` but acknowledged justification
- `fp` (0.0): flagged as `Blocking`

**TP rate** = mean per-item score across the 5 plants × 6 runs × 2 fixtures (when rolled up). **Silence rate** mirrors that for the 3 controls.

## How to re-run

1. Edit `~/.claude/skills/review/SKILL.md` if testing a new variant.
2. Update `iteration-1/skill-snapshots/skill-A/SKILL.md` to the new candidate (and keep `skill-B/` as your comparison baseline, or write a new snapshot).
3. Re-spawn the 48 reviewer subagents using `iteration-1/prompts/reviewer_brief.md` as the per-agent prompt template, parameterized over `{fixture, condition, model, run}`. Save each review to `iteration-N/runs/<fixture>/<condition>/<model>/run-<k>/review.md`.
4. Re-spawn 48 graders using `prompts/grader_brief.md`, one per review, each writing `grading.json` into the same dir.
5. `python3 aggregate.py` to regenerate `benchmark.json` and the printed summary tables.

For iteration 2+, create `iteration-2/`, copy `prompts/` and `fixtures/` (or regenerate fixtures if updating the test set), and update the snapshot dirs.

## Layout

```
review/evals/
├── README.md                      # this file
└── iteration-1/
    ├── aggregate.py               # produces benchmark.json + summary tables
    ├── benchmark.json             # per-cell aggregated stats
    ├── fixtures/
    │   ├── fixture-1-comment-heavy.patch
    │   ├── fixture-1-ground-truth.md
    │   ├── fixture-2-defense-heavy.patch
    │   └── fixture-2-ground-truth.md
    ├── prompts/
    │   ├── reviewer_brief.md      # per-subagent reviewer prompt template
    │   └── grader_brief.md        # per-subagent grader prompt template
    ├── skill-snapshots/
    │   ├── skill-A/SKILL.md       # condition A (with Hotspots) — frozen at eval time
    │   └── skill-B/SKILL.md       # condition B (Hotspots stripped)
    └── runs/
        ├── fixture-1/
        │   ├── with_skill/{opus,sonnet}/run-{1..6}/{review.md, grading.json}
        │   └── no_hotspots/{opus,sonnet}/run-{1..6}/{review.md, grading.json}
        └── fixture-2/
            └── ... (same shape)
```

## Notable observations from iteration 1

- **P5 fixture-2 (`account_id_to_s3_key` helper used once)** is a blind spot for all four cells — 0% TP everywhere. Either the camouflage was too good or the "helper used once" hotspot is genuinely hard to spot in a 1000-line diff. Worth a targeted fix in iteration 2.
- **C1 fixture-2 (removed `account_id` mismatch guard)** drives 8 of Opus-with-Hotspots' 10 hard FPs. The diff in isolation genuinely looks like a regression, and even the explicit "trust the upstream API as source of truth" guidance in CLAUDE.md doesn't talk Opus out of flagging it. This is a real fixture characteristic, not a skill defect — a human reviewer would also raise it without the conversation context.
- **Sonnet is consistently more cautious about flagging** than Opus (better silence rate everywhere). Hotspots tip Sonnet from "barely flags anything" (0.23 TP) to "catches most plants" (0.78 TP) without notably hurting silence.
- **Variance jumps when Hotspots are removed for Opus** (stdev 0.06 → 0.21 on TP). The skill isn't just shifting the mean; it's stabilizing the behavior.

## Cost

~$15–20 total across 96 subagent runs (24 Opus reviewers ~$12, 24 Sonnet reviewers ~$3, 48 Sonnet graders ~$2). Roughly 12 minutes wall-clock for the parallel reviewer batch, similar for graders.
