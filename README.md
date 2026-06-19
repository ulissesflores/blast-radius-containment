# Blast-Radius Containment

A standalone, **deterministic Monte Carlo** model that quantifies the *blast
radius* (fraction of hosts encrypted) of ransomware **lateral propagation**, and
how **Zero Trust microsegmentation** (default-deny east-west, NIST SP 800-207)
combined with **behavioral detection** (a shorter detection window) contains it.

It is **motivated by** the 2024 Change Healthcare ransomware incident — a public
event in which a flat, perimeter-based network let ransomware propagate across
most of a national health-claims clearinghouse — and quantifies, illustratively,
how Zero Trust microsegmentation and behavioral detection would have contained
such propagation. It is an **illustrative** stochastic model (not a forensic
reconstruction of any incident), calibrated to orders of magnitude and grounded
in the Zero Trust literature (NIST SP 800-207; Rais et al., 2024; Anderson, 2020).

## Model in one paragraph

A fleet of `N=1200` hosts is partitioned into `S` segments. Infection starts
from one host (the foothold on the exposed Citrix portal). Each **epoch** —
a *dimensionless propagation round, not a calendar day* — every infected host
attempts `deg` lateral moves; only a fraction `f` of boundary-crossing attempts
are permitted (default-deny east-west). A reached host is compromised with
probability `p` (high, because valid stolen credentials make lateral movement
look legitimate). Containment stops propagation after `D` epochs; a smaller `D`
models behavioral EDR/XDR. Detection speed is expressed as a **ratio** (fast =
3× faster than slow); see the sensitivity analysis for robustness.

## Headline result (seed 513, 400k replicates)

| Configuration | Mean blast radius (95% CI) |
|---|---|
| Flat network + slow detection (victim-like) | **≈ 100.0%** (±0.001 pp) |
| Microsegmentation (16) + slow detection | **≈ 70.2%** (±0.04 pp) |
| Microsegmentation + behavioral EDR/ML (fast) | **≈ 3.5%** (±0.004 pp) |

Reductions vs. flat: 29.8% (segmentation alone) and **96.5%** (defense in depth).
The defense-in-depth ordering holds across every parameter perturbation tested
(see `output/results.json` → `sensitivity.ordering_robust = true`).

## Five-step replication protocol

```bash
# 0. Environment
pip install -r requirements.txt

# 1. Verify source integrity (compare against docs/hash-chain after step 4)
shasum -a 256 blast_radius.py run_all.py make_provenance.py

# 2. Run the test suite (determinism / bit-parity / monotonicity)
python -m pytest -q            # or: python tests/test_blast_radius.py

# 3. Run all experiments (≈ 20 s; writes output/results.json + figures)
python run_all.py

# 4. Bind the SHA-256 chain of truth
python make_provenance.py      # writes output/provenance.json + output/hash-chain.md

# 5. Verify reproducibility: re-run step 3 and confirm results.json is identical
#    (deterministic seeds → bit-identical output).
```

> If any source or result changes, `output/provenance.json:chain_hash` changes.
> The chain is the single source of truth for an audit.

## Layout

```
blast_radius.py      core model + experiments (model, scenarios, sweep, heatmap, sensitivity)
run_all.py           runs everything; writes output/ (results.json, raw_replicas.jsonl, fig1..5)
make_provenance.py   SHA-256 provenance + hash-chain.md
tests/               pytest reproducibility & sanity tests
colab/               self-contained replication notebook (Google Colab)
docs/                algorithm.md (model spec), findings.md (results)
output/              generated artifacts (committed for audit)
```

## Colab

`colab/replication.ipynb` is self-contained (the model is embedded), runs end to
end in Google Colab, and verifies its own SHA-256 hashes — no external repo
needed.

## License

Code: Apache-2.0. Documentation/figures: CC BY 4.0.

## Citation

See `CITATION.cff`. (DOI is minted on public release.)
