# Findings

All numbers from `output/results.json` (master seed 513). Means carry 95%
confidence intervals from the Monte Carlo distribution.

## 1. Main scenarios (400,000 replicates each)

| Configuration | Mean blast radius | 95% CI half-width | P10–P90 |
|---|---|---|---|
| Flat network + slow detection | 99.99% | ±0.001 pp | 100–100% |
| Microsegmentation (16) + slow detection | 70.22% | ±0.043 pp | 51.6–87.0% |
| Microsegmentation + behavioral EDR/ML (fast) | 3.46% | ±0.004 pp | 1.8–4.9% |

- Reduction vs. flat — **segmentation alone**: 29.8%.
- Reduction vs. flat — **defense in depth** (segmentation + fast detection): **96.5%**.

**Reading.** Microsegmentation is *necessary but not sufficient* under a slow
detection window: with 16 segments and slow detection the blast radius is still
~70%, because permitted east-west crossings accumulate over the long window.
Pairing segmentation with faster behavioral detection collapses the blast radius
to ~3.5% — the two controls reinforce each other.

## 2. Segment-granularity sweep (100k, slow detection)

| Segments | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| Mean blast radius | 100.0% | 99.8% | 98.3% | 91.3% | 70.2% | 39.0% | 15.6% |

Under slow detection, meaningful containment requires fine granularity — a
threshold effect, not diminishing returns at low `S`.

## 3. Detection heatmap (40k/cell)

`output/fig3_*` — blast radius over `S × D`. The two axes are complementary:
fine segmentation OR fast detection each helps, and together they collapse the
blast radius with modest granularity.

## 4. Sensitivity

`sensitivity.ordering_robust = true` across all 9 perturbation cells
(`deg ∈ {4,6,8}`, `p ∈ {0.3,0.5,0.7}`, `f ∈ {0.02,0.05,0.10}`). The conclusion
does **not** hinge on the specific parameter values.

## 5. Security × performance frontier

Expected per-call east-west latency `(1 - 1/S)·δ` (δ = 0.8 ms) saturates toward
δ as `S` grows, while the marginal containment gain falls beyond a knee. The
optimal architecture sits at the knee and compensates limited granularity with
faster detection — a design criterion, not a dogma.
