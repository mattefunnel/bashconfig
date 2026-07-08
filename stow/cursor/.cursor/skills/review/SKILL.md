---
name: review
description: Review code for correctness, Funnel idioms, minimality, and security requirements. Use when the user invokes /review, asks for a code review, or provides optional review context such as whether code implements a ticket.
---

# Review

## Scope

Use this skill when the user invokes `/review`, with or without extra context such as:

```text
/review does this code implement ticket foo.bar.baz
```

Review the relevant code changes with a focus on whether the code is:

- Correct.
- Funnel-idiomatic.
- Minimal, with no unnecessary extra behavior, abstractions, dependencies, options, or churn.
- Consistent with Funnel tech standards and developer security requirements.

## Regression Scoping (read first)

**Only block on what this change introduces or makes worse. Do not block on pre-existing problems.**

The goal of a review is to stop *new regressions* from landing, not to fix every pre-existing problem in the files the diff happens to touch. A finding is **blocking only if the diff introduces it or worsens it**. Decide which by looking at the diff markers:

- A problem on an **added or modified line** (`+` in the diff), or one the change *makes worse* (e.g. adds a third caller to an already-questionable helper, widens a public surface, extends a pattern) → **in scope**. Block per the rules below.
- A problem that lives entirely on **unchanged context lines**, or in a part of the file the diff doesn't alter, even if it's right next to the change → **pre-existing, out of scope**. Do **not** block. If it's genuinely useful to mention, put it in **Good To Know** and label it `(pre-existing)`.

When you cannot tell from the diff alone whether a concern is new (e.g. a function is moved, or context is shown without enough surrounding history), say so explicitly rather than assuming it's new — phrase it as "if this line is new in this change, …" and lean toward Good To Know over blocking.

This scoping rule sits **above** every check below, including the Hotspots. A Hotspot violation on a pre-existing, unmodified line is not a blocking finding. The point is not to be lenient about real regressions — those still block hard — it's to avoid expanding the diff's responsibility to the whole file.

## Required References

When available, use these local references as review standards:

- `~/.claude/CLAUDE.md` — Matt's global code standard. The **Code Standard Hotspots** section below summarizes the parts most often violated in fresh code; check these specifically.
- `~/code/funnel-io/tech-standards`
- `~/code/funnel-io/dev-security/developer-requirements`
- **Project ADRs** — locate by searching upward from the review target for `DECISIONS.md`, `docs/adr/`, or `docs/decisions/`. Also check `AGENTS.md` / `CLAUDE.md` at the repo root for an "Invariants" / "Decisions" section that cross-references them.

Read only the parts relevant to the changed code and the user's extra context. Do not copy broad policy text into the response.

## Code Standard Hotspots

These come from `~/.claude/CLAUDE.md` and are the highest-yield checks because fresh code violates them constantly. Flag these as **blocking** when the diff *introduces or worsens* them (see **Regression Scoping** above) and the diff does not already justify them inline. A Hotspot pattern that exists only on unchanged lines is pre-existing — out of scope for blocking.

**1. Speculative defensive flare ("just in case").** Per CLAUDE.md: only pre-guard if the failure is *irreversible* on first occurrence — deletion, force-push, charging money, dropping a DB table, sending an external message. Recoverable failures (network error, oversize response, missing field, parse failure) do NOT qualify. Let them throw the first time and fix the cause. Specifically flag:
   - Byte/length caps on internal-infra responses where no incident motivated the cap (e.g. `read_capped_body`, `MAX_*_BYTES` on requests to internal services).
   - Retry loops, fallback branches, error-swallowing `|| true` / `.unwrap_or_default()` on paths where the right answer is to surface the error.
   - `trap` / signal handlers, background processes, intermediate files for IPC, configurable env vars, retry/backoff added before any real failure pattern was observed.
   - Phrases like "for robustness", "to be defensive", "in case X", "for unattended runs", "might need later" in commit messages or PR descriptions — almost always premature.

**2. Speculative configuration.** Env vars / knobs / Option fields added "in case we need to tune it." If the only value ever used is the hard-coded default, delete the knob and inline the constant. Web server ports, shutdown grace periods, cache TTLs — all candidates.

**3. Premature abstraction.** A helper used once. A trait with one implementor. A newtype that doesn't carry an invariant. CLAUDE.md: "Inline beats extract when the helper is used once. Extract only when (a) the duplication is exact and occurs 3+ times, OR (b) the named concept genuinely clarifies meaning."

**4. Excessive comments.** Default is **zero**. Flag:
   - Multi-paragraph doc blocks on a struct/function whose name + types already document it.
   - Any comment containing "Why:", "Previously:", "Used to:", "Note:", "See X for rationale" — that content belongs in the commit message, PR description, ADR, or a test name.
   - Cross-references like "matches the constant on `foo`" — rots fast; source of truth should live in one place.
   - Comments that restate what the next line does.
   - Comments describing the current investigation / session context ("dialled to 1 while we diagnose…").
   - Keep only comments where deletion would mislead a careful reader: a hidden invariant, a subtle workaround, a non-obvious choice that would otherwise be reverted.
   - Reviewer heuristic: would you suggest deleting this comment in a "tighten this up" pass? If yes, flag it.

**5. Excessive logging.** Default is none. Flag `log.info` / `console.log` / `tracing::info!` added for:
   - Function entry/exit, parameter shapes, intermediate values, "we got a result of size N."
   - Anything that would be deleted within a week of writing it.
   - Keep only: external IO boundaries (with elapsed/status), genuine decision points ("why did the system do Y at 3am"), and error paths that don't throw.

**6. Test stubs / placeholders.** Per CLAUDE.md: no `#[ignore]` tests, no TODO-placeholder test stubs, no `// TODO: add test for X` comments. If a test can't be made to work, don't write it at all. Flag any test whose body is essentially a comment + a no-op assertion (e.g. `let _ = fn_pointer_cast`).

**7. Backwards-compatibility / migration shims for code that has no public consumers.** Renamed `_var` placeholders for removed args, re-exports of moved types, `// removed in favor of X` comments, feature flags for internal switches. If the change is internal, change the code in one go and delete the old form.

## Review Process

1. Understand the user's review target and optional context.
2. Locate project ADRs (see Required References). Skim titles/dates to know what decisions exist; read in full any whose subject overlaps the diff (e.g. ordering, retry/commit policy, validation rejection lists, public API surface, configuration knobs, partial-progress, partition handling).
3. Inspect the diff, touched files, and nearby code needed to judge behavior. Track which lines the change *adds or modifies* versus which are unchanged context — per **Regression Scoping**, only the former can produce blocking findings.
4. Check the relevant Funnel standards and security requirements.
5. Walk the **Code Standard Hotspots** checklist against the diff. A hotspot violation is blocking only when the change *introduces or worsens* it (per **Regression Scoping**) and the diff does not justify it inline (a documented incident, an irreversible failure, or a name-as-invariant case). A hotspot pattern on unchanged context lines is pre-existing — at most a `(pre-existing)` Good To Know note.
6. Prioritize concrete bugs, security issues, requirement mismatches, regressions, missing validation, missing tests for risky behavior, and unnecessary complexity — that the change introduces.
7. Treat minimality as a blocking concern when the change adds avoidable behavior, broad abstractions, dependencies, public surface, configuration, or compatibility shims. Minimality problems that already existed and the diff merely sits beside are out of scope.
8. **ADR adherence is a blocking concern in two directions.** (a) If the diff contradicts a recorded decision without superseding it, flag it as a blocking finding and cite the ADR (e.g. "D17"). (b) Before flagging anything architectural — phase ordering, what's intentionally rejected, retry/commit policy, why something isn't configurable — confirm an ADR doesn't already document it as deliberate. If one does, omit the finding entirely (or downgrade to Good To Know as "D## documents this; flagging only in case the trade-off has shifted").
9. Avoid speculative style comments unless they point to a real correctness, idiom, security, maintenance, or minimality risk.

## Output Format

Return exactly these two sections:

```markdown
## Blocking Findings

[Actionable blocking findings, ordered by severity. Include file/symbol references and the concrete impact.]

## Good To Know

[Non-blocking observations that may help the user. Keep this short.]
```

If there are no blocking findings, write:

```markdown
## Blocking Findings

All good.

## Good To Know

[Optional non-blocking notes, or "None."]
```

## Finding Guidelines

Blocking findings must be actionable, grounded in code, and **introduced or worsened by this change** (see **Regression Scoping**). Include:

- What is wrong.
- Why it matters.
- Where it is.
- What kind of fix is expected.
- If it relates to an architectural decision, the relevant ADR ID (e.g. "violates D17") or a note that no ADR covers it yet.

Good-to-know findings may include useful context, tradeoffs, cleanup opportunities, or **pre-existing** issues the change sits near (label these `(pre-existing)`). They must not dilute the blocking section. A pre-existing problem never belongs in the blocking section, however real it is — the change didn't cause it.
