#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py — run every experiment, write canonical outputs and figures.

Outputs (in ./output):
  results.json        — all summary statistics (means, 95% CIs, percentiles, sensitivity)
  raw_replicas.jsonl  — one auditable record per experiment (params, seed, histogram, summary)
  fig1_blast_distribuicao.png, fig2_blast_vs_segmentos.png,
  fig3_heatmap_seg_deteccao.png, fig4_fronteira_seg_perf.png,
  fig5_sensibilidade.png

Code, docs, metadata and figure labels are in English (the model is a
standalone algorithm).

Reproducibility: deterministic (numpy default_rng with fixed seeds). Re-running
yields bit-identical results.json. After this, run make_provenance.py to bind
the SHA-256 hash chain.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import blast_radius as br

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)
C_FLAT, C_MICRO, C_FAST = "#d95f0e", "#2c7fb8", "#1a9850"


def histogram(arr, bins=50):
    counts, edges = np.histogram(arr, bins=bins, range=(0, 1))
    return {"bin_edges": [round(float(e), 4) for e in edges],
            "counts": [int(c) for c in counts]}


def main():
    arrays, scen = br.main_scenarios()
    sweep = br.segment_sweep()
    heat = br.detection_heatmap()
    sens = br.sensitivity()
    overhead = br.east_west_overhead()

    results = {
        "model": "segment-level SI contact process with bounded fan-out",
        "master_seed": br.MASTER_SEED,
        "params": {"n_hosts": br.N_HOSTS, "deg": br.DEG, "p_compromise": br.P_COMPROMISE,
                   "cross_share": br.CROSS_SHARE, "leak_fraction": br.LEAK_FRACTION,
                   "d_slow": br.D_SLOW, "d_fast": br.D_FAST, "delta_ms": br.DELTA_MS},
        "trials": {"main": br.TRIALS_MAIN, "sweep": br.TRIALS_SWEEP,
                   "heatmap_per_cell": br.TRIALS_HEATMAP, "sensitivity_per_cell": br.TRIALS_SENS},
        "main_scenarios": scen,
        "segment_sweep": {str(k): v for k, v in sweep.items()},
        "detection_heatmap": heat,
        "sensitivity": sens,
        "east_west_overhead_ms": {str(k): round(v, 4) for k, v in overhead.items()},
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

    with (OUT / "raw_replicas.jsonl").open("w") as fh:
        for name, a in arrays.items():
            rec = {"experiment": name, "n": int(a.size),
                   "summary": br.summarize(a), "histogram": histogram(a)}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    _figures(arrays, scen, sweep, heat, sens, overhead)

    print(json.dumps({
        "flat_slow_mean": scen["flat_slow"]["mean"],
        "micro_slow_mean": scen["micro_slow"]["mean"],
        "micro_fast_mean": scen["micro_fast"]["mean"],
        "reductions": scen["_reductions"],
        "sensitivity_ordering_robust": sens["ordering_robust"],
    }, indent=2))


def _figures(arrays, scen, sweep, heat, sens, overhead):
    plt.rcParams.update({"figure.dpi": 160, "font.size": 10})

    # Fig 1 — blast-radius distribution by architecture
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bins = np.linspace(0, 1, 60)
    for key, color in [("flat_slow", C_FLAT), ("micro_slow", C_MICRO), ("micro_fast", C_FAST)]:
        m = scen[key]["mean"] * 100
        lbl = {"flat_slow": f"Flat network + slow detection (mean {m:.0f}%)",
               "micro_slow": f"Microsegmentation (16) (mean {m:.0f}%)",
               "micro_fast": f"Microsegmentation + EDR/ML (mean {m:.0f}%)"}[key]
        ax.hist(arrays[key], bins=bins, alpha=.55, density=True, color=color, label=lbl)
    ax.set_xlabel("Blast radius (fraction of hosts compromised)")
    ax.set_ylabel("Density")
    ax.set_title("Blast-radius distribution by architectural configuration")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "fig1_blast_distribuicao.png"); plt.close(fig)

    # Fig 2 — blast radius vs number of segments
    xs = sorted(sweep.keys())
    ys = [sweep[s]["mean"] * 100 for s in xs]
    lo = [sweep[s]["p10"] * 100 for s in xs]
    hi = [sweep[s]["p90"] * 100 for s in xs]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.fill_between(xs, lo, hi, alpha=.2, color=C_MICRO, label="P10–P90 band")
    ax.plot(xs, ys, "o-", color=C_MICRO, lw=2, label="mean blast radius")
    ax.set_xscale("log", base=2); ax.set_xticks(xs); ax.set_xticklabels(xs)
    ax.set_xlabel("Number of network segments (default-deny east-west)")
    ax.set_ylabel("Mean blast radius (%)")
    ax.set_title("Blast radius vs. microsegmentation granularity (slow detection)")
    ax.legend(fontsize=8); ax.grid(alpha=.3); fig.tight_layout()
    fig.savefig(OUT / "fig2_blast_vs_segmentos.png"); plt.close(fig)

    # Fig 3 — heatmap segments x detection
    seg_grid, d_grid = heat["seg_grid"], heat["d_grid"]
    M = np.array([[heat["values"][f"{s}|{d}"] * 100 for d in d_grid] for s in seg_grid])
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    im = ax.imshow(M, cmap="RdYlGn_r", aspect="auto", origin="lower", vmin=0, vmax=100)
    ax.set_xticks(range(len(d_grid))); ax.set_xticklabels(d_grid)
    ax.set_yticks(range(len(seg_grid))); ax.set_yticklabels(seg_grid)
    ax.set_xlabel("Detection window (epochs to containment)")
    ax.set_ylabel("Number of segments")
    ax.set_title("Mean blast radius (%) — segmentation × detection speed")
    for i in range(len(seg_grid)):
        for j in range(len(d_grid)):
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=8, color="black")
    fig.colorbar(im, ax=ax, label="mean blast radius (%)")
    fig.tight_layout(); fig.savefig(OUT / "fig3_heatmap_seg_deteccao.png"); plt.close(fig)

    # Fig 4 — security x performance frontier
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ox = [overhead[s] for s in xs]; oy = [sweep[s]["mean"] * 100 for s in xs]
    ax.plot(ox, oy, "o-", color="#762a83", lw=2)
    for s, x, y in zip(xs, ox, oy):
        ax.annotate(f"{s} seg.", (x, y), textcoords="offset points", xytext=(6, 6), fontsize=8)
    ax.set_xlabel("Expected east-west overhead per call (ms, performance proxy)")
    ax.set_ylabel("Mean blast radius (%, security proxy)")
    ax.set_title("Security × performance frontier of microsegmentation")
    ax.grid(alpha=.3); fig.tight_layout()
    fig.savefig(OUT / "fig4_fronteira_seg_perf.png"); plt.close(fig)

    # Fig 5 — sensitivity: ordering robust across parameter perturbations
    rows = sens["rows"]
    labels = [f"{r['param']}={r['value']}" for r in rows]
    x = np.arange(len(rows)); w = 0.27
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.bar(x - w, [r["flat_slow"] * 100 for r in rows], w, color=C_FLAT, label="Flat + slow")
    ax.bar(x, [r["micro_slow"] * 100 for r in rows], w, color=C_MICRO, label="Microseg. + slow")
    ax.bar(x + w, [r["micro_fast"] * 100 for r in rows], w, color=C_FAST, label="Microseg. + EDR/ML")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=7)
    ax.set_ylabel("Mean blast radius (%)")
    ax.set_title("Sensitivity: ordering preserved under parameter perturbation")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "fig5_sensibilidade.png"); plt.close(fig)


if __name__ == "__main__":
    main()
