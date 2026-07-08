import json, pathlib
B = pathlib.Path("/tmp/claude/cm-eval/iter2")
src = (B/"CLAUDE.md").read_text().splitlines(keepends=True)
frame = "\n\n---\nYou are pair-programming with me in a terminal session. When I ask for a function, respond with the Rust code."
(B/"variants").mkdir(exist_ok=True)
(B/"variants"/"full.txt").write_text("".join(src)+frame)
drop = {105,106,109,110,111,112,113,114,115,116,117}
kept = [l for i,l in enumerate(src,1) if i not in drop]
(B/"variants"/"ablated-min.txt").write_text("".join(kept)+frame)
print("full", len(src), "ablated-min", len(kept), "dropped", len(src)-len(kept))
