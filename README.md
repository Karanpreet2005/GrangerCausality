# Reproducing Troster (2018), "Testing for Granger-causality in quantiles"

A clean-room reproduction of

> Troster, V. (2018). "Testing for Granger-causality in quantiles."
> *Econometric Reviews* 37(8), 850–866. DOI [10.1080/07474938.2016.1172400](https://doi.org/10.1080/07474938.2016.1172400)

**No code or data was released by the author** — see [§1 of the notes](REPRODUCTION_NOTES.md#1-there-is-no-author-code)
for the full search. Everything in `src/qgc/` is written from the paper's
equations, and every module docstring names the equation or section it implements.

```bash
make setup          # create .venv, install pinned dependencies
make test           # 29 tests, ~17 s
make quick          # smoke run, ~5 min  (NOT a reproduction)
make full           # full reproduction at the paper's settings
```

---

## 1. What the paper does

It proposes an **omnibus test of Granger-causality in quantiles**. Ordinary
Granger causality is tested in the conditional *mean*, which cannot see a
relationship that lives only in the tails. Troster's test looks across a whole
continuum of conditional quantiles instead.

The statistic is a Cramér–von Mises norm of a quantile-marked empirical process:

```
v_T(w, τ) = T^(−1/2) Σ_t ψ_{τ,t}(θ̂) exp(i w′I_t)          (eq. 9)
S_T       = ∫∫ |v_T(w, τ)|² dF_w(w) dF_τ(τ)                (eq. 10)
S_T       = (1/(Tn)) Σ_j | ψ_j′ W ψ_j |                    (eq. 11)
```

Because the weighting measure `F_w` is the d-variate standard normal, the integral
over `w` collapses to a closed-form Gaussian kernel `W_{t,s} = exp(−0.5‖I_t−I_s‖²)`
— eq. (11) is **exact**, not an approximation. The null distribution is
non-pivotal, so critical values come from subsampling with `b = ⌊k·T^(2/5)⌋`.

The paper then presents Monte Carlo evidence (Figs. 1–4) and an empirical
application to gold, Brent crude oil and the USD/GBP exchange rate (Tables 1–4).

## 2. Where the data comes from

The paper uses **Datastream**, which is subscription-only. All three series are
rebuilt from free public sources and validated against Table 1 *before* anything
else runs. Full detail in [`data/README.md`](data/README.md).

| Series | Source | Status |
|---|---|---|
| USD/GBP | FRED `DEXUSUK` | **exact** — matches all seven printed values at 2 dp |
| Oil | FRED `DCOILBRENTEU` | near-exact proxy for Platts Dated Brent |
| Gold | LBMA 15:00 fix × 0.583 | near-exact proxy for S&P GSCI Gold Spot |

The 0.583 factor is a **units conversion, not a fitted parameter**: the ratios
implied by Table 1's mean, minimum and maximum agree to ~0.4%, and the test runs on
log-differences so it is exactly scale-invariant. No p-value depends on it.

A business-day calendar with forward fill reproduces the paper's sample size
exactly: **3,440** observations over 2000-07-03 → 2013-09-06.

## 3. Installation

Requires Python 3.11+. On Apple Silicon nothing else is needed — no GPU, no
Homebrew packages.

```bash
make setup
# equivalently:
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

## 4. Running a quick test

```bash
python run_reproduction.py --quick        # or: make quick
python run_reproduction.py --full --dry-run   # plan + runtime estimates, runs nothing
```

`--quick` reduces **iteration counts and grid coverage only**. Sample sizes, the τ
grid, the estimator and the evaluation procedure are never reduced. Its outputs are
stamped `NOT A REPRODUCTION OF THE PAPER`, the profile name is part of every cache
key so a quick result can never satisfy a full run, and `compare.py` refuses to
emit a verdict unless the profile is `full`.

## 5. Running the full reproduction

```bash
python run_reproduction.py --full         # or: make full
```

Useful flags:

```bash
--stages data,empirical,mc,supwald,figures,compare   # run a subset
--force mc            # invalidate one stage; --force all for everything
--workers 8           # process pool size
--profile validation  # intermediate stability run
```

Stages are cached by a hash of the profile settings, input files and code version,
so re-running only redoes what actually changed.

## 6. Layout

```
run_reproduction.py     single entry point — orchestration only, no science
config/                 all tunable parameters; quick / validation / full profiles
                        paper_targets.yaml — Tables 1–4 transcribed verbatim
src/qgc/
  api.py                public API: granger_causality_in_quantiles(y, z, ...)
  data/providers/       FRED, LBMA, local CSV — swap sources without touching analysis
  data/datasets.py      declarative dataset specs; "troster2018" is one entry
  methods/kernel.py     Gaussian weighting matrix + zero-copy subsample blocks (eq. 11)
  methods/estimators/   pluggable quantile estimators; location-shift QAR is eq. (17)
  methods/statistic.py  S_T (eqs. 9–11)
  methods/subsampling.py b = ⌊kT^(2/5)⌋, B blocks, p-values (Sec. 2.2)
  methods/supwald.py    Koenker–Machado benchmark (eq. 18)
  methods/fast_qr.py    batched quantile regression; validated against statsmodels
  simulation/dgp.py     DGPs 1–4 (eqs. 13–16)
  experiments/          one module per table/figure
  reporting/            tables, figures, figure digitisation, comparison report
  provenance.py         every choice classified by where it came from
  _external_resolutions.py  the eight gaps D1–D8 and how each was resolved
tests/                  29 tests
results/                tables/, figures/, comparison.md
```

## 7. Which experiments are expensive

Measured on an **Apple M4 (Mac16,12), 10 cores (4P + 6E), 16 GB**:

| Stage | Measured runtime |
|---|---|
| data | seconds (downloads on first run) |
| empirical (Tables 2–4, both alignments, all k) | **30 s** |
| mc (Figs. 1–3, 168 cells × 1,000 reps) | **321 s** on 8 workers |
| supwald (Fig. 4, 168 cells × 1,000 reps) | **~15 min** on 8 workers |
| test suite | 17 s |

Two things make this cheap enough to run on a laptop. Subsamples are contiguous
windows, so subsample kernels are **zero-copy diagonal blocks** of the full kernel
rather than recomputed matrices; and the quantile model is a location-shift family,
so **one regression fit serves all 20 quantiles** and every window's fit comes from
running sums.

### Apple Silicon notes

- NumPy's Accelerate backend emits **spurious** `matmul` warnings on ordinary
  finite input. Verified harmless: results are bit-identical to a non-BLAS
  reference, max absolute difference exactly 0. Only those three messages are
  filtered; `assert_finite` still guards real values.
- BLAS threads are **pinned to 1 inside workers** — otherwise each worker's threads
  contend with every other worker and the pool runs *slower*.

## 8. Is external compute required?

**No.** Everything runs on the M4 laptop within about 20 minutes of compute. There
is no GPU path and none would help: the matrices are at most 129×129 and the work
is many tiny operations, so kernel-launch overhead would dominate. Peak memory is
the 3440² empirical kernel, ≈95 MB.

## 9. Where results appear

```
results/tables/*__full.csv|.md     one file per table, profile-stamped
results/figures/figure{1..4}__full.png   our figures, paper curves overlaid
results/figures/paper/             figures extracted from the PDF + digitised targets
results/comparison.md              the reproduction report
logs/                              per-run logs
```

## 10. How results are compared with the paper

`config/paper_targets.yaml` holds Tables 1–4 transcribed verbatim from the PDF with
page references, and is never written to by any code. `reporting/compare.py` joins
our output against it and writes `results/comparison.md`.

Figures are harder: the paper reports its Monte Carlo **only as raster images** (24
Image XObjects, zero Form XObjects — there are no vector coordinates to recover), so
targets are digitised from the published curves. The digitiser separates curves by
colour (red = T 500, black dashed = T 100) and reads the marker value at each tick.
Two **pre-declared** quality checks then flag tracing failures — curve spread, and
monotonicity of the plotted power curves in `c`. Failing points keep their raw value
and are marked `valid = False`; nothing is replaced with a better-agreeing number.

This is also how the causality grid `c` was recovered: the body text never states
it, but the x-axis tick labels read `0.00, 0.01, 0.03, 0.06, 0.12, 0.24, 0.50`.

Every modelling choice is classified in `src/qgc/provenance.py` as
`PAPER_SPECIFIED`, `EXTERNALLY_RESOLVED`, `OUR_ASSUMPTION` or
`DEVIATION_FROM_PAPER`, and unresolved discrepancies are labelled `UNRESOLVED`
rather than explained away.

## 11. Using this on your own data

The reproduction is one *configuration* of a general test, not a hard-wired script.

```python
from qgc import granger_causality_in_quantiles as gcq

res = gcq(y, z, lags=3)                 # τ grid [0.10, 0.90], 20 points
res = gcq(y, z, lags=1, tau=0.50)       # median only
res.p_value, res.statistic, res.reject(0.05)
```

Any two series, any frequency; nothing assumes the inputs are prices. To swap a
data source:

```python
from qgc.data import DATASETS, CsvFile
DATASETS["troster2018"].series["gold"] = CsvFile("data/raw/my_gsci_gold.csv")
```

Estimators are pluggable too — the paper permits Koenker–Bassett, Koenker–Xiao QAR
and CAViaR but implements none of them; see `src/qgc/methods/estimators/`.

---

## 12. Final reproducibility assessment

Run at the `full` profile: 168 Monte Carlo cells × 1,000 replications, 3,440
empirical observations, all three subsample constants, both data alignments.
29/29 tests pass. Full detail in [`results/comparison.md`](results/comparison.md)
and [`REPRODUCTION_NOTES.md`](REPRODUCTION_NOTES.md).

| Target | Outcome | Evidence |
|---|---|---|
| **Table 1** (summary statistics) | **Reproduced** | 21/21 within tolerance. USD/GBP — the one series from the paper's own underlying source — matches **all 7 printed values exactly at 2 dp**. Gold and oil differ only as documented proxies. |
| **Tables 3–4, tails and full grid** | **Reproduced exactly** | **108/108 cells**, every one printed as 0.000 and reproduced as 0.000, across τ = 0.10, τ = 0.90 and τ ∈ [0.10;0.90], all lags, all k. |
| **Tables 3–4, the headline median result** | **Reproduced** | The paper's central empirical claim — gold↔oil causality present in the tails, absent at the median — holds in 17/18 cells (gold→oil at τ=0.50: paper 0.397, ours 0.495). |
| **Tables 3–4, USD/GBP at τ = 0.50** | **Not reproduced** | 5/18 cells. The paper finds significant median causality from USD/GBP (p ≈ 0.006); we find borderline for gold (≈0.05) and none for oil (≈0.44). **UNRESOLVED** — `k` and alignment tested and excluded as causes. |
| **Table 2** (mean causality) | **Reproduced only under a data-alignment shift** | 4/12 at face value, **12/12** with a one-row gold offset (resolution D8). Diagnosed, reported, *not* silently adopted. |
| **Figures 1–3** (S_T size and power) | **Reproduced, approximately** | Against 138 QC-passing digitised points: median absolute difference **0.024**, 104/138 within the traced band. Size → nominal as T grows (T=100: 0.068, T=500: 0.054); power monotone in c in 72/72 series. |
| **Figure 4** (S_T beats Sup-Wald in power) | **Not reproduced** | S_T is more powerful at only 15/72 design points. Our Sup-Wald is correctly sized (0.044) where the paper's is undersized (0.026), which mechanically raises its power. **UNRESOLVED**, partly attributable to the unspecified Sup-Wald critical values. Notably, the paper's *own* digitised curves support its claim only at small c (5/7 at c=0.01, 0/5 at c=0.50). |

### Overall

**The method reproduces; the empirical headline reproduces; two secondary claims do
not.**

The test statistic, subsampling scheme and quantile model were recovered from the
paper alone and are independently validated: all nine printed subsample sizes match
exactly, the closed-form kernel matches numerical integration over ω, and empirical
size under the null lands at 0.05. Given that **no author code or data exists**, and
that both commodity series had to be rebuilt from free proxies, the empirical
agreement — 108/108 tail cells exact — is strong.

What does not reproduce is stated plainly rather than explained away: median
causality from USD/GBP (Tables 3–4), the mean-causality directions without a data
alignment shift (Table 2), and the Sup-Wald power comparison (Figure 4). Each is
classified `UNRESOLVED` with the candidate causes that were tested and excluded.

**No parameter, tolerance or critical value was tuned to improve agreement with the
paper.** Where a choice had to be made that the paper does not determine, it is
recorded in `src/qgc/provenance.py` as `OUR_ASSUMPTION` and, where feasible, both
alternatives are reported.
