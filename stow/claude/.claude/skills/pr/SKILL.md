---
name: pr
description: Use when the user wants to create a pull request from local changes, invokes /pr, or says things like "open a PR", "submit this", "push this up". Handles the full workflow — analyzing changes, ensuring clean commits (via /commit), creating branches, and opening PRs on GitHub. Works with messy working trees (mixed committed/staged/unstaged/untracked changes). Splits into multiple numbered PRs if changes exceed 400 lines.
disable-model-invocation: true
---

# PR

Turn local changes into one or more coherent pull requests.

## Step 1: Understand what we're working with

Run these in parallel:
- `git status`
- `git log --oneline -10`
- `git diff --stat HEAD` (staged + unstaged)
- `git ls-files --others --exclude-standard` (untracked)
- `git rev-parse --abbrev-ref HEAD` (current branch)
- Detect the default branch: check if `origin/main` exists, otherwise use `origin/master`

Then figure out:
- **Am I on the default branch?** If yes, we'll need to create work branches.
- **Am I on a work branch?** If yes, also check `git diff --stat <default-branch>...HEAD` to see what's already committed on this branch.
- **What's the total scope?** Count additions + deletions for everything that will go into the PR (committed-on-branch + staged + relevant unstaged/untracked).

## Step 2: Decide on PR grouping

Read the actual diffs to understand the content — not just filenames or stats.

**Single PR path (most common):**
If the committed + staged changes form one coherent unit, and the total is ≤ 400 lines (additions + deletions):
- Check if any unstaged/untracked files belong with this change
- If they do and total stays ≤ 400, include them
- If not, leave them alone
- Proceed to Step 3 with one PR

**Multiple PR path:**
If the total exceeds 400 lines, or if the changes are clearly separate concerns:
- Group changes into coherent units, each ≤ 400 lines
- Name branches with a number prefix: `1-short-description`, `2-short-description`, etc.
- The descriptions should be concise and distinguishable at a glance

**When you can't split reasonably:**
If a coherent change is > 400 lines and splitting it would break logical coherence, stop and ask the user: "This change is ~N lines. I can: (a) PR it as-is, (b) try to split it — here's how I'd split it: [outline]. What do you prefer?"

## Step 3: Run tests before committing

Run `cargo fmt --all` and `make test` **before** committing. This catches formatting, lint, and test failures before they hit CI.

- If tests fail, fix the issue and re-run before proceeding
- Do not skip this step — CI failures from formatting or test errors are avoidable waste
- For multiple PRs, this is the first pass on the full changeset — each split branch gets verified again in Step 5

## Step 4: Ensure clean commits

Before creating branches and PRs, make sure changes are properly committed. Use the /commit skill's approach:
- If changes are already committed cleanly on a work branch, skip this
- If there are staged/unstaged/untracked changes to include, stage and commit them with a clear message
- Each commit should be a coherent unit

## Step 5: Create branches and push

**If on the default branch:**
- Create a new branch from HEAD: `git checkout -b <branch-name>`
- Branch names: simple, lowercase, hyphenated. No prefixes like `feature/` or `pr/`
  - Single PR: just a descriptive name like `add-retry-logic`
  - Multiple PRs: numbered like `1-add-retry-logic`, `2-update-tests`

**If already on a work branch:**
- Use it as-is for the first (or only) PR
- For additional PRs, create new branches

**For multiple PRs (stacked):**
Each branch contains the cumulative changes up to that point. Create them in order:
1. First branch from default branch with just the first group of changes
2. Second branch from the first branch (it will include PR-1's changes in its diff against main — that's expected and correct, the user will merge them in order)

**Before pushing each branch**, check out the branch and run `cargo fmt --all` and `make test`. Each branch must compile, format, and pass tests independently — a split that leaves an unused import or a missing dependency on one branch will fail CI. If a check fails, fix it on that branch (amend or add a fix commit) before moving on. Only after verification passes, push: `git push -u origin <branch-name>` (this sets tracking to `origin/<branch-name>`, NOT `origin/main`)

**When creating branches from `origin/main`**, use `git checkout -b <name>` followed by `git push -u origin <name>` — do NOT use `git checkout -b <name> origin/main` as that sets the upstream tracking to `origin/main`, which causes `git push` to push directly to main.

## Step 6: Create PRs

Use `\gh pr create` for each PR. All PRs target the default branch (main/master), never a work branch.

```bash
\gh pr create --base main --title "Short title" --body "$(cat <<'EOF'
One sentence: what this PR is.

- context / why this exists (link related issues/PRs/Slack with [this](url) — link liberally)
- the approach in a few words
- forward intent, if any ("if this works, I intend to ...")
- status ("not ready to swap yet — this is a step in confirming it works end-to-end")
- the eventual plan + who needs to be involved

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

PR description style (this is the format the user wants — match it):
- **First line: one terse sentence stating what the PR is.** No preamble.
- **Then a short bullet list** giving the reviewer context: why it exists, the approach, forward intent, current status (esp. "this is a step, not the final swap"), and the eventual plan / who's involved.
- **Link liberally** — related issues, PRs, Slack threads, docs — as inline `[this](url)` / `[that](url)`. The reviewer clicks through for detail; the body stays short.
- Keep it terse and human — bullets are fragments, not paragraphs. No verbose "## What / ## Why / ## Verified / ## Caveats" section walls.
- Don't invent motivation — only state intent/context you actually know (from the conversation or the user); if you don't know the "why", just the one-sentence what + factual bullets.
- No emoji. No "🤖 Generated with…" footer. No test-plan section unless there's genuinely something to say.
- If multiple PRs, note ordering in a bullet: "part 1 of 2" / "merge after #N".

## Step 7: Report

After creating all PRs, report:
- PR URL(s)
- What each PR contains (1-line summary)
- What was left uncommitted (if anything)
- If multiple PRs, note the merge order

## Rules

- **400 line limit**: additions + deletions, including lock files and generated files. This is a hard limit — the user's review process depends on it.
- **All PRs target the default branch**, even stacked ones. The user has been burned by accidentally merging into old work branches.
- **No branch prefixes**: use `descriptive-name`, not `feature/descriptive-name`
- **Number branches when there are multiple**: `1-thing`, `2-other-thing`
- **PR body format**: one-sentence "what this is" + a short bullet list of context (why / approach / intent / status / plan), linking related issues/PRs/Slack inline. Terse fragments, not section walls. Don't invent motivation — only state what you actually know. See Step 6.
- **Leave unrelated changes alone**: if unstaged changes don't belong with the current work, don't touch them
- **No plan/design docs in PRs**: files in `docs/plans/` are working documents, not deliverables — never include them in PR branches
- Use `\gh` (backslash-gh) for GitHub CLI commands — `gh` is aliased in this user's shell
