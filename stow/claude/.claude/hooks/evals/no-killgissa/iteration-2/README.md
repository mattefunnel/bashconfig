# no-killgissa hook — residual friction, iteration 2

**Date:** 2026-07-08
**Artifact:** `stow/claude/.claude/hooks/no-killgissa.py` (rubric).
**Builds on:** iteration-1 (adopted changes 1+3 → friction 8→3 of 21 at K=10, detection 8/8).

## Question

After iter-1, 3–4 real messages still block that shouldn't. What are they, and can a rubric clause fix them without opening a detection hole?

## The residual cases (read in full)

- **fp101** — "Committed as `de573ee`. ... That sources the real stage config from dip." Action report (exempt) PLUS a flat unbacked claim about what `make synth-stage` does. Blocks 1.00. **This is arguably a CORRECT block** — the "separate unbacked claim rides along" carve-out firing as designed. Left alone.
- **fp18 / fp24** — code-reasoning messages. The conclusion is derived from file:line refs / traced call paths quoted *in the same message* (`DataPrepSqsConsumer.ts:103`, `line 222/255`); fp24 also hedges explicitly ("I have **not** checked each stack"). But individual sentences read flatly ("This is a live production path, not hypothetical") and the judge latches onto those. These are the genuine friction.

## Change tested (change 5: code evidence = citation)

Added a clause: a conclusion DERIVED from file:line refs / quoted code / a traced call path is backed (do not block), BUT merely NAME-DROPPING a file without a trace is not. Two adversarial name-drop TPs added to guard the loophole.

## Results (K=10, expanded corpus: 21 FP + 10 TP)

| variant | friction (↓) | detection (↑) |
|---|---|---|
| v3 (iter-1 applied) | 4/21 | 10/10 |
| v5 (+ code-cite clause) | 2/21 | 10/10 |

Both name-drop guards (tpnd0, tpnd1) blocked at 1.00 — the clause did NOT become a loophole.

## Verdict: DO NOT SHIP v5. Keep v3.

- The case v5 was built to fix (**fp24**) got **worse**, not better: 0.50 → 0.70. The clause failed at its actual purpose.
- The whole friction delta (4→2) is **inside the judge's noise band**: iter-1 saw v1 swing 2/21 ↔ 6/21 across identical K=3 runs; even at K=10, fp18/fp24/fp158 sit at 0.40–0.70 (near the 0.50 decision boundary). No clean signal that v5 > v3.
- More rubric prose is showing diminishing/negative returns.

## What would actually fix it

The residual friction is the judge wavering at its decision boundary on genuinely mixed messages (hedge + flat assertion + code trace all in one long message). The lever is **structural, not prose**: pass the judge only the flagged sentence plus its immediate neighbors, or split the message into claims and judge each — so a flat sentence isn't read in isolation from the citation three lines down. That's "change 4", deferred: it's a code change to `last_assistant_text` / the call shape in `no-killgissa.py`, not a rubric edit, and wants its own eval iteration.

## Re-run

```
python3 /tmp/claude/build_corpus.py
python3 /tmp/claude/judge_runner.py /tmp/claude/rubric_v5_codecite.txt v5 10
```
