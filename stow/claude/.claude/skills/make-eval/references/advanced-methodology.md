# Advanced methodology — load on demand

Load this file in Phase 1 only if the eval needs any of: a stripped-down "cold clean" baseline, an artifact type other than a skill/agent (hook, CLAUDE.md, settings), or statistical claims with confidence intervals. For most evals — head-to-head A/B on a skill or agent at K=3 — the SKILL.md body is sufficient.

## Three evaluation regimes

Pick one explicitly. Default for `make-eval` is **warm realistic** — the runs land on a populated context, because that is where the artifact actually fires. Cold regimes are the deliberate exception, reserved for genuine one-shot fixtures (does it trigger / is a single output well-formed) where there is no drift to measure.

| regime | answers | how to set up |
|---|---|---|
| **Warm realistic** (default) | does this help in actual workflow conditions (long sessions, drift, compaction)? | resumed sessions, multi-turn conversations, post-compaction state. Build a clean, condition-identical context primer per fixture (Phase 3) and pose the test turn on top of it. For drift rules, run the primer long / through compaction and measure the per-turn slope. |
| **Configured cold** (exception) | does this help when it's the ONLY added thing, on a blank slate? | clean baseline + just the candidate, fresh context. The `make-eval` skill spawns `general-purpose` subagents with the artifact injected. **Honest limitation:** `general-purpose` subagents still inherit your CLAUDE.md and managed-policy settings. For a TRUE cold-clean baseline, switch to `claude -p` with explicit `settingSources` outside this skill. Use only for one-shot fixtures with no drift component. |
| **Cold clean** (exception) | does this help on a stripped environment? | `claude -p` with `--settings`/`settingSources: []` to skip auto-discovery of hooks/skills/plugins/MCP/CLAUDE.md; disable auto-memory; separate filesystem for full isolation. (Older docs reference a `--bare` flag — the modern equivalent is explicit `settingSources` scoping.) |

**Warm realistic matters when the artifact's behavior depends on long-context conditions.** Skills hit a **5,000-token-per-skill / 25,000-token-combined cap after compaction** — a skill that helps in turn 3 may silently drop out after the conversation gets long. If you care about that, do not infer warm-state behavior from cold-state evals.

## What to evaluate, by artifact type

Different artifacts have different evaluation surfaces. The skill/agent emphasis in SKILL.md is one case; others matter too.

| artifact | what changes vs baseline | how to evaluate |
|---|---|---|
| `CLAUDE.md` addition | always-loaded context | task-level success on tasks the rule should affect; did context cost increase enough to hurt long sessions? |
| Skill (auto-invoked) | on-demand context + automatic trigger | **two dimensions:** effectiveness-when-invoked AND triggering precision/recall (fires when it should AND not when it shouldn't) |
| Skill (manual, `disable-model-invocation: true`) | on-demand context only | effectiveness-when-invoked |
| Hook | deterministic action at lifecycle point | **TPR / FPR / latency / nuisance-block rate** — NOT "did Claude remember the instruction" |
| Subagent / agent | isolated context + tool restrictions | compare vs main-conversation alternative; measure main-context pollution savings + correctness in delegated work |
| Settings (model / effort / permission mode) | capability + operating conditions | factorial design; separate from prompt/rule changes |

**Critical: instructions in CLAUDE.md or skills are ADVISORY. Hooks are DETERMINISTIC.** If a behavior must hold every time (e.g. "never read .env", "always run formatter"), build a hook and evaluate its policy properties — don't try to make instructions enforce hard constraints. CLAUDE.md is for things you'd otherwise re-explain every session; hooks are for things that must hold every run.

**For auto-invoked skills, evaluate two things, not one.** The skill could be excellent when used but trigger on the wrong artifacts (low precision) or fail to trigger when needed (low recall). Anthropic recommends tightening the `description` or setting `disable-model-invocation: true` when this is the failure mode. A skill that scores 9/10 on effectiveness but triggers on 20% of unrelated requests is a net negative.

## Statistical analysis

| outcome type | use | reference |
|---|---|---|
| binary (pass/fail per task) | **McNemar test** on discordant pairs | classical; see mlxtend's `mcnemar` for an ML-comparison-flavored implementation. Mid-p variant has better calibration than the exact conditional form (Fagerland et al., 2013, PMC3716987) |
| continuous (time, count, cost, head-to-head score) | **paired bootstrap** or approximate randomization | Dror, Baumer, Shlomov & Reichart, "The Hitchhiker's Guide to Testing Statistical Significance in NLP", ACL 2018 (https://aclanthology.org/P18-1128/). Has a companion toolkit at github.com/rtmdrr/testSignificanceNLP |
| 0–10 head-to-head ratings (iter-2 meta-eval pattern) | paired t-test on deltas, or sign test if non-normal | standard; Dror et al. discuss test selection by metric distribution |
| many secondary endpoints | **Benjamini-Hochberg FDR control** for the family of exploratory tests | standard. Pre-register the primary endpoint; secondary endpoints labeled exploratory and FDR-controlled. |

**Do NOT use independent-sample t-test on paired data.** Pairing reduces variance dramatically; using the wrong test inflates the effect size needed to reach significance. K=3 paired ≈ K=10 independent in practical power. Dror et al.'s ACL survey found "very few [NLP] papers report statistical significance and many incorrectly use the t-test" — i.e. this is a documented field-wide anti-pattern, not a quirk of LLM evals.

## Power analysis quick table

Rough n needed per cell, assuming α=0.05, power=0.8, paired analysis:

| effect size (Cohen's d) | meaning | n needed |
|---|---|---|
| 0.2 | small (skill helps barely) | ~200 |
| 0.5 | medium (skill helps a bit) | ~35 |
| 0.8 | large (skill clearly helps) | ~15 |
| 1.5 | huge (skill load-bearing) | ~5 |

**Iter-2 of this skill's meta-eval observed Cohen's d ≈ 0.08 overall** (advantage / stdev = 0.11 / 1.32) — far below detectability at K=3. It DID detect the larger between-group effect (Cohen's d ≈ 0.7, real-skill vs adversarial) at n=18.

**For most evals at K=3–6, you can detect d ≈ 0.8 reliably; smaller effects need K=15+ or paired analysis to avoid getting fooled by noise.**

## Benchmark contamination — two different problems, not one

The LLM-eval literature talks about contamination, but there are actually **two** distinct contamination problems for any `make-eval` run. Don't conflate them.

### Training-data contamination (model weights)

A live problem in the literature: public benchmarks decay quickly because their answers leak into training data. The "Retro-Holdout" methodology constructs post-hoc datasets indistinguishable from the original benchmark; on TruthfulQA, "Retro-Misconceptions" revealed up to **16 percentage points** of inflation on contaminated models (Patil et al., "Benchmark Inflation: Revealing LLM Performance Gaps Using Retro-Holdouts", ICML 2024, https://arxiv.org/abs/2410.09247). A 2025 EMNLP survey ("Benchmarking LLMs Under Data Contamination: A Survey from Static to Dynamic Evaluation", https://arxiv.org/abs/2502.17521) covers the field's shift from static benchmarks toward dynamic regeneration.

**Make-eval's default sidesteps this:** user-constructed fixtures drawn from local work (your diffs, your transcripts, your scenarios) have never been on the public web, so they cannot be in any model's training set. If you ever extend `make-eval` to import a public benchmark (MMLU, HumanEval, SWE-bench), build a retro-holdout alongside it and report both numbers — the gap measures the contamination effect.

### Local-disk contamination (filesystem reachable by the agent)

The subagent under test has Read and Bash. The fixture's answer key, the artifact's own evals directory, prior conversation transcripts in `~/.claude/projects/<project>/*.jsonl`, design notes in `~/Documents/notes/`, and auto-memory entries are ALL on the same disk. A subagent that looks for them can find them. This is the **opposite** of the training-data problem: user-constructed fixtures make it WORSE because the answer key literally lives next to the fixture.

This is what the skill's "avoid poisoning" principle and `references/anti-patterns.md` items #1, #2, #3 are about. Specifically:

- **Subagent isolation** (fresh context, no parent memory) prevents poisoning from the conversation that designed the eval. Necessary but not sufficient.
- **Corpus scoping** (real file copies into a sandboxed dir; prompt forbids reads outside it) prevents the subagent from walking back to `~/.claude/projects/` or the artifact's own evals dir.
- **Symlinks leak source paths** via `readlink` even if grep tools skip them. Use `cp`, not `ln -s`.
- **Hide the answer key from the runner.** Put it in `fixtures/<name>-graderhints.md` that only the grader subagent sees, not in `fixtures/<name>.md` that the runner sees. (Iter-2 meta-eval added this — see anti-pattern #4.)

Local-disk contamination is the contamination that actually bites this skill in practice. Training-data contamination is the contamination the literature talks about.

## Pre-registration discipline

Before running the holdout, write down in the README: candidate, control, task distribution, **primary** endpoint, smallest worthwhile effect, analysis rule, stopping rule. Stick to the plan. If the result misses, either drop the candidate or reclassify the work as exploratory and iterate before another confirmatory run.

For exploratory secondary endpoints (which you'll inevitably look at), label them exploratory and use Benjamini-Hochberg or similar FDR control on the family. Don't test ten endpoints and then celebrate the one that moved.

## Why this content lives here, not in SKILL.md

Per the Anthropic skills docs: "Once a skill loads, its content stays in context across turns, so every line is a recurring token cost. State what to do rather than narrating how or why." (https://code.claude.com/docs/en/skills, also "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.")

This content was previously inlined in SKILL.md and the iter-3 meta-eval at `evals/iteration-3/` showed it hurt design quality on clean real-skill fixtures (real-skill advantage went from -0.50 in iter-2 to -1.50 in iter-3). Diagnosis: the menu of regimes/tables/stats distracted designers from the fixture's actual stress points. Putting it in `references/` lets full-mode evals load it on demand without imposing the recurring cost on every invocation.
