# Meta-eval rubric

For grading eval designs produced by either vanilla (condition A) or with-skill (condition B) subagents.

Score each criterion 0–2:
- **2** — strong: criterion is clearly demonstrated with concrete specifics.
- **1** — acceptable: criterion is gestured at but vague or partial.
- **0** — poor: criterion missing, or design falls into the known bad approach for it.

Max total: 20 per design.

## Criteria

### 1. Hypothesis quality

- **2:** specific, testable, falsifiable claim with a concrete metric. E.g. "the Hotspots section improves Sonnet TP rate by ≥20pp on defense-heavy fixtures".
- **1:** general claim but testable. "the skill helps with X".
- **0:** vague ("the skill makes things better") or untestable.

### 2. Condition design

- **2:** A vs B differ in EXACTLY ONE variable. The variable is named explicitly. Both conditions are concrete.
- **1:** A vs B clearly different but the variable is fuzzy (e.g. multiple sections changed at once).
- **0:** conditions overlap or differ in uncontrolled ways. Only one condition specified.

### 3. Fixture quality

- **2:** 2+ fixtures with diverse stress dimensions. Each has plants + controls (or equivalent depth). Ground truth specified.
- **1:** 1 fixture with depth, OR 2+ fixtures but without controls.
- **0:** toy fixtures, single shallow fixture, or no ground truth.

### 4. Isolation strategy

- **2:** explicit plan to prevent poisoning. Uses subagent isolation + corpus scoping (real file copies, NOT symlinks) when needed. Forbids out-of-corpus reads in the prompt.
- **1:** mentions isolation but doesn't detail HOW. Or uses subagents but skips corpus when one was needed.
- **0:** ignores poisoning risk entirely. Proposes symlinks for the corpus.

### 5. Sample size justification

- **2:** K≥3 with rationale. Variance estimates planned. K=1 explicitly avoided OR labeled "directional only".
- **1:** K≥3 mentioned but not defended. K=2 with rationale.
- **0:** K=1 without disclaimer. No K specified.

### 6. Scoring approach

- **2:** scoring rubric pre-declared. Auto vs manual decision matches fixture shape. For auto-graded: grader prompt structure specified.
- **1:** rubric mentioned but partial. Auto vs manual decision somewhat justified.
- **0:** no rubric, or post-hoc scoring proposed.

### 7. Cost estimate

- **2:** rough $ estimate based on run count × model rates. Mentions wall-clock.
- **1:** mentions cost qualitatively but without numbers.
- **0:** no cost estimate.

### 8. Anti-pattern avoidance

- **2:** explicitly dodges 3+ of the known anti-patterns (symlinks, K=1 evidence, post-hoc rubric, fixture regeneration, grader drift, hard caps producing artificial variance, single-model generalization, missing snapshots, cost runaway, tool-prescriptive playbooks, small fixture samples, regenerated fixtures, etc.).
- **1:** dodges 1–2 anti-patterns.
- **0:** falls into at least one anti-pattern (symlinks, K=1, post-hoc rubric, single fixture).

### 9. Report structure

- **2:** README skeleton includes TL;DR table + verdict + observations + limitations + how-to-re-run + cost. Clearly delineated sections.
- **1:** README has most sections but some missing.
- **0:** no report structure proposed, just unstructured prose.

### 10. Tone honesty

- **2:** verdict structure explicitly allows for negative findings ("if the skill doesn't help, the report says so"). Pre-registered predictions where applicable.
- **1:** verdict is structured but doesn't pre-commit to honesty.
- **0:** verdict structure biased toward "skill works".

## Plant / control cross-check

Each fixture's `expected design elements` (plants) and `known bad approaches` (controls) inform the rubric scores:
- Hitting a plant → +1 to the relevant criterion (cap at 2).
- Violating a control → 0 on the relevant criterion (override partial credit).

## Grader output

JSON written to `<OUTPUT_PATH>/grading.json`:

```json
{
  "scores": {
    "hypothesis_quality": 0|1|2,
    "condition_design": 0|1|2,
    "fixture_quality": 0|1|2,
    "isolation_strategy": 0|1|2,
    "sample_size": 0|1|2,
    "scoring_approach": 0|1|2,
    "cost_estimate": 0|1|2,
    "anti_pattern_avoidance": 0|1|2,
    "report_structure": 0|1|2,
    "tone_honesty": 0|1|2
  },
  "total": <0-20>,
  "plants_hit": ["list of expected design elements that were present"],
  "controls_violated": ["list of bad approaches the design fell into"],
  "notes": "1-2 sentences on standout strengths or weaknesses"
}
```
