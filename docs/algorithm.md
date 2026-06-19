# Algorithm specification

## Purpose

Quantify the **blast radius** of ransomware lateral propagation and the marginal
value of two architectural controls — **microsegmentation** (default-deny
east-west) and **faster detection** (shorter containment window) — as a function
of network granularity and detection speed.

## State and dynamics

Let `N` be the number of hosts partitioned into `S` equal segments of size
`m = N/S`. State is the per-segment infected count `I_s` (vectorized over
`trials` Monte Carlo replicates). The seed of the outbreak is one infected host
in segment 0 (the foothold on the exposed Citrix portal).

At each **epoch** (a dimensionless propagation round), a susceptible host in
segment `s` is compromised with probability

```
intra = I_s            * deg / m              * p
inter = (I_total - I_s) * deg * cross * f / (N - m) * p
P(compromise) = 1 - exp(-(intra + inter))
new_infected_s ~ Binomial(susceptible_s, P(compromise))
```

where
- `deg` — lateral move attempts per infected host per epoch (credential reuse),
- `p` — probability a *reached* host is compromised (high under valid credentials),
- `cross` — share of attempts aimed outside the host's own segment,
- `f` — fraction of boundary-crossing attempts permitted (default-deny east-west).

Propagation halts after `D` epochs (the **detection window**). The blast radius
of a replicate is `I_total / N` at halt.

### Pseudocode

```
function simulate(S, D, trials, seed):
    rng <- default_rng(seed)
    m <- N / S
    I[t, s] <- 0 for all trials t, segments s ; I[t, 0] <- 1
    repeat D times:
        Iout  <- rowsum(I) - I
        susc  <- m - I
        intra <- I    * deg / m              * p
        inter <- Iout * deg * cross * f / (N - m) * p
        Ph    <- 1 - exp(-(intra + inter))
        I     <- I + Binomial(max(susc,0), clip(Ph,0,1))
    return rowsum(I) / N            # blast radius per replicate
```

## Why "epoch" is dimensionless

An epoch is one synchronous round of lateral-movement attempts, **not** a
calendar day. The slow/fast detection windows are reported as a **ratio**
(fast = 3× faster). The qualitative conclusion (defense in depth collapses the
blast radius) is shown to be invariant to the parameters in the sensitivity
analysis, so it does not depend on any epoch→time calibration.

## Parameters (illustrative defaults) and grounding

| Symbol | Default | Rationale |
|---|---|---|
| `N` | 1200 | mirrors the immersion-scenario fleet (1,200 servers) |
| `deg` | 6 | bounded lateral reach per host per epoch (credential reuse) |
| `p` | 0.5 | high compromise-on-reach: valid stolen credentials (Anderson, 2020) |
| `cross` | 0.5 | half of attempts aim outside the home segment |
| `f` | 0.05 | few east-west crossings permitted under default-deny (NIST SP 800-207) |
| `D_slow` | 9 | slow detection window (victim-like) |
| `D_fast` | 3 | behavioral EDR/XDR — 3× faster detection |

## Experiments

1. **Main scenarios** (400k replicates): flat+slow, micro(16)+slow, micro(16)+fast; means with 95% CIs.
2. **Segment sweep** (100k): blast radius vs `S ∈ {1,2,4,8,16,32,64}` at `D_slow`.
3. **Detection heatmap** (40k/cell): blast radius over `S × D`.
4. **Sensitivity** (100k/cell): perturb `deg, p, f`; assert the ordering flat ≥ micro-slow ≥ micro-fast in every cell.
5. **Security×performance frontier**: blast radius vs expected east-west PDP/PEP latency `(1 - 1/S)·δ`.

## Limitations

Mean-field at segment level (no explicit host graph); homogeneous segment sizes;
no second-order effects (e.g., heterogeneous connectivity). The robustness of the
conclusion comes from its structure — containment depends jointly on segmentation
granularity and detection speed — not from precise parameter values.
