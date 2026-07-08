# session-search eval — iteration 1

Empirical evaluation of how much value the `session-search` agent's playbook adds over vanilla Claude with the same tools. The question: when I ask "find sessions discussing X", does spawning the `session-search` subagent (with its prescribed jq pipeline, wrapper-stripping, output shape) produce meaningfully better answers than running the same query through a generic `general-purpose` subagent with the same toolkit?

Date: 2026-05-27.

## TL;DR

| dim | vanilla wins | playbook wins | tie |
|---|:-:|:-:|:-:|
| accuracy (top-hit relevance) | | | ✓ |
| coverage (relevant sessions found) | | | ✓ (different subsets, overlap on canonical hits) |
| output structure | | ✓ (explicit Top-hit-detail section) | |
| token efficiency | | ✓ (~20% fewer output tokens) | |
| tool-call count | ✓ (~20% fewer calls) | | |
| wrapper / system-reminder stripping | | | ✓ (both succeeded) |

**Verdict: keep `session-search`, but recognize the value prop is invocation ergonomics + context isolation, NOT dramatically better answers.** For a one-off ad-hoc lookup, vanilla Claude is competitive. For repeated session-mining, the subagent's predictable shape + token efficiency + main-context budget savings win.

## Lesson from round 1 (load-bearing)

The playbook's prescription "use the Grep tool" caused both playbook agents to return **0 matches (false negatives)** in round 1, when the test corpus was built from symlinks. Ripgrep skips symlinks by default unless `--follow` is set, so `Grep` returned nothing. Vanilla agents picked `find -exec grep` instead (which transparently follows symlinks) and worked.

**Implication for playbook design:** over-prescriptive tool guidance can be a liability in unusual environments. Real `~/.claude/projects/` has real files, so this won't bite in production — but it's a cautionary point for any future custom agent whose playbook specifies a particular tool path.

Round 1 outputs are preserved under `runs/*/playbook-round-1-failed.md`. Round 2 (rerun against a real-file copy corpus) is the fair test that produced the TL;DR.

## How the eval is set up

### Conditions tested

- **A: vanilla** — `general-purpose` subagent. Given the task description + tools + scope constraint. No playbook.
- **B: with playbook** — `general-purpose` subagent. Same task description + scope, plus the full body of `agent-snapshot/session-search.md` injected as a directive.

Both conditions use Claude Sonnet (default for `general-purpose` subagents) and the same toolkit: Bash, Read, Grep, Glob.

Agent snapshot frozen at eval time: `agent-snapshot/session-search.md`.

### Fixtures (queries)

Two distinct query shapes designed to stress different dimensions:

- **`query-1-vpc-lattice.md`** — multi-word distinctive term. Real domain topic (AWS service-to-service networking). ~205 raw-grep matches in the corpus, of which ~8–10 are real user-driven discussion sessions.
- **`query-2-actix-to-axum.md`** — kebab-case identifier that **also matches a Claude Code skill name**, so it appears in every recent session's `<system-reminder>` skill listing. ~423 raw-grep matches but only ~4–6 real migration-discussion sessions. Designed specifically to stress-test the agent's noise filtering.

Ground truth (qualitative manual spot-check): `fixtures/query-{1,2}-*.md`.

### Isolation strategy (the user concern)

Both subagents are scoped to a curated corpus at `/tmp/claude/eval-corpus/`, containing **real file copies** of all `.jsonl` files from `~/.claude/projects/` modified BEFORE 2026-05-25. This prevents the subagents from reading transcripts that discuss `session-search` itself (the agent design discussion happened 2026-05-26 to 2026-05-27, the last 2 days).

The prompt explicitly forbids reading anywhere outside the corpus. Subagents have fresh contexts (no parent conversation memory), so even if a subagent ignored the instruction, it has no recall of this design discussion.

Corpus stats:
- 941 in-scope `.jsonl` files
- 91 project directories
- 377 MB total

**Why real-file copies (not symlinks or hard links):**
- Symlinks: ripgrep and Claude Code's `Grep` tool skip them by default → playbook condition false-negatives in round 1. Also, a subagent could `readlink` to discover the source path under `~/.claude/projects/` and walk to siblings (the user's concern about traversal-to-source).
- Hard links: fail with EPERM across APFS volumes on macOS — `/tmp` is on a different volume than the user's home.
- Real `cp` is the simplest reliable option. 377 MB is acceptable.

Build the corpus: `bash corpus/build_corpus.sh`.

### Matrix

2 queries × 2 conditions × **K=1 run per cell** = 4 runs (round 2). Plus 2 round-1 playbook runs preserved as a methodology lesson.

K=1 is a methodological weakness — see [Limitations](#limitations). Iteration 2 should bump to K≥3 per cell to get a variance estimate.

The prompt templates used by both subagents are in `prompts/`:
- `vanilla_brief.md` — for condition A
- `playbook_brief.md` — for condition B (interpolates the full agent file as a directive)

## Scoring

Qualitative + four hard metrics from the Agent tool result (`tool_uses`, `total_tokens`, `duration_ms`) and self-reported (`sessions_returned`, `files_examined`, `trickiest_thing`).

For each run we captured:

| metric | source | what it measures |
|---|---|---|
| `sessions_returned` | self-report | how many hits the agent surfaced |
| `tool_uses` | Agent tool result | round-trips to converge — lower = more efficient |
| `total_tokens` | Agent tool result | context cost (input + output) |
| structure | manual inspection | table vs prose; presence of Top-hit-detail section |
| wrapper stripping | manual inspection | for slash-command-opened sessions, is the opening cleaned? |
| top-hit accuracy | manual spot-check vs the actual jsonl files | are the top 1–2 hits really about the query? |

### Aggregate results (round 2 — fair test)

| dim | A1 vanilla VPC | B1 playbook VPC | A2 vanilla actix | B2 playbook actix |
|---|---:|---:|---:|---:|
| `sessions_returned` | 10 | 8 | 4 | 3 |
| `tool_uses` | 23 | 31 | 17 | 19 |
| `total_tokens` | 52k | 42k | 72k | 46k |
| duration | 5 min | 2 min | 3 min | 2 min |
| structure | table | table + Top-hit-detail | table | table + Top-hit-detail |
| wrappers stripped | yes | yes | yes | yes |
| top-hits relevant | 10/10 (1 borderline) | 8/8 | 3/4 (1 borderline) | 3/3 |

### Overlap analysis

- **Q1 (VPC Lattice):** substantial overlap on the canonical AWS-meeting and query-engine-deploy sessions. Vanilla surfaces 2 more borderline ones; playbook is more curated and demotes hits that were only in subagent results.
- **Q2 (actix-to-axum):** **partial overlap, not subset.** Both found the "stress test the actix-to-axum skill" session. Vanilla uniquely found the "update skill with findings" and "lost authcheck after axum conversion" sessions. Playbook uniquely found the canonical "Convert main.rs from actix-web to axum" migration-kickoff session and the later "revert axum, restore actix-web" session. Neither has full coverage — combined they'd cover more.

## Limitations

- **K=1 per cell.** No variance estimate. The 4 datapoints are directional, not statistically reliable. Bump to K≥3 for iteration 2.
- **Manual spot-check ground truth.** Real ground truth ("which sessions did the user discuss X in?") would require a human reading every candidate. We used a 1-pass spot-check of top hits.
- **Noise caveat asymmetric.** Both Q2 prompts include a caveat about the `actix-to-axum` skill-listing noise (because it's invisible without that hint and would make Q2 unfair). Q1 has no such caveat. This is intentional and documented but worth noting.
- **Two queries is a small sample.** They were chosen for diversity (multi-word vs identifier; distinctive vs noisy), but the result may not generalize to other query shapes (e.g. very short tokens, regex-like patterns, terms used in many contexts).
- **Vanilla model competence varies.** Sonnet today handled both vanilla runs well. A weaker model might benefit more from the playbook. Cross-model comparison is a candidate for iteration 2.

## How to re-run

1. (Optional) edit `~/.claude/agents/session-search.md` if testing a new playbook variant. Snapshot it: `cp ~/.claude/agents/session-search.md agent-snapshot/session-search.md`.
2. Rebuild the corpus: `bash corpus/build_corpus.sh`. Adjust `CUTOFF` in the script if you want a different exclusion window.
3. Spawn 4 (or 4×K for K>1) `general-purpose` subagents in parallel via the Agent tool. Use `prompts/vanilla_brief.md` and `prompts/playbook_brief.md` as templates. Parameterize each with `{QUERY, CUTOFF, OPTIONAL_NOISE_CAVEAT}`.
4. Save each agent's final output to `runs/<query-dir>/<condition>.md`. Save the Agent result's `tool_uses` and `total_tokens` either at the top of the output file or in a separate metrics block.
5. Manually spot-check the top 1–2 hits of each agent against the actual files in the corpus for accuracy.
6. Update the aggregate results table in this README with the new comparison.

For iteration 2+, create `iteration-2/` next to this dir, copy `prompts/` and `fixtures/` (or rewrite if updating the test set), update `agent-snapshot/`, and re-run.

## Layout

```
session-search/iteration-1/
├── README.md                       # this file
├── corpus/
│   └── build_corpus.sh             # builds /tmp/claude/eval-corpus/ from ~/.claude/projects/
├── agent-snapshot/
│   └── session-search.md           # frozen agent under test at eval time
├── fixtures/
│   ├── query-1-vpc-lattice.md      # query 1 description + ground truth notes
│   └── query-2-actix-to-axum.md    # query 2 description + ground truth notes
├── prompts/
│   ├── vanilla_brief.md            # template for condition A
│   └── playbook_brief.md           # template for condition B
└── runs/
    ├── query-1-vpc-lattice/
    │   ├── vanilla.md              # A1 output + metrics
    │   ├── playbook-round-1-failed.md  # B1 round 1 (symlink corpus, false negative — kept as lesson)
    │   └── playbook-round-2.md     # B1 round 2 (fair test)
    └── query-2-actix-to-axum/
        ├── vanilla.md              # A2 output + metrics
        ├── playbook-round-1-failed.md  # B2 round 1 (false negative)
        └── playbook-round-2.md     # B2 round 2 (fair test)
```

## Notable observations from iteration 1

- **Round 1's false negatives were caused by the *corpus*, not the *playbook*.** Symlinks + ripgrep is a known anti-pattern. The playbook itself works fine on the real-file corpus. Iteration 2 should use real-file copies from day 1.
- **Playbook output is more structured, vanilla output is more thorough.** Playbook agents capped at 8 hits per the spec and produced a tight Top-hit-detail section. Vanilla agents went to 10 hits and included more incidental context. Different tradeoffs; neither obviously better.
- **Both conditions correctly stripped slash-command and system-reminder wrappers** (the patch we shipped pre-eval). Wrapper-cleanliness is no longer a differentiator.
- **Playbook is ~20% more token-efficient but uses ~20% more tool calls.** The jq + Grep + count + content sequence in the playbook adds round-trips but pays back in tighter output. Net: roughly even on cost.
- **Coverage gap on Q2.** Neither condition found *all* the actix-to-axum migration sessions. Combining their hits gives better coverage than either alone — argues for a meta-strategy where two agents fan out with different prompts.

## Cost

~$0.50–$1 total across 6 subagent runs (~280k tokens at Sonnet rates). 5–10 min wall-clock per round (parallel agents).
