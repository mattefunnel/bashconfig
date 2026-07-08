# Example evals — read these before designing your own

Two prior evals serve as exemplars for different methodologies. Walk both before starting a new one.

**Note on evaluation regimes.** All examples below are **configured cold** regime (clean baseline + just the candidate). For true **cold clean** (no user CLAUDE.md inheritance), the eval would need to run outside `make-eval`'s Agent-tool-spawned subagents — via `claude -p --bare` instead. For **warm realistic** (post-compaction, multi-turn), neither example covers it. See SKILL.md "Advanced methodology — Three evaluation regimes" for the full taxonomy.

## Gold standard — `/review` skill eval

Path: `~/.claude/skills/review/evals/iteration-1/`

**Question tested:** does the `Code Standard Hotspots` section in `SKILL.md` add signal, or is it just tokens (since CLAUDE.md is in the system prompt every turn already)?

**Setup:**
- 2 conditions: with-Hotspots vs no-Hotspots
- 2 models: Opus 4.7 + Sonnet 4.6
- 2 fixtures: hand-crafted ~800-line Rust diffs (`fixture-1-comment-heavy.patch`, `fixture-2-defense-heavy.patch`)
- Each fixture has 5 plants + 3 controls (battle-tested true negatives from real conversation pushback)
- **K=6 runs per cell** = 48 reviewer runs + 48 grader runs = 96 subagent invocations total
- Cost: ~$15–20. Wall-clock: ~12 min per phase.

**Auto-grading flow:**
1. Reviewer subagent (per condition × model × fixture × k) reads the diff, returns a structured review.
2. Grader subagent (separate Sonnet) reads `(answer key, review output, scoring rubric)` and emits `grading.json` with per-item scores.
3. `aggregate.py` rolls up all 48 grading.json files into `benchmark.json` with mean ± stdev per cell.

**Scoring rubric** (per planted item):
- `tp` (1.0): flagged as `Blocking` with substantively the same concern
- `tp_partial` (0.5): mentioned in `Good To Know` only, OR flagged at the same location with a different concern
- `missing` (0.0): not mentioned at all

Per control:
- `correct_silence` (1.0): not flagged
- `fp_soft` (0.5): raised in `Good To Know` but acknowledged justification
- `fp` (0.0): flagged as `Blocking`

**Result:** TP rate for Sonnet drops 55 pp (0.78 → 0.23) without Hotspots. For Opus, TP drops 18 pp AND variance triples (stdev 0.06 → 0.21) — the section both lifts and stabilizes. **Verdict: keep the Hotspots section.**

**Best practices demonstrated:**
- Plants AND controls in fixtures
- K=6 for variance estimate
- 2 models for robustness check
- Auto-grader subagent scales beyond manual scoring
- Quantitative rubric with regenerable aggregate
- Honest observation that one plant (P5 fixture-2) was 0% TP across all four cells — a fixture characteristic worth fixing in iteration 2

## Lessons-learned — `session-search` agent eval

Path: `~/.claude/agents/evals/session-search/iteration-1/`

**Question tested:** does the `session-search.md` agent's playbook produce meaningfully better answers than vanilla Claude with the same tools?

**Setup:**
- 2 conditions: vanilla `general-purpose` vs `general-purpose` + playbook injection
- 1 model: Sonnet
- 2 fixtures: real-world queries (`VPC Lattice`, `actix-to-axum`)
- **K=1 per cell** — directional only, no variance estimate
- Manual spot-check scoring
- Cost: ~$1. Wall-clock: ~5 min per round.

**What went wrong in round 1:**
- Corpus was built with symlinks. ripgrep skipped them. Both playbook agents got 0 hits and confidently reported "no matches found". Vanilla agents used `find -exec grep` instead and worked.
- Methodology bug, not a playbook bug. Round 2 rebuilt the corpus with real file copies; playbook agents found their hits.

**Best practices demonstrated:**
- Round-1 failures preserved under `playbook-round-1-failed.md` as a methodology lesson
- Symmetric noise caveat across both conditions for Q2 (with documentation of asymmetry vs Q1)
- Artifact snapshot at eval time
- Pre-declared rubric (manual spot-check on structure / wrappers / accuracy / efficiency / brevity / completeness)
- Honest verdict: "playbook is roughly equivalent on accuracy, slightly more structured, slightly fewer tokens, slightly MORE tool calls. Real value is invocation ergonomics + context isolation, not dramatically better answers."

**What was weak:**
- K=1 — no variance estimate
- No pre-built answer key — judged qualitatively by manual spot-check
- Single model
- 2 fixtures is a small sample

## Cost-efficient re-run — `/review` skill iter-2 (dogfood, 2026-05-27)

Path: `~/.claude/skills/review/evals/iteration-2/`

**Question retested:** same hypothesis as iter-1 — does Hotspots add signal? But at reduced scope.

**What changed:**
- K=3 (was K=6)
- Sonnet only (was Opus + Sonnet)
- Same fixtures, same conditions, same prompts (copied forward)
- 12 reviewer runs + 12 grader runs = 24 subagents total
- Cost: ~$3.50 (vs iter-1's ~$15–20)

**Result:** iter-2 confirmed iter-1's headline finding — Hotspots is load-bearing for fixture-2 (TP 0.83 ± 0.06 vs no-Hotspots 0.50 ± 0.10, a 33 pp gap). For fixture-1, both conditions perform similarly. Same shape as iter-1, fewer dollars.

**Best practices demonstrated:**
- Sustainable cadence for SKILL.md regression testing — K=3 + single-model is cheap enough to run on every meaningful edit, K=6 + 2-model is reserved for big methodology changes.
- Fixtures copied forward verbatim (no fixture drift).
- Same `grader_brief.md` (no scoring-rubric drift).

**What was weak:**
- Grader calibration drift surfaced: iter-2 graders gave more `tp_partial` than iter-1 graders did on borderline items. Absolute TP rates shifted (e.g. fixture-2 with-Hotspots: 0.78 → 0.83) even though the gap held.
- K=3 widens confidence intervals — variance estimates are noisier than at K=6.

## Variance dogfood — `session-search` iter-2 (2026-05-27)

Path: `~/.claude/agents/evals/session-search/iteration-2/`

**Question retested:** same as iter-1 — does the playbook produce better answers than vanilla?

**What changed:**
- K=3 (was K=1)
- Same queries, conditions, corpus, prompts
- Manual spot-check (same as iter-1)
- 12 runs total, ~$1.50

**Result:** iter-1's "playbook ≈ vanilla" conclusion was correct **at the mean** but missed the variance story entirely. K=3 revealed:
- Playbook clamps `sessions_returned` to 8.0 ± 0.0 (perfect consistency from its "Cap at 8" rule) while vanilla varies 7–17.
- Token variance for the playbook is **16× lower** than vanilla on Q2 — output stabilization is the real value prop, not better answers.
- The playbook MISSES the canonical "AWS meeting" session that vanilla catches every time, because hit-count ranking is fooled by log-paste noise. Real coverage gap surfaced only at K=3.

**Best practices demonstrated:**
- K=1 → K=3 is the cheapest meaningful upgrade — same setup, 3× cost, qualitatively richer findings.
- Used prompt path indirection (`/tmp/claude/eval-prompts/`) to keep orchestrator outgoing-tokens low.

**What was weak:**
- Still K=3 (not K=6) — confidence intervals are wide; some "differences" might still be noise.
- Manual spot-check on top hits — would benefit from auto-grader for recall@8.
- The hard "Cap at 8" rule means `sessions_returned` doesn't capture the underlying coverage variance — should use ranking-quality metrics instead.

## Meta-eval: the skill evaluating itself (iter-1 and iter-2)

Path: `~/.claude/skills/make-eval/evals/iteration-{1,2}/`

The skill was applied to evaluate itself. Iter-1 used a 10-criterion 0/1/2 Sonnet-graded rubric; iter-2 switched to head-to-head Opus grading with hint-stripped fixtures.

**Iter-1 finding: rubric saturated.** Both vanilla and with-skill scored ~19.7/20 with stdev ~0.5. The Sonnet grader rubber-stamped 234 of 240 dimension-scores at the maximum. Inconclusive — methodology failed to discriminate.

**Iter-2 finding: skill helps on adversarial, hurts on real.** Using head-to-head 0–10 Opus grader + hint-stripped fixtures + 2 new adversarial fixtures:

| fixture group | with-skill advantage (-5 to +5) |
|---|---|
| Real skills (F1 commit, F3 actix-to-axum) | **-0.50** (vanilla wins) |
| Adversarial synthetic (F4 git-yolo, F5 aws-cred-yolo, F6 flake-tolerator) | **+0.44** (with-skill wins) |
| Δ | **+0.94** |

F6 (flake-tolerator) was unanimous: 3 of 3 head-to-head pairs scored with-skill better, σ = 0.0.

**The lesson that drove the skill update:** the full methodology is overhead on clean real skills. Skill now has a "lightweight mode" branch (see `SKILL.md` "Choosing depth"). Vanilla Sonnet's competence on familiar eval shapes covers most of what the skill adds; the skill's contribution is on harder cases (adversarial, safety-critical, multi-condition).

**Methodology lessons (from iter-1 → iter-2):**
- 10-criterion 0/1/2 absolute rubric saturated. **Head-to-head 0–10 comparison** discriminates better.
- Sonnet rubber-stamped. **Opus** was strict enough to use the full 0–10 range.
- Fixtures listing "expected design elements" leaked the answer to designers. **Stripped to graderhints/** file.
- Adversarial fixtures discriminate more than well-formed ones. Iter-2 added 2 (F5, F6) on top of F4.

## Meta-eval iter-3, iter-4: K-scaling and the strawman-baseline trap

Paths: `~/.claude/skills/make-eval/evals/iteration-{3,4}/`

Iter-3 added an "Advanced methodology" section to SKILL.md body and made real-skill scores worse (-1.50 vs iter-2's -0.50). Iter-4 moved that content to `references/advanced-methodology.md` (load-on-demand) — partial real-skill recovery, but adversarial regressed. Both iterations measured at K=10.

**Apparent verdict at iter-4 K=10:** skill loses to vanilla by -0.81 overall. Recommended deprecation.

**Why this verdict was wrong:** see iter-5 below. The "vanilla" condition was a 30-line eval-design checklist — itself an elaborate prompt doing 80% of the skill's job. The "skill loses to vanilla" finding was an artifact of a strawman baseline.

## Meta-eval iter-5: bare-prompt comparison reverses the verdict

Path: `~/.claude/skills/make-eval/evals/iteration-5/`

Replaced the elaborate "vanilla" with a truly bare 4-line prompt: "Design an evaluation of the skill described in {TASK}. Write to {OUT}. Don't read graderhints. Return a 2-3 sentence summary." Same fixtures, same grader, same K=10 (n=60 advantages), same current SKILL.md.

| group | μ ± σ | 95% CI |
|---|---|---|
| Real (F1+F2+F3) | -0.27 | tied |
| Adversarial (F4+F5+F6) | **+1.23** | **skill wins clearly** |
| Overall (n=60) | **+0.48** | **[+0.15, +0.81]** |

**The skill earns its keep** — by +0.48 overall, Cohen's d ≈ 0.37. F5 (aws-cred-yolo) had 3 cells at the maximum advantage. Driven by adversarial-framing nudges (dual safety+efficacy hypotheses, DELETE-permitted-verdict, plant+control fixtures) that bare-prompt designs miss.

**The load-bearing lesson:** the user-facing alternative to "invoke skill X" is "type a 1-3 line prompt and hope Claude figures it out," not "type a 30-line eval-design checklist." Strawman baselines that share the skill's structure smuggle the skill's contribution into the control. See anti-pattern #23.

## When to follow which model

- Use the **review pattern** (auto-graded, K=6, plants+controls) when:
  - You can construct hand-crafted fixtures with clear correct/incorrect answers
  - Accuracy is the primary axis (not just ergonomics)
  - The scoring rubric is item-by-item enumerable
  - You want quantitative claims with confidence intervals
  - Budget allows ~$15+

- Use the **session-search pattern** (manual, K=1–2, real-world fixtures) when:
  - Fixtures are naturally-occurring (queries, documents, real tasks) rather than constructed
  - The judgment is qualitative ("output is well-structured", "wrappers are stripped")
  - You want a quick directional read before committing to a full eval
  - Budget is tight

Most evals should aim for the review pattern after a session-search-style pilot.
