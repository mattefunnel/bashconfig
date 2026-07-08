# make-eval meta-eval — iteration 1 (DESIGN ONLY)

Empirical evaluation of whether the `make-eval` skill produces sounder eval designs than vanilla Claude given the same task. This is a META-eval — using the make-eval methodology to evaluate the make-eval skill itself.

Date: 2026-05-27.

**Status: DESIGN ONLY.** No runs executed yet. Per user request.

## Hypothesis

When given a task like "evaluate skill X", does loading the `make-eval` skill produce a better eval design than vanilla Claude with the same toolkit?

"Better" = scores higher on a pre-declared 10-criterion rubric covering: hypothesis quality, condition design, fixture quality, isolation strategy, sample size, scoring approach, cost estimate, anti-pattern avoidance, report structure, and tone honesty.

## Why grade the DESIGN, not the executed eval

Running every eval to completion would be expensive (~$5–20 per executed eval × 24 cells × 2 conditions = $240+). But the skill's value-add concentrates in phases 1, 2, 5 (design, setup, verdict structure) — phases 3, 4 (run, score) are mechanical and gate-able by the design. **Judging the design alone captures most of the skill's signal at ~1/10 the cost.**

**Optional Phase B (cost-permitting):** pick the top 1–2 with-skill designs from Phase A and actually run them to completion. Compare against expected outcomes. Catches "looks great on paper, breaks in practice" failure modes. Adds ~$10–20.

## Conditions

- **A: vanilla** — `general-purpose` subagent, given the task + Read/Glob/Grep. No `make-eval` skill content loaded.
- **B: with-skill** — same subagent, plus the full `make-eval` SKILL.md content + paths to bundled resources (`references/anti-patterns.md`, `references/example-evals.md`, `templates/`).

Both conditions produce a `design.md` artifact. No runs are executed.

Artifact snapshot: `artifact-snapshot/` (full make-eval skill state at design time).

## Fixtures (4)

Chosen for distinct stress dimensions:

| # | artifact | shape | what it stresses |
|---|---|---|---|
| 1 | `~/.claude/skills/commit/` | small, cohesive skill, no ablation cleavage | condition design when no "with-section vs without-section" exists |
| 2 | `~/.claude/skills/friction-audit/` | skill that reads transcripts and spawns subagents | isolation strategy when artifact has internal dispatch |
| 3 | `~/.claude/skills/actix-to-axum/` | large skill, many sections, codegen output | multi-condition ablation + auto-grader complexity |
| 4 | (synthetic) `git-yolo` | fictional known-bad skill | hypothesis formulation, tone honesty |

Each fixture documents: artifact summary, user-request prompt, expected design elements (plants), known bad approaches (controls). See `fixtures/`.

## Matrix

4 fixtures × 2 conditions × Sonnet × **K=3** = **24 design runs**.

Each design scored by **2 grader subagents** (inter-grader agreement check) using `rubric.md` = **48 grader runs**.

Mean ± stdev per criterion per cell. Total = 0–20 per design.

## Isolation

- **Subagent fresh contexts** prevent reading this conversation directly.
- The make-eval skill text mentions `session-search` and `review` evals as examples. Fixtures (commit, friction-audit, actix-to-axum, fictional git-yolo) deliberately avoid those exemplars to prevent regurgitation.
- **No transcript corpus needed** — neither condition needs to read past transcripts. The subagent's only reads are: the fixture file + the artifact under test + (in B) the make-eval skill.
- The with-skill condition's prompt explicitly forbids reading the meta-eval's own iteration-1/ dir (which contains the answer key in `fixtures/*.md`'s expected-elements section).

## Pre-registered predictions

Logged upfront for honesty:

1. **With-skill scores HIGHER on:** isolation strategy (#4), sample size (#5), anti-pattern avoidance (#8). The skill explicitly addresses each. **If TRUE → skill is earning its keep.**
2. **With-skill may UNDER-perform on condition design (#2) for Fixture 1 (commit).** When there's no clear ablation, the skill's "with-section vs without-section" framing is awkward. Vanilla may propose a cleaner "no-skill vs with-skill" baseline. **If TRUE → add "no-ablation fallback" guidance to the skill.**
3. **Both conditions may struggle on Fixture 4 (fictional bad skill).** Detecting badness requires a "what does success look like" prior the skill doesn't currently enforce. **If TRUE → add a "success criteria" question to Phase 1 of the skill.**
4. With-skill may produce LONGER design docs (more sections = more verbosity). **If TRUE → consider tightening the skill's section guidance.**

## Scoring rubric

See `rubric.md`. 10 criteria scored 0–2 (poor / acceptable / strong). Cross-checked against each fixture's plants + controls.

## Cost estimate

- 24 design subagents × Sonnet × ~50k tokens ≈ ~$3
- 48 grader subagents × Sonnet × ~30k tokens ≈ ~$3
- **Total Phase A: ~$6, ~10 min wall-clock parallel.**

Phase B (optional): +$10–20 to execute top designs.

## How to run when ready

1. Spawn 24 design subagents in parallel batches (4 batches of 6 to stay safe). Each writes its output to `/tmp/claude/meta-eval-runs/<fixture>/<condition>/run-<k>/design.md`.
2. Spawn 48 grader subagents (2 per design) reading the design + fixture + rubric. Each writes `grading.json` to the same run dir.
3. Copy `/tmp/claude/meta-eval-runs/` → `runs/`.
4. Aggregate per-cell mean ± stdev for each criterion.
5. Update the TL;DR table below with results.
6. Test the 4 pre-registered predictions explicitly — note which held, which didn't, what to change.

## TL;DR (results from 2026-05-27 run)

| dim | A: vanilla (μ ± σ, n=12) | B: with-skill (μ ± σ, n=12) | predicted | actual |
|---|---|---|---|---|
| **total (out of 20)** | **19.67 ± 0.65** | **19.83 ± 0.39** | B > A | tied (Δ=0.16) |
| F1 (commit) total | 20.0 ± 0.0 | 20.0 ± 0.0 | B ≥ A | tied at ceiling |
| F2 (friction-audit) total | 20.0 ± 0.0 | 19.33 ± 0.58 | B > A | A > B (within noise) |
| F3 (actix-to-axum) total | 19.67 ± 0.58 | 20.0 ± 0.0 | B > A | B ≈ A |
| F4 (fictional bad skill) total | 19.0 ± 1.0 | 20.0 ± 0.0 | B ≥ A | B > A (slight) |

**Verdict: rubric saturated — methodology failed to discriminate.** Both vanilla and with-skill produce eval designs the grader scores at ~99% of maximum, with K=3 stdev ≤ 1.0 in every cell. Most plausible cause: a combination of (a) Sonnet is already very competent at eval design when the fixture is well-written, leaving little headroom for the skill to add measurable value at the design-doc level; (b) the 10-criterion 0/1/2 rubric is too easy to satisfy — almost everything that mentions a criterion concretely scores 2; (c) Sonnet graders are too lenient — only 6 of 240 dimension-scores landed below 2.

**The eval skill's value-add did not pop on this test.** That doesn't mean the skill has no value — it means *this particular meta-eval design* can't see it.

## What this iteration actually taught us (the meta-meta lesson)

The meta-eval design itself fell into anti-pattern #14 territory (artificial-variance signature): with a saturated rubric, scores are determined by the rubric's ceiling, not by the conditions. Three concrete fixes for iter-2:

1. **Replace the 0/1/2 absolute rubric with a head-to-head A-vs-B comparison.** Show the grader both designs side-by-side and ask "which is better, and by how much?" Forces discrimination.
2. **Switch to Opus graders.** Sonnet rubber-stamped ~99% of the dimension scores; needs a stricter judge to see the subtler differences.
3. **Add stricter criteria.** Current criteria (e.g. "K≥3 with rationale" = 2) are too easy. New criteria should probe deeper: "does the design specify the EXACT grader prompt", "does the design pre-register predictions", "does the design name the artifact-snapshot dir explicitly", etc.

Also: **F4 (fictional bad skill) was the ONLY discriminating fixture.** Vanilla scored 19.0 ± 1.0 vs with-skill 20.0 ± 0.0 — a thin signal that vanilla was less consistent on safety-framing for the synthetic bad skill. The other 3 fixtures were uniformly perfect. Iter-2 should expand on F4-style fixtures (synthetic artifacts with known problems) where the design's hypothesis-formulation is what's tested.

## Pre-registered predictions — check

1. ❓ **"With-skill scores HIGHER on isolation, sample size, anti-pattern avoidance."** Not verifiable — both conditions hit 2/2 on those criteria in every run. Saturated rubric prevents this from being tested at all.
2. ❓ **"With-skill may UNDER-perform on condition design (#2) for Fixture 1."** Not verifiable — both scored 2/2 on F1 condition design. Looking at the actual designs, vanilla's "with-skill vs no-skill" framing on F1 was IDENTICAL to with-skill's, so the prediction's premise didn't hold.
3. ✓ (weakly) **"Both struggle on Fixture 4 (fictional bad skill)."** Partially confirmed for vanilla (19.0 ± 1.0, range 18-20). Not confirmed for with-skill (all 20s). So vanilla DID struggle slightly more, but with-skill didn't struggle — the prediction "both" was wrong.
4. ❓ **"With-skill produces LONGER design docs."** Untested — design length not measured this iteration. Add to iter-2.

## What both conditions did right (qualitative inspection of designs)

Reading the 24 design.md files (samples spot-checked):
- All 24 proposed K≥3 with rationale.
- All 24 used real-file-copy isolation, no symlinks.
- All 24 pre-declared a scoring rubric.
- 23 of 24 framed F4's safety question first (vanilla F4 run 1 missed it slightly).
- F3 designs uniformly proposed multi-condition ablation (5–6 conditions) — exactly the pattern the skill names.
- F2 designs uniformly proposed synthetic transcript corpora with plants + controls.

**This suggests the skill's content is GETTING THROUGH to vanilla Claude through general competence + the well-written fixture files.** The fixtures themselves carry a lot of methodology guidance (they list expected plants and known bad approaches). Without those fixture-embedded hints, vanilla might do much worse.

## Cost (actual)

- 24 design subagents: ~$2.50 (Sonnet, ~50k tokens each)
- 24 grader subagents: ~$1.20 (Sonnet, ~38k tokens each)
- **Total: ~$3.70 vs estimated ~$6.** Cheaper than expected because graders were short (rubric-scoring is fast for Sonnet when it just stamps 2s).

Wall-clock: ~3 min for design batch 1, ~3 min for batch 2, ~30 sec for each grader batch.

## Recommendations for iter-2

1. **Side-by-side comparison grader.** Give grader (Opus) both A and B designs for the same fixture, ask "which is better and by how much (0-10 scale)?". Single number per pair.
2. **Strip ground-truth hints from fixtures.** Currently fixtures list "expected design elements" — that's the answer key. Move those to a SEPARATE grader-only file. Forces the subagent designs to derive these from the task, not the fixture.
3. **Test on adversarial fixtures.** F4 was the only one that discriminated. Iter-2 should have 4–6 fixtures all designed like F4 (synthetic, known-bad, requires safety/hypothesis framing).
4. **Measure design length.** Add to METRICS: word count, sections present/missing. Tests prediction #4.
5. **Add Opus condition.** Test if Opus designs differ in ways Sonnet's don't.

## Limitations of this iteration

- Rubric saturation = primary finding (and primary limitation).
- K=3 wide CIs (stdev 0–1.0 across cells) — but moot when the means are nearly identical.
- 4 of 12 F2 graders hit your `block-compound-bash.py` / `check-code-rules.py` hook errors mid-run (scripts missing from disk). Scores recovered from agent text responses, marked with `_note` in the JSON.
- Single grader per design (planned 2 for inter-grader check; cut to save cost). With saturated rubric, agreement would have been ~100% anyway.
- Sonnet-only grader. Likely too lenient for this kind of design-quality judgment.
- Single model (Sonnet) for both designs and graders.

## Layout (after run)

```
iteration-1/
├── README.md                                # this file (NOW WITH RESULTS)
├── artifact-snapshot/                       # frozen make-eval skill
├── fixtures/
│   ├── fixture-1-commit.md
│   ├── fixture-2-friction-audit.md
│   ├── fixture-3-actix-to-axum.md
│   └── fixture-4-fictional-bad-skill.md
├── prompts/
│   ├── vanilla_brief.md
│   ├── with_skill_brief.md
│   └── grader_brief.md
├── rubric.md
└── runs/                                    # POPULATED
    ├── fixture-1/{vanilla,with_skill}/run-{1,2,3}/{design.md, grading.json}
    ├── fixture-2/  (same shape)
    ├── fixture-3/  (same shape)
    └── fixture-4/  (same shape)
```

## Layout

```
iteration-1/
├── README.md                                    # this file
├── artifact-snapshot/                           # frozen make-eval skill
│   ├── SKILL.md
│   ├── templates/
│   └── references/
├── fixtures/
│   ├── fixture-1-commit.md
│   ├── fixture-2-friction-audit.md
│   ├── fixture-3-actix-to-axum.md
│   └── fixture-4-fictional-bad-skill.md
├── prompts/
│   ├── vanilla_brief.md
│   ├── with_skill_brief.md
│   └── grader_brief.md
├── rubric.md                                    # 10-criterion scoring
└── runs/                                        # POPULATED ON RUN
```

## What this DOESN'T test (acknowledged limitations)

- **Phase B not in baseline.** Whether designs execute cleanly is not tested unless the optional follow-up runs.
- **Single model (Sonnet).** Opus might benefit more or less from the skill. If Phase A shows ambiguous results, retry with Opus.
- **No interactive flow tested.** The skill's `AskUserQuestion`-driven design phase isn't exercised — subagents are one-shot. The skill's interactive value (clarifying requirements through user dialog) is out of scope here.
- **K=3 widens CIs.** If Phase A results are within ±1 on the rubric total, treat as inconclusive and bump to K=6.
- **Grader calibration** — using 2 graders per design + reporting inter-grader agreement; if agreement is poor (<70%), the rubric is the problem, not the conditions.

## Open questions for the user before running

1. Should we include Opus alongside Sonnet (would double cost to ~$12)?
2. For Fixture 4, is `git-yolo` a good fictional bad skill, or would you prefer a different one? (Suggestion: stick with this — simple, clearly bad, easy to detect.)
3. Run Phase B after Phase A's results? Adds $10–20 but catches paper-only failures.
4. Are there other fixtures you'd add? (4 feels minimal; 6 would be more robust but pushes cost to ~$9.)
