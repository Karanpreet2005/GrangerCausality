# Reproduction notes

Working log for the reproduction of:

> Troster, V. (2018). "Testing for Granger-causality in quantiles."
> *Econometric Reviews* 37(8), 850–866. DOI 10.1080/07474938.2016.1172400.

Everything here is provenance: what the paper fixed, what someone else fixed, what
we chose, and where we knowingly differ. `results/comparison.md` holds the numbers.

---

## 1. There is no author code

Searched, all without success: the author's homepage, ORCID, IDEAS/RePEc author
page, EconPapers, ResearchGate, the Universitat de les Illes Balears repository,
MPRA, openICPSR, GitHub, and the Taylor & Francis article page (paywalled, no
supplementary material listed).

One GitHub repository looks superficially relevant —
`QuantLet/GrangerCausalityTestInQuantile` — but its `Metainfo.txt` shows it
implements **Jeong, Härdle & Song (2012)**, *Econometric Theory* 28:861–887: the
*nonparametric* kernel test that Troster compares against. It has no Cramér–von
Mises functional, no subsampling and no parametric QAR. It is not this paper's
method and is not used here.

**Everything in `src/qgc/` is therefore written from the paper's equations.** Each
module docstring names the equation or section it implements.

---

## 2. Method, as implemented

| Element | Implementation | Paper |
|---|---|---|
| Marked process | `v_T(w,τ) = T^(−1/2) Σ ψ_{τ,t}(θ̂) exp(i w′I_t)` | eq. (9) |
| Statistic | `S_T = (1/(Tn)) Σ_j \|ψ_j′ W ψ_j\|` | eq. (11) |
| Kernel | `W_{t,s} = exp(−0.5‖I_t − I_s‖²)` | eq. (11) |
| Subsample size | `b = ⌊k·T^(2/5)⌋` | Sec. 2.2 |
| Subsamples | `B = T − b + 1`, overlapping, contiguous | Sec. 2.2 |
| p-value | `B^{-1} Σ 1(S_{b,i} > S_T)`, non-recentered | Sec. 2.2 |
| Quantile model | `μ₀ + Σμ_j Y_{t−j} + σ·Φ^{-1}(τ)`, Gaussian ML | eq. (17) |
| τ grid | 20 equally spaced points on [0.10, 0.90] | Sec. 4 |

Taking `F_ω` as the d-variate standard normal makes eq. (11) **exact**: the kernel
is the Gaussian characteristic function, so no numerical integration over ω is ever
needed. A unit test confirms the closed form against Monte Carlo integration.

### Two facts that make this cheap

1. **Subsample kernels are free.** Subsamples are contiguous windows, so `I_t` is
   unchanged within a window and `W_{b,i}` is exactly the diagonal block
   `W[i:i+m, i:i+m]`. The kernel is built once and viewed with stride tricks.
2. **The QAR fit does not depend on τ.** Under D3 the model is a location-shift
   family, so one Gaussian ML fit serves all 20 quantiles. All `B` window
   regressions are then obtained from running sums in `O(n p²)` rather than
   `O(B m p²)`.

Together these turn the subsampling loop from the dominant cost into a minor one.

---

## 3. Resolutions D1–D8

Full text with sources in `src/qgc/_external_resolutions.py` (`python -m
qgc._external_resolutions` prints it as a table).

| Tag | Issue | Resolution | Class |
|---|---|---|---|
| D1 | Gold called "per ounce" in the text but "GSCI Gold Spot index" in the Table 1 note; the magnitudes match the index | Treat as the index; immaterial, the test is scale-invariant | EXTERNALLY_RESOLVED |
| D2 | eq. (17) writes `σ_t` but defines no volatility model | Constant σ, per the author's later paper | EXTERNALLY_RESOLVED |
| D3 | Which distribution is `Φ_ε^{-1}`? | Standard normal ⇒ location-shift family | EXTERNALLY_RESOLVED |
| D4 | QAR(3) used in Tables 3–4 but never defined | AR(3) + σΦ^{-1}(τ) | EXTERNALLY_RESOLVED |
| D5 | Later paper says "average the statistics"; target paper defines `Ĝ` | Follow the target paper: average of indicators | PAPER_SPECIFIED |
| D6 | `\|·\|` in eq. (11) is redundant | Implemented as written; a test asserts non-negativity | PAPER_SPECIFIED |
| D7 | Is `I_t` standardised before the kernel? | Standardised. Unstandardised daily log-returns give ‖I_t−I_s‖² ≈ 1e−4, so the kernel is ≈0.9998 everywhere — numerically a matrix of ones | OUR_ASSUMPTION |
| D8 | Table 2's causality directions do not reproduce | A one-row gold offset recovers all 12 cells; both alignments reported | DEVIATION_FROM_PAPER |

**D7 and D8 are the two that could matter most, and neither is settled by the
paper.** D7 is an unavoidable choice — the literal kernel is degenerate on this
data. D8 is diagnosed but not proven; see §6.

---

## 4. Data

Datastream is subscription-only, so all three series are rebuilt from free sources
and validated against Table 1 *before* anything else runs. Details in
`data/README.md`.

- `usdgbp` — FRED `DEXUSUK`. **Exact**: matches all seven printed values at 2 dp.
- `oil` — FRED `DCOILBRENTEU`. Near-exact proxy for Platts Dated Brent.
- `gold` — LBMA 15:00 fix × 0.583, standing in for S&P GSCI Gold Spot.

The 0.583 factor is a **units conversion, not a fitted parameter**: the implied
ratios from Table 1's mean, minimum and maximum are 0.5838 / 0.5837 / 0.5813,
agreeing to ~0.4%. The test runs on log-differences and is exactly invariant to it,
so no p-value anywhere depends on the value.

A business-day index with forward fill gives exactly **3,440** rows over
2000-07-03 → 2013-09-06 — the paper's stated *T*.

---

## 5. Figure digitisation

The paper reports its Monte Carlo results **only as raster images**. Verified from
the PDF object structure: 24 Image XObjects and **zero Form XObjects**, so no
vector coordinates exist to recover.

Method (`src/qgc/reporting/digitize.py`):

1. Rasterise the figure pages with PyMuPDF and split them into sub-panels on the
   whitespace gutters.
2. Locate the axes frame; the y-axis spans 0.0–1.0 and the seven x ticks are evenly
   spaced (a categorical axis).
3. Separate curves by colour — **red = T 500, black dashed = T 100**.
4. At each tick take a narrow column, cluster the pixels, and read the cluster
   median. A narrow window matters: a wide one also catches the connecting line,
   which on a steep segment spans a large y range.

**This is how the `c` grid was recovered.** The body text never states it, but the
x-axis tick labels read `0.00, 0.01, 0.03, 0.06, 0.12, 0.24, 0.50`. That
reclassifies the grid from OUR_ASSUMPTION to PAPER_SPECIFIED.

### Quality control (pre-declared)

Two checks, both properties of the *published plots*, never of our results:

- `spread_ok` — the two or three near-coincident curves of one colour sit within a
  few percent, so a wide pixel spread means something else was caught.
- `monotonic_ok` — plotted rejection curves rise with `c`, so a reading materially
  above the minimum of every later reading in its series cannot be on the curve.

**148 points traced, 138 valid, 10 flagged.** Every flagged point is on a black
dashed T=100 curve at a steep segment. Flagged points keep their raw traced value
and are marked `valid = False` — nothing is replaced with a better-agreeing number,
and the rule is never applied to our computed results.

Digitised values are therefore **approximate targets with a stated failure rate**,
not printed numbers. Claims resting on them are weaker than claims resting on
Tables 1–4.

---

## 6. The τ = 0.50 discrepancies

Under the primary alignment, Tables 3–4 agree with the paper in 130/144 cells at
the 5% level. **All 108 tail and full-grid cells (τ = 0.10, τ = 0.90, τ ∈
[0.10;0.90]) reproduce exactly**, every one printed as 0.000. All 14 disagreements
sit at τ = 0.50.

Causes considered:

| Candidate | Verdict |
|---|---|
| Data proxy (gold/oil source) | Contributes. τ = 0.50 is where the median regression is most sensitive to the exact series. |
| Alignment (D8) | Tested. The offset alignment *worsens* Tables 3–4 (123/144), so it does not explain these. |
| Subsample constant `k` | Tested; all of k ∈ {3,4,5} reported. The τ = 0.50 disagreements persist across all three, so `k` is not the cause. |
| Lags `q` of Z | OUR_ASSUMPTION (q = s). Not excluded. |
| Kernel standardisation (D7) | Not excluded; plausibly matters most at the median, where the marked process is smallest. |
| QAR specification (D2/D3) | Externally resolved; a GARCH sensitivity is available. |
| Numerical precision | Excluded. BLAS output is bit-identical to a non-BLAS reference. |

**Classification: UNRESOLVED.** The most likely contributors are the gold/oil proxy
and D7, but neither is demonstrated. No parameter was adjusted to close the gap.

---

## 7. Computational setup and measured runtimes

Hardware: **Apple M4 (Mac16,12), 10 cores (4 performance + 6 efficiency), 16 GB**.
Python 3.12.9, NumPy 2.1.3, SciPy 1.15.2, statsmodels 0.14.4. BLAS is Apple
**Accelerate**.

| Stage | Measured |
|---|---|
| data (download + Table 1 gate) | seconds |
| empirical (Tables 2–4, both alignments, all k) | **30 s** |
| mc (Figs 1–3; 168 cells × 1,000 reps) | **321 s** on 8 workers |
| supwald (Fig 4; 168 cells × 1,000 reps) | **~69 min** on 8 workers |
| test suite | 7 s |

No GPU is used or useful: matrices are at most 129×129 and the work is many tiny
operations, so kernel-launch overhead would dominate. Peak memory is the 3440²
empirical kernel, ≈95 MB.

### Two Apple-Silicon specifics

1. **Accelerate emits spurious FP warnings** from `matmul` ("divide by zero",
   "overflow", "invalid value") on ordinary finite input. Verified harmless:
   `W @ psi` through Accelerate is **bit-identical** to a non-BLAS `einsum`
   reference, max absolute difference exactly 0. Only those three messages are
   filtered, and `assert_finite` still guards the values that matter.
2. **BLAS threads are pinned to 1 inside workers.** Without it, each worker's
   Accelerate threads contend with every other worker and the pool runs *slower*.

---

## 8. Deviations from the paper

1. **Gold and oil series are proxies** (§4). Documented, validated against Table 1.
2. **Both data alignments are reported** (D8) rather than only the literal one.
3. **Sup-Wald critical values are simulated** from the limiting law rather than
   taken from a printed table, because the paper does not say which it used. The
   simulated 5% value is 8.741 against the 8.8–9.0 usually tabulated.
4. **statsmodels' QR iteration limit is raised** from 1,000 to 20,000. At the
   default, ~0.6% of fits failed to converge and, because Sup-Wald takes a maximum
   over τ, a single unconverged fit moved the statistic by up to 0.17. Raising it
   eliminates non-convergence entirely (0/600).
