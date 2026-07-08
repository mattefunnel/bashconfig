import json, pathlib

BASE = pathlib.Path("/tmp/claude/cm-eval/iter1")
spec = json.loads((BASE / "rules.json").read_text())
src = (BASE / "artifact-snapshot" / "CLAUDE.md").read_text().splitlines(keepends=True)
framing = "\n\n---\n" + spec["neutral_framing"] + "\n"
vdir = BASE / "variants"
vdir.mkdir(parents=True, exist_ok=True)

# FULL = entire CLAUDE.md + framing
(vdir / "full.txt").write_text("".join(src) + framing)

# ABLATED-<id> = CLAUDE.md minus the rule's 1-indexed line ranges + framing
for r in spec["rules"]:
    drop = set()
    for a, b in r["lines"]:
        drop.update(range(a, b + 1))  # 1-indexed inclusive
    kept = [ln for i, ln in enumerate(src, start=1) if i not in drop]
    (vdir / f"ablated-{r['id']}.txt").write_text("".join(kept) + framing)
    print(f"{r['id']:12s} dropped {len(drop):2d} lines -> ablated-{r['id']}.txt ({len(kept)} lines kept)")

print(f"\nfull.txt: {len(src)} lines + framing")
print(f"rules: {len(spec['rules'])}  cells: {len(spec['rules'])*2*5}")
