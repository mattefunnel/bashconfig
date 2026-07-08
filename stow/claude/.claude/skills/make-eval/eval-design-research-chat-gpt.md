# Using evals to optimise a Claude Code setup without fooling yourself

## The short answer

If you want solid conclusions, do not evaluate “prompts” in isolation. Evaluate the whole Claude Code harness that you actually use: the model, effort level, permission mode, `CLAUDE.md`, skills, hooks, subagents, and any external tools or MCP servers. Anthropic’s own CLI and Agent SDK are the right substrate for this, because they use the same tools, agent loop, and context management as Claude Code. For scripted runs, Anthropic recommends `--bare`, which skips auto-discovery of hooks, skills, plugins, MCP servers, auto memory, and `CLAUDE.md`; that makes it much easier to build a clean baseline instead of accidentally measuring your machine’s residue. citeturn25view0turn26view7

The right overall pattern is a paired, task-level A/B design on real work from your own history, with executable verification where possible, independent review in a fresh context, and explicit contamination controls. That means: same task under control and treatment, isolated worktrees or fresh repo snapshots, no shared session state unless that state is part of the workflow you want to optimise, and a reviewer that does **not** inherit the implementation context. Anthropic’s docs explicitly recommend fresh-context review patterns because fresh context reduces bias, and they also warn that performance degrades as the context window fills. citeturn31view4turn31view0turn31view1

If you do that, evals can be genuinely useful for your day-to-day setup. If you do not, they are very easy to game with context leakage, benchmark contamination, cherry-picked tasks, and meaningless micro-gains. Research on LLM evaluation now treats contamination as a live problem rather than a corner case: retro-holdout work shows public benchmark inflation, dynamic benchmark surveys argue that static public benchmarks decay quickly, and search-based agents can directly retrieve benchmark answers from public sources during evaluation. citeturn7search1turn7search2turn7search3turn7search0

## What is actually worth evaluating in Claude Code

The first practical question is not “how do I run an eval?” but “what kind of setup change is this?” Claude Code’s extension points are materially different, so they should not be tested or judged in the same way. Anthropic’s own docs make that distinction fairly clearly. citeturn14view2turn8view2turn18view0turn12view0

### CLAUDE.md and rules

`CLAUDE.md` is persistent session-start context. Anthropic says it is where you put things you would otherwise keep re-explaining: coding conventions, build commands, architectural decisions, non-obvious workflows, and recurring gotchas. It is loaded every session, consumes context every session, and Anthropic recommends keeping each file concise, with a rough target of under 200 lines. Crucially, Claude treats it as **context**, not as enforced policy. If you need an action blocked every time, Anthropic tells you to use a `PreToolUse` hook instead. citeturn14view2turn14view7turn14view0

That means a new instruction belongs in `CLAUDE.md` only if it is broad, stable, and high-frequency. Anthropic’s own guidance is close to an empirical admission rule: add to `CLAUDE.md` when Claude makes the same mistake a second time, when a review catches something Claude should already have known, or when you keep repeating the same correction across sessions. If the instruction is narrow, situational, or procedural, it probably does **not** belong there. citeturn14view2

### Skills

Skills are on-demand. Anthropic’s docs say to create one when you keep pasting the same instructions, checklist, or multi-step procedure, or when a section of `CLAUDE.md` has turned into a procedure rather than a fact. Unlike `CLAUDE.md`, the skill body is loaded only when the skill is used, so long reference material costs almost nothing until it is actually relevant. That makes skills the right place for reusable workflows, review rubrics, repo-specific runbooks, or large domain references that should not bloat every session. citeturn8view2turn10view0turn26view2

There are two methodological wrinkles that matter for evals. First, skills can trigger automatically if their description is broad, so you need to test both “does it help when invoked?” and “does it trigger when it should, and not when it should not?” Anthropic explicitly suggests tightening descriptions or setting `disable-model-invocation: true` when a skill triggers too often. Second, long sessions can blur skill effects: after compaction, Claude Code only re-attaches the most recent invocation of each skill, with a 5,000-token cap per skill and a 25,000-token combined cap. If a skill only helps in the first few turns and then quietly drops out after compaction, that is a real deployment property, not an eval nuisance. citeturn10view5turn10view6turn10view1

### Hooks

Hooks are for zero-exception behaviour. Anthropic describes them as deterministic automation points in Claude Code’s lifecycle, and `PreToolUse` hooks can explicitly deny actions before a tool runs. This is the correct layer for “always run formatter after edits”, “never read `.env`”, “block writes to migrations”, “force an adversarial review pass”, or “log every config change”. It is not the right layer for soft preferences or broad stylistic guidance. citeturn18view0turn11view0

That distinction matters because people often try to fix enforcement problems with longer instructions. Anthropic’s docs are explicit that instructions are advisory and hooks are deterministic. So if a rule must hold on every run, the meaningful eval is not “did Claude remember the instruction?” but “what is the hook’s true-positive rate, false-positive rate, latency cost, and downstream effect on task completion?” citeturn14view0turn18view0turn11view0

### Subagents and agents

Subagents are for isolated work with specialised prompts and tool restrictions. Anthropic says to use them when a side task would flood your main conversation with logs, file contents, or search results you will not need later. Non-fork subagents start in a fresh context window with their own system prompt, tools, and permissions; they do **not** see your conversation history, already-invoked skills, or files you have already read. Forks are different: they inherit the full conversation, the same system prompt and tools, and even benefit from shared prompt cache. For uncontaminated evaluation, that difference is fundamental. citeturn12view0turn12view3turn13view0

There is one subtle exception that can easily distort results. Built-in Explore and Plan agents deliberately skip your `CLAUDE.md` files and the parent session’s git status to keep research quick and cheap. So if you are evaluating “how much do my project rules improve research/planning behaviour?”, built-in Explore and Plan are partly the wrong measurement surface unless you restate the critical rules in the delegated prompt. citeturn12view5turn13view0

### Settings and model controls

Settings deserve their own eval bucket because they often change both capability and operating conditions. Anthropic exposes model selection, permission mode, effort/thinking-related settings, output style, permissions, and environment knobs. Their latest prompt guidance recommends starting at `xhigh` effort for coding and agentic work, using at least `high` for intelligence-sensitive tasks, and then testing downwards or upwards for cost/performance trade-offs. Permission modes also change workflow materially: `plan` makes the session read-only, `auto` uses a separate classifier to approve or deny actions in the background, and `bypassPermissions` should be treated as a sandbox-only mode rather than a convenience setting. Output styles change the system prompt and only take effect on a new session or after `/clear`. citeturn19view0turn20search1turn20search0turn22search2turn9view7

Methodologically, this means you should not test “new skill + new rules + new model + auto mode” as a single blob and then pretend you learned something specific. At minimum, separate “behavioural instruction changes” from “model/effort changes” and from “workflow/permission changes”. Anthropic’s own prompt-engineering overview says not every failed eval is really a prompt problem; sometimes latency, cost, or outcome is better improved through model choice instead. citeturn19view1

## How to build an eval harness that is not contaminated

The cleanest way to think about this is to define evaluation **regimes** rather than a single eval.

A **cold clean** regime should answer: “Does this candidate help when the environment is stripped down?” Use `claude -p` or the Agent SDK in `--bare` mode, or SDK runs with `settingSources: []`, and explicitly disable auto memory. Anthropic’s docs warn that even with `settingSources: []`, managed policy, `~/.claude.json`, and auto memory can still be read unless you remove them or isolate the filesystem; they recommend separate filesystems plus auto-memory disablement for serious isolation. citeturn25view0turn26view4turn26view5

A **configured cold** regime should answer: “Does the candidate help when it is the **only** added thing?” In practice, that means a stripped-down baseline plus just the treatment under test: one candidate `CLAUDE.md`, one skill, one hook, one subagent definition, or one settings file. For command-line evals, `--bare` plus explicit `--settings`, `--append-system-prompt`, `--agents`, `--plugin-dir`, or `--mcp-config` is ideal because only flags you pass take effect. citeturn25view0

A **warm realistic** regime should answer: “Does this help under the same context conditions I actually work in?” Anthropic repeatedly notes that long sessions degrade, that compacted sessions behave differently, and that clean sessions often outperform cluttered ones once a conversation has drifted. So if your real workflow involves resumed sessions, long debugging loops, or compaction, you need a dedicated warm-state eval rather than assuming cold-start results will transfer. citeturn31view0turn31view1turn31view3

For all three regimes, use tasks drawn from your own work rather than toy prompts. The best sources are recent bugs, refactors, code reviews, flaky tests, docs tasks, operational scripts, and repeated questions from your own conversations or issue tracker. Anthropic’s strongest recurring advice is to give Claude a way to verify its work; that means each task in the corpus should come with executable or inspectable success criteria such as tests, lint, a screenshot comparison, or an expected output check. citeturn31view0turn16view1

The practical unit should be the **paired task**. For each task, run both control and treatment on the same code snapshot, preferably in separate worktrees. Anthropic’s worktree docs exist precisely to isolate parallel edits, and their best-practices guide explicitly recommends fresh-context writer/reviewer patterns because independent sessions are less biased by the code they just produced. citeturn27search0turn31view4

Finally, keep grading independent. Anthropic’s own adversarial review pattern is to run a reviewer in a fresh context that sees only the diff and the criteria, not the reasoning that produced the change. The security-guidance plugin applies the same idea in a stronger form: model-backed reviews are separate Claude calls in fresh context rather than the writing instance grading itself. That is exactly the pattern you want for evals. citeturn31view4turn33view0

## How to measure settings, skills, hooks, agents, and rules in a defensible way

The cleanest discipline is to pre-specify a single primary endpoint for each candidate, then collect secondary measures that explain **why** a variant won or lost.

For a new rule in `CLAUDE.md`, the primary endpoint is usually task success or adherence on tasks that should be affected by the rule. Secondary metrics are how many corrective prompts were needed, whether the rule caused regressions on unrelated tasks, and whether context cost increased enough to harm long sessions. This matches Anthropic’s own advice: `CLAUDE.md` should contain only things whose removal would plausibly make Claude worse, because bloated files get ignored and can drown out live instructions. citeturn17view5turn14view7

For a skill, split the problem in two. Measure **effectiveness when invoked** and **invocation quality**. A good skill improves outcomes when used and has high precision/recall about when it should activate. Anthropic’s skills design supports both manual and automatic invocation, and gives you explicit ways to make a skill manual-only when side effects matter. It also supports `context: fork`, which is useful if you want a skill to run in isolation rather than inherit the main conversation. citeturn8view2turn10view3turn10view6

For hooks, score them as policy systems rather than prompting systems. The important outcomes are false blocks, missed blocks, added latency, and whether they actually improve downstream success. Anthropic’s hook system can make deterministic decisions before a tool runs, can inspect JSON inputs and outputs, and can even run agentic or prompt-based review hooks. That makes hooks ideal for hard constraints and review automation, but also means they are easy to overuse unless you explicitly measure nuisance costs. citeturn11view0turn26view3turn32search5

For subagents, compare them to both the main conversation and to alternative subagent setups. The most common wins are reduced main-context pollution, improved review independence, and better specialised focus. Anthropic’s docs suggest subagents mainly when output is verbose, work is self-contained, or tool restrictions matter; they suggest staying in the main conversation when tasks involve lots of shared context and iteration. Your eval should reflect exactly that trade-off. citeturn13view0turn17view3

For settings, use a small factorial design rather than one giant “best setup” claim. Compare model and effort separately from prompt/rule changes. Anthropic already distinguishes these knobs conceptually, recommends particular effort starting points for coding, and says prompt engineering is not always the right fix. citeturn19view0turn19view1

## The statistical layer you actually need

If your primary endpoint is binary — pass/fail on an executable task, reviewer-approved/not-approved, hook-block-correct/hook-block-incorrect — use a **paired** design and analyse the **discordant pairs**, not just the difference in average success rates. McNemar-style analysis exists exactly for paired binary outcomes. Power, sample size, alpha, and effect size are interdependent, so you should declare your smallest worthwhile improvement before you collect the full corpus rather than deciding afterwards that a tiny lift “probably matters”. citeturn5search2turn5search1

If your endpoint is ordinal or continuous — time-to-completion, number of reviewer findings, cost per successful task, or human-intervention count — use a paired resampling or randomisation approach rather than treating the two variants as independent samples. In NLP and adjacent evaluation work, paired bootstrap and approximate randomisation are standard tools; the methodological literature is explicit that significance testing is useful but that the right test depends on the task and metric rather than there being a universal favourite. citeturn6search3turn6search6

Do not let yourself test ten endpoints and five variants and then celebrate the one thing that moved. If you are doing confirmatory testing, pre-specify one primary outcome. If you are exploring many secondary outcomes, label them exploratory and control multiplicity sensibly, for example with false discovery rate methods where appropriate. That is basic anti-p-hacking hygiene, not statistical ornamentation. citeturn35search5turn35search1

The discipline I would recommend is simple. Before running the holdout, write down: the candidate, the control, the task distribution, the primary endpoint, the smallest useful effect, the analysis rule, and the stopping rule. Then live with that plan. If the result misses, either drop the candidate or reclassify the work as exploratory and iterate before another confirmatory run.

## Why so many public Claude Code evals look naive

My read is that this is mostly an incentives-and-operations problem, not an absence-of-statisticians.

Anthropic’s own tooling and docs make prompt-level iteration much easier than full harness evaluation. The Console Evaluation tool lives in the prompt editor and is built around prompt templates with dynamic variables; Anthropic’s prompt-engineering docs assume you already have success criteria, empirical tests, and a prompt draft. That is useful for prompt work, but it does not by itself solve the harder problem of evaluating agentic behaviour with tools, memory, permissions, hooks, subagents, compaction, and external systems. So people naturally reach for the easiest surface first. citeturn8view8turn19view1

The second reason is contamination. Good public evals are getting harder to maintain. Retro-holdout work shows that public availability can inflate benchmark scores; search-time contamination shows that search-based agents can retrieve question-answer pairs from public hosting sites during evaluation; and recent survey work argues that dynamic benchmarks lack standard design criteria and that contamination risks are now central, not peripheral. Even contamination **detection** assumptions are themselves under scrutiny. In other words, the field has real measurement debt. citeturn7search1turn7search3turn7search2turn7search0

The third reason is cost. A serious eval for Claude Code needs representative tasks, hidden or at least disciplined holdouts, repo isolation, executable verification or independent review, enough samples for meaningful power, and usually a second-pass reviewer or adversary. That is far more work than running twenty toy prompts in fresh contexts and tweeting a chart. Anthropic’s own more advanced review patterns — fresh-context subagent review, hook-driven model review, multi-agent PR review — all imply extra engineering and extra spend. citeturn31view4turn33view0turn34view0

So yes, some statistically literate people almost certainly use Claude Code. The reason you do not see more publication-grade evals is, in my view, that most users do not need them badly enough to pay the operational cost, and most public demonstrations optimise for speed, clarity, and social proof rather than for causal identification. That last point is partly an inference, but it fits the structure of the available tooling and the current contamination literature. citeturn8view8turn7search2turn7search3

## A practical measurement stack that is good enough to trust

Use three layers.

First, use **task-level holdout evals** in `claude -p` or the Agent SDK as your main decision-maker. Anthropic’s CLI supports structured JSON output and approximate cost reporting, and the SDK exposes per-step and per-model usage so you can compare both outcome quality and resource spend. Those cost fields are estimates rather than authoritative billing, but they are good enough for development-time comparison. citeturn25view0turn30view1

Second, use **OpenTelemetry** for operational observability. Claude Code can export metrics, events, and traces, including tool activity and events such as skill activation, hook execution, and compaction. That is useful for measuring things people routinely forget to count: how often a skill really fired, how often hooks ran, whether compaction happened before failures, and whether a candidate raises tool churn. citeturn30view0

Third, use **analytics dashboards** only as coarse long-run outcome measures. Anthropic’s analytics can show lines accepted, suggestion accept rate, daily active users and sessions, and for Teams or Enterprise, conservative contribution metrics such as “PRs with Claude Code”. Those are useful for adoption and ROI tracking, but they are broad and deliberately conservative. They are not strong evidence that one specific skill, hook, or instruction caused an improvement. citeturn28view0

The operational rule I would use is strict: a new skill, hook, agent, or persistent rule earns its place only if it improves a pre-specified primary endpoint on representative holdout tasks, survives independent fresh-context review, and does not blow up cost, latency, or nuisance rates. Everything else stays out of the default setup and remains an optional or manual tool.

## Open questions and limitations

There is no single official Anthropic recipe for statistically rigorous, personal-workflow Claude Code evals. Anthropic provides strong primitives — `claude -p`, `--bare`, `settingSources`, worktrees, hooks, subagents, telemetry, and review workflows — but not a full experimental methodology for comparing `CLAUDE.md`, skills, hooks, and agents in a research-grade way. citeturn25view0turn26view4turn30view0

Some relevant features are still evolving. Auto mode is explicitly a research preview; forked subagents are experimental; Code Review is also in research preview. That does not make them unusable, but it does mean that any eval conclusions involving them should be treated as version-specific and periodically rechecked. citeturn20search0turn13view0turn34view0

The most important limitation, though, is external validity. If your real day-to-day work depends on proprietary MCP tools, issue trackers, cloud CLIs, production-like repos, or long-lived resumed sessions, a neat clean-room eval on toy local tasks will not transfer. The right move is not to abandon rigour, but to bring the rigour into the actual environment you care about. Anthropic’s own design choices — same harness in CLI/SDK, worktree isolation, fresh-context review, and explicit context-management guidance — make that possible. citeturn25view0turn27search0turn31view4turn31view0