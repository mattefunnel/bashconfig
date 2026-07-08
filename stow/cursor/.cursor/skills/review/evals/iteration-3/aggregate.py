import json
import math
from pathlib import Path

ROOT = Path(__file__).parent
RUNS = ROOT / "runs"

CONDITIONS = ["with_scoping", "no_scoping"]
MODELS = ["sonnet", "opus"]


def mean_std(xs):
    if not xs:
        return (None, None)
    m = sum(xs) / len(xs)
    if len(xs) == 1:
        return (m, 0.0)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return (m, math.sqrt(var))


def score_run(g):
    planted = g.get("planted", {})
    controls = g.get("controls", {})
    n_p = len(planted) or 1
    n_c = len(controls) or 1
    tp = sum(1 for v in planted.values() if v == "tp")
    tpp = sum(1 for v in planted.values() if v == "tp_partial")
    cs = sum(1 for v in controls.values() if v == "correct_silence")
    fps = sum(1 for v in controls.values() if v == "fp_soft")
    fp = sum(1 for v in controls.values() if v == "fp")
    return {
        "tp_rate": (tp + 0.5 * tpp) / n_p,
        "silence_rate": (cs + 0.5 * fps) / n_c,
        "fp": fp,
    }


def main():
    bench = {}
    fixtures = sorted(p.name for p in RUNS.iterdir() if p.is_dir())
    for fx in fixtures:
        for cond in CONDITIONS:
            for model in MODELS:
                cell = RUNS / fx / cond / model
                if not cell.is_dir():
                    continue
                tp_rates, sil_rates, hard_fps = [], [], 0
                for run_dir in sorted(cell.iterdir()):
                    gj = run_dir / "grading.json"
                    if not gj.exists():
                        continue
                    g = json.loads(gj.read_text())
                    s = score_run(g)
                    tp_rates.append(s["tp_rate"])
                    sil_rates.append(s["silence_rate"])
                    hard_fps += s["fp"]
                if not tp_rates:
                    continue
                tpm, tps = mean_std(tp_rates)
                slm, sls = mean_std(sil_rates)
                bench[f"{fx}/{cond}/{model}"] = {
                    "n": len(tp_rates),
                    "tp_rate_mean": round(tpm, 3),
                    "tp_rate_std": round(tps, 3),
                    "silence_rate_mean": round(slm, 3),
                    "silence_rate_std": round(sls, 3),
                    "hard_fps": hard_fps,
                }

    (ROOT / "benchmark.json").write_text(json.dumps(bench, indent=2) + "\n")

    print(f"{'cell':<48} {'n':>2} {'TP':>13} {'silence':>13} {'hardFP':>7}")
    print("-" * 88)
    for k in sorted(bench):
        b = bench[k]
        tp = f"{b['tp_rate_mean']:.2f}±{b['tp_rate_std']:.2f}"
        sl = f"{b['silence_rate_mean']:.2f}±{b['silence_rate_std']:.2f}"
        print(f"{k:<48} {b['n']:>2} {tp:>13} {sl:>13} {b['hard_fps']:>7}")


if __name__ == "__main__":
    main()
