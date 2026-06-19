# -*- coding: utf-8 -*-
"""Reproducibility and sanity tests for the blast-radius model.

Run: cd sim && python -m pytest -q   (or: python tests/test_blast_radius.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import blast_radius as br


def test_determinism_bit_parity():
    """Same seed -> bit-identical output (the core reproducibility guarantee)."""
    a = br.simulate(16, 9, trials=20_000, seed=123)
    b = br.simulate(16, 9, trials=20_000, seed=123)
    assert np.array_equal(a, b)


def test_seed_changes_output():
    a = br.simulate(16, 9, trials=20_000, seed=1)
    b = br.simulate(16, 9, trials=20_000, seed=2)
    assert not np.array_equal(a, b)


def test_blast_radius_in_unit_interval():
    a = br.simulate(8, 6, trials=10_000, seed=7)
    assert a.min() >= 0.0 and a.max() <= 1.0


def test_flat_slow_saturates():
    """A flat network with a slow detection window encrypts almost everything."""
    a = br.simulate(1, br.D_SLOW, trials=20_000, seed=11)
    assert a.mean() > 0.95


def test_more_segments_never_increase_blast_radius():
    """Monotonicity: finer segmentation must not worsen the mean blast radius (same D)."""
    means = [br.simulate(s, br.D_SLOW, trials=20_000, seed=100 + s).mean()
             for s in (1, 4, 16, 64)]
    assert all(means[i] >= means[i + 1] - 1e-3 for i in range(len(means) - 1))


def test_faster_detection_helps():
    """Shorter detection window must not worsen the mean blast radius (same segments)."""
    slow = br.simulate(16, br.D_SLOW, trials=20_000, seed=55).mean()
    fast = br.simulate(16, br.D_FAST, trials=20_000, seed=56).mean()
    assert fast <= slow + 1e-3


def test_sensitivity_ordering_robust():
    """Defense-in-depth ordering holds across parameter perturbations (small run)."""
    res = br.sensitivity(trials=8_000)
    assert res["ordering_robust"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print(f"{len(fns)} tests passed")
