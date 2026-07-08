import subprocess, pathlib, statistics as st
B = pathlib.Path("/tmp/claude/cm-eval/iter3")
orig = B / "fixture" / "PartitionDistributedQuery.ts"
res = {"full": [], "ablated": []}
detail = {}
for cond, kn in (("full", 5), ("ablated", 15)):
    for k in range(1, kn + 1):
        f = B / "runs" / cond / f"k{k}" / "PartitionDistributedQuery.ts"
        if not f.exists():
            continue
        d = subprocess.run(["diff", str(orig), str(f)], capture_output=True, text=True).stdout
        added = [l[2:] for l in d.splitlines() if l.startswith("> ")]
        code = [l for l in added if l.strip()]
        comments = [l for l in added if l.strip().startswith("//")]
        res[cond].append(len(comments))
        detail[f"{cond}/k{k}"] = {"added_code_lines": len(code), "comment_lines": len(comments)}
print("comment lines added per cell (matching the heavily-commented file = drift):")
for cond in ("full", "ablated"):
    v = res[cond]
    m = round(st.mean(v), 2) if v else None
    print(f"  {cond:8s} mean={m}  per-cell={v}")
print("\nper-cell detail:")
for k, v in detail.items():
    print(f"  {k}: +{v['added_code_lines']} code lines, {v['comment_lines']} comments")
(B / "grading" / "metrics.json").write_text(__import__("json").dumps({"res": res, "detail": detail}, indent=2))
