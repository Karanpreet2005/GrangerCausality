# Reproduction comparison - Troster (2018)

*Testing for Granger-causality in quantiles*, Econometric Reviews 37(8), 850-866. DOI 10.1080/07474938.2016.1172400.

> PROFILE=full - full reproduction at the paper's settings

## Table 1 - summary statistics

8/21 statistics match at the paper's printed 2 dp; 21/21 within relative tolerance.

| Series | Statistic | Paper | Reproduced | Difference | Matches at 2 dp |
|---|---|---:|---:|---:|:--:|
| gold | mean | 466.8900 | 466.4799 | -0.4101 | no |
| gold | std_dev | 282.8300 | 283.2785 | 0.4485 | no |
| gold | median | 382.7400 | 380.3346 | -2.4054 | no |
| gold | skewness | 0.6400 | 0.6378 | -0.0022 | yes |
| gold | kurtosis | 2.0400 | 2.0320 | -0.0080 | no |
| gold | minimum | 149.3900 | 149.2189 | -0.1711 | no |
| gold | maximum | 1101.4800 | 1104.7850 | 3.3050 | no |
| oil | mean | 65.3100 | 65.1380 | -0.1720 | no |
| oil | std_dev | 33.2300 | 32.9695 | -0.2605 | no |
| oil | median | 62.0600 | 62.1500 | 0.0900 | no |
| oil | skewness | 0.3200 | 0.3094 | -0.0106 | no |
| oil | kurtosis | 1.8100 | 1.8187 | 0.0087 | no |
| oil | minimum | 17.0000 | 16.5100 | -0.4900 | no |
| oil | maximum | 143.6000 | 143.9500 | 0.3500 | no |
| usdgbp | mean | 1.6700 | 1.6699 | -0.0001 | yes |
| usdgbp | std_dev | 0.1800 | 0.1828 | 0.0028 | yes |
| usdgbp | median | 1.6100 | 1.6123 | 0.0024 | yes |
| usdgbp | skewness | 0.4900 | 0.4910 | 0.0010 | yes |
| usdgbp | kurtosis | 2.0500 | 2.0525 | 0.0025 | yes |
| usdgbp | minimum | 1.3700 | 1.3658 | -0.0042 | yes |
| usdgbp | maximum | 2.1100 | 2.1104 | 0.0004 | yes |

## Table 2 - Granger-causality in mean

**Alignment `gold_offset`**: 12/12 cells agree at the 5% level.

| Cause | Effect | Lags | Paper p | Reproduced p | Same decision |
|---|---|---:|---:|---:|:--:|
| oil | gold | 1 | 0.314 | 0.650 | yes |
| oil | gold | 2 | 0.548 | 0.671 | yes |
| oil | gold | 3 | 0.097 | 0.799 | yes |
| usdgbp | gold | 1 | 0.965 | 0.301 | yes |
| usdgbp | gold | 2 | 0.749 | 0.350 | yes |
| usdgbp | gold | 3 | 0.821 | 0.233 | yes |
| gold | oil | 1 | 0.017 | 0.000 | yes |
| gold | oil | 2 | 0.014 | 0.000 | yes |
| gold | oil | 3 | 0.035 | 0.000 | yes |
| usdgbp | oil | 1 | 0.421 | 0.824 | yes |
| usdgbp | oil | 2 | 0.752 | 0.381 | yes |
| usdgbp | oil | 3 | 0.154 | 0.509 | yes |

**Alignment `primary`**: 4/12 cells agree at the 5% level.

| Cause | Effect | Lags | Paper p | Reproduced p | Same decision |
|---|---|---:|---:|---:|:--:|
| oil | gold | 1 | 0.314 | 0.013 | NO |
| oil | gold | 2 | 0.548 | 0.042 | NO |
| oil | gold | 3 | 0.097 | 0.068 | yes |
| usdgbp | gold | 1 | 0.965 | 0.000 | NO |
| usdgbp | gold | 2 | 0.749 | 0.000 | NO |
| usdgbp | gold | 3 | 0.821 | 0.000 | NO |
| gold | oil | 1 | 0.017 | 0.655 | NO |
| gold | oil | 2 | 0.014 | 0.338 | NO |
| gold | oil | 3 | 0.035 | 0.526 | NO |
| usdgbp | oil | 1 | 0.421 | 0.828 | yes |
| usdgbp | oil | 2 | 0.752 | 0.376 | yes |
| usdgbp | oil | 3 | 0.154 | 0.502 | yes |

Table 2 is only recovered under the one-row gold offset of resolution D8. That offset is reported, not adopted silently.

## Tables 3-4 - Granger-causality in quantiles

**Alignment `gold_offset`**: 123/144 cells agree at 5%, 93/144 at 1%.

| tau | Cells agreeing at 5% |
|---|---|
| 0.10 | 36/36 |
| 0.50 | 15/36 |
| 0.90 | 36/36 |
| [0.10;0.90] | 36/36 |

**Alignment `primary`**: 130/144 cells agree at 5%, 102/144 at 1%.

| tau | Cells agreeing at 5% |
|---|---|
| 0.10 | 36/36 |
| 0.50 | 22/36 |
| 0.90 | 36/36 |
| [0.10;0.90] | 36/36 |

Detail for the primary alignment at k = 3:

| Table | Cause | Effect | tau | Lags | Paper p | Reproduced p | Same decision |
|---|---|---|---|---:|---:|---:|:--:|
| table3 | oil | gold | 0.10 | 1 | 0.000 | 0.000 | yes |
| table3 | oil | gold | 0.10 | 2 | 0.000 | 0.000 | yes |
| table3 | oil | gold | 0.10 | 3 | 0.000 | 0.000 | yes |
| table3 | oil | gold | 0.50 | 1 | 0.294 | 0.054 | yes |
| table3 | oil | gold | 0.50 | 2 | 0.265 | 0.118 | yes |
| table3 | oil | gold | 0.50 | 3 | 0.323 | 0.525 | yes |
| table3 | oil | gold | 0.90 | 1 | 0.000 | 0.000 | yes |
| table3 | oil | gold | 0.90 | 2 | 0.000 | 0.000 | yes |
| table3 | oil | gold | 0.90 | 3 | 0.000 | 0.000 | yes |
| table3 | oil | gold | [0.10;0.90] | 1 | 0.000 | 0.000 | yes |
| table3 | oil | gold | [0.10;0.90] | 2 | 0.000 | 0.000 | yes |
| table3 | oil | gold | [0.10;0.90] | 3 | 0.000 | 0.000 | yes |
| table3 | usdgbp | gold | 0.10 | 1 | 0.011 | 0.000 | yes |
| table3 | usdgbp | gold | 0.10 | 2 | 0.010 | 0.000 | yes |
| table3 | usdgbp | gold | 0.10 | 3 | 0.006 | 0.000 | yes |
| table3 | usdgbp | gold | 0.50 | 1 | 0.004 | 0.023 | yes |
| table3 | usdgbp | gold | 0.50 | 2 | 0.006 | 0.020 | yes |
| table3 | usdgbp | gold | 0.50 | 3 | 0.007 | 0.084 | NO |
| table3 | usdgbp | gold | 0.90 | 1 | 0.010 | 0.000 | yes |
| table3 | usdgbp | gold | 0.90 | 2 | 0.007 | 0.000 | yes |
| table3 | usdgbp | gold | 0.90 | 3 | 0.013 | 0.000 | yes |
| table3 | usdgbp | gold | [0.10;0.90] | 1 | 0.000 | 0.000 | yes |
| table3 | usdgbp | gold | [0.10;0.90] | 2 | 0.000 | 0.000 | yes |
| table3 | usdgbp | gold | [0.10;0.90] | 3 | 0.000 | 0.000 | yes |
| table4 | gold | oil | 0.10 | 1 | 0.000 | 0.000 | yes |
| table4 | gold | oil | 0.10 | 2 | 0.000 | 0.000 | yes |
| table4 | gold | oil | 0.10 | 3 | 0.000 | 0.000 | yes |
| table4 | gold | oil | 0.50 | 1 | 0.461 | 0.432 | yes |
| table4 | gold | oil | 0.50 | 2 | 0.345 | 0.529 | yes |
| table4 | gold | oil | 0.50 | 3 | 0.384 | 0.506 | yes |
| table4 | gold | oil | 0.90 | 1 | 0.000 | 0.000 | yes |
| table4 | gold | oil | 0.90 | 2 | 0.000 | 0.000 | yes |
| table4 | gold | oil | 0.90 | 3 | 0.000 | 0.000 | yes |
| table4 | gold | oil | [0.10;0.90] | 1 | 0.000 | 0.000 | yes |
| table4 | gold | oil | [0.10;0.90] | 2 | 0.000 | 0.000 | yes |
| table4 | gold | oil | [0.10;0.90] | 3 | 0.000 | 0.000 | yes |
| table4 | usdgbp | oil | 0.10 | 1 | 0.011 | 0.000 | yes |
| table4 | usdgbp | oil | 0.10 | 2 | 0.010 | 0.000 | yes |
| table4 | usdgbp | oil | 0.10 | 3 | 0.006 | 0.000 | yes |
| table4 | usdgbp | oil | 0.50 | 1 | 0.005 | 0.298 | NO |
| table4 | usdgbp | oil | 0.50 | 2 | 0.006 | 0.559 | NO |
| table4 | usdgbp | oil | 0.50 | 3 | 0.006 | 0.433 | NO |
| table4 | usdgbp | oil | 0.90 | 1 | 0.010 | 0.000 | yes |
| table4 | usdgbp | oil | 0.90 | 2 | 0.006 | 0.000 | yes |
| table4 | usdgbp | oil | 0.90 | 3 | 0.012 | 0.000 | yes |
| table4 | usdgbp | oil | [0.10;0.90] | 1 | 0.000 | 0.000 | yes |
| table4 | usdgbp | oil | [0.10;0.90] | 2 | 0.000 | 0.000 | yes |
| table4 | usdgbp | oil | [0.10;0.90] | 3 | 0.000 | 0.000 | yes |

## Figures 1-4 - Monte Carlo

The paper reports these only as raster images (24 Image XObjects, 0 Form XObjects), so targets are digitised from the published curves; see `reporting/digitize.py`. Red curves are T = 500, black dashed T = 100.

104/138 digitised points reproduce within the traced band plus 0.05 tolerance. Mean absolute difference 0.084.

Size at c = 0 (nominal 0.05):

| Figure | DGP | T | Paper | Reproduced | Difference |
|---|---:|---:|---:|---:|---:|
| 1 | 1 | 100 | 0.073 | 0.060 | -0.013 |
| 1 | 1 | 500 | 0.054 | 0.049 | -0.004 |
| 1 | 3 | 500 | 0.029 | 0.057 | 0.028 |
| 2 | 1 | 100 | 0.073 | 0.052 | -0.022 |
| 2 | 1 | 500 | 0.057 | 0.037 | -0.021 |
| 2 | 2 | 100 | 0.068 | 0.071 | 0.003 |
| 2 | 2 | 500 | 0.057 | 0.062 | 0.005 |
| 2 | 3 | 100 | 0.081 | 0.073 | -0.008 |
| 2 | 3 | 500 | 0.066 | 0.058 | -0.008 |
| 3 | 4 | 100 | 0.070 | 0.067 | -0.003 |
| 3 | 4 | 500 | 0.057 | 0.052 | -0.005 |
| 3 | 4 | 500 | 0.056 | 0.054 | -0.002 |
| 4 | 1 | 100 | 0.028 | 0.051 | 0.023 |
| 4 | 1 | 500 | 0.015 | 0.041 | 0.026 |
| 4 | 2 | 500 | 0.019 | 0.038 | 0.019 |
| 4 | 3 | 500 | 0.039 | 0.035 | -0.003 |
| 4 | 4 | 100 | 0.037 | 0.050 | 0.013 |
| 4 | 4 | 500 | 0.019 | 0.046 | 0.027 |

The paper's central Monte Carlo claim is that S_T dominates Sup-Wald in power. Comparing mean rejection frequencies at matched design points:

- S_T has higher power at 15/72 design points with c > 0.
- Size at c = 0: S_T mean 0.060, Sup-Wald mean 0.045 (nominal 0.05); the paper describes Sup-Wald as undersized.

## Provenance of every choice

### PAPER_SPECIFIED (13)

| Item | Value | Source |
|---|---|---|
| Test statistic S_T | CvM norm of the quantile-marked process, eq. (11) | Sec. 2.1, eqs. (9)-(11) |
| Weighting measure F_omega | d-variate standard normal, giving the closed-form kernel | Sec. 2.1 |
| Subsample size | b = [k T^(2/5)], floor | Sec. 2.2; all nine printed b values reproduce exactly |
| Subsample count | B = T - b + 1 overlapping contiguous blocks | Sec. 2.2 step 1 |
| p-value rule | p = B^-1 sum 1(S_b,i > S_T), non-recentered | Sec. 2.2 step 2 (resolution D5) |
| Quantile grid | 20 equally spaced points on [0.10, 0.90] | Sec. 4 |
| Monte Carlo replications | 1,000 | Sec. 4 |
| Sample sizes T | 100, 250, 500 | Sec. 4 |
| Subsample constants k | 3, 4, 5 | Sec. 4 |
| DGPs 1-4 | eqs. (13)-(16) | Sec. 4 |
| Causality grid c | 0.00, 0.01, 0.03, 0.06, 0.12, 0.24, 0.50 | x-axis tick labels of Figs. 1-4, recovered by rasterising the PDF |
| Empirical sample | 3 July 2000 to 6 September 2013, T = 3,440 | Sec. 5 and Table 1 note |
| Empirical transform | log-differences | Sec. 5 |

### EXTERNALLY_RESOLVED (3)

| Item | Value | Source |
|---|---|---|
| sigma specification | constant sigma, not time-varying | Troster, Shahbaz & Uddin (2018), MPRA 84194, eq. (15) - resolution D2 |
| Error quantile function | standard normal inverse CDF; location-shift family | MPRA 84194, below eq. (15) - resolution D3 |
| QAR(3) specification | AR(3) + sigma Phi^-1(tau) | MPRA 84194, eq. (15) - resolution D4 |

### OUR_ASSUMPTION (8)

| Item | Value | Source |
|---|---|---|
| Lags q of Z in I_t | q = s | Tables 3-4 label only the lags of I^Y_t (decision C) |
| k for the empirical tables | all of 3, 4, 5 reported | never stated by the paper (decision B) |
| Standardisation of I_t before the kernel | standardised | not stated; unstandardised daily log-returns make the kernel ~0.9998 everywhere, i.e. numerically a matrix of ones - resolution D7 |
| Random seed | 20160604 | no seed is given anywhere in the paper |
| Monte Carlo burn-in | 100 observations, series started at zero | not stated |
| Mean causality test | SSR-based F test | Table 2 does not say which variant was used |
| ADF / KPSS settings | AIC lag selection; automatic bandwidth | not stated; library defaults chosen so nothing is tuned |
| Sup-Wald critical values | simulated from sup B(tau)^2/(tau(1-tau)) | the paper does not say which critical values it used |

### DEVIATION_FROM_PAPER (3)

| Item | Value | Source |
|---|---|---|
| Gold series | LBMA 15:00 gold fix x 0.583, in place of S&P GSCI Gold Spot | the paper's Datastream series is subscription-only; the proxy matches Table 1 to <=0.5% and the test is scale-invariant |
| Oil series | FRED Europe Brent Spot FOB, in place of Datastream Dated Brent | closest free equivalent; Table 1 minimum 16.51 vs 17.00 printed |
| Data alignment | same-date primary; one-row gold offset also reported | resolution D8 - the paper's Table 2 is only recovered under the offset |

## Resolutions of gaps and inconsistencies

| Tag | Issue | Resolution | Source |
|---|---|---|---|
| D1 | Sec. 5 text calls the gold series 'S&P gold prices (per ounce)' while the Table 1 note calls it the 'S&P GSCI Gold Spot price index'. Table 1's magnitudes (149-1101) match the index, not USD/oz (256-1895). | Treat it as the index. Immaterial for the test, which runs on log-differences and is therefore invariant to the scale factor. | Target paper, Sec. 5 and Table 1 note (p. 863), read against each other. |
| D2 | Eq. (17) writes a time-varying sigma_t but defines no volatility model. | Use a constant sigma as the primary specification; the 't' subscript is treated as a typographical artifact. An AR(p)-GARCH(1,1) variant is run as a sensitivity on the empirical tables only. | Troster, Shahbaz & Uddin (2018), MPRA 84194, eq. (15), which restates the same models as '... + sigma*Phi^-1(tau)' with theta(tau) = (mu0, mu1, mu2, mu3, sigma)'. |
| D3 | Eq. (17) does not say which error distribution Phi_eps^-1 refers to. | Standard normal. The model is therefore a location-shift family: the mu coefficients do not vary with tau, and one Gaussian ML fit serves the whole tau grid. Conditional quantile = fitted AR mean + sigma_hat * Phi^-1(tau). | Troster, Shahbaz & Uddin (2018), MPRA 84194, below eq. (15): 'Phi^-1(.) is the inverse of a standard normal distribution function'. |
| D4 | Tables 3-4 use a 3-lag column but eq. (17) defines only QAR(1) and QAR(2). | QAR(3) = AR(3) plus sigma*Phi^-1(tau), by direct extension. | Troster, Shahbaz & Uddin (2018), MPRA 84194, eq. (15), 'QAR3'. |
| D5 | The author's later paper describes p-values as 'averaging the subsample test statistics'; the target paper defines critical values through the subsample CDF G_hat, i.e. an average of indicators. | Follow the target paper: p = B^-1 * sum_i 1(S_{b,i} > S_T). | Target paper, Sec. 2.2, step 2. |
| D6 | The absolute value in eq. (11) is redundant. | Implemented as written. W is a real symmetric positive semi-definite Gaussian kernel and psi is real, so psi'W psi >= 0 always; a unit test asserts this. | Target paper, eq. (11); standard property of the Gaussian kernel. |
| D7 | The paper does not say whether the conditioning vector I_t is standardised before entering the kernel W_{t,s} = exp[-0.5 (I_t - I_s)^2]. This matters enormously for the empirical application: daily log-returns are O(0.01), so \|\|I_t - I_s\|\|^2 is O(1e-4) and the literal kernel is ~0.9998 everywhere, leaving W numerically indistinguishable from a matrix of ones. The Monte Carlo is unaffected because its DGPs already have unit variance. | Standardise each component of I_t to zero mean and unit variance by default, which is the usual practice for this family of characteristic-function tests. The unstandardised kernel is retained behind a flag and BOTH are reported for the empirical tables, so the choice is visible rather than assumed. | Our own numerical analysis of the empirical series (this is NOT resolved by any Troster paper). Escanciano & Velasco (2006), on whose construction eq. (11) is based, work with standardised regressors. |
| D8 | Table 2's direction of mean causality does not reproduce under face-value alignment. The paper reports gold -> oil significant (p = 0.017/0.014/0.035) and oil -> gold insignificant (0.314/0.548/0.097); rebuilding the series and aligning all three on the same trading date reverses this, giving oil -> gold significant and gold -> oil not. Only 4 of 12 Table 2 cells agree. | Diagnosed as a one-observation relative timing offset in the gold series, not a methodological error. Offsetting gold by a single trading day relative to oil and USD/GBP reproduces ALL 12 of Table 2's cells exactly, including both insignificant panels. This is consistent with the paper's Datastream gold series carrying information as of a later clock time than the LBMA 15:00 London fix (the S&P GSCI Gold index is futures-based and stamped at the US close), and/or with Datastream's date-stamping convention. Daily cross-market lead-lag results are exactly what such an offset moves. BOTH alignments are run and reported: offset 0 is the primary, literal reading; offset -1 is reported as the alignment under which the paper is recovered. The offset is NOT adopted silently to force agreement. | Our own diagnostic over relative offsets in {-1, 0, +1}, run against Table 2. The paper does not state the intraday timestamp of any series. |

