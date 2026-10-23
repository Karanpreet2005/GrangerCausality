# Robustness check: an independent, differently-specified method

This directory is **not part of the Troster (2018) reproduction**. It runs a
second, unrelated, peer-reviewed causality-in-quantiles method on the same
empirical data, to see whether an independently-coded test with a different
specification agrees on the qualitative pattern.

## What was checked, and why it is NOT a duplicate reproduction

While preparing this project, the R package
[`mqqcause`](https://cran.r-project.org/web/packages/mqqcause/index.html)
([source](https://github.com/merwanroudane/qqcaus)) surfaced as a possible prior
implementation of Troster's test. **It is not.** Reading its actual source
(`qq_causality()`, `qq_weights()`, `sup_wald()`) confirms it implements a
different method:

| | `mqqcause` | This reproduction (Troster 2018) |
|---|---|---|
| Method | Sim & Zhou (2015) quantile-on-quantile regression | Troster's parametric CvM omnibus test |
| Quantile grid | **2D**: τ (Y) × θ (X) — 19×19 = 361 cells by default | **1D**: τ (Y) only, 20 points |
| Model per cell | Locally-weighted QR of `Y` on `[1, X−X_θ, Y_lag]`, weighted by proximity of `X` to its θ-quantile | Parametric QAR(p): `Y` on its own lags, tested against `Z`'s lags via a moment condition |
| Significance | Per-cell bootstrap SE → t-value | Single omnibus statistic over the whole τ grid |
| Aggregate test | `sup_wald()`: max\|t\| over all 361 cells, **Bonferroni**-corrected, normal-approximation p-value | Subsampling-based critical value (`b = ⌊kT^(2/5)⌋`), the paper's actual contribution |

The package's README cites Troster (2018) only for the general idea of taking a
*sup over quantiles* as an aggregate summary — it credits the idea, not the
statistic. Its `sup_wald()` is closer in spirit to the **benchmark** Troster's
own paper compares against (his eq. 18) than to his proposed `S_T` test, and even
that resemblance is loose: `sup_wald()` here is a simple Bonferroni correction
over a finite grid of bootstrap t-tests, not Koenker–Machado's proper
Brownian-bridge-based Sup-Wald.

**No prior implementation of Troster's actual `S_T` statistic was found anywhere.**

## What was run

`run_qqcause_robustness.R` runs `qq_causality()` + `sup_wald()` on the exact same
data used throughout this reproduction (`data/processed/logdiff.csv` — the
identical gold/oil/USD-GBP log-returns, same four causal directions), at the
package's own default settings (19×19 grid, bandwidth 0.05, 200 bootstrap
replications).

```bash
Rscript robustness/run_qqcause_robustness.R
```

Requires R (installed here via `brew install r`) and the package, installed into
a local, gitignored library:

```bash
mkdir -p robustness/rlib
Rscript -e 'install.packages(c("mqqcause","farver"), repos="https://cloud.r-project.org", lib="robustness/rlib")'
```

## Results

| Direction | QQ-causality Sup\|t\| | Bonferroni p | Reject @ 5%? | Troster `S_T` at full grid [0.10;0.90] |
|---|---:|---:|:--:|:--:|
| oil → gold | 3.13 | 0.633 | **No** | **Reject** (p = 0.000) |
| usdgbp → gold | 3.85 | 0.043 | **Yes** | **Reject** (p = 0.000) |
| gold → oil | 3.43 | 0.221 | **No** | **Reject** (p = 0.000) |
| usdgbp → oil | 5.01 | 0.0002 | **Yes** | **Reject** (p = 0.000) |

Full per-cell grid: `output/qqcause_full_grid.csv` (4 × 361 rows). Aggregate
summary: `output/qqcause_sup_wald_summary.csv`.

### Reading it honestly

**Agreement:** both methods find significant causality from **USD/GBP** to both
gold and oil — and QQ-causality's finding survives a Bonferroni correction over
361 comparisons, which is a considerably harder bar to clear than Troster's
subsampling test. This is a genuine cross-method confirmation of the reproduction's
USD/GBP finding.

**Disagreement:** Troster's `S_T` rejects the null for **all four** directions at
the full [0.10;0.90] grid — the paper's result, which the reproduction matches
exactly (108/108 tail cells, see the main comparison report). QQ-causality does
**not** find the gold↔oil pair significant once its aggregate test is corrected
for multiple comparisons.

This is not evidence that the reproduction is wrong. The two aggregate tests are
not the same statistic under a shared null — Troster's subsampling critical value
is calibrated for one omnibus CvM statistic over a 20-point grid; a raw Bonferroni
correction over 361 independent-looking cells is a much more conservative bar, and
lower power against a real but modest effect is an expected consequence of that,
not necessarily a sign the effect doesn't exist. It is presented here as a
genuine, unresolved point of disagreement between two legitimate methods, not
explained away in either direction.
