# /review skill eval — iteration 2

Dogfood of the `make-eval` skill at reduced scope vs iter-1. Same hypothesis ("does the Code Standard Hotspots section in SKILL.md add signal over CLAUDE.md alone?"), Sonnet-only, K=3 instead of K=6, both fixtures retained.

Date: 2026-05-27.

## TL;DR

| Cell (K=3) | TP rate (mean ± stdev) | Silence rate (mean ± stdev) | Hard FPs |
|---|---|---|---|
| **fixture-1 with-Hotspots** × Sonnet | 0.933 ± 0.058 | 0.667 ± 0.167 | 2 |
| **fixture-1 no-Hotspots** × Sonnet | 0.900 ± 0.000 | 0.778 ± 0.096 | 1 |
| **fixture-2 with-Hotspots** × Sonnet | **0.833 ± 0.058** | 0.556 ± 0.192 | 4 |
| **fixture-2 no-Hotspots** × Sonnet | **0.500 ± 0.100** | 0.444 ± 0.192 | 5 |

**Verdict (iter-2): confirms iter-1.** Hotspots is **load-bearing for fixture-2 (defense-heavy): TP drops 33 pp without it (0.83 → 0.50)**, replicating iter-1's Sonnet finding (iter-1 reported 0.78 → 0.23 — different absolute numbers because of fixture variance + iter-2 graders' calibration, but the gap is the same shape).

For fixture-1 (comment-heavy), the Hotspots section adds almost no signal at K=3 (0.93 vs 0.90). This was also visible in iter-1 — fixture-1 is easier; the comment-related hotspots are caught even without explicit framing.

## What changed from iter-1

| dim | iter-1 | iter-2 |
|---|---|---|
| K | 6 | 3 |
| models | Opus 4.7 + Sonnet 4.6 | Sonnet only |
| reviewer runs | 48 | 12 |
| grader runs | 48 | 12 |
| total cost | ~$15–20 | ~$3–5 |

Rationale for the reduced scope: iter-1 already established that the Hotspots section is load-bearing for Sonnet (the bigger effect) and stabilizing for Opus. Iter-2 dogfoods the make-eval skill at a more economic cadence and confirms the Sonnet finding holds at smaller K — useful for ongoing regression testing when iterating on SKILL.md.

## How the eval is set up

### Conditions tested

Same as iter-1:
- **A: with-Hotspots** — `skill-snapshots/skill-A/SKILL.md` (full current SKILL.md including the Code Standard Hotspots section).
- **B: no-Hotspots** — `skill-snapshots/skill-B/SKILL.md` (same, Hotspots section stripped).

### Fixtures

Same as iter-1 — copies under `fixtures/`:
- `fixture-1-comment-heavy.patch` + `fixture-1-ground-truth.md`
- `fixture-2-defense-heavy.patch` + `fixture-2-ground-truth.md`

5 planted items + 3 controls per fixture.

### Matrix

2 fixtures × 2 conditions × Sonnet × K=3 = **12 reviewer runs**, each scored by a separate Sonnet grader = 12 grading.json files. Reviewer + grader briefs in `prompts/`.

## Scoring

Same rubric as iter-1 (see `prompts/grader_brief.md`):
- Planted: `tp` (1.0) / `tp_partial` (0.5) / `missing` (0.0).
- Control: `correct_silence` (1.0) / `fp_soft` (0.5) / `fp` (0.0).

TP rate = (tp_count + 0.5 × tp_partial_count) / 5_plants per run.  
Silence rate = (correct_silence_count + 0.5 × fp_soft_count) / 3_controls per run.

## Per-run grading

### Fixture 1 (comment-heavy)

with-Hotspots:
| run | tp | tp_partial | missing | correct_silence | fp | fp_soft | TP rate | silence rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 1 | 0 | 2 | 1 | 0 | 0.90 | 0.667 |
| 2 | 4 | 1 | 0 | 1 | 1 | 1 | 0.90 | 0.50 |
| 3 | 5 | 0 | 0 | 2 | 0 | 1 | 1.00 | 0.833 |

no-Hotspots:
| run | tp | tp_partial | missing | correct_silence | fp | fp_soft | TP rate | silence rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 1 | 0 | 2 | 1 | 0 | 0.90 | 0.667 |
| 2 | 4 | 1 | 0 | 2 | 0 | 1 | 0.90 | 0.833 |
| 3 | 4 | 1 | 0 | 2 | 0 | 1 | 0.90 | 0.833 |

### Fixture 2 (defense-heavy)

with-Hotspots:
| run | tp | tp_partial | missing | correct_silence | fp | fp_soft | TP rate | silence rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 1 | 0 | 2 | 1 | 0 | 0.90 | 0.667 |
| 2 | 4 | 0 | 1 | 2 | 1 | 0 | 0.80 | 0.667 |
| 3 | 4 | 0 | 1 | 1 | 2 | 0 | 0.80 | 0.333 |

no-Hotspots:
| run | tp | tp_partial | missing | correct_silence | fp | fp_soft | TP rate | silence rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 0 | 2 | 1 | 2 | 0 | 0.60 | 0.333 |
| 2 | 1 | 2 | 2 | 2 | 1 | 0 | 0.40 | 0.667 |
| 3 | 2 | 1 | 2 | 1 | 2 | 0 | 0.50 | 0.333 |

## Notable observations

1. **The Hotspots effect concentrates on fixture-2 (defense-heavy).** The defensive-flare planted items (`MAX_PRICING_RESPONSE_BYTES` cap, `PRICING_API_TIMEOUT_SECS` knob, retry layers, placeholder tests) are exactly what the Hotspots section names explicitly. Without that explicit framing, Sonnet often classifies them as "good engineering" and lets them pass. With Hotspots, recall jumps from 0.50 → 0.83.

2. **C3 (intentional fail-fast `expect()` on env vars) drives most of the hard FPs.** Sonnet has a strong prior that `.expect()` in production code is a code smell. Even with the explicit "YAGNI — Constructors are infallible by design" note in CLAUDE.md and an inline docstring, multiple runs blocked on it. iter-1 hit the same pattern. Not a skill defect — fixture-as-designed.

3. **Variance at K=3 is meaningful.** Fixture-2 with-Hotspots silence rate ranges 0.333–0.667 across 3 runs — the same condition can look passing or failing depending on the draw. This is what iter-1's K=6 would also have shown. K=3 is enough to detect this variability but not enough to tighten the confidence interval much.

4. **Iter-1 vs iter-2 absolute TP-rate differences are real.** Iter-1 reported Sonnet with-Hotspots fixture-2 TP at 0.78; iter-2 got 0.83. Iter-1 reported Sonnet no-Hotspots fixture-2 TP at 0.23; iter-2 got 0.50. Differences are partly K=6 vs K=3 luck, partly likely grader-calibration drift (iter-2 graders gave more `tp_partial` than iter-1 did on borderline cases). For tighter cross-iteration comparison, future iterations should use the same grader prompt verbatim and check inter-grader agreement.

## Limitations vs iter-1

- **K=3 vs K=6** — wider confidence intervals; not enough to detect subtle effects with the same statistical power.
- **Sonnet only** — Opus might show a different magnitude of effect. iter-1 reported Hotspots is bigger for Sonnet than Opus, so dropping Opus underestimates the value-of-skill on Opus workloads.
- **No grader-agreement check** — single grader per review. iter-1 had the same limitation but with K=6 the per-cell average smooths out individual grader noise. K=3 is more sensitive to grader idiosyncrasies.

## How to re-run

1. Optionally update `~/.claude/skills/review/SKILL.md`; re-snapshot:  
   `cp ~/.claude/skills/review/SKILL.md skill-snapshots/skill-A/SKILL.md`  
   (and ablate Hotspots for `skill-snapshots/skill-B/SKILL.md`)
2. Spawn 12 reviewer subagents via Agent tool, parameterized over `{fixture, condition, run}`. Each saves to `/tmp/claude/review-iter2-runs/<fixture>/<condition>/run-<k>/review.md`.
3. After reviewers complete, spawn 12 grader subagents (one per review). Each writes `grading.json` next to the review.
4. Copy `/tmp/claude/review-iter2-runs/` → `runs/`.
5. Aggregate manually (or write `aggregate.py`) into the per-run + TL;DR tables above.

## Layout

```
iteration-2/
├── README.md                                    # this file
├── skill-snapshots/                             # frozen skill variants tested
│   ├── skill-A/SKILL.md                         # with Hotspots
│   └── skill-B/SKILL.md                         # no Hotspots
├── fixtures/                                    # copied from iter-1
│   ├── fixture-1-comment-heavy.patch
│   ├── fixture-1-ground-truth.md
│   ├── fixture-2-defense-heavy.patch
│   └── fixture-2-ground-truth.md
├── prompts/                                     # copied from iter-1
│   ├── reviewer_brief.md
│   └── grader_brief.md
└── runs/
    ├── fixture-1/sonnet-runs/
    │   ├── with_hotspots/run-{1,2,3}/review.md + grading.json
    │   └── no_hotspots/run-{1,2,3}/review.md + grading.json
    └── fixture-2/sonnet-runs/  (same shape)
```

## Cost

12 reviewer Sonnet runs (avg ~50k tokens each) + 12 grader Sonnet runs (avg ~38k tokens) ≈ **~$3.50**. Wall-clock: ~5 min for the parallel reviewer batch, ~1 min for the grader batch.

## Conclusion

The `make-eval` skill works for a re-run — methodology was clean, results held up. The reduced K and dropped Opus dimension cost some confidence on the absolute numbers but the qualitative finding ("Hotspots load-bearing for defense-heavy fixture, not as much for comment-heavy") replicates strongly.
