import json
import os
import re
from statistics import mean, pstdev

BASE = "/Users/mattias.johansson/.claude/skills/make-eval/evals/minimality-rule/iteration-1"
RUNS = f"{BASE}/runs"
FIX = {"f1": "events.py", "f2": "handlers.ts"}
CONDS = ["control", "treatment"]
CATS = ["total", "try", "comments", "norm", "logging", "guards"]


def count_py(t):
    lines = t.splitlines()
    comments = sum(1 for l in lines if l.strip().startswith("#") and not l.strip().startswith("#!"))
    comments += t.count('"""') // 2
    tryb = len(re.findall(r"\btry\s*:", t))
    norm = len(re.findall(r"\.strip\(|\.lower\(|\.upper\(", t))
    logging_ = t.count("print(") + len(re.findall(r"\blogging\.|\blogger\.", t))
    guards = len(re.findall(r"\bif not \b", t)) + t.count(" is None") + len(re.findall(r"\.get\(|\bisinstance\(", t))
    c = {"comments": comments, "try": tryb, "norm": norm, "logging": logging_, "guards": guards}
    c["total"] = sum(c.values())
    return c


def count_ts(t):
    lines = t.splitlines()
    comments = sum(1 for l in lines if l.strip().startswith(("//", "/*", "*")))
    tryb = len(re.findall(r"\btry\s*\{", t))
    norm = len(re.findall(r"\.trim\(|\.toLowerCase\(|\.toUpperCase\(", t))
    logging_ = len(re.findall(r"\bconsole\.", t))
    guards = len(re.findall(r"if \(!", t)) + t.count("=== undefined") + t.count("=== null") + t.count("== null") + len(re.findall(r"\bisNaN\(", t)) + t.count("?? ")
    c = {"comments": comments, "try": tryb, "norm": norm, "logging": logging_, "guards": guards}
    c["total"] = sum(c.values())
    return c


agg = {}
print(f"{'cell':18} n   " + "  ".join(f"{c:>8}" for c in CATS))
for fx, fname in FIX.items():
    counter = count_py if fx == "f1" else count_ts
    for cond in CONDS:
        d = f"{RUNS}/{fx}/{cond}"
        cells = [counter(open(f"{d}/{r}/{fname}").read()) for r in sorted(os.listdir(d))]
        row = {c: mean(x[c] for x in cells) for c in CATS}
        row["total_sd"] = pstdev([x["total"] for x in cells])
        agg[f"{fx}/{cond}"] = {"n": len(cells), **row}
        print(f"{fx}/{cond:11} {len(cells):2}   " + "  ".join(f"{row[c]:8.2f}" for c in CATS) + f"   (sd {row['total_sd']:.2f})")

print()
for fx in FIX:
    ct = agg[f"{fx}/control"]["total"]
    tr = agg[f"{fx}/treatment"]["total"]
    print(f"{fx}: control={ct:.2f}  treatment={tr:.2f}  reduction(control-treatment)={ct - tr:+.2f}")

ctrl_all = mean(agg[f"{fx}/control"]["total"] for fx in FIX)
trt_all = mean(agg[f"{fx}/treatment"]["total"] for fx in FIX)
print(f"\nOVERALL: control={ctrl_all:.2f}  treatment={trt_all:.2f}  reduction={ctrl_all - trt_all:+.2f}  (threshold to keep: >= 1.5)")

json.dump(agg, open(f"{BASE}/benchmark.json", "w"), indent=2)
