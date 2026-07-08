# Eval anti-patterns

Methodology bugs that have actually bitten in prior evals. Read before designing a new one.

## 1. Symlink corpus

**What:** built a corpus of symlinks instead of real file copies.

**Why it's broken:** ripgrep skips symlinks by default — `--follow` is needed. Subagents that grep the corpus return 0 hits even when matches exist in the target files. Worse: subagents *rationalize* the absence (e.g. "the corpus genuinely has no actix-to-axum discussion") rather than diagnose the search.

**Bonus failure:** a subagent can `readlink` to discover the source path and walk to forbidden siblings — defeats the isolation.

**Fix:** real file copies (`cp`). Cost ~377 MB for the session-search eval's corpus — acceptable.

**Reference:** `~/.claude/agents/evals/session-search/iteration-1/runs/*/playbook-round-1-failed.md`.

## 2. Hard links across APFS volumes (macOS)

**What:** tried `ln` (hard link) from `~/.claude/projects/...` into `/tmp/claude/...`.

**Why it's broken:** `/tmp` (actually `/private/tmp`) is on a different APFS volume than `~/`. Hard links fail with EPERM.

**Fix:** real file copies, or put the corpus inside the user's home filesystem (e.g. `~/eval-corpus/`).

## 3. K=1 declared as evidence

**What:** ran each cell once, drew conclusions from the 4–8 datapoints.

**Why it's broken:** no variance estimate. Every observation is a coin flip — you can't tell whether the difference between A and B is real or noise. The review eval's K=6 revealed that the Hotspots section *stabilizes* Opus behavior (stdev 0.21 → 0.06) — invisible at K=1. Session-search iter-2 (K=3 vs iter-1's K=1) found that the playbook's hard "Cap at 8" rule produces zero variance in hit count while vanilla varies ±2 — entire variance dimension was hidden at K=1, and the iter-1 conclusion ("playbook ≈ vanilla") was technically correct at the mean but missed the real story.

**Fix:** K≥3 minimum for any quantitative claim. K=3 is enough to detect major variance differences between conditions. K=6 tightens the confidence interval. Label K=1 results as "directional only" in the README.

## 4. Post-hoc rubric

**What:** ran the eval, looked at the outputs, decided how to score them.

**Why it's broken:** invites rationalization toward the result you already expect. The rubric becomes "whichever scoring criteria makes my favorite condition win".

**Fix:** declare the rubric in the README *before* running. Include dimension names, scoring scale (0–2 is good), and what "good" means at each level.

## 5. Confidently wrong subagent rationalization

**What:** a subagent's search returns 0 hits due to a methodology bug (e.g. symlinks); the subagent builds a coherent narrative around the absence ("there are no sessions discussing X because…") and reports it confidently.

**Why it's broken:** silence ≠ correctness. The subagent doesn't know its search is broken; nothing tells it. You can't detect this without ground-truth verification.

**Fix:**
- Always establish a ground-truth file count BEFORE running (e.g. `grep -l <term> <corpus> | wc -l`).
- If a subagent reports 0 hits, cross-check against the expected hits before accepting the result.
- For auto-graded evals, the grader catches this because the ground-truth fixtures have known plants.

## 6. Asymmetric prompts (undeclared)

**What:** condition A's prompt has a hint or caveat that condition B's prompt lacks, or vice versa.

**Why it's broken:** the comparison isn't between (A's artifact vs B's artifact) anymore — it's between (A's artifact + A's prompt hint) vs (B's artifact + B's no-hint). You can't attribute the difference to the artifact.

**Fix:** if the fixture genuinely needs a caveat (e.g. "X is also a skill name; matches in system-reminders don't count"), BOTH conditions get the same caveat. Document why it's needed in the README's "Limitations" section.

**Reference:** session-search eval's Q2 (actix-to-axum) needed a noise caveat that Q1 (VPC Lattice) didn't. Both conditions got the caveat for Q2.

## 7. Single model, generalizing

**What:** ran the eval on Sonnet only, concluded "the playbook doesn't help much".

**Why it's broken:** Sonnet is competent enough that many playbooks add marginal value. Weaker or stronger models may behave differently. The review eval showed the Hotspots section is load-bearing for Sonnet (TP 0.23 → 0.78) but only stabilizing for Opus.

**Fix:** test at least 2 models if the artifact is model-agnostic. If you only have budget for one model, name the model in the verdict ("not tested on Opus").

## 8. No control fixtures (only plants)

**What:** fixtures have items the artifact SHOULD flag, but no items the artifact should NOT flag.

**Why it's broken:** you measure TP rate (recall on the planted items) but not silence rate (correct silence on legitimate code). An artifact that flags everything has 100% TP rate and 0% silence rate. Without controls, you can't see the false-positive cost.

**Fix:** every fixture has plants + controls. Battle-test controls against real conversation pushback ("this looked flag-worthy but is intentional because…"). 5 plants + 3 controls per fixture is the review eval's standard.

## 9. Forgetting to snapshot the artifact

**What:** ran the eval, then edited the artifact, then tried to re-run.

**Why it's broken:** re-runs no longer reflect the version that was tested. Original results become unreproducible.

**Fix:** `cp <artifact-path> iteration-N/artifact-snapshot/` AT eval start. The snapshot is the source of truth for that iteration. Iteration N+1 gets a fresh snapshot.

## 10. Cost runaway

**What:** spun up K=10 × 4 conditions × 3 models × 5 fixtures = 600 subagent runs on Opus. $200+ surprise.

**Why it's broken:** no upfront budget consideration.

**Fix:** compute total run count and rough cost estimate before spawning. Mention it to the user. If running auto-graded, double the count (graders are usually Sonnet, cheap).

Sonnet rates: ~$0.05–$0.20 per subagent run depending on tool count and output size. Opus rates: ~3-5×.

## 11. Tool-prescriptive playbooks

**What:** the playbook says "use the Grep tool" or "use ripgrep" by name.

**Why it's broken:** in unusual test environments (e.g. symlink corpus), the prescribed tool may not work. The subagent follows the playbook into a corner instead of finding an alternative.

**Fix:** in playbook design, prefer abstract instructions ("search the transcripts for X") over tool-specific ones. Where tool choice matters, explain WHY ("use `rg` because it respects `.gitignore`") so the subagent can adapt if needed.

**Reference:** session-search eval round 1, both playbook agents got 0 hits because the playbook said "use the Grep tool" and the tool silently failed on symlinks.

## 12. Fixture sample size too small

**What:** 1 fixture. Generalized to "the artifact works/doesn't work".

**Why it's broken:** fixtures vary in ways the artifact may handle differently. A single fixture is a single data point; the artifact's behavior on it doesn't predict its behavior on others.

**Fix:** 2 fixtures minimum, chosen for diversity (multi-word vs identifier, noisy vs clean, common vs rare). 4+ fixtures for a robust eval.

## 13. Regenerating fixtures between iterations

**What:** swapped fixture-1 for a different diff between iter-1 and iter-2, then compared results.

**Why it's broken:** cross-iteration comparison requires identical inputs. Different fixtures = different problems = uncomparable results. You can't tell whether a metric changed because the SKILL.md changed or because the fixture got harder/easier.

**Fix:** copy fixtures forward verbatim across iterations (`cp -r iteration-1/fixtures iteration-2/fixtures`). If you want to test a new fixture, that's a separate experiment — keep the original alongside it and document the addition in the README.

## 14. Hard-coded limits in playbooks produce artificial variance signatures

**What:** playbook says "return at most 8 hits". Eval measures variance in hit count. Variance is 0. Looks great in the metric.

**Why misleading:** the metric reflects a deterministic rule, not agent behavior. Real coverage variability is hidden under the cap. If two conditions both cap at 8, you can't tell which one was about to surface a 9th hit that vanilla would have included.

**Fix:**
- Be aware of which metrics reflect agent behavior vs which reflect playbook rules. Flag in the README's TL;DR table.
- Measure ranking quality (top-K overlap, Spearman correlation between runs) instead of raw count where caps apply.
- Consider running the eval BOTH with and without the cap to separate the cap's effect from the playbook's other content.

**Reference:** session-search iter-2 — `sessions_returned` had stdev=0 across all 6 playbook runs because of the "Cap at 8" rule.

## 15. Grader calibration drift between iterations

**What:** iter-1 graders gave conservative `tp` scores; iter-2 graders gave more `tp_partial` on the same borderline cases. Same rubric, same artifact, but the absolute TP-rate numbers don't line up between iterations.

**Why it's broken:** makes cross-iteration trend lines noisy. Drift can come from prompt edits, different sampling, model updates between iterations, or even just bigger Sonnet sample noise.

**Fix:**
- Keep `grader_brief.md` **byte-identical** across iterations. If you need to update it, that's a methodology change worth a new prompts/ snapshot.
- For tight cross-iteration comparability, run 2+ graders per review and report inter-grader agreement. Disagreements flag the borderline items the grader prompt needs to disambiguate.
- Don't compare absolute TP rates across iterations without acknowledging this drift. Compare gaps (with-condition − without-condition) which are more robust.

**Reference:** review iter-1 vs iter-2 — same fixture-2 with-Hotspots, iter-1 reported TP=0.78, iter-2 reported 0.83. The shape of the finding ("Hotspots is load-bearing") replicated, but the absolute numbers shifted.

## 16. Inlining long prompts across K runs

**What:** spawning 12 subagents each with the same 600-word prompt inlined; 7,200 outgoing words for the orchestrator.

**Why suboptimal:** bloats orchestrator context, slows the message, increases prompt-cache miss risk. At K=24 the inlined approach becomes expensive enough to matter.

**Fix:** write the resolved prompt once to `/tmp/claude/eval-prompts/<name>.md`, then each Agent spawn becomes `Read /tmp/claude/eval-prompts/<name>.md and follow its instructions. Return your output as the final response.` Each spawn is ~25 words instead of ~600. Skill's `SKILL.md` Phase 3 calls this "Token economy pattern 1".

## 17. Long subagent outputs returned to orchestrator

**What:** reviewer subagent returns a 2,000-word review as its response. 12 reviewers × 2,000 words = 24k incoming tokens for the orchestrator to absorb.

**Why suboptimal:** bulk content lands in orchestrator context where it's not needed (the orchestrator just routes it to graders or saves it). It's only USED later, by graders that read from disk.

**Fix:** tell the subagent to write the full output to `/tmp/claude/<eval>-runs/<cell>/<run>/output.md` and return only a 2–3 sentence summary. Copy to durable storage at the end. Skill's `SKILL.md` Phase 3 calls this "Token economy pattern 2".

## 18. Over-applying full methodology to clean real skills

**What:** designed an eval of a well-formed real skill (`commit`, `actix-to-axum`) using the full 5-phase walkthrough + the entire 17-anti-pattern checklist. Result: with-skill design was longer than vanilla's, more boilerplate-laden, and the Opus head-to-head grader rated it WORSE than vanilla.

**Why broken:** the full methodology is overhead. Anti-pattern walkthroughs and dual-hypothesis frames are load-bearing for adversarial / synthetic / safety-critical artifacts; they're noise for clean real skills where Sonnet's general competence already covers the basics. Adding "this design addresses anti-pattern #N because ..." sections to a simple eval clutters the design without adding signal.

**Fix:** use **lightweight mode** (see `SKILL.md` "Choosing depth: lightweight vs full mode") for clean real artifacts. Reserve the full methodology for adversarial / safety-critical evals.

**Reference:** make-eval iter-2 meta-eval. Real-skill fixtures showed mean -0.50 with-skill advantage (vanilla wins); adversarial synthetic fixtures showed mean +0.44 with-skill advantage. Δ = +0.94 in favor of "use the skill only when warranted".

**Heuristic:** if the artifact has no `--force` / `--no-verify` / `commit credentials` / "trust me" / "always" / "no need to investigate" language in its docs, default to lightweight.

## 19. Using Explore or Plan subagents to test CLAUDE.md behavior

**What:** evaluated whether your CLAUDE.md rules improve Claude's research/planning behavior by running Explore subagents (or built-in Plan) as the test subject.

**Why broken:** built-in Explore and Plan subagents **deliberately skip your CLAUDE.md files** for performance/cost reasons. They never see your rules. So your eval is measuring "Explore on a stripped context" vs "Explore on a stripped context with X injected" — the CLAUDE.md isn't actually a variable in the experiment.

**Fix:** use `general-purpose` subagents (which DO inherit CLAUDE.md), or use `claude -p` (CLI) where you control loading explicitly via `--bare` / `--settings`, or restate the critical CLAUDE.md rules in the delegated subagent prompt rather than relying on auto-load.

**Reference:** Anthropic docs note that Explore and Plan subagents skip CLAUDE.md and the parent session's git status to keep research quick. Documented as a known design choice, not a bug.

## 20. Independent-sample t-test on paired data

**What:** ran K vanilla and K with-skill evals on overlapping fixtures (same fixture, paired comparison). Then ran an independent-sample t-test on the two score sets. Declared inconclusive (p > 0.05).

**Why broken:** the data is paired — each vanilla design has a matching with-skill design on the same fixture-K. Pairing controls for fixture-level variance, which is usually large. Independent t-test treats the data as if vanilla and with-skill came from unrelated samples, inflating the effect size needed to reach significance by ~3-5×.

**Fix:** for binary outcomes (pass/fail), McNemar test on discordant pairs. For continuous outcomes, paired bootstrap or approximate randomization. For 0–10 head-to-head ratings (iter-2 pattern), paired t-test on the deltas. **K=3 paired ≈ K=10 independent** in practical power.

**Reference:** standard methodological literature; see NLP eval references on paired bootstrap.

## 21. Mistaking "instruction Claude remembered" for "rule was enforced"

**What:** added a rule to CLAUDE.md ("never commit .env files"). Evaluated by counting how often Claude actually skipped .env in eval transcripts.

**Why broken:** CLAUDE.md is **advisory context**, not enforced policy. The right measurement is not "did Claude follow the instruction" (which is the artifact's success metric) — it's "what's the TPR/FPR of the enforcement layer". If you actually need this behavior 100% of the time, the artifact should be a `PreToolUse` hook, not a CLAUDE.md line. Then the eval becomes: does the hook block .env commits with what TPR/FPR/latency?

**Fix:** match artifact to constraint strength:
- For soft preferences and broad guidance: CLAUDE.md or skill, evaluate "did Claude follow it" rate.
- For things that must hold every run: hook, evaluate TPR/FPR/latency/nuisance-block-rate.

If you find yourself adding stronger-and-stronger language to a CLAUDE.md rule to make Claude follow it more reliably, that's a signal that the rule belongs in a hook, not in advisory context.

## 22. Putting reference material in SKILL.md body instead of references/

**What:** added a "Three regimes" table, a "What to evaluate by artifact type" table, and a power-analysis lookup directly into the SKILL.md body, on the theory that "more methodology = better designs". The iter-3 meta-eval of this very skill showed designs got **worse**, not better — real-skill advantage went from -0.50 (iter-2) to -1.50 (iter-3).

**Why broken:** Per Anthropic's official skills doc (https://code.claude.com/docs/en/skills): "Once a skill loads, its content **stays in context across turns**, so every line is a recurring token cost." And: "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files."

Every line in SKILL.md is paid for on every turn of every session where the skill is invoked. Reference tables that apply to 5% of evals (hooks, settings, statistical claims) cost 100% of the time. Subagents invoked with the skill loaded then walk that menu instead of focusing on the actual fixture.

**Fix:** SKILL.md holds the default workflow + decision points. Reference material — tables that apply only in specific regimes, statistical methods, artifact-type-specific evaluation surfaces, power analysis lookups — lives in `references/<topic>.md` and gets loaded on demand only when the eval needs it. SKILL.md should pointer to references/ from a 1-line trigger ("if artifact is a hook, load references/advanced-methodology.md").

This is the single load-bearing structural rule of skill design. If you're tempted to inline a methodology table "for completeness", measure whether it actually helps before paying the recurring token cost — iter-3 of this skill is empirical evidence that the default expectation ("more methodology = better") is wrong.

## 23. Strawman "vanilla" baseline that's itself an elaborate prompt

**What:** when evaluating "does skill X add value vs no-skill", the "vanilla" condition is itself a 20-40-line briefing that already prescribes most of what the skill would prescribe (plants/controls, K size, isolation, scoring rubric, anti-patterns avoided, etc.). The skill's measured advantage is tiny or negative because the comparison eats most of the skill's contribution before measurement.

**Why broken:** the real user-facing alternative to "invoke skill X" is "type a 1-3 line prompt and hope Claude figures it out" — not "type a 30-line eval-design checklist." If the "vanilla" condition prescribes the same structure the skill does, you're not measuring the skill against a realistic baseline; you're measuring whether the skill adds anything beyond an alternate elaborate prompt. Both can be valuable, but the comparison answers a different question than the one users care about.

Concrete trigger that exposed this: iter-4 of this skill's meta-eval reported "skill loses to vanilla at K=10 overall." iter-5 replaced the elaborate "vanilla" with a truly bare prompt ("design an evaluation of this skill, that's it") — same skill state, same fixtures, same grader, same K=10. Result flipped to **skill wins +0.48 (significant), with adversarial fixtures showing +1.23**. The earlier "loss" was an artifact of the strawman baseline doing 80% of the skill's job.

**Fix:** the "vanilla" condition should be the prompt a user would actually type if they didn't have the skill. For most skills that's 1-5 lines: "do X for this artifact". If your baseline prompt is longer than that, ask whether you've smuggled the skill's contribution into the control.

**Optional second comparison:** if you ARE interested in "does this skill beat an alternative elaborate prompt", set that up as a separate condition (three-arm: bare / elaborate-alternative / skill). Don't conflate it with the user-facing value question.

## 24. Cold eval of a drift-prevention (warm-regime) rule

**What:** evaluated an anti-drift CLAUDE.md rule — "logging: default to none", "comments: default to ZERO", "prefer shortest / inline over extract" — with a single-shot cold `claude -p` probe. The rule looked **redundant** (the model wrote clean, minimal, comment-free code on turn 1 whether or not the rule was present) and got classified `CUT_REDUNDANT`.

**Why broken:** these rules don't target turn-1 behavior — they target **drift that accumulates over a long session**. The user added them precisely because, after a conversation has been going for a while, the model starts adding logging/comments/abstraction it wouldn't add cold. The reported rationalization is telling: *"a future reader won't have **our context**"* — the accumulated conversation builds an imagined outside reader, and the model starts writing explanatory artifacts to serve it. A cold probe has no accumulated context, so that pressure never arises and the rule's value is invisible. Measuring cold and concluding "redundant" is a category error: you tested the rule in the one regime where it was never meant to fire.

**Fix:**
- Classify the rule first (Phase-1 item 8). If it says "default to", "stop adding", "keep it minimal", or otherwise fights a *tendency* rather than a one-shot *choice*, it is a **warm-regime** rule.
- Run warm: resumed multi-turn sessions (`claude -p ... --resume <session_id>`) that accumulate ~12–15 turns of realistic, discussion-heavy work *without mentioning the target behavior*, then a final code-writing turn. Hold the same injected system prompt (rule present vs absent) across the whole session.
- Measure the **per-turn slope** of the unwanted behavior (comment count / log lines / single-use helpers), not just the final turn. The hypothesis is that rule-absent drifts upward while rule-present stays flat — that slope difference is the rule's value, and it is zero by construction in a cold eval.

**Reference:** CLAUDE.md ablation iter-1 (`~/.claude/evals/claude-md/iteration-1/`). Poisoning was correctly ruled out (verified: empty memory dir, `--setting-sources ""` confirmed no CLAUDE.md loaded, surgical ablation), yet the `logging`/`shortest`/`comments` cut verdicts were still **invalid** — not from contamination but from testing a warm-regime rule in the cold regime.

**Corollary — "go warm" is not enough; reproduce the actual *trigger*.** A warm multi-turn session is necessary but not sufficient. Iter-2 ran the `comments` rule warm (12-turn resumed sessions) and STILL saw no drift — because the sessions were **greenfield** (writing new functions), and the `comments` rule's load-bearing clause is the *"ignore match-surrounding-density"* override, whose trigger is **editing an existing comment-heavy file**. No surrounding comments → no pressure to match → rule looks redundant even warm. Iter-3 supplied the real trigger (Opus editing a real 95-comment meld-api file, adding a non-trivial function) and the drift appeared: rule-absent matched the heavy style (≈2/5 runs added explanatory comments), rule-present never did (0/5) — identical code, comments the only delta. **Identify the rule's specific triggering condition and reproduce THAT, not just "a long session."** For "match surrounding density" that means a real, dense fixture file edited in place (`--allowedTools "Read Edit" --permission-mode acceptEdits`), and grading the comments in the *added* lines via diff. Reference: `evals/claude-md/iteration-3/`.

## 25. Probe too trivial to exhibit the behavior (floor effect)

**What:** the eval task is so simple that the behavior under test cannot occur, so both arms score identically at the floor. Iter-3 round 1 asked the model to add a **one-line** function (`return MAP[id] ?? DEFAULT`); both rule-present and rule-absent added zero comments — not because the rule is redundant, but because a one-liner needs no comment in any regime. The probe had no power to discriminate.

**Why broken:** a null result is then ambiguous between "the artifact does nothing" and "the probe couldn't reveal what the artifact does." You can't tell which, and you'll often misread it as the former.

**Fix:** the probe must make the target behavior a *live choice*. For comment/logging/abstraction drift, request **non-trivial** output — multiple branches, a magic-number/clamp decision, an edge case, something a careful author might plausibly annotate. Iter-3 round 2 (a ~10-line function with a `[0.1,1.0]` clamp + branches) discriminated cleanly where the one-liner couldn't. Sanity check before running: *on the no-artifact arm, is there even an opportunity for the bad behavior to appear?* If not, harden the probe.

**Reference:** `evals/claude-md/iteration-3/` round 1 (recorded in its README as the fixture-design lesson).

## 26. Empty-context eval of an always-loaded artifact (ceiling effect)

**What:** evaluated a CLAUDE.md block (Funnel tech defaults) cold and single-shot — clean ~250-word design tasks, `--allowed-tools ''`, no prior context. The block "failed" its pre-registered +1.5 efficacy bar (came in at +0.70).

**Why misleading:** the per-check breakdown showed the failure was a **ceiling artifact, not a weak artifact**. On an empty context a capable model (Sonnet/Opus) already picks most mainstream-good defaults unprompted — AWS compute 10/10, Postgres-not-MySQL 10/10, the whole React stack 10/10 — *with no block at all*. Those checks were pinned at the ceiling, so the block had zero headroom to improve them, and averaging them in dragged the gap below threshold. The block's real, large effects were only on the **non-obvious, org-specific** checks where the model's prior diverges from the org default: Bedrock-for-LLM 0→10/10, avoid-Go-for-new-work 8→0/10 violations, avoid-GraphQL 2→0/10. An empty-context eval drowns those genuine wins in a sea of already-aced mainstream defaults. The same artifact tested in a realistic ~150k populated context — where the model is juggling real distraction and its priors are under load — would discriminate where the block actually earns its keep.

**Why it matters more for capable models:** the bigger the model, the more trivially it handles an empty context, so the more an empty-context eval flatters-or-flattens the artifact. Opus on a blank slate is close to a no-op test. The artifact has to prove itself at 150k+, not at 5k.

**Fix:**
- Default to a **populated context primer (~150k tokens of realistic prior work)** for every run — SKILL.md Phase 3. Plants + controls are necessary but not sufficient; they need a non-trivial context to be measured in (principle 1: populated AND planted).
- Pick a **primary endpoint scoped to the divergent-from-default checks**, or stratify plants into "model already does this" vs "org-specific override" and report them separately. A single blended mean across both buckets mis-prices the artifact whenever the baseline is a competent generalist rather than a naive one.
- When pre-registering the threshold, ask: *what does the no-artifact arm already score?* If you expect it near-ceiling on most plants, the threshold is measuring headroom that doesn't exist — fix the fixtures (harder/divergent checks, populated context) before committing the number.

**Reference:** `~/Documents/notes/evals/claude-md-funnel-block/iteration-1/` — clean separation (several cells stdev 0.00) was itself the tell that the inputs were unrealistically easy. Recorded in that README's verdict as the iter-2 methodology fix.
