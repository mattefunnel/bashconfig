# [ARTIFACT_NAME] eval — iteration [N]

Empirical evaluation of `[ARTIFACT_PATH]` (type: skill | agent).

**Hypothesis:** [ONE_SENTENCE_CLAIM — e.g. "the Hotspots section in SKILL.md catches more code-standard violations than no-Hotspots"]

Date: [ISO_DATE].

## TL;DR

(Fill in after running.)

| dim | A wins | B wins | tie |
|---|:-:|:-:|:-:|
| [DIM_1 — e.g. accuracy] | | | |
| [DIM_2 — e.g. token efficiency] | | | |
| [DIM_3 — e.g. tool-call count] | | | |

**Verdict:** [ONE_SENTENCE — be honest about strength of evidence].

## Conditions

- **A: [NAME_A]** — [WHAT_IT_IS]
- **B: [NAME_B]** — [WHAT_IT_IS, AND THE EXACT DIFFERENCE FROM A]

Artifact snapshot: `artifact-snapshot/[FILE]` (frozen at eval time).

## Fixtures

- `fixtures/[FIXTURE_1].md` — [ONE_LINE_DESCRIPTION + WHY_THIS_FIXTURE]
- `fixtures/[FIXTURE_2].md` — ...

Each fixture file documents: query/scenario, expected ground truth, difficulty notes.

## Isolation

[Describe what could poison the test and how it's prevented.]

Example: "Both subagents are scoped to a curated corpus at `/tmp/claude/eval-corpus/`, containing real file copies of `~/.claude/projects/*.jsonl` modified BEFORE [CUTOFF_DATE]. This prevents reading transcripts that discuss the artifact's design (which happened on [DESIGN_DATES]). Subagents have fresh contexts so cannot access this conversation."

Build the corpus: `bash corpus/build_corpus.sh`.

## Matrix

[Q] queries × [C] conditions × [M] models × **K=[K] runs per cell** = [TOTAL] runs.

[IF K<3: "K=[K] is directional only — no variance estimate. Bump to K≥3 in iteration [N+1]."]

Reviewer briefs in `prompts/`.

## Scoring (pre-declared — declared before running)

For each run, capture:
- `sessions_returned` / equivalent — how many hits
- `tool_uses` — from Agent tool result
- `total_tokens` — from Agent tool result
- structure / wrapper handling / [other qualitative dimensions]

For each fixture, score each run on:
- [Rubric dim 1, e.g. "0–2 for structure: 0=prose, 1=loose list, 2=ranked table with all fields"]
- [Rubric dim 2]
- ...

[If using auto-grader: describe grading.json schema and aggregate.py output.]

## Results

(Fill in after running.)

| metric | A1 | B1 | A2 | B2 | ... |
|---|---:|---:|---:|---:|---:|
| `sessions_returned` | | | | | |
| `tool_uses` | | | | | |
| `total_tokens` | | | | | |
| ... | | | | | |

[For K≥3: report as mean ± stdev.]

## How to re-run

1. (Optional) edit `[ARTIFACT_PATH]` if testing a new variant; resnapshot: `cp [ARTIFACT_PATH] artifact-snapshot/`.
2. [If corpus] Rebuild: `bash corpus/build_corpus.sh`. Adjust `CUTOFF` in the script if needed.
3. Spawn [TOTAL] `general-purpose` subagents in parallel batches via the Agent tool, using `prompts/[A]_brief.md` and `prompts/[B]_brief.md` templates. Parameterize per `{QUERY, CUTOFF, OPTIONAL_CAVEAT}`.
4. Save each output to `runs/<fixture>/<condition>/<model>/run-<k>/output.md`.
5. Score (manual rubric in this README, or `python3 aggregate.py` if auto-graded).
6. Update TL;DR table above.

For iteration [N+1], create the next iteration dir, copy `prompts/` and `fixtures/` (or rewrite if updating the test set), update `artifact-snapshot/`, and re-run.

## Layout

```
iteration-[N]/
├── README.md                    # this file
├── artifact-snapshot/           # frozen artifact under test
├── corpus/                      # if applicable
│   └── build_corpus.sh
├── fixtures/                    # one .md per fixture
├── prompts/                     # one .md per condition
├── runs/                        # one output.md per (fixture, condition, model, k)
└── aggregate.py (optional)      # produces benchmark.json
```

## Notable observations

(Fill in after running — 3–5 bullets of what was non-obvious.)

## Limitations

(Fill in honestly. K=1? Single model? Asymmetric prompts? Manual spot-check rather than auto-grade? Sample size of fixtures? Say it.)

## Cost

[Estimate before running; report actual after.]
