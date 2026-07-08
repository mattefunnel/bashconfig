# Comments rule, editing a heavily-commented file — iteration 3

**Artifact:** `~/.claude/CLAUDE.md` comments cluster (`Comments: default to ZERO` + the **"ignore match-surrounding-density"** override, snapshot lines 107–114).
**Question:** iter-1 (cold) and iter-2 (warm, greenfield) both failed to show the comments rule is load-bearing — but neither supplied the condition the override was written for: **a heavily-commented existing file being edited**. Does the rule matter THEN?
**Date:** 2026-06-03
**Verdict:** **YES — reproduced.** Editing a real comment-saturated meld-api file, the model WITHOUT the rule sometimes matches the surrounding heavy comment style; WITH the rule it never does. The comments rule is load-bearing in this (realistic) condition. **KEEP confirmed, now with positive evidence.**

## Method
- **Fixture:** real copy of `meld-api/.../splitCombine/PartitionDistributedQuery.ts` — 847 loc, **95 inline `//` explanatory comments** (account names, Slack links, commented-out experiments). The densest inline-comment file in meld-api.
- **Conditions:** full (comments cluster present) vs ablated-comments (lines 107–114 removed; rest of CLAUDE.md identical). Cold-clean `claude -p --setting-sources ""`, Opus, **`--allowedTools "Read Edit" --permission-mode acceptEdits`** — the model edits a fresh per-cell copy of the file in place. K=5.
- **Task (rule-neutral):** add `effectiveScalingFactor(accountId, sourceType, calculatedRpm)` — base factor lookup, source-type weighting via the existing helper, clamp to `[0.1, 1.0]`, empty-account fallback. ~10 lines with branches + magic-number clamp = genuine opportunity to comment.
- **Metric (deterministic):** diff edited vs original; count `//` comment lines in the ADDED lines only.

## Results (full K=5, ablated K=15)
| condition | mean comment lines added | drift rate | per cell |
|---|---|---|---|
| full (rule present) | **0.0** | **0/5** | [0,0,0,0,0] |
| ablated (rule removed) | **0.67** | **6/15 (40%)** | [0,0,1,2,0,0,0,2,3,0,0,1,0,1,0] |

One-sided and stable: **full never drifts (0/5); ablated drifts ~40% of the time (6/15).** Added code length was identical (~9–13 lines both arms) — the difference is purely explanatory comments. The K=15 ablated arm confirms the K=5 directional read (2/5 → 6/15, both ≈40%).

**Side-by-side (k4), the clean demonstration** — same logic, comments are the only delta:
- ablated: `// Combine an account's base scaling factor with the source-type row weighting, / // clamped to a sane range. Heavier rows (inflated rpm) shrink the effective factor.` above the function.
- full: identical function body, no comment.

## Round 1 (recorded, fixture-design lesson)
The first probe asked for a **one-line** function (`return MAP[id] ?? DEFAULT`). Both arms scored 0/0 — a one-liner needs no comment in any regime, so the probe couldn't discriminate. Lesson: a comment-drift probe must request **non-trivial** code (branches / magic numbers / an edge case) or there's nothing to comment. Round 2 (above) fixed this.

## Interpretation
This is the condition iter-1 (cold, greenfield) and iter-2 (warm, greenfield) structurally could not reproduce: there was no surrounding commented code to match. Supply it — a real comment-heavy file + a non-trivial edit — and the drift appears without the rule and vanishes with it. The **"ignore match-surrounding-density" override** is doing exactly its job.

The effect is **probabilistic** (≈40% of ablated runs drift, 6/15 — not every run) but **one-sided and mechanistically clean** (full=0 always). The rule's value is preventing that ~40% drift on real edits — which is precisely the lived-experience complaint that motivated it.

## Limitations
- Ablated arm extended to K=15 (drift rate pinned at 6/15 ≈ 40%); full arm left at K=5 (stable 0/5 — all-zero, no variance to resolve).
- One file, one change shape. Bigger/refactor edits of commented code would likely drift more.
- Opus 4.8 only.
