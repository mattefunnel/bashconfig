---
name: upstream-contrib
description: Port the shareable, non-internal changes from this private bashconfig onto the public upstream (folkol/bashconfig) as a PR, redacting or dropping employer/private internals and secrets. Use when the user says "contribute to upstream", "make a PR to origin/folkol", "port our public changes up", "publish the shareable dotfiles changes", or invokes /upstream-contrib.
disable-model-invocation: true
---

# upstream-contrib

Publish the parts of this private config that are safe to share to the public
upstream, leaving employer internals and secrets behind. This repo has a private
`master` (with internal tooling) and a public `origin` (`folkol/bashconfig`).
Each run ports the delta accumulated since the last publish.

## Remotes (verify with `git -C <repo> remote -v`)
- `origin` → `folkol/bashconfig` — the **public** upstream. PRs go here.
- Other remotes (e.g. an employer fork) hold the private history — never the PR target.

## Step 1: Find the base — the point the last port was cut from

The base is NOT `origin/master` verbatim (that includes the merge commit of the
last port). It's the private-master commit the last port branched from.

```
git -C <repo> fetch origin
git -C <repo> log --oneline -15 origin/master        # find the last "publish/port" merge
git -C <repo> log --oneline -30 master
```

Find the merge-base of the last publish and use the private-side parent as the
base: `git -C <repo> merge-base master origin/master`. That commit is where the
last port diverged; everything on `master` after it is this run's candidate delta.

```
BASE=$(git -C <repo> merge-base master origin/master)
git -C <repo> diff --stat $BASE..master
```

## Step 2: Classify the delta

The raw diff is usually huge because internal-only trees (eval run-transcripts,
fixtures embedding internal data) live on private `master`. Cut those out first
to see the real candidate set:

```
git -C <repo> diff --stat $BASE..master \
  -- ':(exclude)*/evals/*' ':(exclude)evals/*' ':(exclude)*/runs/*'
```

Then read each remaining file's diff (`git -C <repo> diff $BASE..master -- <file>`)
and sort into three buckets:

- **SHIP** — generic tooling with no employer internals: hooks, skills, generic
  CLAUDE.md rules, settings.json sandbox/permission structure. Paths that name
  *this repo's own* dirs (`~/code/bashconfig/...`) are fine; they're not secrets.
- **REDACT** — shareable in substance but the diff carries a specific internal
  value (a real aws-vault profile name, a colleague's email as git co-author, an
  internal hostname/path). Port the substance, replace the value with the
  placeholder the public tree already uses. If the ONLY change in a file is such
  a value and the public file already has a placeholder, **skip the file** — don't
  regress the placeholder.
- **DROP** — cannot be shared at all: secrets/ARNs/account-ids/tokens
  (`.bash_profile_funnel` and similar), content-bearing eval fixtures/transcripts
  that embed internal CLAUDE.md or customer data, staging duplicates (`_staged/`),
  internal audit notes, and symlinks that point outside the repo.

When unsure whether something is internal, treat it as DROP and tell the user.

## Step 3: Grep-gate every SHIP/REDACT file before it lands

Run a leak scan over the files you intend to ship. Tune the term list to the
employer's vocabulary (ask the user if unsure). Example:

```
rg -ni "funnel|meld|\bdip\b|\bbob\b|<colleague-names>|<real-profile>|firebase|customer" <files...>
```

Zero hits is the bar. A hit means either redact the value or drop the file.

## Step 4: Build the branch off the PUBLIC baseline

Branch from `origin/master`, not private `master`:

```
git -C <repo> branch --no-track <branch> origin/master
git -C <repo> worktree add <worktree-path> <branch>
```

Worktree location: normally `.worktrees/<name>` inside the repo. But if the
repo's `.claude` tree is under sandbox `denyWrite`, a checkout inside the repo
fails — put the worktree under `/tmp/claude/<name>` instead and note the deviation.

Copy SHIP files verbatim from `master`
(`git -C <repo> show master:<path> > <worktree>/<path>`), hand-edit REDACT files
to swap internal values for placeholders, and hand-curate partial-file ports
(e.g. add only the generic sections of a CLAUDE.md, not the "who I am" block).

## Step 5: Verify, commit, PR

- Re-run the Step 3 grep over the final worktree diff. Zero hits.
- `git -C <worktree> diff origin/master -- <ship files>` — eyeball it once more.
- Commit. The public repo uses a `Co-Authored-By: Claude <noreply@anthropic.com>`
  trailer and no employer co-author — match the public convention, not the
  private `.gitconfig` git-mob co-author.
- `git -C <worktree> push -u origin <branch>` (or the fork the user PRs from).
- `\gh pr create --repo folkol/bashconfig --base master` with a body that lists
  what was ported and, explicitly, what was redacted/dropped and why — so the
  redaction decisions are reviewable. Follow the `pr` skill's body format.

## Redaction ledger

Put the "what I dropped and why" list in the PR body every time. It's the audit
trail that makes the next run's classification decisions greppable in PR history.
