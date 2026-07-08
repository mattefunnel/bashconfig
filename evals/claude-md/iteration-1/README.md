# CLAUDE.md section ablation — iteration 1

**Artifact:** `~/.claude/CLAUDE.md` (snapshot in `artifact-snapshot/`, 239 lines at eval time)
**Question:** which behavioral sections are pulling their weight? (which can be removed?)
**Date:** 2026-06-03
**Verdict in one line:** of 19 behavioral rules tested, **6 are load-bearing**, **7 are redundant** (Opus already complies without them), **3 fail even when present**, and **3 are framing-confounded / inconclusive**. Plus duplicates and reference bloat to trim (no eval needed).

## Method

Leave-one-out ablation, cold-clean, K=5, Opus.

- For each rule: **FULL** = entire CLAUDE.md injected; **ABLATED** = CLAUDE.md with exactly that rule's lines removed. Both injected via `claude -p --setting-sources "" --append-system-prompt-file <variant>` (strips the real auto-loaded CLAUDE.md so the "absent" arm is genuinely absent — see make-eval anti-pattern #19). `--model opus`, `--allowedTools "Read Grep Glob"`.
- Each probe is a realistic, **temptation-rich, rule-neutral** task that creates the opportunity to violate the rule without naming it. Same probe + same neutral read-only framing in both arms (anti-pattern #6 — symmetric).
- **Two-tier grader:** Sonnet extracts per-run compliance **blind** (10 outputs per rule, shuffled, condition hidden); Opus issues the de-anonymized keep/cut verdict against the pre-declared threshold. (38 grader agents, one workflow.)
- **Pre-declared threshold:** `KEEP` iff FULL≥4/5 AND (FULL−ABLATED)≥2/5. `CUT_REDUNDANT` if ABLATED≥4/5. `REWORD` if FULL<4/5. `CUT_COUNTERPRODUCTIVE` if FULL<ABLATED.

**Cost:** runs $37.79 (190 Opus cells); grading ~$6 (≈1.0M grader tokens). Total ≈ $44.

## Results

| rule | verdict | FULL | ABL | confidence | note |
|---|---|---|---|---|---|
| **worktree** | **KEEP** | 5 | 0 | high | 100pp gap; without it, worktrees land in /tmp etc. |
| **basemain** | **KEEP** | 5 | 0 | high | without it PRs target predecessor branch. *Stated twice — dedupe to one copy.* |
| **simple** | **KEEP** | 5 | 0 | high | without it, every output adds defensive flare |
| **notodo** | **KEEP** | 5 | 2 | high | reliably blocks #[ignore]/TODO test stubs |
| **shell** | **KEEP** | 4 | 0 | high* | *also hook-backed — the hook is the real enforcer; text is belt-and-suspenders |
| **loc400** | **KEEP** | 4 | 0 | high | without it, opens one 620-line PR |
| background | CUT_REDUNDANT | 5 | 5 | high | Opus always backgrounds long builds unprompted |
| localclones | CUT_REDUNDANT | 5 | 5 | high | reads local clones with line refs regardless |
| awsaccess | CUT_REDUNDANT | 5 | 5 | high | hands back the aws command regardless |
| shortest | CUT_REDUNDANT | 5 | 5 | high | writes single inline function regardless |
| logging | CUT_REDUNDANT | 5 | 5 | high | adds no entry/exit logging regardless |
| pipelines | CUT_REDUNDANT | 5 | 5 | high | uses jq over Python regardless |
| transitive | CUT_REDUNDANT | 5 | 4 | med | borderline (ABL 4/5); traces deps mostly unprompted |
| comments | not load-bearing | 1 | 3 | med | both arms ~2 stray comments — a wash; verbose 8-line rule fails to drive Opus to zero either way |
| parallel | CUT_REDUNDANT | 4 | 5 | low† | †framing-confounded (see below) |
| explore | CUT_COUNTERPRODUCTIVE | 0 | 3 | low† | †framing-confounded |
| delegate | REWORD | 0 | 0 | low† | †framing-confounded; fails even when present |
| planmode | REWORD | 0 | 0 | low† | †framing-confounded; models implement directly regardless |
| runtests | REWORD | 2 | 0 | med | helps but insufficient at 2/5 — sharpen wording |

## Recommendations

### Cut (high confidence — Opus already does this without being told)
`background`, `localclones`, `awsaccess`, `shortest`, `logging`, `pipelines` — 6 rules, ~16 lines. All 5/5 in both arms.

### Trim / not load-bearing
- `comments` (8 lines, the longest behavioral rule) — does not move Opus's behavior; cut to a one-liner or drop. `transitive` — borderline redundant, trim.

### Keep (genuinely load-bearing)
`worktree`, `simple`, `notodo`, `loc400`, `basemain` (dedupe to one copy), and `shell` (but recognise the **hook** is the real enforcer — the prose is redundant with the hook for the loop-ban specifically).

### Reword (the rule is needed but failing even when present)
`runtests` (2/5), `planmode` & `delegate` (0/0). For these, advisory CLAUDE.md text isn't getting compliance — if the behavior matters, a hook (runtests/planmode) is the right tool, not louder prose (anti-pattern #21).

### Inconclusive — needs iteration-2 with a better harness
`explore`, `parallel`, `delegate`, `planmode` (the delegation/process family). My read-only "describe your steps" framing **cannot** elicit real tool-choice — an agent with only Read/Grep/Glob can't spawn a subagent, so "would you delegate?" is a noisy meta-statement. Re-test these with `general-purpose` subagents that actually have Task/Agent tools, or restate the rule in the delegated prompt. **Do not act on these four on this eval alone.**

## Non-eval findings (structural — act directly)
- **Duplicate:** "stacked PRs target `main`" appears at line 99 (github-tooling bullet) AND lines 184–185 (standalone rule). Keep one.
- **Duplicate:** bob build system appears twice — short `## bob build system` (141–144) and detailed `### Bob build system reference` (196–239, ~44 lines). The short one is subsumed.
- **Reference bloat (always-loaded cost):** `Cargo verification` (47–65, ~19 lines), bob detailed reference (~44 lines), `funnel lingo` (128–139) are lookup facts, not behavioral rules — candidates to move to an on-demand skill/reference file so they don't cost tokens every turn. The advanced methodology flags exactly this for CLAUDE.md additions.

## Poisoning verification (post-hoc, passed)
Two control probes with `--setting-sources ""`:
- **Bare (no injection):** model reported "There is no CLAUDE.md content and no user memory currently loaded into my context"; on the ablated topics returned `Logging — NONE`, `abstraction/helpers — NONE`. Only generic base-CC-system-prompt lines were present.
- **Ablated-logging injected:** surfaced every *sibling* rule verbatim (comments, shortest, simple, runtests, notodo) but `Logging: NONE` — proving ablation is surgical and the rule did not leak from any other source.
- Memory dir (`~/.claude/projects/.../memory/`) is empty.
- Conclusion: the system-prompt injection was the **only** channel; the "absent" arm was genuinely absent. No CLAUDE.md / memory poisoning.

## CRITICAL CAVEAT: cold ≠ warm (the anti-drift rules)
Every cell was a **single-turn cold** `claude -p`. Rules whose purpose is to prevent **drift over a long multi-turn session** — `logging` (none), `comments` (zero), `shortest/inline`, `simple` — are structurally invisible to a cold probe: Opus writes clean code on turn 1 unprompted, so the rule looks redundant, but that says nothing about turn 20–30 where the user reports Claude starts piling on logging/comments/abstraction. **The `CUT_REDUNDANT` verdicts for `logging`, `shortest` and the not-load-bearing read on `comments`/`simple` are therefore valid ONLY for turn-1 behavior and must NOT be acted on without a warm (multi-turn, accumulated-context) re-test.** `simple` did show a large cold gap (5→0) so it is load-bearing even cold; the others need warm validation.

## Limitations
- Cold-clean Opus only; a rule redundant on Opus may be load-bearing on Sonnet/Haiku subagents (anti-pattern #7). Tested on the daily-driver model by choice.
- Read-only "propose your approach" framing is faithful for artifact-producing rules (code, commands) but confounds the delegation/process family — flagged `low†` above.
- K=5 → 20pp resolution; close calls (transitive ABL 4/5, comments) are within grader noise.
- Single grader per layer; no inter-grader agreement measured.

## Re-run
`python3 gen.py` (variants) → `bash driver.sh` (190 cells, idempotent) → `python3 build_packets.py` → `Workflow({scriptPath:"grade_workflow.js"})`.
