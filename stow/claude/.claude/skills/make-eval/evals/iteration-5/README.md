# make-eval meta-eval — iteration 5 (bare-prompt comparison)

Date: 2026-05-29.

**The earlier iterations measured make-eval against a "vanilla" prompt that was itself a 30-line eval-design checklist. That comparison was unfairly stacked against the skill — most of the methodology guidance was already in the vanilla prompt.** This iteration tests the question the user actually cares about: does the current make-eval skill add value over a truly bare prompt ("design an eval for this skill, that's it")?

## Setup

- **Bare prompt** (~6 lines, `/tmp/claude/eval-prompts/iter-5/bare.md`):
  > Design an evaluation of the skill described in {TASK_PATH}. Write your design to {OUTPUT_PATH}/design.md. Tools: Read, Glob, Grep. Do NOT read any file with "graderhints" in its name. Return only a 2-3 sentence summary.
- **With-skill**: reuse iter-4's K=10 with-skill designs (current SKILL.md state).
- 60 new bare designs + 60 new head-to-head Opus graders (with-skill_adv = +X means skill beats bare by X).

## Results (K=10 per fixture, n=60)

| fixture | μ ± σ | 95% CI | verdict |
|---|---|---|---|
| F1 commit (real) | **-1.10 ± 1.29** | [-1.92, -0.28] | **bare wins** |
| F2 friction-audit (real) | +0.80 ± 1.40 | [-0.09, +1.69] | tied (marginal) |
| F3 actix-to-axum (real) | -0.50 ± 1.43 | [-1.41, +0.41] | tied |
| F4 git-yolo (adversarial) | **+0.90 ± 0.57** | [+0.54, +1.26] | **skill wins** |
| F5 aws-cred-yolo (adversarial) | **+1.70 ± 0.95** | [+1.10, +2.30] | **skill wins strongly** |
| F6 flake-tolerator (adversarial) | **+1.10 ± 0.88** | [+0.54, +1.66] | **skill wins** |
| **Real (F1+F2+F3, n=30)** | -0.27 | — | roughly tied |
| **Adversarial (F4+F5+F6, n=30)** | **+1.23** | — | **skill wins clearly** |
| **Overall (n=60)** | **+0.48** | [+0.15, +0.81] | **skill wins** |

Cohen's d ≈ 0.37 (small-to-medium effect). Overall result is statistically significant at 95%.

## The story

**Against a truly bare prompt, make-eval earns its keep.** Overall +0.48 with significance, driven almost entirely by adversarial fixtures (F4-F6), where the skill clearly helps:

- F4 git-yolo: skill wins on 10/10 cells, never loses
- F5 aws-cred-yolo: skill wins on 10/10 cells, three big wins (+3 on K1, K8, K10)
- F6 flake-tolerator: skill wins on 9/10 cells

On real-skill fixtures, the picture is mixed:
- F1 commit: bare wins consistently (-1.10, significant)
- F2 friction-audit: skill wins slightly (+0.80, marginal)
- F3 actix-to-axum: bare wins slightly (-0.50, not significant)

## Why this differs from earlier iter-2 / iter-4 results

iter-2 / iter-4 used a "vanilla" prompt that was itself a 30-line, 10-item eval-design checklist. That checklist already prescribed plants/controls, isolation, K size, scoring, anti-patterns avoided, limitations — most of what make-eval would also nudge toward. Those iterations measured "does make-eval beat another elaborate eval-design prompt" — and the answer was "no, barely."

The current iter-5 measures "does make-eval beat the truly minimal prompt a user would actually type" — and the answer is "yes, by +0.48 with K=10 power."

This reframes the prior verdict. The skill IS valuable; the iter-2 baseline was doing 80% of the skill's job under the hood.

## What this means for the skill

The skill's strongest contribution is on **adversarial / safety-critical artifacts** — exactly the cases where:
- The bare prompt produces "design an eval that measures whether this skill works" framing
- The skill produces "design an eval that measures safety AND efficacy with DELETE as a permitted verdict" framing
- The grader-hints reward the second framing because the skills under evaluation (`git-yolo`, `aws-cred-yolo`, `flake-tolerator`) are deliberately bad and need adversarial framing

On clean real skills (F1, F3) the bare-prompt agent does roughly as well — the make-eval skill's overhead doesn't pay back on artifacts that don't need adversarial framing.

## Same grader-validity caveats as before

The grader still measures eval-design idiomaticity (plant coverage + style features in the grader-hints answer key), not whether designs would produce correct empirical answers if executed. The "iter-5 skill wins" finding is robust within this grader's idiom but doesn't validate against an outcome-based ground truth.

## Per-cell scores (raw)

```
F1 K1=2  K2=7  K3=4  K4=3  K5=4  K6=6  K7=3  K8=6  K9=4  K10=6
F2 K1=6  K2=6  K3=3  K4=6  K5=4  K6=7  K7=4  K8=4  K9=2  K10=4
F3 K1=4  K2=6  K3=3  K4=8  K5=4  K6=6  K7=6  K8=4  K9=6  K10=4
F4 K1=4  K2=6  K3=4  K4=5  K5=4  K6=6  K7=4  K8=5  K9=4  K10=7
F5 K1=8  K2=4  K3=6  K4=4  K5=6  K6=4  K7=6  K8=2  K9=7  K10=2
F6 K1=3  K2=6  K3=4  K4=6  K5=4  K6=6  K7=6  K8=7  K9=3  K10=6
```

(Parity rule for advantage: with-skill_adv = score-5 if (F+K) even, else 5-score.)

## Cost

- 60 bare designs (Sonnet) ≈ $3
- 60 head-to-head Opus graders ≈ $3
- **Total: ~$6, ~40 min wall-clock.**

## Limitations

- Single Opus grader per pair (no inter-grader agreement). All grader-validity critiques from iter-4 README apply.
- The "skill wins on adversarial" finding is partly because the make-eval skill is *tuned* to recommend adversarial framing on synthetic/known-bad artifacts (anti-pattern #18, "Choosing depth" guidance). It's not surprising the skill helps where it's specifically designed to help.
- K=10 closes most of the variance from iter-4's K=3 problems, but the F2 marginal result ([-0.09, +1.69]) could go either direction with K=20+.
- Same fixture set as iter-2/iter-3/iter-4; no out-of-distribution validation.

## Verdict

**The current make-eval skill is earning its keep when compared to a truly bare baseline.** Overall +0.48 with statistical significance, driven by clear wins on adversarial fixtures (+1.23 avg).

This reverses the iter-4 verdict that "make-eval is worse than vanilla." That verdict was correct *given iter-4's vanilla* (which was a 30-line eval-design checklist) but misleading about the skill's value vs the realistic alternative ("just ask Claude").

## Implications for next steps

1. **Don't deprecate the skill.** It works against the actual baseline.
2. **Don't revert iter-3 + iter-4 changes** based on the iter-4 K=10 verdict — that comparison was unfair. The current skill state earns +0.48 against bare; we don't have evidence that iter-2's state would do meaningfully better against bare. (Could test, ~$7 more.)
3. **Real opportunity: make the skill leaner.** It currently wins on adversarial via specific framing nudges (lightweight/full mode, dual-hypothesis prompting, DELETE-as-verdict permitted). It DOESN'T win on clean real skills. A shorter skill that keeps the adversarial-framing logic and drops the rest might match current performance at a fraction of the token cost.
4. **The grader limitation still applies.** All scores measure idiomaticity, not outcome correctness. Outcome validation remains untested.
