# Paper specification

Everything needed to reproduce Troster (2018), extracted from the article itself.
This is the Phase 1 record: what the paper fixes, and — equally important — what it
leaves open. Items it does not determine are marked `NOT SPECIFIED IN PAPER` and
carried into `src/qgc/provenance.py`.

> Troster, V. (2018). "Testing for Granger-causality in quantiles."
> *Econometric Reviews* 37(8), 850–866. DOI 10.1080/07474938.2016.1172400.
> Universitat de les Illes Balears. Funding: Spain MEC ECO2014-58991-C3-3-R.

## Method (Sections 2–3)

| Component | Value | Source |
|---|---|---|
| Null hypothesis | `E[ψ_{τ,t}(θ₀) \| I^Y_t, I^Z_t] = 0` a.s. ∀τ∈T | eq. (6) |
| Marked residual | `ψ_{τ,t}(θ) = 1(Y_t ≤ m(I^Y_t, θ(τ))) − τ` | Sec. 2.1 |
| Marked process | `v_T(ω,τ) = T^(−1/2) Σ_t ψ_{τ,t}(θ̂) exp(iω′I_t)` | eq. (9) |
| Statistic | `S_T = ∫∫ \|v_T(ω,τ)\|² dF_ω dF_τ` (Cramér–von Mises) | eq. (10) |
| Weighting measure `F_ω` | CDF of a d-variate standard normal | Sec. 2.1 |
| Measure `F_τ` | uniform discrete on an n-point grid | Sec. 2.1 |
| Computable form | `S_T = (1/(Tn)) Σ_j \| ψ_j′ W ψ_j \|` | eq. (11) |
| Kernel | `W_{t,s} = exp(−0.5 (I_t − I_s)²)` | eq. (11) |
| Weighting function | `g(I_t,ω) = exp(iω′I_t)` | Sec. 2.1 |
| Critical values | subsampling, **non-recentered** | Sec. 2.2 |
| Subsample size | `b = ⌊k·T^(2/5)⌋` (Sakov & Bickel 2000) | Sec. 2.2 |
| Subsamples | `B = T − b + 1`, overlapping and contiguous | Sec. 2.2, step 1 |
| Decision rule | `Ĝ(x)=B⁻¹Σ1(S_{b,i}≤x)`; reject if `S_T > Ĝ⁻¹(1−τ)` | Sec. 2.2, step 2 |

Because `F_ω` is the d-variate standard normal, the ω integral is the Gaussian
characteristic function and eq. (11) is **exact** — no numerical integration.

## Quantile models (eq. 17)

```
m₁ = μ₀(τ) + μ₁(τ)·Y_{t−1}                  + σ_t·Φ_ε⁻¹(τ)
m₂ = μ₀(τ) + μ₁(τ)·Y_{t−1} + μ₂(τ)·Y_{t−2}  + σ_t·Φ_ε⁻¹(τ)
```

- `θ_T(τ) = (μ₀(τ), μ₁(τ), μ₂(τ), σ_t)′`, estimated by **maximum likelihood**
- τ grid: **20 equally spaced points on [0.10, 0.90]** (Sec. 4)

## Monte Carlo (Section 4)

```
DGP1: Y_t = 0.5·Y_{t−1} + c·Z_{t−1}   + ε₁ₜ ;  Z_t = ε₂ₜ                    (13)
DGP2: Y_t = 0.5·Y_{t−1} + c·Z_{t−1}   + ε₁ₜ ;  Z_t = 1 + 0.8·Z_{t−1} + ε₂ₜ  (14)
DGP3: Y_t = 0.5·Y_{t−1} + c·Z²_{t−1}  + ε₁ₜ ;  Z_t = 1 + 0.8·Z_{t−1} + ε₂ₜ  (15)
DGP4: Y_t = 0.4·Y_{t−1} + c·Z_{t−1}   + ε₃ₜ ;  Z_t = ε₂ₜ, ε₃ₜ~N(0, 0.6−c)   (16)
```

- `ε_it ~ i.i.d. N(0,1)`; `c = 0` gives size, `c ≠ 0` gives power
- `T ∈ {100, 250, 500}`; `k ∈ {3,4,5}`
- `b` = 18/25/31 (T=100), 27/36/45 (T=250), 36/48/60 (T=500) — **all nine verified**
  to satisfy `⌊k·T^(2/5)⌋`, which is how floor rounding was confirmed
- **1,000 replications**; 5% nominal; max simulation s.e. ≈ 0.016
- Fig. 1 = DGP1–3 QAR(1); Fig. 2 = DGP1–3 QAR(2); Fig. 3 = DGP4; Fig. 4 = Sup-Wald

### Sup-Wald benchmark (eq. 18, Koenker & Machado 1999)

```
W1: μ₀(τ) + μ₁(τ)Y_{t−1} + β₁(τ)Z_{t−1}                 + σ_t Φ_ε⁻¹(τ)
W2: μ₀(τ) + μ₁(τ)Y_{t−1} + β₁(τ)Z_{t−1} + μ₂(τ)Y_{t−2}  + σ_t Φ_ε⁻¹(τ)
H₀: β₁(τ) = 0 for all τ ∈ T
```

## Empirical application (Section 5)

| Item | Value |
|---|---|
| Series | S&P GSCI Gold Spot index; Crude Oil Dated Brent (USD/barrel); USD/GBP |
| Source | **Datastream** |
| Period | 3 July 2000 → 6 September 2013, daily |
| Sample size | **T = 3,440** |
| Transformation | log-differences; ADF and KPSS reject stationarity of log levels |
| Reported | Table 1 (levels), Table 2 (mean causality), Tables 3–4 (subsampling p-values) |

Reported values are transcribed verbatim, with page references, in
[`../config/paper_targets.yaml`](../config/paper_targets.yaml) — the immutable
comparison baseline.

## `NOT SPECIFIED IN PAPER`

1. Software, language, library versions, hardware, runtime, **random seeds**
2. `k` used for the empirical Tables 3–4
3. Number of lags `q` of `Z` in `I_t` — Tables 3–4 label only the lags of `I^Y_t`
4. Whether `σ` is constant or time-varying → resolution D2, tested by experiment 06
5. Which distribution `Φ_ε⁻¹` refers to → resolution D3
6. The QAR(3) specification used in the 3-lag column → resolution D4
7. ~~The grid of `c` values in Figs. 1–4~~ — **recovered**: the x-axis tick labels
   read `0.00, 0.01, 0.03, 0.06, 0.12, 0.24, 0.50`, so this is PAPER_SPECIFIED
8. Which mean-causality test variant produced Table 2
9. ADF/KPSS deterministic terms and lag selection
10. `n` for the single-τ rows of Tables 3–4 (taken as n = 1)
11. Datastream calendar and missing-day handling → business days + forward fill,
    which reproduces T = 3,440 exactly
12. Monte Carlo burn-in and initial conditions
13. Whether `I_t` is standardised before the kernel → resolution D7
14. Which Sup-Wald critical values were used → simulated from the limiting law

## Availability

No code, data, or supplementary material was released. See
[`../REPRODUCTION_NOTES.md`](../REPRODUCTION_NOTES.md) §1 for the full search.
