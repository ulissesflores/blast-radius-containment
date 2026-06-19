#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blast_radius.py — Monte Carlo model of ransomware lateral propagation and its
containment by Zero Trust microsegmentation and behavioral detection.

A standalone, reproducible model motivated by the 2024 Change Healthcare
ransomware incident. It is an ILLUSTRATIVE stochastic model (not a forensic
reconstruction of any incident), calibrated to orders of magnitude and grounded
in the Zero Trust literature (Rose et al., 2020, NIST SP 800-207; Rais et al.,
2024; Anderson, 2020).

Model (segment-level susceptible-infected contact process with bounded fan-out)
------------------------------------------------------------------------------
A fleet of `n_hosts` hosts is partitioned into `n_segments` network segments.
Infection starts from a single host (the foothold obtained on the exposed
Citrix portal). At each discrete EPOCH every infected host attempts `deg`
lateral moves; only a fraction `leak_fraction` of the attempts that cross a
segment boundary are permitted (default-deny east-west, per NIST SP 800-207).
A reached host is compromised with probability `p_compromise` (high, because
valid stolen credentials make lateral movement indistinguishable from
legitimate use — Anderson, 2020). Containment stops propagation after
`detection_epochs` epochs; a smaller value models behavioral EDR/XDR (ML).

IMPORTANT — "epoch" is a DIMENSIONLESS propagation round, NOT a calendar day.
Detection speed is expressed as a RATIO (e.g., fast = 3x faster than slow);
the qualitative conclusion is shown to be robust to this choice in the
sensitivity analysis, so it does not hinge on any epoch->time mapping.

Per-host infection pressure in a segment with I_in in-segment infected and
I_out out-of-segment infected (mean-field, bounded fan-out):
    intra = I_in * deg / seg_size * p_compromise
    inter = I_out * deg * cross_share * leak_fraction * p_compromise / (N - seg_size)
    P(host compromised this epoch) = 1 - exp(-(intra + inter))

Determinism: every experiment draws from numpy.random.default_rng(seed); the
same seed yields bit-identical output (see tests/).
"""
from __future__ import annotations
import numpy as np

# --- Default illustrative parameters (documented in docs/algorithm.md) --------
N_HOSTS = 1200          # fleet size (mirrors the immersion scenario: 1,200 servers)
DEG = 6                 # lateral move attempts per infected host per epoch
P_COMPROMISE = 0.5      # P(compromise | reached) — high: valid credentials
CROSS_SHARE = 0.5       # share of attempts aimed outside the host's own segment
LEAK_FRACTION = 0.05    # fraction of east-west crossings permitted (default-deny)
D_SLOW = 9              # detection window (epochs) — slow, victim-like configuration
D_FAST = 3              # detection window (epochs) — behavioral EDR/XDR (3x faster)
DELTA_MS = 0.8          # per-call east-west latency added by a PDP/PEP (performance proxy)

MASTER_SEED = 513
TRIALS_MAIN = 400_000   # main scenarios
TRIALS_SWEEP = 100_000  # segment-granularity sweep
TRIALS_HEATMAP = 40_000 # per cell of the (segments x detection) heatmap
TRIALS_SENS = 100_000   # per sensitivity cell


def simulate(n_segments, detection_epochs, *, trials, seed,
             n_hosts=N_HOSTS, deg=DEG, p_compromise=P_COMPROMISE,
             cross_share=CROSS_SHARE, leak_fraction=LEAK_FRACTION):
    """Return an array (length=trials) of blast radius = fraction of hosts compromised."""
    rng = np.random.default_rng(seed)
    seg_size = n_hosts // n_segments
    inf = np.zeros((trials, n_segments), dtype=np.int64)
    inf[:, 0] = 1
    denom = max(n_hosts - seg_size, 1)
    for _ in range(detection_epochs):
        I_seg = inf
        I_out = I_seg.sum(axis=1, keepdims=True) - I_seg
        susc = seg_size - I_seg
        intra = I_seg * deg / seg_size * p_compromise
        inter = I_out * deg * cross_share * leak_fraction * p_compromise / denom
        p_host = 1.0 - np.exp(-(intra + inter))
        new = rng.binomial(np.maximum(susc, 0), np.clip(p_host, 0.0, 1.0))
        inf = I_seg + new
    return inf.sum(axis=1) / n_hosts


def summarize(arr):
    """Mean blast radius, 95% CI half-width of the mean, and key percentiles."""
    n = arr.size
    mean = float(arr.mean())
    sd = float(arr.std(ddof=1))
    ci95 = float(1.96 * sd / np.sqrt(n))
    return {
        "trials": int(n),
        "mean": mean,
        "sd": sd,
        "ci95_halfwidth": ci95,
        "p10": float(np.percentile(arr, 10)),
        "p50": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
        "p99": float(np.percentile(arr, 99)),
    }


def main_scenarios(trials=TRIALS_MAIN):
    """The three headline configurations. Returns (arrays, stats)."""
    specs = {
        "flat_slow":  dict(n_segments=1,  detection_epochs=D_SLOW),   # victim-like flat network
        "micro_slow": dict(n_segments=16, detection_epochs=D_SLOW),   # microsegmentation, slow detection
        "micro_fast": dict(n_segments=16, detection_epochs=D_FAST),   # microsegmentation + behavioral EDR/ML
    }
    arrays, stats = {}, {}
    for i, (name, kw) in enumerate(specs.items()):
        a = simulate(trials=trials, seed=MASTER_SEED + i, **kw)
        arrays[name] = a
        stats[name] = summarize(a)
    flat = stats["flat_slow"]["mean"]
    stats["_reductions"] = {
        "micro_vs_flat_pct": round(100 * (flat - stats["micro_slow"]["mean"]) / flat, 2),
        "defense_in_depth_vs_flat_pct": round(100 * (flat - stats["micro_fast"]["mean"]) / flat, 2),
    }
    return arrays, stats


def segment_sweep(seg_grid=(1, 2, 4, 8, 16, 32, 64), trials=TRIALS_SWEEP):
    out = {}
    for s in seg_grid:
        a = simulate(s, D_SLOW, trials=trials, seed=MASTER_SEED + 1000 + s)
        out[s] = summarize(a)
    return out


def detection_heatmap(seg_grid=(1, 2, 4, 8, 16, 32, 64),
                      d_grid=(2, 3, 4, 6, 9, 12), trials=TRIALS_HEATMAP):
    grid = {}
    for s in seg_grid:
        for d in d_grid:
            a = simulate(s, d, trials=trials, seed=MASTER_SEED + 7 * s + d)
            grid[f"{s}|{d}"] = float(a.mean())
    return {"seg_grid": list(seg_grid), "d_grid": list(d_grid), "values": grid}


def sensitivity(trials=TRIALS_SENS):
    """Vary deg, p_compromise, leak_fraction one-at-a-time; confirm the ordering
    flat_slow > micro_slow > micro_fast (defense-in-depth collapse) holds in all cells."""
    base = dict(deg=DEG, p_compromise=P_COMPROMISE, leak_fraction=LEAK_FRACTION)
    variations = {
        "deg": [4, 6, 8],
        "p_compromise": [0.3, 0.5, 0.7],
        "leak_fraction": [0.02, 0.05, 0.10],
    }
    rows, robust = [], True
    k = 0
    for param, values in variations.items():
        for v in values:
            kw = dict(base); kw[param] = v
            flat = simulate(1, D_SLOW, trials=trials, seed=MASTER_SEED + 5000 + k, **kw).mean()
            ms = simulate(16, D_SLOW, trials=trials, seed=MASTER_SEED + 6000 + k, **kw).mean()
            mf = simulate(16, D_FAST, trials=trials, seed=MASTER_SEED + 7000 + k, **kw).mean()
            ordering_ok = bool(flat >= ms >= mf)
            robust = robust and ordering_ok
            rows.append({"param": param, "value": v,
                         "flat_slow": float(flat), "micro_slow": float(ms),
                         "micro_fast": float(mf), "ordering_ok": ordering_ok})
            k += 1
    return {"rows": rows, "ordering_robust": robust}


def east_west_overhead(seg_grid=(1, 2, 4, 8, 16, 32, 64), delta_ms=DELTA_MS):
    """Performance proxy: expected per-call east-west latency added by inline PDP/PEP.
    Under uniform service-to-service calls, fraction crossing a boundary ~ (1 - 1/S)."""
    return {s: (1 - 1 / s) * delta_ms for s in seg_grid}
