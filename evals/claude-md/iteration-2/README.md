# CLAUDE.md minimalism cluster — iteration 2 (WARM)

**Artifact:** `~/.claude/CLAUDE.md` minimalism cluster — `simple`, `shortest`, `comments` (default ZERO), `logging` (default none).
**Question:** iter-1 was cold and said these were redundant. Are they load-bearing in a **warm** (long, accumulated-context) session — the regime they were written for (drift after many turns; "a future reader won't have *our context*")?
**Date:** 2026-06-03
**Verdict in one line:** **Drift did NOT reproduce in this harness — and the model articulated the anti-comment philosophy unprompted even with the cluster removed. But this synthetic warm harness does not reproduce the user's real drift conditions, so it is NOT a basis to cut. Recommendation: KEEP.**

## Method
- 2 conditions: **full** (cluster present) vs **ablated-min** (the 4 rules removed; sibling code-standard rules kept). K=4 → 8 sessions.
- Each session = a **12-turn `claude -p --resume` chain**, cold-clean (`--setting-sources ""`), Opus, system prompt injected at turn 1 and carried across resumes (verified: resumed turns retain both context and the injected rule).
- Turns are **discussion-heavy** (design back-and-forth that builds shared context, never mentioning comments/logging), with **code turns at 3, 6, 9, 11** (increasing context depth) and a **turn-12 rationale probe**.
- Metric: per-code-turn comment lines / log statements / fn-count (helper proliferation), looking for an upward **slope** with accumulated context in ablated vs flat in full.
- Cost: 96 Opus calls ≈ $24.

## Results — mean per code turn (t3 → t11 = low → high accumulated context)

| metric | cond | t3 | t6 | t9 | t11 |
|---|---|---|---|---|---|
| comment lines | full | 0 | 0.5 | 0 | 0.5 |
| comment lines | ablated | 0 | 0 | 0 | 0 |
| log statements | full / ablated | 0 | 0 | 0 | 0 |
| fn-count | full | 1 | 1 | 1.25 | 1.5 |
| fn-count | ablated | 1 | 1 | 1 | 1 |
| doc-comment lines | both | 0 | 0 | 0 | 0 |

**No drift.** Comment/log counts stay at ~0 in BOTH conditions across all depths — no upward slope. If anything, ablated ran *lower* than full (0 vs 0.5 comments; flat vs rising fn-count), the reverse of the hypothesis (noise at K=4).

**Rationale turn (turn 12) — the striking part:** even in the **ablated** sessions (rules removed), the model wrote zero comments/logs AND justified it with the exact philosophy of the deleted rule, unprompted:
> "the decisions live in our conversation, the commit message, and ideally a test name; a code comment would just rot … none of these had a hidden invariant a careful reader would trip over."

It even named "the 'default to zero' rule" as the aim — while that rule was **not** in its context (ablation verified: `ablated-min.txt` contains 0 matches of the comments rule; memory empty; `--setting-sources ""`). So this is the model independently reconstructing the principle, not leakage.

## Interpretation (honest)
Two non-exclusive explanations, and I can't separate them with this harness:
1. **Opus 4.8 has internalized minimalism** — it writes comment-free, log-free, single-function code and reasons about *why* even without the rule. On this model the cluster may genuinely be near-redundant.
2. **The harness doesn't reproduce the real drift conditions.** What's missing vs the user's actual sessions: (a) **no surrounding commented code to "match"** — the base CC system prompt says "match surrounding comment density", and the `comments` rule's override (#"Ignore match-surrounding-density … this code is over-commented") only bites when there IS commented legacy code in context, which greenfield function-writing never supplies; (b) no **compaction** events; (c) only 11 short, single-topic turns vs real multi-hour, multi-topic sessions; (d) read-only (no real file edits / refactors of existing code).

## Recommendation: KEEP the cluster
- I have **no empirical basis to cut** these: the cold eval can't see drift-prevention rules, and this warm eval failed to *reproduce* the drift it was meant to measure. Absence of reproduction ≠ proof of uselessness.
- The user's **lived experience** that Claude drifts after many turns is the stronger evidence here, and the rules are cheap (a few lines).
- Sharpest insight: the **"ignore match-surrounding-density" override** is precisely the part whose value lives in the condition this harness lacks (real commented code in context). That one earns its keep on real edits even if greenfield probes can't show it.
- A faithful iter-3 would need: real repo context with existing commented code, much longer sessions, and ideally post-compaction state — expensive and hard to synthesize. Lived experience is a reasonable stopping point.

## Limitations
- Synthetic warm ≠ real warm (see Interpretation #2). This is the dominant caveat.
- Opus 4.8 only. Older / smaller models likely drift more — the rule may be more load-bearing there.
- K=4; comment counts near the floor, so slope resolution is limited (can't distinguish "0" from "rarely 0.5").
- fn-count is a crude helper-proliferation proxy.
