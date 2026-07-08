---
name: align-compactor-notes
description: Update the iceberg-compaction notes repo to match the current state of code in ~/code/iceberg-rust-compactor and ~/code/transform. Use this whenever the user mentions aligning notes, syncing notes with code, updating TODOs, checking what's changed in the compactor, or says things like "update the notes", "align with reality", "what's new in the code", "sync the notes". Also trigger when the user checks off work, asks about stale TODOs, or wants to capture recent decisions.
disable-model-invocation: true
---

# Align Notes with Code Reality

Update the iceberg-compaction work notes so they reflect what the code actually looks like right now. The notes are a research/engineering notebook; the code repos are the source of truth.

## Locations

| What | Where |
|------|-------|
| Notes repo | Current working directory (`iceberg-compaction/`) |
| Main deliverable | `~/code/iceberg-rust-compactor` (main branch) |
| Adjacent code | `~/code/transform` (main branch) |

## Files to update

| File | Format | What drifts |
|------|--------|-------------|
| `TODO.txt` | Checkbox lists grouped by phase | Items done but not checked off; new work not listed |
| `DECISIONS.md` | Numbered `D##` entries, append-only | Architectural choices made in code but not recorded |
| `TIMELINE.md` | Date-stamped entries by phase | "Current State" section frozen at an old date; new milestones missing |
| `WORKLOG.md` | Correctness findings, review context | New learnings from implementation not captured |
| `gotcha-*.txt/md` | One file per discovered constraint | New gotchas in code comments or commit messages |

## Workflow

### Phase 1: Gather state (parallel)

Launch two parallel efforts:

**Code state** — build a picture of what happened in the repos since the notes were last touched:

1. Recent commits on main in both repos. Use `git -C <path> log --oneline` and scan for PR merge commits. The notes reference PRs by number (`PR #NN`), so collect the full set of merged PR numbers.
2. Current crate/module structure: `ls ~/code/iceberg-rust-compactor/crates/`, check for new crates, new modules, new binaries, new test files, new scripts.
3. Read key structural files: `Cargo.toml` (workspace members, dependencies), `README.md`, `ARCHITECTURE.md` in the compactor repo.
4. Check for open PRs: `\gh pr list -R funnel-io/iceberg-rust-compactor --state open` — these might imply upcoming TODOs.

**Notes state** — read the current notes to know what's already documented:

1. Read `TODO.txt`, `DECISIONS.md`, `TIMELINE.md`, `WORKLOG.md` in full.
2. List all `gotcha-*.txt` and `gotcha-*.md` files and read their content (or at least titles).
3. Note the highest PR number referenced in TODO.txt, the latest date in DECISIONS.md, and the date in TIMELINE.md's "Current State" section. These are the "last sync" markers.

### Phase 2: Cross-reference

For each `[ ]` item in TODO.txt:
- If it references a PR number → check if that PR is merged on main. If merged, mark it done.
- If it describes work (not a PR) → check the code for evidence it's been done. Look at relevant modules, tests, commit messages.
- If the concern is moot (code restructured, approach changed) → flag it for removal or update.

For the code side:
- For each PR merged after the "last sync" markers that ISN'T already referenced in the notes → it probably needs a TODO check-off, a new DECISIONS entry, or both.
- For structural changes (new crates, renamed modules, new dependencies) → check if DECISIONS.md or ARCHITECTURE docs reflect them.
- For code comments containing `TODO`, `FIXME`, `HACK`, `XXX` → check if corresponding items exist in TODO.txt.
- For commit messages mentioning gotchas, workarounds, or "discovered that..." → check if a gotcha file exists.

### Phase 3: Apply updates

Follow the existing conventions exactly. Read the files before editing — match the style of what's already there.

**TODO.txt conventions:**
- Completed: `- [x] Description` — only add an indented `Done:` annotation if the resolution was non-obvious (e.g., different approach than planned, complex multi-PR effort). For straightforward items, just check the box.
- New items: add to the most appropriate existing section. If no section fits, add a new `## Phase: Description` section in the right position (Done sections at top, Now/Next/Later at bottom).
- PR references: `PR #NN` format.
- Comments: lines starting with `#` — use for context that isn't a task.

**DECISIONS.md conventions:**
- Format: `### D{N}: Title (YYYY-MM-DD)` where N is the next sequential number.
- Append-only — later entries take precedence over earlier ones.
- Include the reasoning and trade-offs, not just the decision. Reference related PRs.
- Group under existing `## Section` headers where appropriate.

**TIMELINE.md conventions:**
- Date-stamped entries: `- **YYYY-MM-DD** — What happened.`
- Grouped by phase with `## Phase N: Name (date range)` headers.
- Update the "Current State" section at the bottom with today's date and an accurate summary.
- Add new phases if the work has moved into a genuinely new stage.

**WORKLOG.md conventions:**
- Grouped under `## Topic` headers (e.g., "Correctness Findings", "Code Review Findings").
- Each finding is `### Title (YYYY-MM-DD)` followed by explanation.
- Only add entries for genuine learnings — things that were surprising, that corrected a previous understanding, or that future developers need to know. Don't log routine work.

**Gotcha files:**
- Naming: `gotcha-{short-kebab-description}.txt` or `.md`.
- One constraint per file.
- Include: what the gotcha is, how it was discovered, and what to do about it.
- Only create a new file if the gotcha is genuinely new and not covered by an existing one.

### Phase 4: Summary

After all edits, output a summary to the conversation organized as:

1. **TODO.txt** — items checked off (with brief reason) and new items added
2. **DECISIONS.md** — new decisions documented
3. **TIMELINE.md** — new entries and updated "Current State"
4. **WORKLOG.md** — new findings
5. **New gotcha files** — any created
6. **Flagged for review** — anything uncertain (items that might be done but you couldn't confirm, items that might be moot, etc.)

## Constraints

- Do NOT commit changes. Edit files only.
- Use `git -C <path>` for all git commands in external repos (never `cd && git`).
- When uncertain whether something is done, leave it unchecked and flag it in the summary.
- Preserve existing formatting. Don't reformat sections you didn't change.
- Don't add evidence tags (`[TRACED]` etc.) unless you've actually verified the claim against source code.
- Use today's date (from the conversation context) for new entries.
