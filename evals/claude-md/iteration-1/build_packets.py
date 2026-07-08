import json, pathlib, random, string

BASE = pathlib.Path("/tmp/claude/cm-eval/iter1")
spec = json.loads((BASE / "rules.json").read_text())
(BASE / "grading" / "packets").mkdir(parents=True, exist_ok=True)
(BASE / "grading" / "keys").mkdir(parents=True, exist_ok=True)

missing = []
for ri, r in enumerate(spec["rules"]):
    rid = r["id"]
    items = []  # (cond, k, result_text)
    for cond in ("full", "ablated"):
        for k in range(1, 6):
            p = BASE / "runs" / rid / cond / f"run-{k}.json"
            if not p.exists() or p.stat().st_size == 0:
                missing.append(f"{rid}/{cond}/{k}")
                continue
            try:
                txt = json.loads(p.read_text()).get("result", "")
            except Exception:
                missing.append(f"{rid}/{cond}/{k}(parse)")
                continue
            items.append((cond, k, txt))
    rng = random.Random(1000 + ri)
    rng.shuffle(items)
    labels = [f"R{i:02d}" for i in range(len(items))]
    key = {}
    packet = [f"# Grading packet: rule `{rid}`\n",
              f"## Compliance rubric\n{r['rubric']}\n",
              "## Outputs to grade\nFor EACH output below, decide compliance with the rubric above. "
              "Judge only by the rubric. You do not know which condition produced which output.\n"]
    for lab, (cond, k, txt) in zip(labels, items):
        key[lab] = {"cond": cond, "k": k}
        packet.append(f"\n### Output {lab}\n```\n{txt}\n```\n")
    (BASE / "grading" / "packets" / f"{rid}.md").write_text("".join(packet))
    (BASE / "grading" / "keys" / f"{rid}.json").write_text(json.dumps(key, indent=2))

print(f"packets: {len(spec['rules'])}")
print(f"missing/empty cells: {len(missing)}")
if missing:
    print("  " + ", ".join(missing[:40]))
