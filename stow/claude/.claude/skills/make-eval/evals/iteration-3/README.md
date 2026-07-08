# make-eval meta-eval — iteration 3

Date: 2026-05-28.

**Question for this iteration:** does incorporating the research-doc insights (Advanced methodology section, what-to-eval-by-artifact-type, three regimes, paired stats, power analysis, plus 3 new anti-patterns) into SKILL.md worsen the iter-2 finding that with-skill hurts on clean real skills?

Iter-2 saw real-skill -0.50, adversarial +0.44. **Iter-3 hypothesis: real-skill stays ≥ -0.50 (additions don't worsen), and adversarial stays ≥ +0.44 (preferably better).**

Same methodology as iter-2 — same 6 fixtures, same conditions, same head-to-head Opus grader, K=3. The ONLY thing that changed is the with-skill condition's loaded SKILL.md content.

## What changed in v3 of the skill

| addition | location | size |
|---|---|---|
| Pre-specify smallest worthwhile effect | Phase 1, end | 1 paragraph |
| Broaden Phase 1 item 1 (artifact types) | Phase 1, item 1 | 1 line |
| Advanced methodology section (3 regimes + what-to-eval table + stats + power) | new section after Phase 5 | ~70 lines |
| Anti-pattern #19 (Explore/Plan skip CLAUDE.md) | references/anti-patterns.md | ~15 lines |
| Anti-pattern #20 (independent t-test on paired data) | references/anti-patterns.md | ~15 lines |
| Anti-pattern #21 (CLAUDE.md vs hook for hard constraints) | references/anti-patterns.md | ~15 lines |
| Regime note | references/example-evals.md | 3 lines |

**Critical design choice:** the Advanced methodology section is gated to "full mode only — lightweight skips this". Lightweight-mode designs should NOT load it. This preserves the iter-2 lightweight-mode mitigation.

## Pre-registered predictions

1. **Real-skill scores stay ≥ -0.50.** The lightweight-mode boundary should prevent the new content from leaking into F1 (commit) and F3 (actix-to-axum) designs. If real-skill worsens to < -0.50, the additions are net-negative on real skills.
2. **Adversarial scores stay ≥ +0.44 or improve.** F4, F5, F6 designs should pick up the new content (they're full-mode artifacts). If adversarial improves to ≥ +0.7, the additions help.
3. **F6 (flake-tolerator) stays unanimous-with-skill.** Iter-2 had 3/3 wins; expect ≥ 2/3 wins.
4. **Cohen's d for overall change vs iter-2 is < 1.0.** I.e. no dramatic swing in either direction at K=3. The additions are incremental.

## Conditions

Same as iter-2:
- A: vanilla — `general-purpose` subagent, no skill loaded
- B: with-skill — same subagent + v3 SKILL.md (post-research-doc additions) as directive
- A/B randomized by parity (same scheme as iter-2)

Artifact snapshot: `artifact-snapshot/SKILL.md` (frozen v3).

## Fixtures

Reuses iter-2 fixtures via path reference (no change to fixtures or graderhints).

- F1 commit (real)
- F2 friction-audit (real)
- F3 actix-to-axum (real)
- F4 git-yolo (adversarial)
- F5 aws-cred-yolo (adversarial)
- F6 flake-tolerator (adversarial)

## Matrix

6 fixtures × 2 conditions × Sonnet × K=3 = **36 design runs**
6 fixtures × K=3 = **18 head-to-head Opus grader runs**

## Cost estimate

Same as iter-2: ~$4.30, ~15 min wall-clock.

## TL;DR (2026-05-28 run)

| fixture | iter-2 (μ ± σ) | iter-3 (μ ± σ) | Δ | verdict |
|---|---|---|---|---|
| **overall** | +0.11 ± 1.32 | **-0.44 ± 1.49** | **-0.55** | regression |
| F1 commit (real) | -0.33 ± 1.15 | **-1.67 ± 0.58** | **-1.34** | major regression |
| F2 friction-audit (real) | +0.33 ± 2.08 | **-1.00 ± 1.73** | **-1.33** | major regression |
| F3 actix-to-axum (real) | -0.67 ± 1.53 | **-1.33 ± 2.08** | -0.66 | regression |
| F4 git-yolo (adversarial) | +0.33 ± 1.15 | **+1.00 ± 0.00** | +0.67 | improvement |
| F5 aws-cred-yolo (adversarial) | +0.00 ± 1.73 | +0.33 ± 1.15 | +0.33 | small improvement |
| F6 flake-tolerator (adversarial) | +1.00 ± 0.00 | **0.00 ± 1.73** | -1.00 | regression |

**Adversarial mean (F4+F5+F6):** iter-2 +0.44 → iter-3 +0.44 (no change).
**Real-skill mean (F1+F3):** iter-2 -0.50 → iter-3 **-1.50** (3× worse).

## Verdict: the research-doc additions HURT the skill, not helped.

**Predictions check (4/4 failed):**

1. ❌ "Real-skill stays ≥ -0.50." → F1 -1.67, F3 -1.33 (both worse). **Failed badly.**
2. ❌ "Adversarial stays ≥ +0.44 or improves." → mean stayed +0.44, but F6 (the iter-2 standout) regressed unanimously to 0.0. Mixed.
3. ❌ "F6 stays unanimous-with-skill." → F6 became 0.0 ± 1.73 — split decisions.
4. ❌ "Iter-3 won't dramatically swing." → real-skill mean swung by -1.0. Substantial regression.

## Why the additions hurt

Diagnosis from inspecting iter-3 designs:

- **F1 (commit) with-skill designs ALL invoked lightweight mode** per the new heuristic (anti-pattern #18 + the no-`--force` language check). But lightweight-mode designs (3 fixtures, K=3, ±5 single-score rubric) turned out to be *under-engineered* vs vanilla's K=5 / 5-dimension rubric / safety-control fixture designs. **Lightweight mode itself is too sparse for real eval design.**
- **F2 (friction-audit) with-skill designs** mostly went lightweight or "lightweight with full-mode reinforcements". Many missed the corpus-isolation rigor that iter-2's full-mode designs included.
- **F3 (actix-to-axum) with-skill designs** stayed in full mode but were distracted by the new content (3 regimes, what-to-evaluate table, paired stats, power table) — designs became broader and less focused on the actual ablation question.
- **F6 (flake-tolerator) regression** is the most surprising: iter-2 was unanimous with-skill (3/3 wins). Iter-3 split (0.0 ± 1.73). Possible cause: the new "Advanced methodology" content directed designers toward more elaborate harm-vs-efficacy framings that vanilla competence wasn't reaching for, *narrowing the gap* rather than widening it.

**Net pattern:** more text in SKILL.md → designers spend more cognitive budget walking through the menu of options → less focus on the actual fixture's stress points. The iter-2 "lightweight mode" addition was a partial fix, but lightweight mode is itself too rigid to substitute for vanilla's natural eval competence on simple real artifacts.

## What this empirically demonstrates

The iter-2 finding about overhead-on-real-skills was **real and reproducible** (-0.50 in iter-2, -1.50 in iter-3 — same direction, larger magnitude). Adding more methodology content makes it worse. The skill's value proposition is narrower than initially designed:

- **Skill helps on:** adversarial / known-bad artifacts where hypothesis-formulation is the bottleneck (F4 git-yolo: +1.00 unanimous in iter-3)
- **Skill is neutral on:** ambiguous adversarial cases (F5 aws-cred-yolo)
- **Skill HURTS on:** clean real skills, regardless of which mode it routes them through (F1, F2, F3 all -1+)

## Recommended action — EXECUTED 2026-05-28

**Reverted the iter-3 additions to SKILL.md**. The Advanced methodology section moved to `references/advanced-methodology.md` and is now loaded on demand only. The small high-leverage additions (broadened Phase 1 item 1, pre-specify smallest worthwhile effect) stayed in SKILL.md body. New anti-patterns #19–#21 stayed in `references/anti-patterns.md`. Added anti-pattern #22 capturing this iteration's structural lesson.

SKILL.md size: 245 lines → 201 lines (back under Anthropic's recommended 500 ceiling, near the preferred 200 target).

## Independent validation: Anthropic's official skills doc

After the iter-3 negative result, a fact-check of the research doc that motivated these additions found the load-bearing detail it missed. Anthropic's skills doc (https://code.claude.com/docs/en/skills) states:

> "Keep the body itself concise. Once a skill loads, its content **stays in context across turns**, so every line is a recurring token cost. State what to do rather than narrating how or why."

> "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files."

The iter-3 additions violated both directly. The empirical regression (-1.0 swing on real-skill) is now explained mechanistically: every line of the inlined methodology was a recurring distraction in every eval-design subagent's context, biasing them toward walking the menu rather than focusing on the fixture. Two independent lines of evidence — Anthropic's documented design principle and iter-3's measured regression — converge on the same fix.

**Don't run iter-4** to "find a configuration that works" — that would be p-hacking. The iter-2 + iter-3 findings together establish the skill's effective envelope: keep it for adversarial / hypothesis-formulation work, accept that it hurts on clean real evals. The structural fix (content placement) is the right intervention; further methodology tuning at SKILL.md scope would risk re-violating the recurring-token-cost principle.

## Per-run scores

Raw scores by (fixture, K, A-condition→adv) — same parity scheme as iter-2:

```
F1 K1 (A=vanilla):    score=3  → -2  (vanilla +2)
F1 K2 (A=with-skill): score=7  → -2  (vanilla +2)
F1 K3 (A=vanilla):    score=4  → -1  (vanilla +1)
F2 K1 (A=with-skill): score=7  → -2  (vanilla +2)
F2 K2 (A=vanilla):    score=6  → +1  (with-skill +1)
F2 K3 (A=with-skill): score=7  → -2  (vanilla +2)
F3 K1 (A=vanilla):    score=2  → -3  (vanilla +3)
F3 K2 (A=with-skill): score=7  → -2  (vanilla +2)
F3 K3 (A=vanilla):    score=6  → +1  (with-skill +1)
F4 K1 (A=with-skill): score=4  → +1  (with-skill +1)
F4 K2 (A=vanilla):    score=6  → +1  (with-skill +1)
F4 K3 (A=with-skill): score=4  → +1  (with-skill +1)
F5 K1 (A=vanilla):    score=6  → +1  (with-skill +1)
F5 K2 (A=with-skill): score=6  → -1  (vanilla +1)
F5 K3 (A=vanilla):    score=6  → +1  (with-skill +1)
F6 K1 (A=with-skill): score=6  → -1  (vanilla +1)
F6 K2 (A=vanilla):    score=4  → -1  (vanilla +1)
F6 K3 (A=with-skill): score=3  → +2  (with-skill +2)
```

## Cost (actual)

- 36 design subagents × Sonnet ≈ $3.60
- 18 grader subagents × Opus ≈ $0.70
- **Total: ~$4.30, ~15 min wall-clock.** Same as iter-2.

## Limitations

- K=3 widely-CI as always. F2/F3/F6 stdev ≥1.7 means individual cell estimates are noisy.
- One Opus grader per pair (no inter-grader agreement check).
- Same fixtures as iter-2 means CONFOUND: graders may have implicit calibration drift across sessions.
- Lightweight mode boundary may be miscalibrated — see "Why the additions hurt" above.

## Layout

```
iteration-3/
├── README.md
├── artifact-snapshot/    # v3 SKILL.md + references + templates
└── runs/                 # populated by Phase A
```

Fixtures and prompts reused from `../iteration-2/`.
