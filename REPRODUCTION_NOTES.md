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

### A known limitation: saturated curve segments

Frame removal strips any pixel row covering more than 40% of the plot box width.
That correctly removes the axes and the dashed 5% reference line, but it also
removes a curve that has **saturated at 1.0**, because such a curve lies along the
top of the box. Where a rejection frequency has reached 1.0, the tracer therefore
reads the last non-saturated point instead, biasing the traced value *downwards*.

This is visible in the DGP3 panels, whose curves reach 1.0 very early. It inflates
the reported mean absolute difference against our own results, and it does so in a
direction that makes our reproduction look *worse*, not better. It is left in place
and reported rather than corrected, since correcting it would improve apparent
agreement and the QC rules were fixed in advance.

Digitised values are therefore **approximate targets with a stated failure rate**,
not printed numbers. Claims resting on them are weaker than claims resting on
Tables 1–4.

---

## 6. The τ = 0.50 discrepancies

Under the primary alignment, Tables 3–4 agree with the paper in 130/144 cells at
the 5% level. **All 108 tail and full-grid cells (τ = 0.10, τ = 0.90, τ ∈
[0.10;0.90]) reproduce exactly**, every one printed as 0.000. All 14 disagreements
sit at τ = 0.50.

The 14 disagreements are **not spread across the median row** — they are
concentrated almost entirely in the USD/GBP directions:

| Direction | Cells agreeing at τ = 0.50 | Paper mean p | Ours mean p |
|---|---|---:|---:|
| gold → oil | 9/9 | 0.397 | 0.495 |
| oil → gold | 8/9 | 0.294 | 0.230 |
| usdgbp → gold | 5/9 | 0.006 | 0.050 |
| usdgbp → oil | **0/9** | 0.006 | 0.439 |

So **the paper's headline median result reproduces**: the gold/oil pair shows
causality in the tails and none at the median, 17/18 cells. What does not
reproduce is the paper's finding of *significant* median causality running from
USD/GBP to both commodities (p ≈ 0.004–0.007), where we find borderline evidence
for gold (p ≈ 0.05) and none at all for oil (p ≈ 0.44).

Causes considered:

| Candidate | Verdict |
|---|---|
| Subsample constant `k` | **Excluded.** Agreement is 8/12, 7/12, 7/12 for k = 3, 4, 5 — essentially identical, so the disagreement is not a `k` artefact. |
| Alignment (D8) | **Excluded.** The offset alignment is *worse* at τ = 0.50 (15/36 against 22/36), so it does not explain these. |
| Numerical precision | **Excluded.** BLAS output is bit-identical to a non-BLAS reference. |
| Data proxy | **Possible, partial.** USD/GBP itself is exact (FRED `DEXUSUK` matches every printed Table 1 digit), but the *dependent* series in these tests are the gold and oil proxies. |
| Kernel standardisation (D7) | **Possible, not excluded.** It plausibly bites hardest at the median, where the marked process is smallest. |
| σ specification (D2) | **Demonstrated partial contributor** — see below. |
| Lags `q` of Z | **Possible, not excluded.** OUR_ASSUMPTION (q = s). |
| QAR specification (D2/D3) | Externally resolved; a GARCH sensitivity is available. |

### Experiment 06 measures how much D2 contributes

The decision-F sensitivity re-runs the empirical tests with the alternative
reading of `σ_t` — an AR(p)-GARCH(1,1) conditional scale instead of a constant —
at k = 5 and lag 1. Of 16 cells, 14 reach the same 5% decision, and **both cells
that change sit at τ = 0.50**, precisely where the unresolved discrepancy lives:

| Direction | τ | Paper | Constant σ (D2) | GARCH σ |
|---|---|---:|---:|---:|
| usdgbp → gold | 0.50 | 0.004 | 0.052 (no reject) | **0.025 (reject)** |
| oil → gold | 0.50 | 0.294 | 0.058 | 0.039 |
| usdgbp → oil | 0.50 | 0.005 | 0.356 | 0.226 |
| gold → oil | 0.50 | 0.461 | 0.456 | 0.404 |

Under the GARCH reading, `usdgbp → gold` flips to agree with the paper's rejection,
and the mean absolute error against the paper at τ = 0.50 falls from **0.160 to
0.139**. So D2 is not merely a candidate — it demonstrably moves the median
results toward the paper.

**We did not switch to it.** D2's resolution (constant σ) rests on the author's own
later paper restating the same models with a constant σ, which is stronger evidence
than "the alternative agrees better". The constant-σ specification also reproduces
the tails perfectly (108/108), whereas the GARCH variant introduces non-zero
p-values at τ = 0.90 where the paper prints 0.000. Choosing GARCH to close the
median gap would trade an exact tail reproduction for a better median one, on no
evidential basis.

**Classification: UNRESOLVED.** The failure is specific and reproducible — median
causality from USD/GBP — and three candidate causes were tested and excluded. The
remaining candidates (the gold/oil proxy, D7, and `q`) are consistent with it but
none is demonstrated. No parameter was adjusted to close the gap.

---

## 6b. The Sup-Wald power comparison (Figure 4) — NOT reproduced

The paper states (Sec. 4) that "the subsampling S_T test considerably outperforms
the Sup-Wald procedure in terms of power". **We do not reproduce this**, and the
reason is specific.

| Quantity | Paper (digitised) | Ours |
|---|---:|---:|
| Sup-Wald size at c = 0 | 0.026 | 0.044 |
| S_T size at c = 0 | ~0.05 | 0.060 |
| S_T more powerful than Sup-Wald (c > 0) | 19/40 points | 15/72 points |

Two separate observations:

1. **Our Sup-Wald is correctly sized where the paper's is undersized** (0.044 vs
   0.026 against a 0.05 nominal level). A test that under-rejects under the null
   also under-rejects under the alternative, so an undersized Sup-Wald will look
   less powerful. This traces directly to an `OUR_ASSUMPTION`: the paper never
   says which Sup-Wald critical values it used, so we simulate them from the
   limiting law (`sup_τ B(τ)²/(τ(1−τ))`, giving 8.741). A more conservative
   tabulated value would reproduce the paper's undersizing.

2. **The paper's own figures do not support the blanket claim.** Comparing its
   Fig. 1–3 curves against its Fig. 4 curves, digitised the same way, S_T is
   higher only at small `c` and Sup-Wald overtakes as `c` grows:

   | c | 0.01 | 0.03 | 0.06 | 0.12 | 0.24 | 0.50 |
   |---|---|---|---|---|---|---|
   | S_T higher at | 5/7 | 4/6 | 6/8 | 3/7 | 1/7 | 0/5 |

   Averaged over the design the two are nearly level (T=100: 0.318 vs 0.331;
   T=500: 0.498 vs 0.519). The paper's claim holds near the null, which is where
   its DGPs concentrate, but not across the grid.

**Classification: UNRESOLVED, partially attributable to `OUR_ASSUMPTION`.** A
clean test would need a *size-adjusted* power comparison — calibrating both tests
to the same empirical size before comparing power — which the paper does not do
and which our stored rejection rates do not permit after the fact. We did not
adjust our critical values to recover the paper's conclusion.

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
