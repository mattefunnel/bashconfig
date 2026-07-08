import pathlib
B = pathlib.Path("/tmp/claude/cm-eval/iter3")
src = (B / "CLAUDE.md").read_text().splitlines(keepends=True)
(B / "variants").mkdir(exist_ok=True)
(B / "variants" / "full.txt").write_text("".join(src))
drop = set(range(107, 115))  # comments cluster incl. the match-surrounding-density override
kept = [l for i, l in enumerate(src, 1) if i not in drop]
(B / "variants" / "ablated-comments.txt").write_text("".join(kept))
print("full", len(src), "ablated", len(kept), "dropped", len(src) - len(kept))
