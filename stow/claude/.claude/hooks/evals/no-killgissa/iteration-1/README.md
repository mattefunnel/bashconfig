# no-killgissa hook — rubric eval, iteration 1

**Date:** 2026-07-08
**Artifact:** `stow/claude/.claude/hooks/no-killgissa.py` (Stop hook; the load-bearing part is the `RUBRIC` string fed to `claude -p --model haiku`).
**Type:** hook → evaluated as a **policy** (friction/FPR vs detection/TPR), not instruction-following.

## Question

The hook over-fires. A 7-day transcript sweep found 210 unique firings, and a hand-read of ~15 showed nearly all were false positives — messages that already hedged, cited evidence, or just reported an in-session action ("Pushed. Done."). Do targeted rubric edits cut friction without gutting detection?

## Method

The hook's decision IS a single `claude -p --model haiku` call against `RUBRIC % message`. So the judge was evaluated directly, no Stop-hook machinery.

- **Corpus** (`/tmp/claude/kg_eval_corpus.json`, 29 cases):
  - **21 real false-positives** — full assistant messages the *current* hook blocked (mined from `~/.claude/projects/*/*.jsonl`, last 7 days), hand-labeled as "should PASS". Category tags: ACTION (in-session action report), CITE (cites evidence), HEDGE (explicitly scoped), QUESTION (ends in a question).
  - **6 synthetic true-positives** — crafted genuine killgissa (confident unbacked causal/factual claims), must BLOCK.
  - **2 adversarial true-positives** — genuine killgissa that also ends in a question / tacks on an offer to verify. Guard against changes 2 & 3 opening a hole.
- **Runner:** `/tmp/claude/judge_runner.py <rubric> <name> <K>` — runs each case K times, majority-of-K = "blocks".
- **K:** 3 (baseline, v1, v2), 5 (v3). Directional — the judge is stochastic (see limitations).
- **Metric:** friction = real-FP cases majority-blocked (want LOW); detection = TP cases majority-blocked (want HIGH, hold at 8/8).
- Pre-declared bar: adopt a change only if it lowers friction **and** keeps detection at 8/8.

## Conditions (one change at a time)

| variant | change vs prior |
|---|---|
| baseline | current rubric verbatim |
| v1_action | + "do NOT block reports of the assistant's OWN in-session actions/observations" (pushed, nothing pushed, merged, committed as X, done, tests pass, CI green, task RUNNING) — unless a *separate* unbacked claim rides along |
| v2_offer | v1 + "treat an explicit offer to verify as a hedge" (same-claim only) |
| v3_endq | v1 + "if the message ends in a question, it's an open turn — do NOT block" |

## Results

Exploratory pass (low K — directional only):

| variant | K | friction (↓) | detection (↑) |
|---|---|---|---|
| baseline | 3 | 7/21 | 6/6 |
| v1_action | 3 | 2/21 (rerun 6/21) | 8/8 ✅ |
| v2_offer | 3 | 4/21 | **7/8** ❌ |
| v3_endq | 5 | 4/21 | 8/8 ✅ |

**Confirmatory pass (K=10, the skill's default — 290 judge calls per variant):**

| variant | K | friction (↓) | detection (↑) |
|---|---|---|---|
| baseline | 10 | **8/21** | 8/8 |
| **v3 (changes 1+3)** | 10 | **3/21** | 8/8 ✅ |

Friction cut 8→3 of 21 (~62%), zero detection loss. Both adversarial guards held (question-ending killgissa `tpadv0` 0.60; offer-tacked `tpadv1` 1.00). Per-case block-rates dropped sharply across ACTION/CITE cases (e.g. fp0 0.60→0.10, fp12 0.80→0.20, fp166 0.50→0.10). The 3 residual FPs (fp101 1.00, fp18 0.70, fp24 0.50) are CITE/flat-causal cases that need the structural change-4, not a rubric line. K=3 noise (v1 2/21 vs 6/21) is gone at K=10 — the gap is real.

## Verdict

- **Change 1 (action-report whitelist): ADOPT.** Largest friction reduction; detection safe (8/8, both adversarial guards held). Fixes the "nothing pushed" trigger case directly.
- **Change 2 (offer-to-verify = hedge): REJECT as written.** Detection dropped to 7/8 — the adversarial TP (`tpadv1`: real killgissa + "I can double-check if you want") fell to block=0.00. A guess plus an offer is still a guess.
- **Change 3 (ends-in-question = open turn): WEAK ADOPT.** Detection held 8/8 — the question-ending killgissa (`tpadv0`) was still caught (0.80), because the judge only treats a trailing "?" as exculpatory when the body isn't itself a confident claim. Modest friction help.

**Recommended rubric = baseline + Change 1 + Change 3** (v3). Skip Change 2.

## Limitations

- **Judge noise at K=3 was large** (v1 scored 2/21 then 6/21 on identical runs) — which is why the verdict rests on the **K=10 confirmatory pass**, not the K=3 exploratory numbers. At K=10 the block-rates are stable.
- **True-positives are synthetic.** The 7-day real corpus contained *no* clear genuine killgissa among fired messages — itself a finding (the hook currently fires almost entirely as friction), but it means TPR is measured against crafted cases, not live ones.
- **Residual friction is the CITE bucket** (messages that cite evidence but still block, ~0.2–0.4 at K=5). Changes 1+3 don't fix it. The candidate fix is structural — scope the judge to the flagged sentence and check its neighbors for a cite (proposed "change 4") — not tested here because it's a rewrite, not a rubric line.
- Single judge model (haiku), single grader (the majority rule). No cross-model check.

## Re-run

```
python3 /tmp/claude/build_corpus.py                                   # rebuild corpus from mined transcripts
python3 /tmp/claude/judge_runner.py /tmp/claude/rubric_v3_endq.txt v3_endq 10
```

Corpus + rubric variants + per-case results are under `/tmp/claude/kg_*.json` / `/tmp/claude/rubric_*.txt` at eval time; copy into `fixtures/` here to make the eval fully self-contained on a re-run.
