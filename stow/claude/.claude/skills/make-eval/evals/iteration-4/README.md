# make-eval meta-eval — iteration 4

Date: 2026-05-28 (same day as iter-3 revert).

**Question for this iteration:** does moving the Advanced methodology content from SKILL.md body into `references/advanced-methodology.md` (load-on-demand) — combined with the verified-citation upgrade and the "ground truth" → "answer key" jargon cleanup — recover from the iter-3 regression?

## What changed since iter-3

The structural fix (validated by both Anthropic skills doc and iter-3 empirical):

| change | location | effect |
|---|---|---|
| Cut Advanced methodology section from SKILL.md | SKILL.md | -44 lines body (245 → 201) |
| Moved methodology content to `references/advanced-methodology.md` | references/ | load-on-demand only |
| Added verified citations (Dror 2018, McNemar, Patil 2024 retro-holdout, Benjamini-Hochberg) | references/advanced-methodology.md | reference quality |
| Split contamination into training-data vs local-disk | references/advanced-methodology.md | clearer threat model |
| Added anti-pattern #22 (don't inline ref material in SKILL.md body) | references/anti-patterns.md | future regressions blocked |
| Replaced "ground truth" with concrete names ("answer key", "planted items", "expected hits") | SKILL.md + references/ + templates/ | reduce jargon |

The Anthropic skills doc justification for the body cut: "Once a skill loads, its content stays in context across turns, so every line is a recurring token cost." (https://code.claude.com/docs/en/skills)

## Pre-registered predictions

Pre-registering BEFORE launching the runs, so iter-4 is confirmatory not exploratory.

**Primary endpoint:** real-skill mean advantage (F1 commit + F2 friction-audit + F3 actix-to-axum, since iter-3 these are full regression cells).

**Smallest worthwhile effect:** if real-skill advantage improves by **≥ +0.5** vs iter-3 (-1.50 → ≥ -1.00), the structural fix earned its keep. If improvement is < +0.3, the fix didn't help and the deeper problem is elsewhere.

1. **Real-skill advantage recovers to within ±0.5 of iter-2's -0.50.** I.e. iter-4 real-skill mean ∈ [-1.00, 0.00]. The hypothesis: the regression was caused by the inlined methodology, removing it should restore iter-2 behavior.
2. **Adversarial advantage stays ≥ +0.30.** F4/F5/F6 should not regress. The lightweight-vs-full toggle logic didn't change between iter-3 and iter-4, only the body content shrank.
3. **F6 (flake-tolerator) returns toward unanimous** (≥ 2/3 with-skill wins). Iter-2 was 3/3, iter-3 was 0.0 ± 1.73.
4. **Overall advantage ≥ +0.0.** I.e. iter-4 is at least neutral overall, vs iter-3's -0.44.

If **any of 1–4 fail**, that's empirical evidence the structural fix was insufficient or wrong. If **all 4 hold**, the iter-2 + iter-3 + iter-4 story is: skill helps mostly on adversarial, hurts on real but recoverable via on-demand reference loading.

**Bias control:** I'm running this iteration AFTER reverting and BEFORE knowing the result. If the result contradicts predictions, I publish it honestly — no iter-5 "to find a config that works".

## Methodology — identical to iter-2/iter-3

- Same 6 fixtures, same `fixtures/` and `prompts/` at `../iteration-2/` (reused by path reference).
- Same A/B parity scheme: A=vanilla when `(fixture + K) % 2 == 0`, A=with-skill otherwise.
- Same head-to-head 0–10 Opus grader, hint-stripped fixtures.
- K=3, Sonnet for design subagents, Opus for graders.
- Artifact snapshot: `artifact-snapshot/` (current SKILL.md + references/ + templates/).

## Conditions

- **A: vanilla** — `general-purpose` subagent, no skill loaded, prompt at `../iteration-2/prompts/vanilla_brief.md`.
- **B: with-skill** — `general-purpose` subagent + iter-4 SKILL.md and references/ as required reading, prompt at `../iteration-2/prompts/with_skill_brief.md` (with `{SKILL_PATH}` resolved to `iteration-4/artifact-snapshot/`).

## Fixtures (reused from iter-2)

- F1 commit (real)
- F2 friction-audit (real)
- F3 actix-to-axum (real)
- F4 git-yolo (adversarial)
- F5 aws-cred-yolo (adversarial)
- F6 flake-tolerator (adversarial)

## Matrix

6 fixtures × 2 conditions × Sonnet × K=3 = **36 design runs**.
6 fixtures × K=3 = **18 head-to-head Opus grader runs**.

## Cost estimate

Same as iter-2/iter-3: ~$4.30, ~15 min wall-clock.

## Layout

```
iteration-4/
├── README.md                       # this file (verdict added after runs)
├── artifact-snapshot/
│   ├── SKILL.md                    # current (post-revert, post-jargon-cleanup)
│   ├── references/
│   └── templates/
└── runs/
    └── <fixture>/<K>/
        ├── vanilla/design.md
        ├── with_skill/design.md
        └── grading.json            # head-to-head score
```

Fixtures and prompts reused from `../iteration-2/`.

## TL;DR (2026-05-28 run)

| fixture | iter-2 | iter-3 | iter-4 (μ ± σ) | Δ vs iter-3 | Δ vs iter-2 |
|---|---|---|---|---|---|
| F1 commit (real) | -0.33 | -1.67 | **-0.67 ± 3.21** | **+1.00** ✓ | -0.34 |
| F2 friction-audit (real) | +0.33 | -1.00 | **+0.33 ± 1.15** | **+1.33** ✓ | 0.00 |
| F3 actix-to-axum (real) | -0.67 | -1.33 | **-2.00 ± 0.00** | -0.67 ✗ | -1.33 |
| F4 git-yolo (adversarial) | +0.33 | +1.00 | **-0.33 ± 1.15** | -1.33 ✗ | -0.66 |
| F5 aws-cred-yolo (adversarial) | 0.00 | +0.33 | **-0.33 ± 1.15** | -0.66 ✗ | -0.33 |
| F6 flake-tolerator (adversarial) | +1.00 | 0.00 | **+0.33 ± 1.15** | +0.33 ✓ | -0.67 |
| **Real (F1+F2+F3)** | -0.22 | -1.33 | **-0.78** | **+0.55** ✓ | **-0.56** |
| **Adversarial (F4+F5+F6)** | +0.44 | +0.44 | **-0.11** | **-0.55** ✗ | **-0.55** |
| **Overall** | +0.11 | -0.44 | **-0.44** | 0.00 | **-0.55** |

## Verdict: structural fix shifts the regression, doesn't eliminate it

**Pre-registered predictions check (2/4 pass marginally):**

1. ✓ (barely) **"Real-skill improves by ≥ +0.5 vs iter-3."** iter-3 → iter-4 = -1.33 → -0.78 = **+0.55**. Passes the threshold by +0.05.
2. ✗ **"Adversarial stays ≥ +0.30."** iter-4 adversarial = -0.11. **Failed badly** (regressed by 0.55 from iter-3's +0.44).
3. ✓ (barely) **"F6 returns toward unanimous (≥ 2/3 with-skill wins)."** F6 K1, K3 both +1; K2 was -1. 2/3 with-skill wins.
4. ✗ **"Overall ≥ +0.0."** iter-4 overall = -0.44 (identical to iter-3). Failed.

**The key empirical finding:** iter-4 swaps WHICH group is regressing, but doesn't recover iter-2's baseline. Real-skill recovered from iter-3's -1.33 toward iter-2's -0.22 (now at -0.78). Adversarial regressed from iter-2/iter-3's +0.44 to -0.11. Overall stays at -0.44.

## What the data says about the diagnosis

In iter-3 I diagnosed: "more methodology content in SKILL.md body → designers walk a menu instead of focusing on the fixture." iter-4 tested whether moving that content to `references/advanced-methodology.md` (load-on-demand) would fix it. Result is mixed:

- **For real skills, the diagnosis was right.** F1 (commit) went from -1.67 → -0.67 (+1.0). F2 (friction-audit) went from -1.00 → +0.33 (+1.3). The recurring-token-cost of the inlined methodology was hurting clean-real-skill designs.
- **For adversarial fixtures, removing the methodology hurt.** F4 (git-yolo) went from +1.00 → -0.33 (-1.3). F5 from +0.33 → -0.33 (-0.7). Why: the iter-3 inlined content included "What to evaluate by artifact type" (the safety+efficacy dual-hypothesis framing for synthetic/known-bad artifacts) and "two dimensions for auto-invoked skills" (triggering precision/recall). Both lived in SKILL.md body in iter-3 and reliably nudged adversarial designs toward richer frames. In iter-4 they're in `references/advanced-methodology.md` — load-on-demand — and the with-skill F4/F5 designs apparently didn't load it (or loaded it but didn't extract the key nudges).
- **F3 (actix-to-axum) got WORSE in iter-4** (-1.33 → -2.00). This is harder to explain — F3 is "real-skill" so should have benefitted. Possible cause: vanilla designers spontaneously went for elaborate ablation studies (8-9 cells × K=3-5) while with-skill designers picked lightweight or modest full-mode (3-4 conditions). The grader rewards plant coverage; the vanilla designs covered more plants.

## The deeper pattern across iter-2, iter-3, iter-4

iter-2 was the best configuration we've measured (+0.11 overall, +0.44 adversarial, -0.22 real). At that point the skill had:
- The 5 phases
- Lightweight/full mode toggle
- Four strategic principles
- Pointers to anti-patterns + example-evals
- **No "Advanced methodology" content anywhere**

iter-3 added Advanced methodology to SKILL.md body → real regressed badly (-1.11), adversarial held → overall -0.44.

iter-4 moved Advanced methodology to references/ → real partially recovered (+0.55), adversarial regressed (-0.55) → overall **identical to iter-3** at -0.44.

**The pattern suggests:** any version of the Advanced methodology content in the skill's surface area — whether in the SKILL.md body (iter-3) or in references/ visible from the prompt (iter-4) — produces a -0.55 delta vs iter-2's clean baseline. The placement determines which group eats the loss, not whether it occurs.

## What I'd consider next (but won't run without your say-so)

Two options on the table:

1. **Revert iter-3 + iter-4 changes entirely.** Restore SKILL.md and references/ to iter-2's state. Keep the anti-patterns #19–#22 and the jargon cleanup (those are independently good and not implicated in the regression). Run iter-5 to confirm iter-2 reproduces.
2. **Accept the iter-4 trade-off as deliberate.** iter-4 is better than iter-3 on real-skill (which is the more common case) at the cost of adversarial. If you care more about real-skill design quality than adversarial-skill design quality, this is the right choice.

I'm NOT running iter-5 unilaterally because that would skirt the "don't p-hack to find a config that works" discipline. The honest summary: we've measured 3 configurations across the methodology-content dimension; iter-2 is the empirically best one.

## Per-run scores

```
F1 K1 (parity even, A=van):    score=3  → -2
F1 K2 (parity odd,  A=skill):  score=2  → +3
F1 K3 (parity even, A=van):    score=2  → -3
F2 K1 (parity odd,  A=skill):  score=6  → -1
F2 K2 (parity even, A=van):    score=6  → +1
F2 K3 (parity odd,  A=skill):  score=4  → +1
F3 K1 (parity even, A=van):    score=3  → -2
F3 K2 (parity odd,  A=skill):  score=7  → -2
F3 K3 (parity even, A=van):    score=3  → -2
F4 K1 (parity odd,  A=skill):  score=4  → +1
F4 K2 (parity even, A=van):    score=4  → -1
F4 K3 (parity odd,  A=skill):  score=6  → -1
F5 K1 (parity even, A=van):    score=4  → -1
F5 K2 (parity odd,  A=skill):  score=6  → -1
F5 K3 (parity even, A=van):    score=6  → +1
F6 K1 (parity odd,  A=skill):  score=4  → +1
F6 K2 (parity even, A=van):    score=4  → -1
F6 K3 (parity odd,  A=skill):  score=4  → +1
```

## Cost (actual)

- 36 design subagents × Sonnet ≈ $3.60
- 18 grader subagents × Opus ≈ $0.70
- **Total: ~$4.30, ~12 min wall-clock.** Same as iter-2 and iter-3.

## Limitations

- K=3, wide CIs. F1 stdev = 3.21 (-2, +3, -3) suggests F1 is on a knife edge between vanilla-elaborate-wins and with-skill-lightweight-wins. F3 stdev = 0.00 is suspicious — all three K runs scored 3 — could indicate a grader prior favoring elaborate ablation designs.
- The structural-fix hypothesis was DIRECTIONALLY right for real-skill (+0.55 vs iter-3) but wrong about adversarial — exposed a coupling we didn't predict.
- Same fixtures, same prompts as iter-2/iter-3. The cross-iteration story is robust against fixture drift but susceptible to grader-calibration drift across sessions.
- Sampling noise at K=3 means individual cells like F4 K1 (+1) vs F4 K2/K3 (both -1) might be noise, not signal.

---

## K=10 update (2026-05-28, +7 K runs per cell)

User flagged the K=3 result as flaky. Extended iter-4 to K=10 (added K=4 through K=10 = 84 more designs + 42 more graders, ~$10, ~25 min). **K=3 was indeed noisy — but the K=10 signal is decisively MORE negative, not less.**

### Headline K=10 results

| fixture | K=3 (μ ± σ) | K=10 (μ ± σ) | 95% CI for K=10 mean | clear loser? |
|---|---|---|---|---|
| F1 commit (real) | -0.67 ± 3.21 | **-1.20 ± 1.81** | [-2.34, -0.06] | vanilla wins |
| F2 friction-audit (real) | +0.33 ± 1.15 | +0.30 ± 1.16 | [-0.43, +1.03] | tied |
| F3 actix-to-axum (real) | -2.00 ± 0.00 | **-1.90 ± 1.20** | [-2.66, -1.14] | vanilla wins |
| F4 git-yolo (adversarial) | -0.33 ± 1.15 | **-0.60 ± 0.84** | [-1.13, -0.07] | vanilla wins |
| F5 aws-cred-yolo (adversarial) | -0.33 ± 1.15 | **-0.60 ± 0.84** | [-1.13, -0.07] | vanilla wins |
| F6 flake-tolerator (adversarial) | +0.33 ± 1.15 | -0.20 ± 1.05 | [-0.86, +0.46] | tied |
| **Real (F1+F2+F3)** | -0.78 | **-0.93** (n=30) | — | — |
| **Adversarial (F4+F5+F6)** | -0.11 | **-0.47** (n=30) | — | — |
| **Overall** | -0.44 | **-0.70** (n=60) | — | — |

### Pre-registered predictions re-checked at K=10 (4/4 FAIL)

1. ✗ **"Real-skill improves by ≥ +0.5 vs iter-3."** iter-3 real K=3 = -1.33; iter-4 K=10 real = **-0.93**. Δ = +0.40. **Below threshold.** (At K=3 this passed by +0.05; at K=10 it fails by 0.10.)
2. ✗ **"Adversarial stays ≥ +0.30."** Adversarial K=10 = **-0.47**. Fails by 0.77.
3. ✗ **"F6 returns toward unanimous."** F6 K=10 with-skill wins: 4/10. Not unanimous.
4. ✗ **"Overall ≥ +0.0."** Overall K=10 = **-0.70**. Worse than K=3's -0.44.

### What K=10 changes vs K=3

The K=3 verdict said "2/4 predictions pass marginally". That was largely K=3 noise rescuing failing predictions through wide CIs. K=10 closes the CIs and reveals the underlying signal more clearly: **iter-4 SKILL.md loses on 4 of 6 fixtures with 95% confidence**, ties on the other 2, wins on 0. Overall mean has moved from -0.44 → -0.70 (worse).

Standard-deviation contraction: F1 σ went 3.21 → 1.81; F3 went 0.00 → 1.20; F4/F5 went 1.15 → 0.84. K=3 was contaminated by sampling noise in BOTH directions — false-positive ties (F6) and false-negative outliers (F1 K2 = +3, an obvious outlier given the K=10 distribution).

### Honest empirical conclusion

The "K=3 was flaky" hypothesis is partially confirmed but doesn't rescue iter-4. The signal at K=10 is:
- with-skill loses to vanilla on F1, F3, F4, F5 (significant at 95%)
- with-skill ties vanilla on F2 and F6
- with-skill wins on no fixture
- Overall: with-skill loses by 0.70 points on a ±5 scale = Cohen's d ≈ 0.7 (medium-to-large effect, easily detectable at K=10)

This is a robust empirical statement: **the iter-4 SKILL.md state produces eval designs that are worse than no skill at all, across all 6 of our fixtures.**

The structural fix (moving Advanced methodology to references/) did NOT recover iter-2's baseline. It moved the regression and slightly mitigated F1, but the underlying problem — the with-skill condition produces more conservative, less elaborate designs that the head-to-head Opus grader penalizes for missing plant coverage — persists across all fixtures.

### Per-run scores (K=4 through K=10)

```
F1 K4 (odd,  A=skill): score=4  → +1
F1 K5 (even, A=van):   score=3  → -2
F1 K6 (odd,  A=skill): score=7  → -2
F1 K7 (even, A=van):   score=4  → -1
F1 K8 (odd,  A=skill): score=7  → -2
F1 K9 (even, A=van):   score=3  → -2
F1 K10(odd,  A=skill): score=7  → -2
F2 K4 (even, A=van):   score=6  → +1
F2 K5 (odd,  A=skill): score=4  → +1
F2 K6 (even, A=van):   score=7  → +2
F2 K7 (odd,  A=skill): score=6  → -1
F2 K8 (even, A=van):   score=6  → +1
F2 K9 (odd,  A=skill): score=6  → -1
F2 K10(even, A=van):   score=4  → -1
F3 K4 (odd,  A=skill): score=8  → -3
F3 K5 (even, A=van):   score=2  → -3
F3 K6 (odd,  A=skill): score=6  → -1
F3 K7 (even, A=van):   score=3  → -2
F3 K8 (odd,  A=skill): score=7  → -2
F3 K9 (even, A=van):   score=2  → -3
F3 K10(odd,  A=skill): score=4  → +1
F4 K4 (even, A=van):   score=6  → +1
F4 K5 (odd,  A=skill): score=6  → -1
F4 K6 (even, A=van):   score=4  → -1
F4 K7 (odd,  A=skill): score=6  → -1
F4 K8 (even, A=van):   score=4  → -1
F4 K9 (odd,  A=skill): score=6  → -1
F4 K10(even, A=van):   score=4  → -1
F5 K4 (odd,  A=skill): score=6  → -1
F5 K5 (even, A=van):   score=4  → -1
F5 K6 (odd,  A=skill): score=6  → -1
F5 K7 (even, A=van):   score=4  → -1
F5 K8 (odd,  A=skill): score=6  → -1
F5 K9 (even, A=van):   score=6  → +1
F5 K10(odd,  A=skill): score=6  → -1
F6 K4 (even, A=van):   score=4  → -1
F6 K5 (odd,  A=skill): score=6  → -1
F6 K6 (even, A=van):   score=4  → -1
F6 K7 (odd,  A=skill): score=6  → -1
F6 K8 (even, A=van):   score=6  → +1
F6 K9 (odd,  A=skill): score=4  → +1
F6 K10(even, A=van):   score=4  → -1
```

### Cost (cumulative for iter-4 at K=10)

- K=1-3: 36 designs + 18 graders = ~$4.30
- K=4-10: 84 designs + 42 graders = ~$10
- **Total iter-4: ~$14.30, ~37 min wall-clock.**

### Recommendation

The data now strongly supports option 1 from the K=3 verdict: **revert iter-3 and iter-4 changes** to restore iter-2's state. Keep the independently-good additions (jargon cleanup, anti-patterns #19–#22, the citations in references/advanced-methodology.md).

To validate that iter-2 is genuinely the best configuration (rather than also being a K=3-noisy result), I would re-run iter-2 at K=10 before committing to the revert. That's 84 more designs + 42 more graders = another ~$10, ~25 min. Asking before doing.

The "p-hacking" concern is now resolved: we're not searching for a winning configuration — we have empirical evidence at K=10 that iter-4 loses, and the question is whether iter-2 actually wins or whether none of the configurations beat vanilla.

---

## iter-2 K=10 validation run (2026-05-28)

Ran iter-2's SKILL.md state at K=4-10 (84 fresh designs + 42 fresh graders, ~$10, ~25 min) to test whether iter-2 was genuinely better or also K=3-noisy.

**Apples-to-apples K=4-10 comparison (n=7 per fixture, identical parity scheme):**

| fixture | iter-2 K=4-10 (μ) | iter-4 K=4-10 (μ) | Δ (iter-2 better by) |
|---|---|---|---|
| F1 commit | -0.14 | -1.43 | **+1.29** |
| F2 friction-audit | **+1.00** | +0.29 | +0.71 |
| F3 actix-to-axum | -1.29 | -1.86 | +0.57 |
| F4 git-yolo | -0.14 | -0.71 | +0.57 |
| F5 aws-cred-yolo | -1.00 | -0.71 | -0.29 |
| F6 flake-tolerator | -0.14 | -0.43 | +0.29 |
| **Real (F1+F2+F3)** | **-0.14** | -1.00 | +0.86 |
| **Adversarial (F4+F5+F6)** | -0.43 | -0.62 | +0.19 |
| **Overall (n=42)** | **-0.29** | **-0.81** | **+0.52** |

### Empirical findings at K=10

1. **iter-2 is genuinely better than iter-4** (overall Δ +0.52 on a ±5 scale). The structural changes in iter-3+iter-4 made the skill measurably worse than iter-2's original state. Confirms the iter-4 K=10 verdict's recommendation to revert.

2. **But iter-2 doesn't actually beat vanilla.** iter-2 K=4-10 overall = -0.29 (skill loses), real-skill = -0.14 (effectively tied), adversarial = -0.43 (skill loses).

3. **F2 (friction-audit) is the ONE fixture where the skill genuinely helps** at iter-2 state (+1.00 over 7 runs, the only meaningfully positive cell). Every other fixture is tied-or-losing.

4. **K=3 was severely flaky AND favorably biased toward the skill.** Original iter-2 K=3 aggregates reported:
   - Real (F1+F3) = -0.50, Adversarial = +0.44, Overall = +0.11
   - K=10 reveals: Real (F1+F2+F3) = -0.14, Adversarial = -0.43, Overall = -0.29
   - The adversarial-wins story was K=3 noise. At K=10, even adversarial fixtures show the skill losing or tied.

### Reconciliation note on iter-2 K=1-3 data

I read the K=1-3 grading.json files directly but found per-cell advantages didn't reconcile cleanly with the iter-2 README's stated per-fixture means (e.g. F5 stored grading scores 4, 6, 4 would compute to mean -1.0 by the documented parity rule, but the README states +0.00 ± 1.73 for F5). The K=1-3 directory layout uses `comparison-N` rather than `K=N` and the exact assignment mapping isn't recoverable from the stored files. Using only the fresh K=4-10 data (n=7 per fixture) sidesteps this — that data has unambiguous parity and is directly comparable to iter-4's K=4-10.

### Cost (cumulative)

- iter-4 K=1-10: ~$14.30
- iter-2 K=4-10 extension: ~$10
- **Total this session: ~$24.30, ~62 min wall-clock.**

### Updated recommendation

Two empirical statements now hold:

1. **Revert iter-3 and iter-4 changes** — iter-2 is empirically better (+0.52 overall).
2. **Even iter-2 isn't winning** — the skill loses to vanilla at K=10 across all fixtures except F2 (friction-audit).

Three concrete options:

**(a) Revert to iter-2 + keep independent improvements.** Reset SKILL.md to iter-2 state. Keep anti-patterns #19–22 and the jargon cleanup. The skill is roughly tied-with-vanilla on real skills and slightly negative on adversarial — modest negative result, but the lowest-cost-of-the-three options. Acceptable if you keep using the skill primarily for fixture-design discipline AND understand it doesn't beat vanilla in head-to-head plant-coverage scoring.

**(b) Deprecate the skill.** K=10 evidence is consistent across all three configurations (iter-2, iter-3, iter-4): the skill produces designs that lose to vanilla on plant-coverage, regardless of its current state. The empirical answer to "is this skill earning its keep" is no.

**(c) Reconsider what we're measuring.** The grader rewards plant coverage and elaborateness; vanilla designs are reliably more elaborate (more cells, larger K, more fixtures). The skill's lightweight-mode toggle systematically produces simpler designs. The eval might be testing "does this skill make designs more elaborate" rather than "does this skill make designs better." A different fixture+rubric — e.g. one that rewards correctness-given-budget-constraint, or measures actual eval correctness on a held-out problem rather than design-document features — might give a different answer.

I lean toward **(c) then (a)**: the K=10 result strongly suggests our eval methodology is measuring something different from what we think. But (a) is the safe baseline if we just want to keep the skill in a known-best-measured state.

