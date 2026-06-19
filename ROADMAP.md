# Roadmap

## v1.0.0 — current

Segment-level mean-field susceptible–infected contact process with bounded
fan-out and default-deny east-west leakage. 400k Monte Carlo replicates, 95%
CIs, sensitivity analysis, SHA-256 chain of truth, pytest determinism suite,
Colab notebook. Status: **released**.

## v2.0 — explicit host-graph topology (planned)

**Motivation.** v1.0 is mean-field: hosts are aggregated into segments, so the
expected blast radius is essentially fixed by the parameters and Monte Carlo
only tightens confidence intervals (more replicates do not change the mean).
Real datacenter east-west connectivity is **not** uniform, and that structure is
exactly what governs lateral movement. v2.0 replaces the mean field with an
**explicit graph of host nodes** to capture it.

**Design.**

1. **Explicit graph.** `N` host nodes; edges = permitted east-west reachability.
   Segments become dense communities; inter-segment edges are sparse and gated.
2. **Heterogeneous topology with hubs.** A heavy-tailed degree distribution with
   a few **hub nodes** (domain controllers, jump boxes, hypervisors, service
   accounts, backup servers) whose compromise reaches many hosts at once.
3. **Percolation / SI on the graph** instead of segment-level pressure.
4. **Empirically grounded parameters** — lateral-movement and dwell-time priors
   from public incident telemetry (e.g. Verizon DBIR, Mandiant M-Trends) rather
   than illustrative constants.
5. **Stochastic detection** as a process (hazard rate) instead of a fixed epoch.

**Expected new findings (what changes vs. v1.0).**

- Blast-radius distributions become **multimodal / heavy-tailed**: most runs
  contained, a minority catastrophic when a hub is hit early. Here 400k replicates
  *matter* — they estimate tail probabilities, not just a stable mean.
- A sharper, more actionable result: **hardening and isolating the few hub nodes
  dominates** uniform segment multiplication.
- Topology-dependent security × performance frontiers.

**Non-goals.** v2.0 remains an illustrative research model; it does not claim to
reconstruct any specific incident's network.

**Engineering.** New `graph.py` (topology generators + percolation), extended
tests (degree-distribution invariants, hub-removal monotonicity), new figures
(distribution multimodality, hub-impact curve), and the same hash-chain
discipline. The mean-field model is retained for comparison/ablation.
