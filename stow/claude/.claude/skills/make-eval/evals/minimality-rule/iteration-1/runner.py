import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

BASE = "/Users/mattias.johansson/.claude/skills/make-eval/evals/minimality-rule/iteration-1"
SCRATCH = "/tmp/claude/mineval"
CLAUDE = "/Users/mattias.johansson/.local/bin/claude"
K = 15
MODEL = "sonnet"
TIMEOUT = 900

RULE = open(f"{BASE}/rule.txt").read()

FIXTURES = [
    {"name": "f1", "file": "events.py", "src": f"{BASE}/fixtures/f1_events.py", "tasks": f"{BASE}/fixtures/f1_tasks.md"},
    {"name": "f2", "file": "handlers.ts", "src": f"{BASE}/fixtures/f2_handlers.ts", "tasks": f"{BASE}/fixtures/f2_tasks.md"},
]
CONDITIONS = ["control", "treatment"]


def run_one(fx, cond, k):
    scratch = f"{SCRATCH}/{fx['name']}/{cond}/run-{k}"
    os.makedirs(scratch, exist_ok=True)
    shutil.copy(fx["src"], f"{scratch}/{fx['file']}")
    prompt = open(fx["tasks"]).read()
    args = [CLAUDE, "-p", "--setting-sources", "project",
            "--dangerously-skip-permissions", "--model", MODEL]
    if cond == "treatment":
        args += ["--append-system-prompt", RULE]
    args.append(prompt)
    outdir = f"{BASE}/runs/{fx['name']}/{cond}/run-{k}"
    os.makedirs(outdir, exist_ok=True)
    try:
        r = subprocess.run(args, cwd=scratch, capture_output=True, text=True, timeout=TIMEOUT)
        transcript = r.stdout + ("\n[STDERR]\n" + r.stderr if r.stderr else "")
    except subprocess.TimeoutExpired:
        transcript = "[TIMEOUT]"
    open(f"{outdir}/transcript.txt", "w").write(transcript)
    shutil.copy(f"{scratch}/{fx['file']}", f"{outdir}/{fx['file']}")
    return f"{fx['name']}/{cond}/run-{k}"


jobs = [(fx, c, k) for fx in FIXTURES for c in CONDITIONS for k in range(1, K + 1)]
done = 0
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(run_one, *j) for j in jobs]
    for f in futs:
        done += 1
        print(f"[{done}/{len(jobs)}] {f.result()}", flush=True)
print("DONE", flush=True)
