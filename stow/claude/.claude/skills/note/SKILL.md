---
name: note
description: Write a date-prefixed note to ~/Documents/notes from the current conversation, in the user's terse voice. Use when the user invokes /note, says "make a note", "note this", "write this up as a note", or names one or more topics to capture. Default to one note on the most recent topic (including any research/measurements from the conversation); if the user lists several topics, write one note per topic.
user-invocable: true
---

# Note

Capture what we just discussed as a note (or notes) under `~/Documents/notes/`.

## Where notes go

Directory: `~/Documents/notes/`. Use today's date from the environment's `Today's date`. Three shapes:

1. **Single date-prefixed file** (default): `YYYY-MM-DD-<kebab-topic>.md`. Use when everything fits in one text file.
2. **Date-prefixed folder**: `YYYY-MM-DD-<kebab-topic>/` with an entry doc (`README.md`, or `DESIGN.md` for a design) plus topic `.md` files and raw artifacts (`*.txt` command dumps, `screenshots/`, sub-dirs). Use when there's more than one file's worth — several sub-topics, or artifacts to keep alongside the writeup. Inner files are kebab-named and NOT re-dated (the folder carries the date).
3. **Non-date-prefixed folder**: `<kebab-topic>/`. For evergreen notes mutated over time, or a topic specific enough that a date wouldn't help disambiguate. Only use this when the user says the note is long-lived / not a point-in-time capture.

Default to shape 1. It's normal to start as one file and later switch to a folder — if a single file already exists for this topic and the user is adding related artifacts, convert it: make the folder, move the file in as `README.md`, add the new files.

Leave `~/Documents/notes/main.md` alone — it's an append-only ledger owned by the shell `note` command, not part of this skill. Never write to it.

## What to write

Default (no args, or a single topic): **one** note on the **most recent** topic we worked on, including its research — the commands run, measurements, log excerpts, URLs, code. Not just the conclusion; the raw material that got us there.

With args (`/note topic-a topic-b ...`): **one note per topic**, each pulling the relevant part of *this conversation*. Topics are the user's words — map each to the matching thread we discussed. If a topic is ambiguous, ask once, else pick the obvious match.

## Voice — match the user's, do NOT use the assistant default

The voice (distilled from `~/Documents/notes/*.md` dated **before 2025-06-01** — do not imitate notes after that date):

- **Terse. Fragments and bullets, not paragraphs.** A note can be three lines. Say the thing, stop.
- **Paste raw material verbatim.** `$ command` + its output, URLs on their own line, log lines, code blocks, numbers. The evidence IS the note. Don't summarize what a command showed — paste it.
- **Structure is light:** `#` title, a few `##` sections when there's genuinely more than one thing. Often just a title and bullets.
- **First person, present:** "we think it is clicked", "we updated the resource policy manually". 
- **No flair.** No **bold inline labels** (`**Root cause:**`, `**Impact:**`, `**Read:**`). No hedging prose, no "in summary", no takeaway/recommendations section unless there's a real next action. No emoji unless the source material had them.
- If something is unproven, say so in-line and plainly ("NOT verified — hypothesis"), don't build a scaffold around it.
- Nesting and shorthand are fine: indented sub-bullets, `->` for consequence/mapping, `+X` for "added X", `N.b.`, `Q:`, a bare `TODO:`, inline links. Mixed English/Swedish is fine — keep the user's wording, don't translate.

Litmus test: if it reads like a written-up report, it's wrong. It should read like the user's own scratch notes — dense, raw, a bit telegraphic.

### Baked-in voice samples

These are real excerpts from pre-2025-06-01 notes. Match this texture; you do NOT need to re-read the note files to find the voice.

From `owasp-top-10.md` — title is a bare URL, bullets are fragments, `N.b.` aside, mixed-language `Q:`:
```
# https://owasp.org/www-project-top-ten/

Change since 2017 (other than order):
- 'Broken Authentication' was renamed to 'Identification and Authentication Failures'
- (new) Insecure Design
- XXE was merged with Security Misconfiguration

## Broken Access Control
- violation of least privilege or deny by default
- insecure direct object reference (change userid to someone else's)

N.b.
'EA hacked last year' (EA Digital Illusions CE AB)
- bought stolen cookie
- social engineering (slack message to IT person and claimed to have lost the phone)
```

From `git-fundamentals.md` — `$ command` then verbatim output, `+object` shorthand for "added", `->` for mapping, deep indentation, raw hashes pasted:
```
- scenario from $ git help tutorial, with 'manual zip-version' at the same time.

$ git init
+ .git (from template)

$ git add
db: + af5626b4a114abcb82d63db7c8082c3c4756e51b blob 14
index: + 100644 af5626b4a114abcb82d63db7c8082c3c4756e51b 0 README.md

- commit: a hanger that ties a tree together with parent commits and some metadata
    commit: tree|parents|author|committer|message|timestamp

TODO: List all plumbing commands, find the 'plumbing decomposition' of common porcelain operations
```

## Steps

1. Resolve topic(s): most-recent-topic by default, or one per arg.
2. For each, gather the concrete material from this conversation (commands, outputs, measurements, links, code, the conclusion).
3. Pick the shape (see Where notes go). Single file unless there are clearly multiple sub-topics or raw artifacts to keep — then a date-prefixed folder. If a single file for this topic already exists and you're adding more, convert it to a folder (`README.md` = the old file).
4. Use the baked-in voice samples above. Only read pre-2025-06-01 note files if you need more examples than those.
5. Write in that voice: `~/Documents/notes/YYYY-MM-DD-<topic>.md`, or the folder + its files.
6. Report the path(s) written. Don't ask for confirmation before writing; the user reviews the file.
