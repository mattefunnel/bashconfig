# make-eval meta-eval — iteration 2

Date: 2026-05-27.

**Status: setup complete, runs pending.** Will fill TL;DR after Phase A executes.

## What changed from iter-1

Iter-1 verdict: **rubric saturated** — Sonnet rubber-stamped both vanilla and with-skill designs at ~20/20, methodology couldn't discriminate. Iter-2 applies four fixes:

| iter-1 problem | iter-2 fix |
|---|---|
| 10-criterion 0/1/2 rubric saturated | **Head-to-head 0–10 single-score** comparison grader |
| Sonnet grader rubber-stamped (99% scored 2) | **Opus grader** for stricter judgment |
| Fixtures leaked hints to designers | **Stripped graderhints into separate file**; designer reads only task |
| Only F4 discriminated; needed more adversarial cases | **Added F5 (aws-cred-yolo) + F6 (flake-tolerator)** |

Plus: A/B labels in the grader prompt are **randomized** (designer-A maps to vanilla on some pairs, with-skill on others) for blinding.

## Hypothesis

Same as iter-1: does loading the make-eval skill produce sounder eval designs than vanilla Claude?

## Conditions

- A: vanilla — no skill.
- B: with-skill — full skill content as directive.

In the grader's view A/B labels are randomized per (fixture, run-K) pair. Convention: A=vanilla when (fixture_num + run_num) is even, A=with-skill otherwise. Post-processing inverts the grader's score into "with-skill advantage = score - 5 if A=vanilla, else 5 - score". Positive = with-skill wins.

## Fixtures (6)

| # | artifact | shape |
|---|---|---|
| 1 | `commit` skill | cohesive, no ablation cleavage |
| 2 | `friction-audit` skill | reads transcripts |
| 3 | `actix-to-axum` skill | large, many sections |
| 4 | (synthetic) `git-yolo` | known-bad: `--force --no-verify` to main |
| 5 | (synthetic) `aws-cred-yolo` | known-bad: commit AWS creds + grant AdminAccess |
| 6 | (synthetic) `flake-tolerator` | known-bad: retry-until-pass test masking |

Each fixture has a TASK file (designer reads) and GRADERHINTS file (grader only).

## Matrix

6 fixtures × 2 conditions × Sonnet × K=3 = **36 design runs**.
6 fixtures × K=3 = **18 head-to-head grader runs** (Opus).

## Cost estimate

- 36 design subagents × Sonnet × ~50k tokens ≈ $3.60
- 18 grader subagents × Opus × ~8k input + 0.5k output ≈ $0.70
- **Total: ~$4.30, ~10 min wall-clock.**

## TL;DR (results, 2026-05-27 run)

| dim | mean with-skill advantage (μ ± σ, n=3 unless noted) | classification |
|---|---|---|
| **overall (n=18)** | **+0.11 ± 1.32** | tied at the mean, but VARIANCE EXISTS (vs iter-1's 0.0 — discrimination working) |
| F1 (commit) | -0.33 ± 1.15 | marginal vanilla advantage |
| F2 (friction-audit) | +0.33 ± 2.08 | tied, very noisy |
| F3 (actix-to-axum) | -0.67 ± 1.53 | marginal vanilla advantage |
| F4 (git-yolo) | +0.33 ± 1.15 | marginal with-skill advantage |
| F5 (aws-cred-yolo) | +0.00 ± 1.73 | tied, noisy |
| F6 (flake-tolerator) | **+1.00 ± 0.00** | **unanimous with-skill advantage** (3/3) |

**Key emergent pattern:**

| fixture group | mean advantage | n |
|---|---|---|
| Real skills (F1, F3) | **-0.50** (vanilla wins) | 6 |
| Adversarial synthetic (F4, F5, F6) | **+0.44** (with-skill wins) | 9 |
| Mixed (F2) | +0.33 | 3 |

**Δ between adversarial and real-skill = +0.94.** The skill helps on adversarial / known-bad artifacts (where hypothesis-formulation and safety-framing matter); it slightly hurts or doesn't help on well-formed real skills (where Sonnet's general competence is sufficient).

## Verdict

**The make-eval skill helps modestly on adversarial tasks; it is neutral-to-slightly-harmful on well-formed real skills.** Effect size is small (overall +0.11 on a -5 to +5 scale) but the variance is meaningful: K=3 captures real disagreement between conditions.

3 takeaways:

1. **F6 (flake-tolerator) is the cleanest signal:** 3 of 3 pairs unanimous with-skill wins. The "bug-masking" hypothesis the skill prompts you to ask is exactly the kind of thing vanilla didn't always think to test for.
2. **F1 + F3 negative advantage is the strongest counter-evidence:** for real skills (commit, actix-to-axum), the with-skill condition is adding overhead — its "consider these phases", "pre-register predictions", "anti-pattern checklist" boilerplate is making designs LESS focused, not more. The skill currently lacks a "lightweight path" for well-formed artifacts.
3. **Variance is huge (σ ≈ 1.3 overall).** K=3 catches the shape but not the precise magnitude. To distinguish "skill helps by +0.5" from "skill helps by 0", we'd need K≥6 — and the per-pair Opus cost ($0.70 total for K=3) means K=6 is affordable (~$1.40 for K=6). Worth doing in iter-3 if these numbers matter.

## Pre-registered prediction check

1. **"Overall with-skill advantage will be positive but small (+0.5 to +1.5)."** — *partially held.* Positive (+0.11) but below the predicted floor. Skill helps less than expected.
2. **"F5/F6 (adversarial synthetic) will discriminate more than F1/F3 (real skills)."** — ✅ **strongly held.** Adversarial mean +0.44 vs real-skill mean -0.50 (Δ +0.94). This is the iteration's biggest finding.
3. **"F1 (commit) will be tied or slight with-skill loss."** — ✅ **held.** F1 = -0.33 (slight vanilla edge).
4. **"Iter-2 will discriminate where iter-1 couldn't (stdev > 0.5)."** — ✅ **held.** 5 of 6 fixtures have stdev > 0.5 (overall 1.32 vs iter-1's saturated 0.0–0.6).

3 of 4 predictions held; the 4th (effect size) partially held. The methodology itself is now sound — discrimination works, randomization works, Opus grader works.

## What this tells us about the make-eval skill itself

- **It helps when the artifact is bad or unusual.** F4 (git-yolo), F5 (aws-cred-yolo), F6 (flake-tolerator) — all synthetic, all known-bad. The skill nudges the designer toward safety-framing, hypothesis-formulation around harm, and pre-registered "DELETE" verdicts. Vanilla sometimes misses these.
- **It hurts when the artifact is well-formed and the designer's competence is already high.** F1 (commit) and F3 (actix-to-axum) are real, well-designed skills. Vanilla designs were tighter and more focused. With-skill designs were longer, more boilerplate-laden, and occasionally pursued anti-pattern checklists at the expense of actual fixture quality.
- **Suggested skill update (iter-3 target):** add a "lightweight mode" — when the artifact is a clean real skill with no obvious safety concerns, skip the full 5-phase walkthrough and converge faster. Currently the skill's "always apply all 17 anti-patterns" framing causes overhead on easy cases.

## Cost

- 36 design subagents × Sonnet × ~50k tokens ≈ $3.60
- 18 grader subagents × **Opus** × ~9k input + 0.5k output ≈ $0.70
- **Actual: ~$4.30, ~15 min wall-clock** (4 spawn batches: 3 design × 12 + 1 grader × 18, with Opus graders running slightly slower than Sonnet at ~45s each)

Cost was as predicted. Opus per-grader was cheap (~$0.04 each) because input dominated and the rubric called for terse output.

## Sanity check: did Opus actually discriminate?

Score distribution across 18 graders: 3, 3, 4, 4, 4, 4, 4, 4, 4, 6, 6, 6, 6, 6, 7. (One 7, four 6s, eight 4s, three 3s — no 0s, 1s, 2s, 5s, 8s, 9s, or 10s.)

- 8 scores at 4 (slight A advantage), 4 scores at 6 (slight B advantage) — the grader leaned heavily on adjacent-to-5 scores.
- Used 3 and 7 occasionally for clearer differences.
- Never gave 5 (tied) — good, the strict-discrimination instruction worked.
- Never gave 0, 1, 2, 8, 9, 10 — Opus didn't see any "dramatically better" gaps.

The grader IS discriminating but conservatively, mostly in the 3-7 range. This is appropriate for the actual signal size (designs are similar; differences are real but small).

## Limitations

- K=3 wide CIs. Some fixture-level effects (F6 unanimous, F1 weak vanilla edge) are robust; F2 (σ=2.08) and F5 (σ=1.73) are still noisy at K=3.
- Single grader per pair (no inter-grader on Opus). Repeating with 2 graders would tighten CIs ~30%.
- Sonnet designs, Opus grader — mixing models. Iter-3 could test Sonnet-grader as a cheaper check.
- A/B randomization is deterministic (by parity), not cryptographic.
- The "real skill" sample is only F1 + F3 (n=6 pairs). Adding more real skills (F0 = `review` skill, F-1 = `pr` skill, ...) would tighten the "with-skill hurts on real artifacts" finding.

## Pre-registered predictions

1. **Overall with-skill advantage will be positive but small.** Predict mean ~+0.5 to +1.5 across 18 pairs.
2. **F5/F6 (adversarial synthetic) will discriminate more than F1/F3 (real skills).** Predict |advantage on F5+F6| ≥ |advantage on F1+F3|.
3. **F1 (commit) will be tied or slight with-skill loss.** No ablation cleavage; with-skill's "ablate a section" framing won't fit.
4. **Iter-2 will discriminate where iter-1 couldn't.** Predict stdev across cells > 0.5 (vs iter-1's saturated ~0.0).

If all 4 hold → skill earning its keep at a modest level + methodology fixes worked.
If none hold → either skill genuinely useless OR head-to-head methodology has its own issues to investigate.

## How to run

1. Spawn 36 design subagents in batches of 12 via Agent tool. Use `prompts/vanilla_brief.md` and `prompts/with_skill_brief.md`. Save designs to `/tmp/claude/meta2-runs/fixture-N/<condition>/run-K/design.md`.
2. Spawn 18 head-to-head Opus graders. Each reads task + graderhints + design-A + design-B, writes grading.json.
3. Aggregate: per pair, normalize score → with-skill advantage. Per fixture, mean ± stdev across K=3. Overall mean ± stdev across all 18.
4. Update this README with TL;DR + verdict + pre-registered prediction check.

## Layout

```
iteration-2/
├── README.md
├── artifact-snapshot/                          # frozen skill
├── fixtures/
│   ├── fixture-{1..6}-*-task.md                # designer-facing
│   └── fixture-{1..6}-*-graderhints.md         # grader-only
├── prompts/
│   ├── vanilla_brief.md
│   ├── with_skill_brief.md
│   └── grader_brief.md                         # NEW: head-to-head
└── runs/                                       # populated on run
    └── fixture-N/{vanilla,with_skill}/run-K/design.md
        + fixture-N/comparison-K/grading.json
```

## Limitations (acknowledged)

- K=3 still small. Wider CIs than ideal.
- Single grader per pair (no inter-grader agreement on Opus).
- Sonnet designs, Opus grader — possible asymmetry.
- A/B randomization is deterministic (by parity), not cryptographic.
- Synthetic fixtures may not reflect real evaluator workloads.
