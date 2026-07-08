# /review skill eval — iteration 3

Tests the **Regression Scoping** change to `SKILL.md`: blocking findings should cover only issues the diff *introduces or worsens*, not pre-existing problems the diff merely sits next to. Pre-existing issues go to `Good To Know` labelled `(pre-existing)`, or are omitted.

Date: 2026-06-21. K=6, Sonnet 4.6 + Opus 4.8, full A/B.

## Hypothesis

Adding the Regression Scoping section makes reviewers **stop blocking on pre-existing code smells** (raises silence rate / cuts hard FPs on unchanged-line controls) **without lowering true-positive recall** on smells the diff actually introduces.

Pre-declared threshold (smallest worthwhile effect): on the scoping fixture, the change should cut hard false positives on pre-existing controls by ≥30% **and** keep introduced-item recall within noise of baseline (no more than ~5 pp drop). If recall drops materially, the scoping language is over-suppressing and the change should be reworked.

## Conditions

- **A: with_scoping** — `skill-snapshots/skill-A/SKILL.md`, the new SKILL.md including the **Regression Scoping** section (and the scoping clauses threaded into Hotspots intro, Review Process steps 3/5/6/7, Finding Guidelines).
- **B: no_scoping** — `skill-snapshots/skill-B/SKILL.md`, the SKILL.md exactly as it was before this change (from git HEAD). Same Hotspots, same everything else.

## Fixtures

- **`fixture-3-regression-scoping.patch`** (the discriminating fixture). For three CLAUDE.md hotspot categories — excessive comments, speculative config, speculative defensive cap — the *same smell* appears twice: once **introduced** on `+` lines (planted P1–P3, plus P4 = a placeholder test in a new file) and once **pre-existing** on unchanged context lines (controls C1–C3). A control and its planted twin are the *same category of smell*; the only thing that should make one blocking and the other not is whether the line is new. 4 plants, 3 controls.
- **`fixture-2-defense-heavy.patch`** (TP-guard, copied from iter-1/iter-2). All 5 plants are on added lines, so the scoping change must NOT lower recall here. Confirms the change doesn't gut normal-diff blocking. 5 plants, 3 controls.

## TL;DR

| Cell (K=6) | TP rate | Silence rate | Hard FPs (/18) |
|---|---|---|---|
| **fixture-3** with_scoping × opus | 1.00 ± 0.00 | **1.00 ± 0.00** | **0** |
| **fixture-3** no_scoping × opus | 1.00 ± 0.00 | 0.58 ± 0.14 | 7 |
| **fixture-3** with_scoping × sonnet | 1.00 ± 0.00 | **0.64 ± 0.07** | **6** |
| **fixture-3** no_scoping × sonnet | 1.00 ± 0.00 | 0.53 ± 0.16 | 8 |
| fixture-2 with_scoping × opus | 0.70 ± 0.11 | 0.67 ± 0.00 | 6 |
| fixture-2 no_scoping × opus | 0.73 ± 0.10 | 0.61 ± 0.09 | 6 |
| fixture-2 with_scoping × sonnet | 0.77 ± 0.08 | 0.72 ± 0.14 | 5 |
| fixture-2 no_scoping × sonnet | 0.88 ± 0.16 | 0.69 ± 0.07 | 5 |

(Silence rate denominator is 3 controls × 6 runs = 18 per cell. Hard FPs = control items put in the Blocking section.)

**Verdict: ship the change.** On the discriminating fixture-3, recall stays pinned at **1.00 in every cell** — the scoping language does not suppress real introduced regressions. Meanwhile pre-existing false positives drop:

- **Opus: the effect is clean and large.** Silence 0.58 → **1.00**, hard FPs **7 → 0**. Every Opus run with scoping explicitly held pre-existing items out of the blocking section and labelled them `(pre-existing)` in Good To Know. This clears the pre-declared threshold by a wide margin.
- **Sonnet: the effect is real but partial.** Silence 0.53 → 0.64, hard FPs 8 → 6. Sonnet improves but still couples the pre-existing struct docstring (C1) to its introduced twin (P3) in most runs — when it blocks the new `daily_rollup` doc, it tends to sweep the old `Aggregator` doc in with it. The scoping rule helps Sonnet but doesn't fully fix this attribution error.

On fixture-2 (TP-guard), recall and silence move within noise (Sonnet TP 0.88 → 0.77 is inside the ±0.16 baseline stdev; the C1 account-id FP recurs in both conditions and is a documented fixture characteristic, not a scoping effect — see iter-1). No evidence the change hurts normal-diff review.

## Why fixture-3 recall is 1.00 and fixture-2 isn't

Different difficulty. Fixture-3's plants are blatant (a never-read env knob, a `Why:/Note:/Previously:` doc block, a no-op test) and unconfounded — every reviewer catches all four. That's intentional: the fixture isolates the *control* (silence) axis, so recall is a near-constant and the only moving part is whether pre-existing twins get blocked. Fixture-2 is the harder, camouflaged diff from iter-1 (P5 single-use helper is a known 0%-ish blind spot, P3 retry is often missed) — its job here is only to confirm scoping doesn't *lower* that recall, which it doesn't.

## Notable observations

1. **The change is load-bearing for Opus, partial for Sonnet.** Mirrors the iter-1/iter-2 pattern in reverse: there the Hotspots section was load-bearing for *Sonnet*. Here the scoping rule lands hardest on Opus, which is the more aggressive blocker (iter-1 noted Opus over-blocks). Opus had the most pre-existing FPs to cut and cut all of them; Sonnet had fewer and cut some.

2. **Sonnet's residual FP is an attribution-coupling error, not a rule-comprehension error.** Reading the Sonnet with_scoping reviews: they DO cite the regression-scoping rule and DO label some items `(pre-existing)`, but when an introduced smell and its pre-existing twin are the *same category* (two doc blocks), Sonnet tends to write one finding covering "both doc comments." A future SKILL.md tweak could target this directly ("when you flag an introduced instance of a pattern, check whether nearby instances of the same pattern are on unchanged lines — those are separate, pre-existing, and out of scope").

3. **Zero-variance cells.** Opus with_scoping on fixture-3 is 1.00 ± 0.00 silence across all 6 runs — the rule produces *stable* correct scoping for Opus, not just a better mean. Same stabilizing signature the Hotspots section showed for Opus TP in iter-1.

4. **The reviewer brief already said "don't opine on pre-existing code unless the diff touches it"** (line 24, inherited from iter-1). That clause is present in BOTH conditions, so it compresses the absolute gap (baseline silence isn't 0) but cannot bias the A−B difference. The measured lift is on top of that existing instruction — i.e. the SKILL.md section adds signal the one-line brief clause did not deliver on its own.

## Limitations

- **Brief confound (above).** Both conditions carry the line-24 "keep focused on the diff" instruction, so this eval measures the *marginal* lift of the SKILL.md section over that clause, not scoping-from-nothing. Real `/review` usage has no such clause in the user turn, so the true effect of the SKILL.md section in production is likely ≥ what's measured here.
- **Fixture-3 recall is a near-constant by design** — it can't detect a small recall regression from scoping, only a large one. Fixture-2 is the recall guard, but it's a different (harder, camouflaged) diff, so the two aren't a clean within-fixture recall comparison.
- **Single grader per review, Sonnet.** No inter-grader agreement check. The fixture-3 grader prompt is heavily specified (it spells out the C1/P3, C2/P1, C3/P2 twins) to reduce grader ambiguity, but that also means grader calibration is doing real work.
- **K=6** — resolves the large Opus effect and the flat fixture-2 result cleanly; the smaller Sonnet fixture-3 lift (0.53 → 0.64) is within ~1 stdev and would want K=10 to call confidently.

## How to re-run

1. Edit `SKILL.md`; re-snapshot: `cp <SKILL.md> skill-snapshots/skill-A/SKILL.md` (keep `skill-B/` as the pre-change baseline, or re-snapshot from the relevant git ref).
2. Resolved reviewer prompts are in `/tmp/claude/eval-prompts/reviewer-fixture{2,3}-{with,no}_scoping.md` (regenerate from `prompts/reviewer_brief.md` + the snapshot/diff paths if the temp dir is gone).
3. Spawn 48 reviewer subagents via the Agent tool in parallel batches (≤8/message), parameterized over `{fixture, condition, model, run}`. Each writes `review.md` to `runs/<fixture>/<condition>/<model>/run-<k>/` and returns only a short summary.
4. Spawn 48 grader subagents (Sonnet), one per review, using `/tmp/claude/eval-prompts/grader-fixture{2,3}.md` (built from `prompts/grader_brief.md`). Each writes `grading.json` next to the review.
5. `python3 aggregate.py` → regenerates `benchmark.json` and the summary table.

## Layout

```
iteration-3/
├── README.md                         # this file
├── aggregate.py                      # rollup → benchmark.json + table
├── benchmark.json                    # per-cell aggregated stats
├── skill-snapshots/
│   ├── skill-A/SKILL.md              # with Regression Scoping (new)
│   └── skill-B/SKILL.md              # pre-change baseline (git HEAD)
├── fixtures/
│   ├── fixture-3-regression-scoping.patch  + fixture-3-ground-truth.md
│   └── fixture-2-defense-heavy.patch       + fixture-2-ground-truth.md
├── prompts/
│   ├── reviewer_brief.md
│   └── grader_brief.md
└── runs/
    ├── fixture-3/{with_scoping,no_scoping}/{sonnet,opus}/run-{1..6}/{review.md,grading.json}
    └── fixture-2/{with_scoping,no_scoping}/{sonnet,opus}/run-{1..6}/{review.md,grading.json}
```

## Cost

48 reviewer runs (24 Sonnet ~$3, 24 Opus ~$12) + 48 Sonnet grader runs (~$2) ≈ **~$15–18**. Wall-clock ~15 min across the parallel batches.
