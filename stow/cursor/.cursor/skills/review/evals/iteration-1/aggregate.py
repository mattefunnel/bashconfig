#!/usr/bin/env python3
"""Aggregate eval grading.json files into a benchmark summary."""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).parent / "runs"
FIXTURES = ["fixture-1", "fixture-2"]
CONDITIONS = ["with_skill", "no_hotspots"]
MODELS = ["opus", "sonnet"]
RUNS = list(range(1, 7))

# Map outcomes to numeric score for aggregation
TP_SCORE = {"tp": 1.0, "tp_partial": 0.5, "missing": 0.0}
SILENCE_SCORE = {"correct_silence": 1.0, "fp_soft": 0.5, "fp": 0.0}


def normalize(v):
    """Some graders returned {'verdict': '...', 'note': '...'} instead of a plain string."""
    if isinstance(v, dict):
        return v.get("verdict") or v.get("value") or v.get("score") or ""
    return v


def load_grading(fixture, condition, model, run):
    path = ROOT / fixture / condition / model / f"run-{run}" / "grading.json"
    if not path.exists():
        return None
    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def per_cell_stats(fixture, condition, model):
    runs = [load_grading(fixture, condition, model, r) for r in RUNS]
    runs = [r for r in runs if r is not None]
    if not runs:
        return None

    tp_rates = []
    silence_rates = []
    raw_tp = []
    raw_silence = []
    fp_count = 0
    fp_soft_count = 0
    tp_strict_count = 0
    missing_count = 0

    p_outcomes = {f"P{i}": [] for i in range(1, 6)}
    c_outcomes = {f"C{i}": [] for i in range(1, 4)}

    for r in runs:
        # TP rate per run: avg of TP_SCORE across 5 P items
        p_items = r.get("planted", {})
        c_items = r.get("controls", {})

        tp_run = []
        for k, v in p_items.items():
            nv = normalize(v)
            tp_run.append(TP_SCORE.get(nv, 0.0))
            p_outcomes.setdefault(k, []).append(nv)
            if nv == "tp":
                tp_strict_count += 1
            elif nv == "missing":
                missing_count += 1

        silence_run = []
        for k, v in c_items.items():
            nv = normalize(v)
            silence_run.append(SILENCE_SCORE.get(nv, 0.0))
            c_outcomes.setdefault(k, []).append(nv)
            if nv == "fp":
                fp_count += 1
            elif nv == "fp_soft":
                fp_soft_count += 1

        if tp_run:
            tp_rates.append(statistics.mean(tp_run))
        if silence_run:
            silence_rates.append(statistics.mean(silence_run))

    return {
        "n_runs": len(runs),
        "tp_rate_mean": statistics.mean(tp_rates) if tp_rates else 0,
        "tp_rate_stdev": statistics.stdev(tp_rates) if len(tp_rates) > 1 else 0,
        "silence_rate_mean": statistics.mean(silence_rates) if silence_rates else 0,
        "silence_rate_stdev": statistics.stdev(silence_rates) if len(silence_rates) > 1 else 0,
        "fp_total": fp_count,
        "fp_soft_total": fp_soft_count,
        "tp_strict_total": tp_strict_count,
        "missing_total": missing_count,
        "p_outcomes": p_outcomes,
        "c_outcomes": c_outcomes,
    }


def main():
    print("# Benchmark Summary\n")
    print(f"Each cell = {len(RUNS)} runs. TP rate = mean score on 5 planted items (tp=1, tp_partial=0.5, missing=0).")
    print(f"Silence rate = mean score on 3 controls (correct_silence=1, fp_soft=0.5, fp=0).\n")

    # Aggregate by cell
    cells = {}
    for fx in FIXTURES:
        for cond in CONDITIONS:
            for mdl in MODELS:
                cells[(fx, cond, mdl)] = per_cell_stats(fx, cond, mdl)

    # Table: per-cell summary
    print("## Per-cell scores\n")
    print(f"{'fixture':<10} {'condition':<14} {'model':<8} {'n':>3}  {'TP_rate':>10}  {'silence':>10}  {'FP':>4}  {'FP_soft':>8}")
    print("-" * 80)
    for (fx, cond, mdl), s in cells.items():
        if s is None:
            print(f"{fx:<10} {cond:<14} {mdl:<8}  NO DATA")
            continue
        tp = f"{s['tp_rate_mean']:.2f}±{s['tp_rate_stdev']:.2f}"
        sil = f"{s['silence_rate_mean']:.2f}±{s['silence_rate_stdev']:.2f}"
        print(f"{fx:<10} {cond:<14} {mdl:<8} {s['n_runs']:>3}  {tp:>10}  {sil:>10}  {s['fp_total']:>4}  {s['fp_soft_total']:>8}")

    # Roll up by condition × model (across both fixtures)
    print("\n## Roll-up by condition × model (across both fixtures)\n")
    print(f"{'condition':<14} {'model':<8} {'n':>3}  {'TP_rate':>10}  {'silence':>10}  {'FP':>4}  {'FP_soft':>8}")
    print("-" * 70)
    for cond in CONDITIONS:
        for mdl in MODELS:
            all_tp_rates = []
            all_sil_rates = []
            fp_total = 0
            fp_soft_total = 0
            n_runs = 0
            for fx in FIXTURES:
                s = cells.get((fx, cond, mdl))
                if s is None:
                    continue
                # We need the per-run rates not the mean to compute stdev across all runs
                runs = [load_grading(fx, cond, mdl, r) for r in RUNS]
                runs = [r for r in runs if r is not None]
                for r in runs:
                    p_items = r.get("planted", {})
                    c_items = r.get("controls", {})
                    tp_run = [TP_SCORE.get(normalize(v), 0.0) for v in p_items.values()]
                    sil_run = [SILENCE_SCORE.get(normalize(v), 0.0) for v in c_items.values()]
                    _ = (tp_run, sil_run)
                    if tp_run:
                        all_tp_rates.append(statistics.mean(tp_run))
                    if sil_run:
                        all_sil_rates.append(statistics.mean(sil_run))
                fp_total += s['fp_total']
                fp_soft_total += s['fp_soft_total']
                n_runs += s['n_runs']
            if not all_tp_rates:
                continue
            tp_m = statistics.mean(all_tp_rates)
            tp_s = statistics.stdev(all_tp_rates) if len(all_tp_rates) > 1 else 0
            sil_m = statistics.mean(all_sil_rates)
            sil_s = statistics.stdev(all_sil_rates) if len(all_sil_rates) > 1 else 0
            print(f"{cond:<14} {mdl:<8} {n_runs:>3}  {tp_m:.2f}±{tp_s:.2f}  {sil_m:.2f}±{sil_s:.2f}  {fp_total:>4}  {fp_soft_total:>8}")

    # Per-item breakdown for the with_skill vs no_hotspots comparison
    print("\n## Per-item TP rate, by condition × model (both fixtures combined)\n")
    print(f"{'item':<6} {'condition':<14} {'model':<8} {'tp%':>6} {'partial%':>9} {'miss%':>7}")
    print("-" * 60)
    for fx, item_set in [("fixture-1", [f"P{i}" for i in range(1,6)]), ("fixture-2", [f"P{i}" for i in range(1,6)])]:
        for item in item_set:
            for cond in CONDITIONS:
                for mdl in MODELS:
                    runs = [load_grading(fx, cond, mdl, r) for r in RUNS]
                    runs = [r for r in runs if r is not None]
                    outs = [normalize(r.get("planted", {}).get(item, "?")) for r in runs]
                    n = len(outs)
                    if n == 0:
                        continue
                    tp_pct = 100 * outs.count("tp") / n
                    pp_pct = 100 * outs.count("tp_partial") / n
                    miss_pct = 100 * outs.count("missing") / n
                    print(f"{fx[-1]}/{item:<3} {cond:<14} {mdl:<8} {tp_pct:>5.0f}% {pp_pct:>8.0f}% {miss_pct:>6.0f}%")

    # Per-control item: % correct silence
    print("\n## Per-control: % correct_silence, by condition × model\n")
    print(f"{'item':<6} {'condition':<14} {'model':<8} {'silence%':>9} {'fp_soft%':>9} {'fp%':>5}")
    print("-" * 60)
    for fx in FIXTURES:
        for item in ["C1", "C2", "C3"]:
            for cond in CONDITIONS:
                for mdl in MODELS:
                    runs = [load_grading(fx, cond, mdl, r) for r in RUNS]
                    runs = [r for r in runs if r is not None]
                    outs = [normalize(r.get("controls", {}).get(item, "?")) for r in runs]
                    n = len(outs)
                    if n == 0:
                        continue
                    cs = 100 * outs.count("correct_silence") / n
                    fps = 100 * outs.count("fp_soft") / n
                    fp = 100 * outs.count("fp") / n
                    print(f"{fx[-1]}/{item:<3} {cond:<14} {mdl:<8} {cs:>8.0f}% {fps:>8.0f}% {fp:>4.0f}%")

    # Save to benchmark.json
    benchmark = {
        "cells": {f"{fx}/{cond}/{mdl}": s for (fx, cond, mdl), s in cells.items()},
    }
    with open(ROOT.parent / "benchmark.json", "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"\nbenchmark.json written to {ROOT}/benchmark.json")


if __name__ == "__main__":
    main()
