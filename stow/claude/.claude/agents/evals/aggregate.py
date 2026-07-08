#!/usr/bin/env python3
"""Roll up agent-eval run outputs into per-cell mean/stdev metrics.

Usage: python3 aggregate.py            # prints tables + writes benchmark.json under each agent dir
Reads runs/<fixture>/<condition>/run-*.md, scores each with regexes, aggregates K runs/cell.
"""
import json, re, statistics
from pathlib import Path

ROOT = Path("/tmp/claude/agenteval")

# per-agent config: dir, fixtures -> word budget, condition list fixed
AGENTS = {
    "pr-watcher": {"multi": 150, "single": 200},
    "build-output-triage": {"fail": 200, "warn": 200},
    "parity-compare": {"bucket": 250, "truncate": 250},
}
CONDITIONS = ["vanilla", "agent"]

def words(t): return len(t.split())

def score(agent, fixture, text):
    wc = words(text)
    budget = AGENTS[agent][fixture]
    m = {"word_count": wc, "over_budget": int(wc > budget)}
    if agent == "pr-watcher":
        m["has_table"] = int(bool(re.search(r"\|.*\|.*\|", text)) or bool(re.search(r"(?im)^\s*[-*]?\s*(state|ci|review|mergeable)\s*:", text)))
        m["raw_json"] = int(bool(re.search(r'statusCheckRollup|__typename|"reviewDecision"|"headRefName"', text)))
    elif agent == "build-output-triage":
        m["correct_status"] = int(bool(re.search(r"(?i)\b(fail|error|did not compile|pass|built|compiled|success)\b", text)))
        raw = len(re.findall(r"-->", text)) + len(re.findall(r"(?im)^\s*(warning:|error\[)", text))
        m["raw_dump"] = int(raw >= 6)
    else:  # parity-compare
        m["is_punchlist"] = int(bool(re.search(r"\[(missing|partial|divergent)\]", text)) or len(re.findall(r"(?m)^\s*[-*]\s", text)) >= 2)
        base = fixture  # bucket / truncate
        rust = len(re.findall(rf"{base}\.rs:\d+", text))
        java = len(re.findall(rf"{base.capitalize()}\.java:\d+", text))
        m["has_filerefs"] = int(rust >= 2 and java >= 2)
    return m

def agg(vals):
    return {"mean": round(statistics.mean(vals), 2),
            "stdev": round(statistics.pstdev(vals), 2) if len(vals) > 1 else 0.0,
            "n": len(vals)}

for agent, fixtures in AGENTS.items():
    bench = {}
    for fixture in fixtures:
        for cond in CONDITIONS:
            d = ROOT / agent / "iteration-1" / "runs" / fixture / cond
            files = sorted(d.glob("run-*.md")) if d.exists() else []
            per = [score(agent, fixture, f.read_text()) for f in files]
            if not per:
                continue
            keys = per[0].keys()
            bench[f"{fixture}/{cond}"] = {k: agg([p[k] for p in per]) for k in keys}
    out = ROOT / agent / "iteration-1" / "benchmark.json"
    out.write_text(json.dumps(bench, indent=2))
    print(f"\n=== {agent} ===")
    for cell, metrics in bench.items():
        print(f"  {cell}")
        for k, v in metrics.items():
            print(f"    {k:14s} {v['mean']:>8} ± {v['stdev']:<6} (n={v['n']})")
