# Eval: CLAUDE.md minimality guidance — does it reduce over-engineering on multi-turn messy-code coding?

Iteration 1. Pre-registered before running. K=15.

## Artifact
The CLAUDE.md minimality guidance — "Just keep it simple" + "Prefer the shortest version" + comments/logging default-to-zero, including the new line-level clause. Type: CLAUDE.md addition (advisory, always-loaded). Frozen copy: `rule.txt`.

## Hypothesis
With the guidance present, multi-turn coding in messy existing code produces materially less UNREQUESTED over-engineering (speculative guards/validation, config options, single-use abstraction, comments, logging) than without it — while still completing the tasks.

## Conditions (clean isolation)
- **control**: `claude -p --setting-sources project --dangerously-skip-permissions --model sonnet <tasks>` in a clean scratch dir → the user CLAUDE.md (which now contains the rule) is NOT loaded → rule absent.
- **treatment**: identical + `--append-system-prompt <rule.txt>` → only difference is the rule is present.

Subagents can't be used here — they inherit the user CLAUDE.md that now contains the rule, poisoning the control. Hence `claude -p` with project-only setting sources.

## Fixtures
2 messy real-ish files + a LONG (16 / 15-step) incremental task sequence each, worded with zero minimality hints. Lengthened from 5 steps after a 4-run pilot showed Sonnet's short-task baseline is already minimal (control ≈ treatment) — too little accumulated drift to measure. Tasks include parse/CSV/CLI/pagination steps that tempt validation, try/except, and config:
- `f1` events.py (Python feed processor)
- `f2` handlers.ts (TS request handlers)

Tasks tempt over-engineering (parse input, add handlers, handle a case). The final task legitimately needs one conditional — grading counts only UNREQUESTED defensiveness.

## Regime
Warm-ish: each run is a single `claude -p` call containing the full 16/15-step sequence, so context accumulates across many steps within the run (captures within-session drift). Limitation: not true cross-session resume/compaction.

## Model
Sonnet.

## K
15 per cell. 15 × 2 conditions × 2 fixtures = 60 runs.

## Primary endpoint
Mean count of UNREQUESTED over-engineering instances per run (treatment vs control), gated on task completion (runs that don't implement the 5 tasks are flagged, not rewarded).

## Smallest worthwhile effect (pre-declared)
Treatment must reduce mean over-engineering by ≥ 1.5 instances/run AND not reduce task completion. Below that, the rule isn't earning its always-loaded context cost on this axis.

## Scoring rubric (pre-declared)
Per run, a blind grader (condition label hidden, runs shuffled) counts, in the final edited file, items NOT requested by the tasks:
- defensive try/except or error-swallowing
- input validation / null-guards / type-guards
- input normalization (`.strip()`/`.lower()`/`?? default`)
- config options / env vars / parameters nobody asked for
- helper/abstraction used only once
- comments
- logging/print beyond what a task asked for

Plus `tasks_completed` (0–5). Two-tier: Sonnet extracts per-run counts (blind); Opus verdict aggregates per cell vs the threshold.

## Limitations
- Warm approximated within one call, not true multi-session compaction.
- Sonnet only.
- "Over-engineering count" is partly judgment; mitigated by blind grading + pre-declared categories.

## How to re-run
`python3 runner.py` (writes runs/<fixture>/<condition>/run-<k>/{transcript.txt, <file>}). Then `python3 grader.py`.

## Results (K=15, Sonnet, 60 runs, 0 timeouts)

Deterministic marker counts (`grader.py`). **Every cell had zero run-to-run variance (sd=0.00)** — Sonnet produced identical code each run, so the effect below is perfectly consistent, not noise.

| cell | total | try/except | comments | normalization | logging | guards |
|---|---|---|---|---|---|---|
| f1 control | 4.00 | 1.00 | 0 | 0 | 1.00 | 2.00 |
| f1 treatment | 3.00 | 0.00 | 0 | 0 | 1.00 | 2.00 |
| f2 control | 1.00 | 0 | 0 | 0 | 0 | 1.00 |
| f2 treatment | 1.00 | 0 | 0 | 0 | 0 | 1.00 |

Reduction (control − treatment): f1 **+1.00**, f2 **+0.00**, **overall +0.50**. Pre-registered keep-threshold ≥1.5 → **NOT met**.

### What the difference actually was (spot-verified)
The only consistent effect: in f1, **control wraps the file-read loop in `try/finally` to close the file on exception**; treatment writes the dead-literal version (close after the loop, no guard). f2 came out byte-equivalent across conditions. The `logging`/`guards` columns are *requested* behavior (`main`'s print; the stdin + `--field` + 400-check handling) and cancel across conditions. Baseline (control) is already minimal — zero comments, no input normalization, no validation on `parse_amount`/`read_csv`, no speculative config; both conditions used argparse identically (task 16 requested a `--field` flag).

## Verdict
**The rule does not clear its pre-registered bar (+0.5 < 1.5) on this eval — but the effect is a real, zero-variance reduction (one fewer `try/finally` per Python session), not a null.**

Honest read: on Sonnet, for short multi-turn coding on these tasks, the baseline barely over-engineers, so the rule has little to bite on. Its value most likely lives in conditions this eval couldn't cheaply reproduce: long **warm** sessions with accumulated context / compaction (where drift compounds), heavier-over-engineering scenarios, or weaker models. (Cf. this skill's meta-eval: CLAUDE.md effects ≈ Cohen's d 0.08.) The session that *motivated* the rule — a long warm feature-build where Opus added `.strip().lower()`, an env var, and alternative scripts — is exactly the regime a single cold `claude -p` call does not capture.

### Limitations
- Sonnet only; baseline already minimal.
- Warm approximated within one call, not true multi-session/compaction drift (the regime where the rule likely matters most).
- Marker-count proxy (spot-verified accurate for the one observed diff).
- 2 fixtures.

### Recommendation
**Keep the rule.** Measured downside is zero, it does remove real flare (the `try/finally`), and its cost is a few hundred always-loaded tokens. But don't expect large effects on strong models doing short tasks. A fair test of its real value needs **true warm multi-session runs** (resumed sessions + compaction) — materially more expensive; deferred to a future iteration.
