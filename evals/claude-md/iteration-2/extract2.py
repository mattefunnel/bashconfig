import json, re, pathlib, statistics as st

B = pathlib.Path("/tmp/claude/cm-eval/iter2")
CODE_TURNS = [3, 6, 9, 11]
CONDS = ["full", "ablated"]
KS = [1, 2, 3, 4]

def code_blocks(md):
    return "\n".join(re.findall(r"```(?:rust)?\n(.*?)```", md, re.S))

def metrics(code):
    lines = code.splitlines()
    comment = sum(1 for l in lines if re.search(r"(^|\s)//(?!/)", l) and "://" not in l)
    doc = sum(1 for l in lines if l.strip().startswith("///") or l.strip().startswith("//!"))
    log = sum(1 for l in lines if re.search(r"\b(log::|log\.|tracing::|info!|debug!|trace!|warn!|error!|println!|eprintln!|console\.log)", l))
    fns = len(re.findall(r"\bfn\s+\w+", code))
    nonblank = sum(1 for l in lines if l.strip())
    return dict(comment=comment, doc=doc, log=log, fns=fns, code_lines=nonblank)

rows = {c: {t: [] for t in CODE_TURNS} for c in CONDS}
missing = []
for c in CONDS:
    for k in KS:
        for t in CODE_TURNS:
            p = B / "runs" / c / f"k{k}" / f"turn-{t:02d}.json"
            if not p.exists() or p.stat().st_size == 0:
                missing.append(f"{c}/k{k}/t{t}"); continue
            try:
                res = json.loads(p.read_text()).get("result", "")
            except Exception:
                missing.append(f"{c}/k{k}/t{t}(parse)"); continue
            rows[c][t].append(metrics(code_blocks(res)))

def avg(c, t, key):
    vals = [m[key] for m in rows[c][t]]
    return round(st.mean(vals), 2) if vals else None

print(f"missing/empty turns: {len(missing)}  {missing[:20]}")
print("\nMean COMMENT lines per code turn (drift = rise across turns):")
print(f"{'cond':9s} " + "  ".join(f"t{t:>2d}" for t in CODE_TURNS))
for c in CONDS:
    print(f"{c:9s} " + "  ".join(f"{avg(c,t,'comment'):>4}" for t in CODE_TURNS))
print("\nMean LOG statements per code turn:")
for c in CONDS:
    print(f"{c:9s} " + "  ".join(f"{avg(c,t,'log'):>4}" for t in CODE_TURNS))
print("\nMean fn-count (helper proliferation proxy):")
for c in CONDS:
    print(f"{c:9s} " + "  ".join(f"{avg(c,t,'fns'):>4}" for t in CODE_TURNS))
print("\nMean DOC-comment lines per code turn:")
for c in CONDS:
    print(f"{c:9s} " + "  ".join(f"{avg(c,t,'doc'):>4}" for t in CODE_TURNS))

summary = {c: {t: {key: avg(c, t, key) for key in ["comment","doc","log","fns","code_lines"]} for t in CODE_TURNS} for c in CONDS}
(B / "grading" / "metrics.json").write_text(json.dumps({"summary": summary, "raw": {c: {str(t): rows[c][t] for t in CODE_TURNS} for c in CONDS}, "missing": missing}, indent=2))
print("\nwrote grading/metrics.json")
