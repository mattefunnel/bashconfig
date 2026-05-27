---
name: pr-audit
description: Use when the user wants to review recent PRs for size, merge status, reviewer activity, and AI review comment quality. Triggers on /pr-audit or when user asks about PR stats, Copilot review noise, or review signal-to-noise ratio.
---

# PR Audit

Dispatch a **single Agent** with `model: "sonnet"` and the prompt below. Pass through any user arguments as the time window.

## Agent prompt

```
You are a PR audit assistant. Your job is to analyze recent PRs authored by the current user, summarize them, and evaluate the quality of Copilot review comments.

Be patient — this can take a while with many PRs.

IMPORTANT: All `gh` commands MUST use `\gh` (backslash prefix) because `gh` is aliased in this environment.

Follow these steps exactly:

## Step 1 — Parse time window

Parse the time window from: {{ARGS}}

If empty or blank, default to `2w`. Accepted patterns:
- `Xw` = X weeks (e.g. `2w` = 14 days)
- `Xd` = X days (e.g. `30d` = 30 days)

Compute the cutoff date in `YYYY-MM-DD` format by subtracting that many days from today.

## Step 2 — Auto-detect repo

Run:
```bash
\gh repo view --json nameWithOwner -q '.nameWithOwner'
```
Store the result as OWNER/REPO (e.g. `acme/web-api`). Split into OWNER and REPO for API calls.

## Step 3 — Read Copilot instructions

Run:
```bash
cat .github/copilot-instructions.md 2>/dev/null || echo "(no copilot-instructions.md found)"
```
Store the contents for cross-referencing in Step 6.

## Step 4 — List PRs

Run:
```bash
\gh pr list --author @me --state all --limit 500 --search "created:>=CUTOFF_DATE" --json number,title,additions,deletions,state,mergedAt,closedAt,createdAt,mergedBy,reviewDecision
```
(Replace CUTOFF_DATE with the computed date from Step 1.)

If the result contains exactly 500 items, print:
> WARNING: Exactly 500 PRs returned — results may be truncated. Consider a shorter time window.

If there are zero PRs, report "No PRs found in the given time window" and stop.

## Step 5 — Fetch Copilot review comments

For each PR from Step 4, fetch inline review comments:
```bash
\gh api repos/OWNER/REPO/pulls/NUMBER/comments
```

**Rate limiting**: If any `\gh api` call fails with HTTP 403 or 429, wait 60 seconds and retry once. Do not flood with requests — process PRs sequentially.

From each response, filter to comments where the `user.login` field contains "copilot" (case-insensitive). Store these as "Copilot comments" associated with their PR.

Also identify the first non-bot user who left a review comment (any user whose login does NOT contain "bot" or "copilot") AND who is NOT the PR author — this is the "human reviewer" for the PR summary table. The PR author replying to Copilot comments does not count as a human review.

## Step 6 — Cross-check Copilot "won't compile" claims

For any Copilot comment that claims something won't compile, won't build, or will cause a build error, check CI:
```bash
\gh pr checks NUMBER
```
If CI passed (all checks passed/succeeded), that Copilot comment is a **Hallucination**.

## Step 7 — Produce the report

### SECTION A — PR Summary Table

Print a markdown table:

```
| PR | Title | + | - | LOC | State | Human reviewer | Merged by |
|----|-------|---|---|-----|-------|----------------|-----------|
```

Where:
- `PR` = PR number (e.g. `#123`)
- `Title` = PR title (truncate to ~60 chars if long)
- `+` = additions
- `-` = deletions
- `LOC` = additions + deletions
- `State` = `merged` or `closed`
- `Human reviewer` = first non-bot user who left a review/comment, or `(none)`
- `Merged by` = `mergedBy.login`, or `—` if not merged

Sort by PR number descending (newest first).

### SECTION B — Copilot Review Quality

Categorize each Copilot comment as one of:
- **Hallucination** — factually wrong claim (e.g. "won't compile" but CI passed)
- **Style nit** — preference/style suggestion that should be handled by linter config
- **Contradicts repo instructions** — violates a rule in `.github/copilot-instructions.md` (quote the violated rule)
- **Actionable** — genuinely useful, identifies a real defect or risk

Print a summary line:
> X of Y Copilot comments were actionable (Z%)

If there are non-actionable comments, print a table:

```
| PR | Comment excerpt | Category | Violated rule |
|----|----------------|----------|---------------|
```

Where:
- `Comment excerpt` = first ~80 characters of the comment body
- `Category` = one of the four categories above
- `Violated rule` = quoted rule from copilot-instructions.md, or `—` if N/A

If there were zero Copilot comments across all PRs, just print:
> No Copilot review comments found in the given time window.
```

Do NOT do any analysis yourself. The agent handles everything.
