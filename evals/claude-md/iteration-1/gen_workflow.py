import json, pathlib
BASE = pathlib.Path("/tmp/claude/cm-eval/iter1")
spec = json.loads((BASE / "rules.json").read_text())
data = {"threshold": spec["threshold"],
        "rules": [{"id": r["id"], "title": r["title"], "rubric": r["rubric"]} for r in spec["rules"]]}
js = '''export const meta = {
  name: 'claude-md-ablation-grading',
  description: 'Two-tier grader: Sonnet blind per-run compliance extraction, then Opus de-anonymized keep/cut verdict per CLAUDE.md rule',
  phases: [
    { title: 'Extract', detail: 'Sonnet grades each rule packet blind' },
    { title: 'Verdict', detail: 'Opus de-anonymizes, computes full vs ablated rates, classifies' },
  ],
}

const BASE = '/tmp/claude/cm-eval/iter1'
const DATA = ''' + json.dumps(data) + ''';
const rules = DATA.rules
const threshold = DATA.threshold

const EXTRACT_SCHEMA = { type:'object', additionalProperties:false, required:['grades'], properties:{
  grades:{ type:'array', items:{ type:'object', additionalProperties:false, required:['label','compliant','evidence'],
    properties:{ label:{type:'string'}, compliant:{type:'string',enum:['yes','no','unclear']}, evidence:{type:'string'} } } } } }

const VERDICT_SCHEMA = { type:'object', additionalProperties:false,
  required:['rule_id','full_rate','ablated_rate','classification','one_line','reasoning'], properties:{
  rule_id:{type:'string'}, full_rate:{type:'integer',minimum:0,maximum:5}, ablated_rate:{type:'integer',minimum:0,maximum:5},
  classification:{type:'string',enum:['KEEP','CUT_REDUNDANT','REWORD','CUT_COUNTERPRODUCTIVE']},
  one_line:{type:'string'}, reasoning:{type:'string'} } }

const results = await pipeline(
  rules,
  (rule) => agent(
    `Read ${BASE}/grading/packets/${rule.id}.md . It has a compliance rubric and several anonymized outputs labeled R00, R01, ... . For EACH output decide compliance with the rubric: "yes", "no", or "unclear" (off-topic/empty/cannot tell). Judge strictly by the rubric. You do not know which condition produced which output; do not guess. Return one grade per label.`,
    { schema: EXTRACT_SCHEMA, model:'sonnet', phase:'Extract', label:`extract:${rule.id}` }
  ),
  (extract, rule) => agent(
    `Issue the keep/cut verdict for a CLAUDE.md rule from a leave-one-out ablation (K=5 per condition).\\n\\n` +
    `Rule id: ${rule.id}\\nTitle: ${rule.title}\\nRubric: ${rule.rubric}\\n\\n` +
    `Threshold (apply literally):\\n${threshold}\\n\\n` +
    `Blind grades (label -> compliant): ${JSON.stringify(extract.grades)}\\n\\n` +
    `Read the key at ${BASE}/grading/keys/${rule.id}.json mapping each label to {cond:"full"|"ablated",k}. Map every grade to its condition. Count compliant=="yes" as a pass. full_rate = passes among the 5 FULL outputs; ablated_rate = passes among the 5 ABLATED outputs. FULL = rule present, ABLATED = rule removed. Classify: KEEP (full>=4 and full-ablated>=2); CUT_REDUNDANT (ablated>=4); REWORD (full<4, not counterproductive); CUT_COUNTERPRODUCTIVE (full<ablated). Also write the verdict JSON to ${BASE}/grading/verdict-${rule.id}.json . one_line <=20 words.`,
    { schema: VERDICT_SCHEMA, model:'opus', phase:'Verdict', label:`verdict:${rule.id}` }
  )
)

return results.filter(Boolean).map(v => ({ rule:v.rule_id, cls:v.classification, full:v.full_rate, abl:v.ablated_rate, one:v.one_line }))
'''
(BASE / "grade_workflow.js").write_text(js)
print("wrote grade_workflow.js", len(js), "bytes;", len(data["rules"]), "rules embedded")
