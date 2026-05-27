---
name: commit
description: Use when the user asks to commit changes, invokes /commit, or when preparing changes for a PR. Analyzes the working tree (committed, staged, unstaged, untracked), groups related changes into coherent commits, and commits them. Use this whenever git changes need to be organized and committed — even as part of a larger workflow like /pr.
---

# Commit

Analyze the working tree and create clean, well-grouped commits.

## Step 1: Survey the full working tree

Run these in parallel:
- `git status` (never use `-uall`)
- `git diff --stat HEAD` (what changed overall — staged + unstaged vs HEAD)
- `git diff --stat --cached` (what's already staged)
- `git diff --stat` (unstaged tracked changes)
- `git log --oneline -10` (recent messages for style matching)
- `git ls-files --others --exclude-standard` (untracked files)

## Step 2: Understand what's there

Read the actual diffs (not just stats) to understand the content of changes. Group them mentally:
- What's already committed on this branch but not on the default branch?
- What's staged?
- What's modified but unstaged?
- What's untracked?

Look for coherence: do the staged changes form a logical unit? Are there unstaged or untracked files that clearly belong with them (e.g., a new test file for a new module that's staged)?

## Step 3: Group and commit

The goal is commits where each one is a coherent, reviewable unit. Usually this means one commit, but if the changes are clearly separate concerns, make separate commits.

**If the staged changes form one coherent change:**
- Check if any unstaged/untracked files obviously belong with them (same module, related test, etc.)
- If so, stage those too
- Commit together
- Leave unrelated changes alone

**If nothing is staged but there are modifications/untracked files:**
- Group related files and stage them together
- If everything is one logical change, stage and commit it all
- If there are clearly separate concerns, make separate commits

**If the user passed specific files or instructions**, follow those.

## Commit message style

- Match the style of recent commits in the repo
- Brief, imperative mood ("Add X", "Fix Y", "Update Z")
- Focus on what changed, not why (the PR description handles "why")
- 1 line is fine; 2 lines if needed. No essays.
- End with: `Co-Authored-By: Claude <noreply@anthropic.com>`
- Always use a HEREDOC for the message

## Rules

- Never use `git add -A` or `git add .` — always name specific files
- Never commit files that look like secrets (.env, credentials, tokens)
- Never use `--amend` unless the user explicitly asks
- Always run `git status` after committing to verify
- Report what was committed: short summary + commit hash
