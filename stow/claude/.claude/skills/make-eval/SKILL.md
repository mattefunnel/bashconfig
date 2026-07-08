---
name: make-eval
description: Design and run an empirical evaluation of a Claude Code skill or agent — does the playbook/instructions actually improve performance vs vanilla? Use when the user wants to test/benchmark/evaluate a custom skill or agent, validate that a playbook adds value, ask "is this skill worth keeping", "does this agent beat vanilla Claude", or capture an eval report under the artifact's own directory. Triggers on "/make-eval", "evaluate this skill", "run an eval", "benchmark X", "is this skill worth keeping", "does this playbook help", "test variant A vs B".
---

# make-eval

Designs and runs an empirical eval of a custom skill or agent, writes the report under the artifact's own directory (`<artifact>/evals/iteration-N/`).

The skill exists because:
1. Custom skills and agents accumulate over time and not all of them are pulling their weight.
2. Vibes-based "this feels useful" judgments are unreliable — measure.
3. Eval methodology has subtle gotchas (sample size, isolation, corpus design, scoring) that bite repeatedly. This skill captures the lessons so each new eval starts from the prior one's mistakes.

## When to invoke

- "Is this skill worth keeping?"
- "Does my custom subagent beat vanilla Claude on the same task?"
- "Test the impact of the X section in my SKILL.md"
- "Benchmark variant A vs variant B"
- The user wants to capture an eval as a reproducible artifact, not a one-off check.

## Choosing depth: lightweight vs full mode (decide BEFORE Phase 1)

The 5 phases below describe the FULL methodology. For evaluating well-formed real skills with no obvious safety concerns, a **lightweight variant is appropriate and recommended**. Iter-2 of the meta-eval (`evals/iteration-2/`) found that applying the full methodology to clean real skills **hurts** design quality — F1 (`commit`) and F3 (`actix-to-axum`) both showed vanilla outperforming with-skill at ~-0.5 on a ±5 scale. The skill's overhead exceeds its value-add when the artifact doesn't need adversarial framing.

**Use FULL mode when:**
- The artifact is synthetic / fictional / known-bad (advocates dangerous practices like `--force`, `--no-verify`, `commit credentials`).
- Safety, security, correctness, or compliance boundaries are at stake.
- The artifact has multiple internal sections worth ablating.
- A decision with real consequences ($ spend, deprecation, deployment) will follow.

**Use LIGHTWEIGHT mode when:**
- The artifact is a well-formed real skill / agent in active use.
- No obvious safety concerns in the artifact's docs.
- You want a quick directional read on "is this paying its keep".
- Budget is tight.

**Lightweight mode differences:**

| dimension | full | lightweight |
|---|---|---|
| 5-phase walkthrough | all 5 | phases 1, 3, 5 (skip 2 detailed setup, 4 detailed scoring) |
| anti-patterns | walk all 17 | check just 3 load-bearing: K≥3, no-symlinks-if-corpus, pre-declared rubric |
| conditions | multi-section ablation OK | binary A/B (with-skill vs no-skill) |
| hypotheses | safety AND efficacy frames | single hypothesis |
| design length | 1000–2000 words | cap at 500 words / 5–6 sections |
| scoring | auto-grader (plants + controls) | manual spot-check is fine (K still defaults to 10 — eyeballing 10 runs/cell is tractable) |
| sections required | TL;DR, conditions, fixtures, isolation, sample size, scoring, cost, anti-patterns avoided, report structure, limitations | TL;DR, conditions, fixtures, K, scoring, cost |

**Heuristic:** if you can describe the artifact's purpose in one sentence AND its docs contain no `--force`, `--no-verify`, "trust me", "always", or "just commit it" language, default to lightweight. Otherwise full.

## Five phases — walk through interactively

Don't skip phases — each one resolves a decision that shapes the next.

### 1. Design (interactive)

Pin down these 8 items before any setup. Use `AskUserQuestion` if anything is ambiguous. Capture each answer in the iteration's `README.md` as you go.

| # | item | typical answers |
|---|---|---|
| 1 | **Artifact under test** | path to a skill (`~/.claude/skills/<name>/SKILL.md`), an agent (`~/.claude/agents/<name>.md`), a hook script, a `CLAUDE.md` addition, a `settings.json` change, or any other Claude Code customization. The artifact type determines methodology — for hooks/CLAUDE.md/settings (not just skills+agents), load `references/advanced-methodology.md`. |
| 2 | **Hypothesis** | one specific claim, e.g. "the Hotspots section is load-bearing for review quality on Sonnet" |
| 3 | **Conditions** | A vs B (and maybe C). Typical: with-skill / no-skill; or full-playbook / ablated-playbook (specific section removed) |
| 4 | **Fixtures** | 2–4 concrete test cases. Either real-world queries (like session-search), or hand-crafted diffs with planted items + controls (like review) |
| 5 | **Models** | at minimum the model the artifact normally runs on; ≥2 models if model-agnostic |
| 6 | **K (runs per cell)** | **K=10 = default** — needed to resolve close rates on binary outcomes (distinguishes 80% vs 90%); K=6 = acceptable when cost-bound; K=3 = coarse, directional only (buckets to 0/33/67/100%, so 80% and 90% collapse together); K=1 = single-shot, no variance |
| 7 | **Isolation** | what data could poison the test? Recent transcripts about the artifact's design? The artifact's own evals dir? User's notes mentioning it? Plan to exclude. |
| 8 | **Context regime (warm vs cold)** | **Warm** (resumed, populated multi-turn context) is the DEFAULT. Real usage is warm: the artifact fires partway into a session that has already accumulated context, and many rules only earn their keep there — they fight **drift over a long session** ("stop adding logging/comments/abstraction after many turns", anti-nagging, post-compaction recall). A cold single-shot **under-measures** these: the model complies on turn 1 unprompted, so the rule looks redundant when it isn't. Warm runs accumulate context, then measure the per-turn slope (does the unwanted behavior creep in?), rule-present vs rule-absent — see Phase 3's warm-run mechanics. Use **cold** (single-shot, fresh context) only as a deliberate exception for a genuine one-shot choice with no drift component (e.g. "does the skill trigger on this query", "is this single output well-formed"). **Tell:** if the rule contains "default to", "stop adding", "keep it", or fights a tendency rather than a one-shot choice, it is a warm-regime rule — which is most of them. Load `references/advanced-methodology.md` for the three-regime detail. |

**Anti-pattern check:** before proceeding, walk `references/anti-patterns.md` and confirm none apply.

**Pre-specify the smallest worthwhile effect.** Before running, write down the threshold below which you would drop the candidate (e.g. "if total improvement < 0.5 on a 0–10 head-to-head scale, the skill isn't worth its overhead"). Without this you'll p-hack: try multiple endpoints, find one that moved, declare victory.

### 2. Setup (mechanical)

Create `~/.claude/{skills|agents}/<artifact-name>/evals/iteration-N/` (mirror existing iteration-N if present; bump to N+1 for new runs). Layout:

```
iteration-N/
├── README.md                    # methodology + verdict — fill incrementally
├── artifact-snapshot/           # frozen copy of artifact at eval time (critical)
│   └── <SKILL.md or agent.md>
├── fixtures/
│   └── <fixture-name>.md        # one file per fixture: task description + expected answer (planted items, expected hits, etc.)
├── prompts/
│   ├── <condition-A>_brief.md   # prompt template per condition
│   └── <condition-B>_brief.md
├── corpus/                      # OPTIONAL — if isolation requires curated dataset
│   └── build_corpus.sh
├── runs/
│   └── <fixture>/<condition>/<model>/run-<k>/output.md
└── aggregate.py                 # OPTIONAL — auto-graded scoring rollup
    benchmark.json               # produced by aggregate.py
```

Use templates in this skill's `templates/` dir as starting points:
- `templates/README.md` — README skeleton with `[FILL: ...]` placeholders
- `templates/vanilla_brief.md` — condition A prompt template
- `templates/playbook_brief.md` — condition B prompt template (injects the artifact snapshot)
- `templates/build_corpus.sh` — real-file-copy corpus builder

**Hard rule on corpus building (if isolation requires a curated dataset):** use **real file copies** (`cp`), NOT symlinks, NOT hard links across volumes. Reasons:
1. ripgrep skips symlinks by default → false-negative 0-hit results.
2. `readlink` on a symlink leaks the source path; a motivated subagent can walk to forbidden siblings.
3. Hard links fail with EPERM across APFS volumes on macOS (`/tmp` is on a different volume than `~/`).

**Snapshot the artifact:** `cp <artifact-path> iteration-N/artifact-snapshot/`. Without a snapshot, re-runs don't reflect the version that was tested.

### 3. Run (parallel batches)

Total runs = `K × |conditions| × |models| × |fixtures|`.

**Warm by default — do NOT run "the rest" in empty contexts.** Real usage is warm: the artifact fires partway into a session that has already done work. An empty-context run measures the artifact on a blank slate, where the model often does the right thing unprompted and the artifact looks redundant. That under-measures every drift-fighting rule. So the runs themselves must happen in *populated* context unless you've explicitly chosen cold for a genuine one-shot fixture (Phase 1, item 8).

**Warm-run mechanics:**
- Build a **context primer** per fixture: a realistic multi-turn lead-in that fills the context the way a real session would (several turns of related work, accumulated files, prior tool output), ending at the point where the artifact's behavior is tested. Keep the primer **identical** across conditions — it's part of the fixture, not the manipulation.
- **Size the primer to ~150k tokens by default.** This is the load-bearing number: a capable model (esp. Opus) handles an empty context almost trivially, so an artifact that looks valuable at 5k may be noise the model already absorbs — or, conversely, a rule that's redundant cold only starts paying off once context is full. ~150k is where real work happens (it's the ≈p75–p90 of typical session context and the explicit "must pull its weight past here" bar). Make the primer **realistic noise, not filler**: real prior turns, real files, real tool output related to the task — padding with lorem/irrelevant text doesn't reproduce the distraction pressure that makes context hard. Note the tail: ~14% of real turns run **200k+**, so for safety/correctness-critical artifacts add a second probe at ~250k. Cheap directional checks may drop to ~75–100k, but say so in the README — don't silently test at 10k and claim the artifact earns its keep.
- Drive it as a resumed/multi-turn session (prime the context, then issue the test turn), or hand the subagent a prompt that *reconstructs* the primer as prior context and then poses the test turn. Either way the test turn lands on a non-empty context.
- For drift rules, run the primer **long** (or to/through compaction) and measure the **per-turn slope** — does the unwanted behavior creep in over turns? — rule-present vs rule-absent, not just a single final-turn snapshot.
- Cold (single-shot, fresh context) is the **labelled exception**: use it only for the one-shot fixtures Phase 1 flagged, and say so in the README.

Spawn subagents **in parallel batches** via the Agent tool (multiple `Agent` calls in one assistant message).

**Isolation under a warm default:** fresh subagent contexts used to be the primary anti-poisoning mechanism, but warm runs deliberately populate context — so that protection is gone by design. The primer must be **clean** (no mention of the artifact, its design, or the hypothesis) and isolation shifts onto **corpus scoping** + forbidding out-of-corpus reads (Phase 2). Treat corpus scoping as load-bearing, not belt-and-suspenders, whenever you run warm.

For each run:
- `subagent_type: "general-purpose"` unless evaluating a specific subagent type
- Same toolkit across conditions (commonly: Bash, Read)
- Same query/task **and same context primer** across conditions — only the artifact (present/absent) differs
- Self-report metrics at the end (`--- METRICS ---` block)
- Save the agent's verbatim output + the Agent tool result's `tool_uses` and `total_tokens` to `runs/<fixture>/<condition>/<model>/run-<k>/output.md`

Batch size: 4–8 subagents per assistant message. Larger batches may hit rate limits.

**Token economy patterns (from iter-2 dogfood at `~/.claude/agents/evals/session-search/iteration-2/`):** when K is large or prompts are long, two patterns dramatically cut orchestrator-context cost. Use them by default for any non-trivial eval.

1. **Prompt path indirection.** Write the resolved prompt once to `/tmp/claude/eval-prompts/<name>.md`, then each Agent spawn becomes: `prompt: "Read /tmp/claude/eval-prompts/<name>.md and follow its instructions exactly. Return your output as the final response."` (~25 words). Saves ~600 words × K of outgoing tokens. Use for any prompt repeated verbatim across multiple runs.

2. **Subagent writes to disk, returns summary only.** For tasks where the subagent's output is long (>500 words — reviews, structured reports, full analyses), instruct the subagent to write to `/tmp/claude/<eval>-runs/<cell>/<run>/output.md` and return only a 2–3 sentence summary. Orchestrator never sees the bulk content; copy to durable storage at the end. Review iter-2 used this for 12 reviewers — saved ~24k tokens of incoming context.

Combined, a 24-run batch costs ~3k+3k tokens for the orchestrator instead of 50k+ inlined.

**Cost estimate before spawning:** rough Sonnet cost per run ≈ $0.05–$0.20 depending on tool count. K=10 × 2 cond × 2 models × 2 fixtures = 80 runs ≈ $8–16. Mention the estimate to the user before committing — and if cost-bound, drop K (10 → 6 → 3) before dropping conditions or fixtures.

### 4. Score

Two approaches — pick based on fixture design:

**Auto-graded** (review skill's pattern, scales to K=6+):
- Build fixtures with **plants** (items the artifact SHOULD flag) and **controls** (look-flag-worthy but intentional — true negatives).
- After each reviewer run, spawn one grader subagent that reads `(answer key, run output, scoring rubric)` and emits `grading.json` with per-item scores. The "answer key" is whatever the fixture defines as the correct response — planted issues to be caught, expected files to be found, etc.
- `aggregate.py` rolls up to `benchmark.json` with mean ± stdev per cell.
- See `~/.claude/skills/review/evals/iteration-1/` for a reference implementation.

**Manual spot-check** (session-search pattern, tractable up to ~K=10; beyond that prefer auto-grading):
- Inspect each run output. Score on the pre-declared rubric (structure / accuracy / wrapper handling / completeness / efficiency / brevity).
- Write scores directly into the README's results table.

**Two-tier (mechanical extract + strong verdict)** — the default whenever per-run scoring is *observable/binary* but the cross-cell decision is *interpretive*. This is the common shape for ablation evals ("is section X load-bearing?") and any keep/cut decision.
- **Layer 1 — extraction (cheap model, e.g. Sonnet), one per run:** read `(run output, rubric)` → emit an observable fact (`compliant: yes/no/unclear`, count, did-it-do-X). Mechanical on purpose: a strong model here only adds interpretation variance (drift — see anti-pattern #15). Grade **blind** — hide the condition label and shuffle, so the extractor can't infer the hypothesis.
- **Layer 2 — verdict (strong model, e.g. Opus), one per cell/condition-group:** read all of that cell's extracted facts (de-anonymized via a key the extractor never saw) → compute rates and classify against the **pre-declared threshold**. This is where judgment lives, at a fraction of the call volume (per-rule, not per-run).
- Why both: Sonnet rubrics *saturate* on subtle comparative calls (iter-2 meta-eval switched to an Opus verdict grader for exactly this); but using Opus for the per-run facts is wasteful and *less* reproducible. Splitting puts each model where it's strongest.
- Don't reach for two-tier when grading is pure-mechanical (plants/controls → just count: Layer 2 is optional) or pure-judgment (head-to-head design quality → there's no mechanical Layer 1).

For all three: **declare the rubric in the README before running.** Post-hoc rubrics are post-hoc rationalizations.

### 5. Verdict (interactive)

Fill in the README:
- TL;DR table with winner per dimension
- One-sentence verdict
- Notable observations (3–5 bullets)
- **Limitations** — be honest. K=1? Single model? Asymmetric prompts? Say it.
- Cost
- How to re-run

**Be honest about negative findings.** If the playbook doesn't help, say so. The point of the eval is signal, not justification.

## Beyond the default case — load on demand

The 5 phases above + lightweight/full toggle cover skills and agents at K=6–10 with head-to-head or auto-grader scoring. Load `references/advanced-methodology.md` if any of these apply:

- The artifact is a **hook** (evaluate as policy: TPR / FPR / latency, not instruction-following), a **`CLAUDE.md` addition** (evaluate always-loaded context cost), or a **settings change** (factorial design separating model/effort from prompt changes).
- You want a **cold-clean** baseline (subagents inherit your CLAUDE.md by default — true cold-clean needs `claude -p` with `settingSources` outside this skill).
- You care about **post-compaction behavior** (skills are capped at 5,000 tokens per skill / 25,000 tokens combined after compaction — a skill that helps in turn 3 may drop out at turn 30).
- You want **statistical claims** (McNemar for paired binary; paired bootstrap for continuous; never independent-sample t-test on paired data — K=3 paired ≈ K=10 independent).
- The artifact is an **auto-invoked skill** and you need to measure invocation precision/recall, not just effectiveness-when-invoked.

## Capturing the four strategic principles

This skill exists to enforce four practices that empirically separate good evals from vibes:

1. **Non-trivial context — populated AND planted, not either/or.** A fixture needs *both* (a) a realistically **populated context** (~150k tokens of real prior work — see Phase 3's primer sizing) so the artifact is tested under the distraction pressure of a real session, *and* (b) **plants + controls** (or known-noise queries) so you can score signal against true negatives. The two do different jobs: plants/controls give you something to measure; populated context makes the measurement *mean* something. An empty-context plants-only fixture answers "does the artifact help on a blank slate" — almost always trivially yes-or-redundant for a capable model, and not the question that matters. The Q2 (`actix-to-axum`) fixture in the session-search eval shows both together: the planted term appears in ~4 real discussions buried among 423 noise files. Toy problems on empty contexts don't reveal the artifact's actual behavior.

2. **Avoid poisoning** — under the warm default you deliberately give up fresh-context isolation, so the context **primer must be clean** (no mention of the artifact, its design, or the hypothesis) and corpus-scoping becomes the load-bearing anti-poisoning mechanism — add it whenever the artifact's design has been discussed in recent transcripts/notes. Real file copies, NOT symlinks. Forbid out-of-corpus reads in the prompt. The skill defaults to "ask about poisoning" in phase 1. (For the cold exception fixtures, fresh subagent context still does this work for free.)

3. **Large enough sample** — default **K=10** for any quantitative claim. K is a resolution knob and it coarsens fast on binary outcomes: K=3 only buckets to 0/33/67/100% (so 80% vs 90% are indistinguishable — the failure that set this default), K=6 to ~17-pt steps, K=10 to 10-pt steps. Drop to K=6 only when cost-bound, K=3 only for a directional read, K=1 for single-shot (labeled "directional only" in the README). Variance findings invisible at K=1: (a) review iter-1's K=6 revealed the Hotspots section *stabilizes* Opus behavior (stdev 0.21 → 0.06); (b) session-search iter-2's K=3 revealed the playbook clamps `sessions_returned` to 8.0 ± 0.0 while vanilla varies ±2 — output stabilization is the playbook's real value prop, hidden when you only have one sample per cell. Low K catches large qualitative gaps like these; only K=10 resolves close rates (80% vs 90%).

4. **Report goes under the artifact** — `~/.claude/<skills|agents>/<name>/evals/iteration-N/` keeps the eval co-located with the thing it evaluates. New iterations are versioned (iteration-1, iteration-2, ...). The README at iteration-N/ is the primary report.

## Resources

- `templates/README.md` — eval README skeleton
- `templates/vanilla_brief.md` — prompt template for the no-skill / no-playbook condition
- `templates/playbook_brief.md` — prompt template that injects the artifact snapshot as a directive
- `templates/build_corpus.sh` — real-file-copy corpus builder (do NOT use symlinks)
- `references/anti-patterns.md` — methodology bugs with concrete examples from prior evals — READ BEFORE DESIGNING
- `references/example-evals.md` — pointers to `review` and `session-search` evals as exemplars
- `references/advanced-methodology.md` — three regimes (cold-clean / configured-cold / warm), what-to-eval-by-artifact-type (hooks, CLAUDE.md, settings), statistical tests, power tables — load only when you need beyond the default case

## Exemplars

- **Gold standard:** `~/.claude/skills/review/evals/iteration-1/` — K=6, auto-graded, plants + controls, 2 models, ~$15–20.
- **Cost-efficient re-run (iter-2 dogfood):** `~/.claude/skills/review/evals/iteration-2/` — K=3, Sonnet only, ~$3.50. Confirms iter-1's load-bearing finding at 1/4 cost — a good cadence for ongoing SKILL.md regression testing.
- **Lessons-learned:** `~/.claude/agents/evals/session-search/iteration-1/` — K=1, manual spot-check, symlink-corpus failure mode preserved in round-1-failed/ outputs. Read the README for the "symlink + ripgrep = silent false negative" cautionary tale.
- **K=1 → K=3 variance dogfood:** `~/.claude/agents/evals/session-search/iteration-2/` — same setup as iter-1, K=3 reveals variance story K=1 missed (zero-variance hit count from playbook's hard cap; 16× lower token variance than vanilla).
- **Methodology iteration (rubric → head-to-head):** `~/.claude/skills/make-eval/evals/iteration-{1,2}/` — the meta-eval, with iter-1 demonstrating rubric saturation (Sonnet absolute rubric maxed out at 19.7/20 for both conditions, couldn't discriminate) and iter-2 fixing it via head-to-head Opus grader + hint-stripped fixtures + adversarial fixtures. **The finding that motivated this section:** full methodology helps on adversarial work (+0.44 avg) but slightly hurts on clean real skills (-0.50 avg). Hence lightweight mode.
